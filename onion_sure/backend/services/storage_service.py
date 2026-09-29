"""
Image Storage Service Abstraction
Smart India Hackathon 2026 - Problem Statement PS26031

Decoupled storage provider supporting:
- Local filesystem storage (for development and edge devices)
- Extensible to MinIO / AWS S3 / Supabase
- SHA256 checksum calculation
- Never stores large raw binaries in PostgreSQL
"""

import os
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Tuple
import uuid

from ..config import settings


class BaseStorageProvider(ABC):
    @abstractmethod
    def store_file(self, content: bytes, filename: str, content_type: str = "image/jpeg") -> Tuple[str, str, int, str]:
        """Returns: (storage_key, bucket, size_bytes, sha256_hash)"""
        pass

    @abstractmethod
    def retrieve_file(self, storage_key: str) -> bytes:
        """Returns file content bytes."""
        pass


class LocalStorageProvider(BaseStorageProvider):
    def __init__(self, base_dir: Path = settings.STORAGE_LOCAL_DIR, bucket: str = settings.STORAGE_BUCKET):
        self.base_dir = base_dir
        self.bucket = bucket
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def store_file(self, content: bytes, filename: str, content_type: str = "image/jpeg") -> Tuple[str, str, int, str]:
        hasher = hashlib.sha256(content)
        sha256_hash = hasher.hexdigest()
        file_size = len(content)

        extension = Path(filename).suffix or ".jpg"
        unique_name = f"{uuid.uuid4().hex}{extension}"
        storage_key = str((self.base_dir / unique_name).as_posix())

        with open(storage_key, "wb") as f:
            f.write(content)

        return storage_key, self.bucket, file_size, sha256_hash

    def retrieve_file(self, storage_key: str) -> bytes:
        path = Path(storage_key)
        if not path.exists():
            path = self.base_dir / Path(storage_key).name
        if not path.exists():
            raise FileNotFoundError(f"File not found at storage key: {storage_key}")
        with open(path, "rb") as f:
            return f.read()


class ImageStorageService:
    def __init__(self, provider: BaseStorageProvider = None):
        self.provider = provider or LocalStorageProvider()

    def save_image(self, content: bytes, filename: str, content_type: str = "image/jpeg") -> Dict[str, Any]:
        storage_key, bucket, size_bytes, sha256_hash = self.provider.store_file(content, filename, content_type)
        return {
            "storage_key": storage_key,
            "bucket": bucket,
            "file_size_bytes": size_bytes,
            "sha256_hash": sha256_hash,
            "content_type": content_type,
            "filename": filename,
        }

    def save_file(self, content: bytes, filename: str, content_type: str = "application/octet-stream") -> Dict[str, Any]:
        return self.save_image(content, filename, content_type)

    def get_file(self, storage_key: str) -> bytes:
        return self.provider.retrieve_file(storage_key)


image_storage_service = ImageStorageService()
