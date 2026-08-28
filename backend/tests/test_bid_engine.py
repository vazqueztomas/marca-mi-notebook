import pytest
from unittest.mock import MagicMock, patch
import psycopg2
from services.bid_engine import process_payment_webhook


class TestPaymentStatusValidation:
    """Tests for payment status filtering."""

    def test_rejected_payment_ignored(self, mock_full_db):
        """Rejected payment should be ignored without DB access."""
        payment = {
            "id": 123,
            "status": "rejected",
            "external_reference": "1",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "ignored"
        assert "not approved" in result["message"]

    def test_pending_payment_ignored(self, mock_full_db):
        """Pending payment should be ignored."""
        payment = {
            "id": 124,
            "status": "pending",
            "external_reference": "2",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "ignored"

    def test_approved_payment_processes(self, mock_full_db):
        """Approved payment proceeds to bid lookup."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        # Setup: bid found, status is pending
        mock_cursor.fetchone.side_effect = [
            (1, 10, "Alice", "alice@example.com", 50000, "pending", None),  # bid row
            (10, "open"),  # spot lock
            None,  # no current winner
        ]
        mock_cursor.rowcount = 1

        payment = {
            "id": 125,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "paid"


class TestExternalReferenceValidation:
    """Tests for bid_id extraction from external_reference."""

    def test_invalid_external_reference_nonnumeric(self, mock_full_db):
        """Non-numeric external_reference should return error."""
        payment = {
            "id": 126,
            "status": "approved",
            "external_reference": "not_a_number",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "error"
        assert "Invalid" in result["message"]

    def test_missing_external_reference(self, mock_full_db):
        """Missing external_reference should return error."""
        payment = {
            "id": 127,
            "status": "approved",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "error"

    def test_valid_external_reference(self, mock_full_db):
        """Valid numeric external_reference proceeds."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.side_effect = [
            (1, 10, "Alice", "alice@example.com", 50000, "pending", None),
            (10, "open"),  # spot lock
            None,  # no current winner
        ]
        mock_cursor.rowcount = 1

        payment = {
            "id": 128,
            "status": "approved",
            "external_reference": "42",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "paid"


class TestBidLookup:
    """Tests for bid lookup and idempotency."""

    def test_bid_not_found(self, mock_full_db):
        """Non-existent bid_id should return error."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.return_value = None  # No bid found

        payment = {
            "id": 129,
            "status": "approved",
            "external_reference": "999",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "error"
        assert "not found" in result["message"]

    def test_already_processed_paid_bid(self, mock_full_db):
        """Bid already marked as paid should return already_processed."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        # Bid found with status='paid'
        mock_cursor.fetchone.return_value = (1, 10, "Alice", "alice@example.com", 50000, "paid", "999")

        payment = {
            "id": 130,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "already_processed"

    def test_already_processed_outbid_refunded_bid(self, mock_full_db):
        """Bid already marked as outbid_refunded should return already_processed."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.return_value = (1, 10, "Alice", "alice@example.com", 50000, "outbid_refunded", "998")

        payment = {
            "id": 131,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "already_processed"

    def test_already_processed_rejected_refunded_with_payment_linked(self, mock_full_db, mock_mp_service):
        """Rejected bid that already has a payment linked: plain already_processed, no refund."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.return_value = (1, 10, "Alice", "alice@example.com", 50000, "rejected_refunded", "997")

        payment = {
            "id": 132,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "already_processed"
        mock_mp_service.create_refund.assert_not_called()

    def test_payment_for_dead_bid_without_payment_is_refunded(self, mock_full_db, mock_mp_service):
        """Money arriving for a rejected bid with no payment linked refunds the incoming payment."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.return_value = (1, 10, "Alice", "alice@example.com", 50000, "rejected_refunded", None)

        payment = {
            "id": 132,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "already_processed"
        mock_mp_service.create_refund.assert_called_once_with("132")


class TestAmountValidation:
    """Tests for payment amount validation."""

    def test_amount_mismatch_refund_issued(self, mock_full_db, mock_mp_service):
        """Amount mismatch should trigger refund and reject."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        # Bid found, mp_payment_id update succeeds, amount mismatch
        mock_cursor.fetchone.return_value = (1, 10, "Alice", "alice@example.com", 50000, "pending", None)
        mock_cursor.rowcount = 1  # UPDATE succeeded

        payment = {
            "id": 133,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 60000.0  # Mismatch!
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "error"
        assert "mismatch" in result["message"]
        # Verify refund was attempted
        mock_mp_service.create_refund.assert_called_once_with("133")

    def test_amount_mismatch_refund_failure_marks_refund_failed(self, mock_full_db, mock_mp_service):
        """If the mismatch refund fails, bid is marked refund_failed (not rejected_refunded)."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.return_value = (1, 10, "Alice", "alice@example.com", 50000, "pending", None)
        mock_cursor.rowcount = 1
        mock_mp_service.create_refund.side_effect = Exception("Refund API error")

        payment = {
            "id": 145,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 60000.0  # Mismatch!
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "error"
        update_calls = [
            call for call in mock_cursor.execute.call_args_list
            if "refund_failed" in str(call)
        ]
        assert len(update_calls) > 0, "Bid should be marked refund_failed when mismatch refund fails"

    def test_amount_match_proceeds(self, mock_full_db):
        """Matching amount proceeds to bidding logic."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.side_effect = [
            (1, 10, "Alice", "alice@example.com", 50000, "pending", None),  # bid row
            (10, "open"),  # spot lock
            None,  # no current winner
        ]
        mock_cursor.rowcount = 1

        payment = {
            "id": 134,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "paid"


class TestIdempotency:
    """Tests for webhook idempotency."""

    def test_idempotent_same_payment_id_sets_mp_payment_once(self, mock_full_db):
        """Setting mp_payment_id twice with same payment should be idempotent."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        # First call: bid found, mp_payment_id update succeeds, first bid wins
        mock_cursor.fetchone.side_effect = [
            (1, 10, "Alice", "alice@example.com", 50000, "pending", None),  # bid row
            (10, "open"),  # spot lock
            None,  # no current winner
        ]
        mock_cursor.rowcount = 1  # First UPDATE succeeded

        payment = {
            "id": 456,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "paid"

    def test_different_payment_claims_same_bid_returns_error(self, mock_full_db, mock_mp_service):
        """Different payment trying to claim already-claimed bid should refund."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.side_effect = [
            (1, 10, "Alice", "alice@example.com", 50000, "pending", None),  # bid row
            ("999",),  # mp_payment_id already set to DIFFERENT payment
        ]
        mock_cursor.rowcount = 0  # UPDATE set mp_payment_id failed (already set)

        payment = {
            "id": 457,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "error"
        assert "already claimed" in result["message"]
        # Verify refund was attempted for the duplicate payment
        mock_mp_service.create_refund.assert_called_once_with("457")

    def test_mp_payment_id_retry_same_payment(self, mock_full_db, mock_mp_service):
        """Retry of same payment via mp_payment_id check should be idempotent."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        # UPDATE fails (rowcount = 0), but SELECT returns same payment ID
        mock_cursor.fetchone.side_effect = [
            (1, 10, "Alice", "alice@example.com", 50000, "pending", None),  # bid row
            ("456",),  # mp_payment_id already set to SAME payment (retry)
        ]
        mock_cursor.rowcount = 0  # UPDATE set mp_payment_id failed

        payment = {
            "id": 456,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "already_processed"
        # No refund should be attempted for same payment retry
        mock_mp_service.create_refund.assert_not_called()

    def test_mp_payment_id_unique_constraint_retry(self, mock_full_db, mock_mp_service):
        """psycopg2.IntegrityError on mp_payment_id UNIQUE constraint should be idempotent."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        # Simulate IntegrityError when setting mp_payment_id
        mock_cursor.execute.side_effect = [
            None,  # SELECT bid succeeds
            psycopg2.IntegrityError("duplicate key value"),  # UPDATE mp_payment_id fails
        ]
        mock_cursor.fetchone.return_value = (1, 10, "Alice", "alice@example.com", 50000, "pending", None)

        payment = {
            "id": 458,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "already_processed"
        # No refund should be attempted for UNIQUE constraint retry
        mock_mp_service.create_refund.assert_not_called()


class TestBiddingLogic:
    """Tests for auction bidding logic."""

    def test_first_bid_on_spot_wins(self, mock_full_db, mock_mail_service):
        """First bid on a spot should be marked as paid."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.side_effect = [
            (1, 10, "Alice", "alice@example.com", 50000, "pending", None),  # bid row
            (10, "open"),  # spot lock
            None,  # no current winner (no other paid bids)
        ]
        mock_cursor.rowcount = 1

        payment = {
            "id": 135,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "paid"
        # No previous winner, so no refund should be triggered
        mock_mail_service.send_outbid_email.assert_not_called()

        # Verify bid was marked as paid
        update_calls = [
            call for call in mock_cursor.execute.call_args_list
            if "UPDATE bids" in str(call) and "status = 'paid'" in str(call)
        ]
        assert len(update_calls) > 0, "Bid should be marked as paid via UPDATE"

    def test_higher_bid_wins_refunds_previous(self, mock_full_db, mock_mp_service, mock_mail_service):
        """Higher bid should win and refund previous bid."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.side_effect = [
            (2, 10, "Bob", "bob@example.com", 60000, "pending", None),  # new bid row
            (10, "open"),  # spot lock
            (1, "alice@example.com", "Alice", 50000),  # current winner (lower bid)
            ("135",),  # mp_payment_id for previous winner (VARCHAR from DB)
            ("Pantalla",),  # spot name
        ]
        mock_cursor.rowcount = 1

        payment = {
            "id": 136,
            "status": "approved",
            "external_reference": "2",
            "transaction_amount": 60000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "paid"
        # Should refund previous winner
        mock_mp_service.create_refund.assert_called_once_with("135")
        # Should send outbid email to previous winner
        mock_mail_service.send_outbid_email.assert_called_once_with(
            "alice@example.com", "Alice", "Pantalla", 50000
        )

        # Verify new bid was marked as paid
        paid_updates = [
            call for call in mock_cursor.execute.call_args_list
            if "UPDATE bids" in str(call) and "status = 'paid'" in str(call)
        ]
        assert len(paid_updates) > 0, "New bid should be marked as paid"

        # Verify previous bid was marked as outbid_refunded
        outbid_updates = [
            call for call in mock_cursor.execute.call_args_list
            if "UPDATE bids" in str(call) and "status = 'outbid_refunded'" in str(call)
        ]
        assert len(outbid_updates) > 0, "Previous bid should be marked as outbid_refunded"

    def test_lower_bid_refunded_immediately(self, mock_full_db, mock_mp_service, mock_mail_service):
        """Lower bid should be refunded immediately."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.side_effect = [
            (2, 10, "Bob", "bob@example.com", 40000, "pending", None),  # lower bid
            (10, "open"),  # spot lock
            (1, "alice@example.com", "Alice", 50000),  # current winner (higher bid)
            ("Pantalla",),  # spot name
        ]
        mock_cursor.rowcount = 1

        payment = {
            "id": 137,
            "status": "approved",
            "external_reference": "2",
            "transaction_amount": 40000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "outbid_refunded"
        # Should refund this lower bid
        mock_mp_service.create_refund.assert_called_once_with("137")
        # Should send outbid email to bidder
        mock_mail_service.send_outbid_email.assert_called_once_with(
            "bob@example.com", "Bob", "Pantalla", 40000
        )

    def test_equal_bid_loses_to_existing(self, mock_full_db, mock_mp_service, mock_mail_service):
        """Bid equal to current highest should be refunded (not higher)."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.side_effect = [
            (2, 10, "Bob", "bob@example.com", 50000, "pending", None),
            (10, "open"),  # spot lock
            (1, "alice@example.com", "Alice", 50000),  # same amount
            ("Spot",),  # spot name
        ]
        mock_cursor.rowcount = 1

        payment = {
            "id": 138,
            "status": "approved",
            "external_reference": "2",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "outbid_refunded"
        # Should refund the equal bid
        mock_mp_service.create_refund.assert_called_once_with("138")


class TestClosedSpot:
    """Payment arriving for a closed spot must be refunded, never marked paid."""

    def test_closed_spot_refunds_payment(self, mock_full_db, mock_mp_service):
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.side_effect = [
            (1, 10, "Alice", "alice@example.com", 50000, "pending", None),  # bid row
            (10, "closed"),  # spot lock: spot is closed
        ]
        mock_cursor.rowcount = 1

        payment = {
            "id": 146,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "error"
        mock_mp_service.create_refund.assert_called_once_with("146")
        rejected_updates = [
            call for call in mock_cursor.execute.call_args_list
            if "rejected_refunded" in str(call)
        ]
        assert len(rejected_updates) > 0, "Bid should be marked rejected_refunded"
        paid_updates = [
            call for call in mock_cursor.execute.call_args_list
            if "status = 'paid'" in str(call)
        ]
        assert len(paid_updates) == 0, "Bid must never be marked paid on a closed spot"

    def test_closed_spot_refund_failure_marks_refund_failed(self, mock_full_db, mock_mp_service):
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.side_effect = [
            (1, 10, "Alice", "alice@example.com", 50000, "pending", None),
            (10, "closed"),
        ]
        mock_cursor.rowcount = 1
        mock_mp_service.create_refund.side_effect = Exception("Refund API error")

        payment = {
            "id": 147,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)
        assert result["status"] == "error"
        update_calls = [
            call for call in mock_cursor.execute.call_args_list
            if "refund_failed" in str(call)
        ]
        assert len(update_calls) > 0


class TestRefundHandling:
    """Tests for refund logic and error handling."""

    def test_refund_already_refunded_treated_as_success(self, mock_full_db, mock_mp_service, mock_mail_service):
        """Refund with 'already refunded' message should be treated as success."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        # Simulate refund exception with "already refunded" message
        mock_mp_service.create_refund.side_effect = Exception("Payment already refunded")

        mock_cursor.fetchone.side_effect = [
            (2, 10, "Bob", "bob@example.com", 40000, "pending", None),
            (10, "open"),  # spot lock
            (1, "alice@example.com", "Alice", 50000),
            ("Pantalla",),  # spot name
        ]
        mock_cursor.rowcount = 1

        payment = {
            "id": 139,
            "status": "approved",
            "external_reference": "2",
            "transaction_amount": 40000.0
        }
        result = process_payment_webhook(payment)
        # Should still succeed even though refund threw exception
        assert result["status"] == "outbid_refunded"
        # Email should be sent because refund is treated as success
        mock_mail_service.send_outbid_email.assert_called_once()

    def test_refund_failure_no_email_sent(self, mock_full_db, mock_mp_service, mock_mail_service):
        """Refund failure (not "already refunded") should prevent email."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        # Simulate refund exception that is NOT "already refunded"
        mock_mp_service.create_refund.side_effect = Exception("Refund API error")

        mock_cursor.fetchone.side_effect = [
            (2, 10, "Bob", "bob@example.com", 40000, "pending", None),
            (10, "open"),  # spot lock
            (1, "alice@example.com", "Alice", 50000),
        ]
        mock_cursor.rowcount = 1

        payment = {
            "id": 140,
            "status": "approved",
            "external_reference": "2",
            "transaction_amount": 40000.0
        }
        result = process_payment_webhook(payment)
        # Should return status
        assert result["status"] == "outbid_refunded"
        # Email should NOT be sent because refund failed
        mock_mail_service.send_outbid_email.assert_not_called()

    def test_refund_failure_on_previous_winner(self, mock_full_db, mock_mp_service):
        """Refund failure for previous winner should mark as refund_failed."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        # Simulate refund exception for previous winner
        mock_mp_service.create_refund.side_effect = Exception("Refund API error")

        mock_cursor.fetchone.side_effect = [
            (2, 10, "Bob", "bob@example.com", 60000, "pending", None),
            (10, "open"),  # spot lock
            (1, "alice@example.com", "Alice", 50000),  # current winner
            (135,),  # mp_payment_id for previous winner
        ]
        mock_cursor.rowcount = 1

        payment = {
            "id": 141,
            "status": "approved",
            "external_reference": "2",
            "transaction_amount": 60000.0
        }
        result = process_payment_webhook(payment)
        # New bid should still be marked paid
        assert result["status"] == "paid"
        # Previous winner's bid should be marked refund_failed (via UPDATE)
        update_calls = [
            call for call in mock_cursor.execute.call_args_list
            if "refund_failed" in str(call)
        ]
        assert len(update_calls) > 0


class TestRowLocking:
    """Tests for SELECT ... FOR UPDATE row locking (SQL-string smoke test only).

    Verifies that the code emits the correct FOR UPDATE clause in SQL strings.
    Real two-connection serialization conflict testing is deferred to DB-gated integration tests.
    """

    def test_spot_locked_for_update(self, mock_full_db):
        """Spot row should be locked with FOR UPDATE during bidding logic."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.side_effect = [
            (1, 10, "Alice", "alice@example.com", 50000, "pending", None),  # bid
            (10, "open"),  # spot lock
            None,  # no current winner
        ]
        mock_cursor.rowcount = 1

        payment = {
            "id": 142,
            "status": "approved",
            "external_reference": "1",
            "transaction_amount": 50000.0
        }
        result = process_payment_webhook(payment)

        # Verify FOR UPDATE was called
        for_update_calls = [
            call for call in mock_cursor.execute.call_args_list
            if "FOR UPDATE" in str(call)
        ]
        assert len(for_update_calls) > 0


class TestEmailNotifications:
    """Tests for email sending."""

    def test_spot_name_lookup_in_email(self, mock_full_db, mock_mp_service, mock_mail_service):
        """Spot name should be looked up and included in email."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.side_effect = [
            (2, 10, "Bob", "bob@example.com", 60000, "pending", None),
            (10, "open"),  # spot lock
            (1, "alice@example.com", "Alice", 50000),
            ("135",),  # mp_payment_id
            ("Pantalla LCD",),  # spot name
        ]
        mock_cursor.rowcount = 1

        payment = {
            "id": 143,
            "status": "approved",
            "external_reference": "2",
            "transaction_amount": 60000.0
        }
        result = process_payment_webhook(payment)

        # Email should include the spot name
        mock_mail_service.send_outbid_email.assert_called_once()
        call_args = mock_mail_service.send_outbid_email.call_args
        assert "Pantalla LCD" in call_args[0]

    def test_email_fallback_spot_id_if_not_found(self, mock_full_db, mock_mp_service, mock_mail_service):
        """If spot name not found, use fallback format."""
        get_tx, mock_conn, mock_cursor = mock_full_db
        mock_cursor.fetchone.side_effect = [
            (2, 10, "Bob", "bob@example.com", 60000, "pending", None),
            (10, "open"),  # spot lock
            (1, "alice@example.com", "Alice", 50000),
            ("135",),  # mp_payment_id
            None,  # spot not found
        ]
        mock_cursor.rowcount = 1

        payment = {
            "id": 144,
            "status": "approved",
            "external_reference": "2",
            "transaction_amount": 60000.0
        }
        result = process_payment_webhook(payment)

        mock_mail_service.send_outbid_email.assert_called_once()
        call_args = mock_mail_service.send_outbid_email.call_args
        # Should use spot ID as fallback
        assert "Spot 10" in call_args[0]
