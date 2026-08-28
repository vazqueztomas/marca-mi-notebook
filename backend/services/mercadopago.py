from config import get_settings
from loguru import logger
import mercadopago
import uuid

settings = get_settings()


class MercadoPagoService:
    def __init__(self):
        sdk = mercadopago.SDK(settings.mercadopago_access_token)
        self.client = sdk

    def create_preference(self, spot_id: int, amount_ars: int, bidder_email: str, bidder_name: str) -> tuple[str, str]:
        """Create a Mercado Pago preference for payment.
        Returns: (preference_id, checkout_url)
        """
        preference_data = {
            "items": [
                {
                    "title": f"Sticker lugar #{spot_id}",
                    "quantity": 1,
                    "unit_price": float(amount_ars)
                }
            ],
            "payer": {
                "email": bidder_email,
                "name": bidder_name
            },
            "back_urls": {
                "success": f"{settings.frontend_url}/success",
                "failure": f"{settings.frontend_url}/failure",
                "pending": f"{settings.frontend_url}/pending"
            },
            "external_reference": f"spot_{spot_id}_{uuid.uuid4().hex[:8]}",
            "notification_url": f"{settings.backend_url}/api/webhooks/mercadopago",
            "sandbox_init_point": settings.mercadopago_sandbox
        }

        try:
            preference = self.client.preference().create(preference_data)
            preference_id = preference["response"]["id"]
            # In sandbox, init_point key exists; in prod, depends on MP SDK version
            checkout_url = preference["response"].get("init_point", preference["response"].get("sandbox_init_point"))
            logger.info(f"MP preference created: {preference_id}")
            return preference_id, checkout_url
        except Exception as e:
            logger.error(f"MP preference creation failed: {e}")
            raise


    def get_payment(self, payment_id: str) -> dict:
        """Fetch payment details from Mercado Pago.
        Returns payment object with id, external_reference, amount, status, etc.
        """
        try:
            payment = self.client.payment().get(payment_id)
            if not payment or payment.get("status") != 200:
                raise ValueError(f"MP payment fetch failed: {payment}")
            return payment["response"]
        except Exception as e:
            logger.error(f"Failed to fetch MP payment {payment_id}: {e}")
            raise

    def create_refund(self, payment_id: str) -> dict:
        """Create a refund for a payment via Mercado Pago.
        Returns refund response.
        """
        try:
            refund = self.client.refund().create(payment_id)
            if not refund or refund.get("status") not in [200, 201]:
                raise ValueError(f"MP refund creation failed: {refund}")
            logger.info(f"Refund created for payment {payment_id}")
            return refund["response"]
        except Exception as e:
            logger.error(f"Failed to refund payment {payment_id}: {e}")
            raise


mp_service = MercadoPagoService()
