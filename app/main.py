"""Aplicación FastAPI del Simulador de CO₂ Evitado RAEE.

Autoría del código: Leandro Damian Chumbita — Técnico Superior en Programación.
La organización configurable (ORG_NAME) es independiente de la autoría.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from app import AUTHOR, AUTHOR_TITLE, __version__
from app.core.config import BASE_DIR, get_settings
from app.core.database import init_db
from app.routes import api_router, catalog_router, scenarios_router, views_router
from app.seed import SEED_VERSION, seed_if_empty

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_if_empty()
    yield


app = FastAPI(
    title=settings.app_title,
    description="Estimaciones paramétricas de CO₂ evitado en la gestión de RAEE.",
    version=__version__,
    lifespan=lifespan,
)

app.include_router(api_router)
app.include_router(catalog_router)
app.include_router(scenarios_router)
app.include_router(views_router)


@app.get("/favicon.jpg", include_in_schema=False)
@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    """Sirve el favicon ubicado en la raíz del proyecto."""
    return FileResponse(BASE_DIR / "co2-favicon.jpg", media_type="image/jpeg")


@app.get("/co2-home.jpg", include_in_schema=False)
def co2_image() -> FileResponse:
    """Imagen de impacto ambiental usada en la portada."""
    return FileResponse(BASE_DIR / "co2-home.jpg", media_type="image/jpeg")


@app.get("/health", tags=["Sistema"])
def health() -> JSONResponse:
    """Verificación rápida de que la app inició y cargó la semilla."""
    return JSONResponse(
        {
            "status": "ok",
            "app": settings.app_title,
            "organization": settings.org_name,
            "db_path": settings.database_path.as_posix(),
            "seed_version": SEED_VERSION,
            "author": AUTHOR,
            "author_title": AUTHOR_TITLE,
        }
    )
