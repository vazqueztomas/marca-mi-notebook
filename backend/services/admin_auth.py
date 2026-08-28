import hashlib
import hmac
import secrets
import time

from config import get_settings

settings = get_settings()

SESSION_LIFETIME_SECONDS = 24 * 3600


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _sign(expiry_ts: str) -> str:
    return hmac.new(settings.webhook_secret.encode(), expiry_ts.encode(), hashlib.sha256).hexdigest()


def create_session(email: str) -> str:
    """Create stateless signed token (serverless-safe): '<expiry_ts>.<hmac>'."""
    expiry_ts = str(int(time.time()) + SESSION_LIFETIME_SECONDS)
    return f"{expiry_ts}.{_sign(expiry_ts)}"


def verify_session(token: str) -> dict | None:
    """Verify signed token, return session data or None."""
    expiry_ts, _, signature = token.partition(".")
    if not signature or not expiry_ts.isdigit():
        return None
    if not hmac.compare_digest(signature.encode(), _sign(expiry_ts).encode()):
        return None
    if int(expiry_ts) < time.time():
        return None
    return {"email": settings.admin_email, "expires_at": int(expiry_ts)}


def login_admin(password: str) -> str | None:
    """Verify admin password, return token if valid."""
    expected_hash = hash_password(settings.admin_password)
    provided_hash = hash_password(password)
    if secrets.compare_digest(expected_hash, provided_hash):
        return create_session(settings.admin_email)
    return None
