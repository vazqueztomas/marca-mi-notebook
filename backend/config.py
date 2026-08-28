from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""
    supabase_url: str
    supabase_key: str
    supabase_storage_bucket: str = "logos"

    mercadopago_access_token: str
    mercadopago_sandbox: bool = True

    resend_api_key: str
    # Resend allows onboarding@resend.dev for testing; set a verified domain in prod
    mail_from: str = "onboarding@resend.dev"

    admin_email: str
    admin_password: str
    webhook_secret: str

    # Comma-separated list — supports the vercel.app URL plus custom domain(s)
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"

    @property
    def frontend_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_url.split(",") if origin.strip()]

    # ISO timestamp, fixed once at launch — not recomputed on redeploy
    auction_ends_at: str = "2026-09-27T00:00:00Z"
    # ARS per USD, manually updated (dólar blue sell)
    ars_per_usd: float = 1555


@lru_cache
def get_settings() -> Settings:
    return Settings()
