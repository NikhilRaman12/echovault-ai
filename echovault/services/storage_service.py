"""Secure local storage service for audio, backups, and vault artifacts."""

import re
import hashlib
from pathlib import Path
from typing import Tuple
from echovault.config import config


class StorageSecurityError(Exception):
    """Raised when an unsafe file operation or path traversal is detected."""
    pass


class StorageService:
    def __init__(self, base_dir: Path = config.data_dir):
        self.base_dir = base_dir.resolve()
        self.audio_dir = config.audio_storage_dir.resolve()
        self.vault_dir = config.vault_storage_dir.resolve()
        self.backup_dir = config.backup_dir.resolve()
        
        for d in [self.base_dir, self.audio_dir, self.vault_dir, self.backup_dir]:
            d.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_sha256(data: str | bytes) -> str:
        """Compute SHA-256 hash for deduplication and integrity verification."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal and illegal characters."""
        clean = Path(filename).name
        clean = re.sub(r"[^\w\s\.-]", "", clean).strip()
        clean = re.sub(r"\s+", "_", clean)
        return clean or "unnamed_audio"

    def verify_sandbox(self, target_path: Path) -> Path:
        """Ensure path is within the allowed data sandbox directory."""
        resolved = target_path.resolve()
        if not str(resolved).startswith(str(self.base_dir)):
            raise StorageSecurityError(f"Path traversal detected: {target_path} is outside {self.base_dir}")
        return resolved

    def save_audio(self, file_bytes: bytes, original_name: str, memory_id: str) -> Tuple[Path, str, int]:
        """Save raw audio securely with memory ID prefix."""
        safe_name = self.sanitize_filename(original_name)
        ext = Path(safe_name).suffix.lower()
        if ext not in config.allowed_audio_extensions:
            raise ValueError(f"Unsupported audio format '{ext}'. Allowed: {config.allowed_audio_extensions}")
        
        target_path = self.audio_dir / f"{memory_id}_{safe_name}"
        self.verify_sandbox(target_path)
        
        target_path.write_bytes(file_bytes)
        sha256_hash = self.compute_sha256(file_bytes)
        return target_path, sha256_hash, len(file_bytes)

    def delete_file(self, file_path: str | Path) -> bool:
        """Safely delete a file inside the sandbox."""
        if not file_path:
            return False
        p = Path(file_path)
        if not p.is_absolute():
            p = self.base_dir / p
        try:
            resolved = self.verify_sandbox(p)
            if resolved.exists() and resolved.is_file():
                resolved.unlink()
                return True
        except Exception:
            return False
        return False


storage_service = StorageService()
