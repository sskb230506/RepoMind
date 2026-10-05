from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    WORKER_NAME: str = "repomind-worker"
    DATABASE_URL: str = (
        "postgresql://repomind_user:repomind_password@localhost:5432/repomind_db"
    )
    WORKER_POLL_INTERVAL: int = 5
    WORKER_LOG_LEVEL: str = "INFO"
    WORKER_CONCURRENCY: int = 2


worker_settings = WorkerSettings()
