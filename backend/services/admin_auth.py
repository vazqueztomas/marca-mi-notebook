import secrets
import hashlib
from datetime import datetime, timedelta
from config import get_settings

settings = get_settings()

# In-memory session store (for MVP; replace with Redis in prod)
_sessions: dict[str, dict] = {}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_session(email: str) -> str:
    """Create admin session, return token."""
    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        "email": email,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    return token

def verify_session(token: str) -> dict | None:
    """Verify session token, return session data or None."""
    session = _sessions.get(token)
    if not session:
        return None
    if datetime.utcnow() > session["expires_at"]:
        del _sessions[token]
        return None
    return session

def login_admin(password: str) -> str | None:
    """Verify admin password, return token if valid."""
    expected_hash = hash_password(settings.admin_password)
    provided_hash = hash_password(password)
    if expected_hash == provided_hash:
        return create_session(settings.admin_email)
    return None
