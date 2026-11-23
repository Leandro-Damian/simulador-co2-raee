"""Routers HTTP: API JSON y vistas HTML."""

from app.routes.api import router as api_router
from app.routes.catalog_api import router as catalog_router
from app.routes.scenarios_api import router as scenarios_router
from app.routes.views import router as views_router

__all__ = ["api_router", "catalog_router", "scenarios_router", "views_router"]
