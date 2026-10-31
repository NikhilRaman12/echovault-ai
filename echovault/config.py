"""Application configuration and environment management for EchoVault AI."""

import os
from pathlib import Path
from dataclasses import dataclass, field

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / os.getenv("ECHOVAULT_DATA_DIR", "data")
DB_PATH = Path(os.getenv("ECHOVAULT_DB_PATH", str(DATA_DIR / "echovault.db")))
AUDIO_STORAGE_DIR = DATA_DIR / "audio"
VAULT_STORAGE_DIR = DATA_DIR / "vault"
BACKUP_DIR = DATA_DIR / "backups"

@dataclass
class AppConfig:
    app_title: str = "EchoVault AI"
    tagline: str = "Some voices fade. Their stories don't have to."
    version: str = "0.1.0"
    
    # Paths
    base_dir: Path = BASE_DIR
    data_dir: Path = DATA_DIR
    db_path: Path = DB_PATH
    audio_storage_dir: Path = AUDIO_STORAGE_DIR
    vault_storage_dir: Path = VAULT_STORAGE_DIR
    backup_dir: Path = BACKUP_DIR
    
    # Ollama / Gemma Settings
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    gemma_model: str = os.getenv("GEMMA_MODEL", "gemma:2b")
    ollama_timeout_seconds: int = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "45"))
    ollama_max_retries: int = int(os.getenv("OLLAMA_MAX_RETRIES", "2"))
    
    # Limits & Audio
    max_audio_size_mb: int = int(os.getenv("MAX_AUDIO_SIZE_MB", "25"))
    whisper_model_size: str = os.getenv("WHISPER_MODEL_SIZE", "tiny")
    max_text_length_chars: int = 50000
    
    # Allowed formats
    allowed_audio_extensions: tuple = field(default_factory=lambda: (".wav", ".mp3", ".m4a", ".ogg", ".flac"))

    def ensure_directories(self) -> None:
        """Create storage directories if they do not exist."""
        for d in [self.data_dir, self.audio_storage_dir, self.vault_storage_dir, self.backup_dir]:
            d.mkdir(parents=True, exist_ok=True)

config = AppConfig()
config.ensure_directories()
