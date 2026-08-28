import pytest
from unittest.mock import MagicMock, patch, Mock
import psycopg2


@pytest.fixture
def mock_mp_service():
    """Mock Mercado Pago service."""
    with patch('services.bid_engine.mp_service') as mp_mock:
        mp_mock.create_refund = MagicMock(return_value={})
        yield mp_mock


@pytest.fixture
def mock_mail_service():
    """Mock mail service."""
    with patch('services.bid_engine.mail_service') as mail_mock:
        mail_mock.send_outbid_email = MagicMock(return_value=True)
        yield mail_mock


@pytest.fixture
def mock_full_db():
    """Full mock database context manager with proper nesting."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone = MagicMock()
    mock_cursor.fetchall = MagicMock(return_value=[])
    mock_cursor.rowcount = 1
    mock_cursor.execute = MagicMock()

    mock_conn = MagicMock()
    # Mock the cursor as a context manager
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=None)
    mock_conn.cursor = MagicMock(return_value=mock_cursor)
    mock_conn.commit = MagicMock()
    mock_conn.rollback = MagicMock()

    # Mock the connection as a context manager
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=None)

    with patch('services.bid_engine.get_transaction') as get_tx:
        # Make get_transaction return a context manager
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=mock_conn)
        cm.__exit__ = MagicMock(return_value=None)
        get_tx.return_value = cm
        yield get_tx, mock_conn, mock_cursor


@pytest.fixture
def payment_approved():
    """Base approved payment fixture."""
    return {
        "id": 123456,
        "status": "approved",
        "external_reference": "1",
        "transaction_amount": 50000.0
    }


@pytest.fixture
def payment_rejected():
    """Rejected payment fixture."""
    return {
        "id": 123457,
        "status": "rejected",
        "external_reference": "2",
        "transaction_amount": 50000.0
    }
