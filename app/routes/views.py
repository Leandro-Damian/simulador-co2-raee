from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app import AUTHOR, AUTHOR_TITLE
from app.core.config import get_settings

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))
settings = get_settings()


def _context(title: str, page_title: str) -> dict[str, Any]:
    return {
        "app_title": settings.app_title,
        "org_name": settings.org_name,
        "author": AUTHOR,
        "author_title": AUTHOR_TITLE,
        "title": title,
        "page_title": page_title,
    }


@router.get("/", include_in_schema=False)
def home(request: Request):
    """Portada de la aplicación con acceso rápido y guía de uso."""
    return templates.TemplateResponse(
        request=request, name="home.html", context=_context("Inicio", "Inicio")
    )


@router.get("/factores", include_in_schema=False)
def factors_panel(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="factors.html",
        context=_context("Factores", "Panel de Factores y Referencias"),
    )


@router.get("/calculadora", include_in_schema=False)
def quick_calculator(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="calculator.html",
        context=_context("Calculadora", "Calculadora rápida de CO₂ evitado"),
    )


@router.get("/catalogo", include_in_schema=False)
def catalog_panel(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="catalog.html",
        context=_context("Catálogo", "Catálogo extensible y composición (BOM)"),
    )


@router.get("/simulador", include_in_schema=False)
def simulator_panel(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="simulator.html",
        context=_context("Simulador", "Simulador de lotes y escenarios"),
    )


@router.get("/manual", include_in_schema=False)
def user_manual(request: Request):
    """Manual de Usuario dentro de la aplicación (Bloque 4)."""
    return templates.TemplateResponse(
        request=request,
        name="manual.html",
        context=_context("Manual", "Manual de Usuario"),
    )
