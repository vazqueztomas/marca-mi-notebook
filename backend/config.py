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

    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
