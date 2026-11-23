"""Carga de datos inicial."""

from app.seed.seed import SEED_VERSION, seed_database, seed_if_empty

__all__ = ["SEED_VERSION", "seed_database", "seed_if_empty"]
