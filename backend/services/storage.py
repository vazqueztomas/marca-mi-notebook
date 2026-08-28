import base64
from datetime import datetime
from ..config import get_settings
import httpx
from loguru import logger

settings = get_settings()

class SupabaseStorageClient:
    def __init__(self):
        self.base_url = f"{settings.supabase_url}/storage/v1"
        self.bucket = settings.supabase_storage_bucket
        self.auth_header = {
            "Authorization": f"Bearer {settings.supabase_key}"
        }

    async def upload_logo(self, file_bytes: bytes, original_filename: str) -> str:
        """Upload logo to Supabase Storage, return public URL."""
        # Sanitize filename
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        safe_name = f"logos/{timestamp}_{original_filename}"

        url = f"{self.base_url}/object/{self.bucket}/{safe_name}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                content=file_bytes,
                headers={
                    **self.auth_header,
                    "Content-Type": "application/octet-stream"
                }
            )

        if response.status_code != 200:
            logger.error(f"Storage upload failed: {response.text}")
            raise Exception(f"Failed to upload logo: {response.status_code}")

        public_url = f"{settings.supabase_url}/storage/v1/object/public/{self.bucket}/{safe_name}"
        logger.info(f"Logo uploaded: {public_url}")
        return public_url

# Singleton instance
storage_client = SupabaseStorageClient()
