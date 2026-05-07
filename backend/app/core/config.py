from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Reusable YOLO Vision Platform"
    app_env: str = "local"
    secret_key: str = "change-this-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    database_url: str = "sqlite:///./yolo_web.db"
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    admin_username: str = "admin"
    admin_password: str = "admin123456"
    upload_dir: str = "../storage/uploads"
    result_dir: str = "../storage/results"
    model_dir: str = "../storage/models"
    default_model_path: str = ""
    confidence_threshold: float = 0.25
    video_sample_fps: int = 2
    task_max_retries: int = 2
    stream_frame_timeout_seconds: int = 30
    max_upload_mb: int = 512

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.backend_cors_origins.split(",") if item.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("sqlite:///./"):
            relative = self.database_url.removeprefix("sqlite:///./")
            return f"sqlite:///{(self.backend_root / relative).as_posix()}"
        return self.database_url

    @property
    def backend_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return (self.backend_root / path).resolve()

    @property
    def uploads_path(self) -> Path:
        return self.resolve_path(self.upload_dir)

    @property
    def results_path(self) -> Path:
        return self.resolve_path(self.result_dir)

    @property
    def models_path(self) -> Path:
        return self.resolve_path(self.model_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
