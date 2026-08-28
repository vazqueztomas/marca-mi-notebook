import re
from datetime import datetime
from pathlib import Path

import httpx
from loguru import logger

from config import get_settings

settings = get_settings()


class StorageUploadError(Exception):
    pass


class SupabaseStorageClient:
    def __init__(self):
        self.base_url = f"{settings.supabase_url}/storage/v1"
        self.bucket = settings.supabase_storage_bucket
        self.auth_header = {
            "Authorization": f"Bearer {settings.supabase_key}",
            "apikey": settings.supabase_key,
        }

    async def upload_logo(self, file_bytes: bytes, original_filename: str) -> str:
        """Upload logo to Supabase Storage, return public URL."""
        # Sanitize: keep only the basename, replace anything unsafe
        base = re.sub(r"[^A-Za-z0-9._-]", "_", Path(original_filename).name)
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        safe_name = f"logos/{timestamp}_{base}"

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

        if response.status_code not in (200, 201):
            logger.error(f"Storage upload failed: {response.text}")
            raise StorageUploadError(f"Failed to upload logo: {response.status_code}")

        public_url = f"{settings.supabase_url}/storage/v1/object/public/{self.bucket}/{safe_name}"
        logger.info(f"Logo uploaded: {public_url}")
        return public_url

# Singleton instance
storage_client = SupabaseStorageClient()
