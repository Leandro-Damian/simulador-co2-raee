from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# app/core/config.py -> parents[0]=core, parents[1]=app, parents[2]=raíz del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Parámetros de la aplicación, sobreescribibles mediante variables de entorno o .env."""

    app_title: str = "Simulador de CO₂ Evitado RAEE"
    org_name: str = "Electrogreem S.R.L."
    db_path: str = "data/simulador_co2.db"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def database_path(self) -> Path:
        path = Path(self.db_path)
        return path if path.is_absolute() else BASE_DIR / path

    @property
    def database_url(self) -> str:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{self.database_path.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
