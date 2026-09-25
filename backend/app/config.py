from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_prefix="ARES_", extra="ignore")

    db_path: str = "data/ares.db"
    chroma_path: str = "data/chroma_db"
    upload_dir: str = "data/uploads"

    ollama_host: str = "http://localhost:11434"
    llm_model: str = "mistral"
    embed_model: str = "nomic-embed-text"

    jwt_secret: str = "change-me"
    token_expire_minutes: int = 720

    top_k: int = 6
    max_routed_files: int = 3
    chroma_batch_size: int = 250
    cache_ttl_seconds: int = 300

    @property
    def db_file(self) -> Path:
        return (BASE_DIR / self.db_path).resolve()

    @property
    def chroma_dir(self) -> Path:
        return (BASE_DIR / self.chroma_path).resolve()

    @property
    def uploads_dir(self) -> Path:
        return (BASE_DIR / self.upload_dir).resolve()


settings = Settings()
settings.db_file.parent.mkdir(parents=True, exist_ok=True)
settings.chroma_dir.mkdir(parents=True, exist_ok=True)
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
