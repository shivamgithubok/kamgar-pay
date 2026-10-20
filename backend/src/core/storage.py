import os
import shutil
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional, Tuple

from fastapi import HTTPException, UploadFile, status

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
}

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

BASE_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


class BaseStorageProvider(ABC):
    @abstractmethod
    def save_worker_file(self, worker_id: str, upload_file: UploadFile) -> Tuple[str, str, int, str]:
        """Saves a file for a worker. Returns (storage_path, unique_file_name, file_size, mime_type)."""
        pass

    @abstractmethod
    def delete_file(self, storage_path: str) -> bool:
        """Deletes a file given its storage_path. Returns True if deleted."""
        pass

    @abstractmethod
    def get_absolute_path(self, storage_path: str) -> Optional[Path]:
        """Gets absolute Path if local storage."""
        pass


class LocalStorageProvider(BaseStorageProvider):
    def __init__(self, base_dir: Path = BASE_UPLOAD_DIR):
        self.base_dir = base_dir

    def _validate_file(self, upload_file: UploadFile) -> str:
        filename = upload_file.filename or ""
        ext = os.path.splitext(filename)[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension '{ext}'. Allowed formats: PDF, JPG, PNG",
            )

        mime_type = upload_file.content_type or ""
        if mime_type not in ALLOWED_MIME_TYPES and ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{mime_type}'. Allowed formats: PDF, JPG, PNG",
            )

        return ext

    def save_worker_file(self, worker_id: str, upload_file: UploadFile) -> Tuple[str, str, int, str]:
        ext = self._validate_file(upload_file)
        unique_file_name = f"{uuid.uuid4().hex}{ext}"

        worker_dir = self.base_dir / "workers" / worker_id
        worker_dir.mkdir(parents=True, exist_ok=True)

        destination_path = worker_dir / unique_file_name

        file_size = 0
        try:
            with open(destination_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
            file_size = destination_path.stat().st_size
        except Exception as exc:
            if destination_path.exists():
                destination_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file to storage",
            ) from exc

        if file_size > MAX_FILE_SIZE_BYTES:
            destination_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({file_size / (1024*1024):.2f}MB) exceeds maximum limit of 10MB",
            )

        relative_storage_path = f"workers/{worker_id}/{unique_file_name}"
        mime_type = upload_file.content_type or "application/octet-stream"

        return relative_storage_path, unique_file_name, file_size, mime_type

    def delete_file(self, storage_path: str) -> bool:
        file_path = self.base_dir / storage_path
        if file_path.exists() and file_path.is_file():
            try:
                file_path.unlink()
                return True
            except OSError:
                return False
        return False

    def get_absolute_path(self, storage_path: str) -> Optional[Path]:
        file_path = (self.base_dir / storage_path).resolve()
        # Security check: ensure path is inside base_dir
        if not str(file_path).startswith(str(self.base_dir.resolve())):
            return None
        if file_path.exists() and file_path.is_file():
            return file_path
        return None


# Default instance
storage_provider = LocalStorageProvider()
