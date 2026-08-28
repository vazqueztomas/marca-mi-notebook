from config import get_settings
from loguru import logger
import resend

settings = get_settings()


class MailService:
    def __init__(self):
        resend.api_key = settings.resend_api_key

    def send_outbid_email(self, bidder_email: str, bidder_name: str, spot_name: str, amount_ars: int) -> bool:
        """Send 'you've been outbid' email to previous bid winner.
        Returns True if email sent successfully, False on failure."""
        try:
            resend.Emails.send({
                "from": settings.mail_from,
                "to": [bidder_email],
                "subject": f"¡Te superaron en {spot_name}!",
                "html": f"""
                <p>Hola {bidder_name},</p>
                <p>Alguien acaba de ofertar más alto en <strong>{spot_name}</strong>.</p>
                <p>Te devolvimos automáticamente tu puja de ${amount_ars:,} ARS.</p>
                <p><a href="{settings.frontend_url}">Volvé a competir</a></p>
                <p>¡Suerte!</p>
                """
            })
            logger.info(f"Outbid email sent to {bidder_email} for {spot_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to send outbid email to {bidder_email}: {e}")
            return False


mail_service = MailService()
