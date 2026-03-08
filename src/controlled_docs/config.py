from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass(slots=True)
class AppConfig:
    app_env: str = "development"
    database_url: str = "sqlite:///./artifacts/controlled_docs.db"
    embedding_backend: str = "local"
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 110
    chunk_overlap: int = 25
    retrieval_top_k: int = 5
    log_level: str = "INFO"
    review_window_days: int = 365
    config_path: Path | None = None

    @classmethod
    def from_env(cls, env_path: str | None = ".env", yaml_path: str | None = None) -> "AppConfig":
        if env_path:
            load_dotenv(env_path, override=False)

        path_value = yaml_path or os.getenv("CONFIG_PATH")
        yaml_values: dict[str, Any] = {}
        if path_value:
            config_path = Path(path_value)
            if config_path.exists():
                yaml_values = yaml.safe_load(config_path.read_text()) or {}
            else:
                raise FileNotFoundError(f"Config path does not exist: {config_path}")
        else:
            config_path = None

        def get_value(key: str, default: Any) -> Any:
            env_value = os.getenv(key)
            if env_value not in (None, ""):
                return env_value
            return yaml_values.get(key.lower(), default)

        return cls(
            app_env=get_value("APP_ENV", "development"),
            database_url=get_value("DATABASE_URL", "sqlite:///./artifacts/controlled_docs.db"),
            embedding_backend=get_value("EMBEDDING_BACKEND", "local"),
            openai_api_key=get_value("OPENAI_API_KEY", None),
            openai_embedding_model=get_value("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            chunk_size=int(get_value("CHUNK_SIZE", 110)),
            chunk_overlap=int(get_value("CHUNK_OVERLAP", 25)),
            retrieval_top_k=int(get_value("RETRIEVAL_TOP_K", 5)),
            log_level=str(get_value("LOG_LEVEL", "INFO")).upper(),
            review_window_days=int(get_value("REVIEW_WINDOW_DAYS", 365)),
            config_path=config_path,
        )

