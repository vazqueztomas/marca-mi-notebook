from config import get_settings
from loguru import logger
from resend import Resend

settings = get_settings()


class MailService:
    def __init__(self):
        self.resend = Resend(api_key=settings.resend_api_key)

    def send_outbid_email(self, bidder_email: str, bidder_name: str, spot_name: str, amount_ars: int):
        """Send 'you've been outbid' email to previous bid winner."""
        try:
            self.resend.emails.send({
                "from": "noreply@marchami-notebook.com",
                "to": bidder_email,
                "subject": f"¡Te superaron en {spot_name}!",
                "html": f"""
                <p>Hola {bidder_name},</p>
                <p>Alguien acaba de ofertar más alto en <strong>{spot_name}</strong>.</p>
                <p>Te devolvimos automáticamente tu puja de ${amount_ars:,} ARS.</p>
                <p><a href="https://marcha-mi-notebook.com">Volvé a competir</a></p>
                <p>¡Suerte!</p>
                """
            })
            logger.info(f"Outbid email sent to {bidder_email} for {spot_name}")
        except Exception as e:
            logger.error(f"Failed to send outbid email to {bidder_email}: {e}")
            # Don't raise — mail failure shouldn't block the bid flow


mail_service = MailService()
