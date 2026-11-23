"""Semilla inicial idempotente del Simulador de CO₂ Evitado RAEE.

Incluye:
  - catálogo completo de categorías/subcategorías RAEE y reglas de recepción;
  - fracciones por peso (con fracción comodín "Otros") y factores de referencia;
  - atributos dinámicos, BOM editable y componentes sueltos;
  - ejemplo Lenovo ThinkCentre M82 SFF y un escenario de demostración.

Los valores de factores son estimaciones paramétricas: se ajustan en el
Panel de Factores y Referencias (Bloque 2).
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import (
    AcceptanceRule,
    AttributeDef,
    AttributeValue,
    Brand,
    Category,
    Component,
    Equivalence,
    EquipmentModel,
    Factor,
    Fraction,
    Scenario,
    ScenarioItem,
    SeedMeta,
    Subcategory,
)

SEED_VERSION = 3

# ---------------------------------------------------------------------------
# Catálogo RAEE
# ---------------------------------------------------------------------------

CATEGORIES: list[dict[str, Any]] = [
    {
        "code": "INFORMATICA",
        "name": "Informática y oficina",
        "description": "Equipos de cómputo, impresión y periféricos de oficina.",
        "subcategories": [
            "Computadoras de escritorio",
            "Notebooks",
            "Servidores",
            "Monitores",
            "Impresoras",
            "Fotocopiadoras",
            "Escáneres",
            "Teclados",
            "Mouses",
            "Webcams",
            "Calculadoras",
            "Teléfonos fijos e inalámbricos",
            "Posnets",
            "Destructores de papel",
            "Placas electrónicas",
            "UPS",
            "Periféricos y accesorios de oficina",
        ],
    },
    {
        "code": "TELECOMUNICACIONES",
        "name": "Telefonía, redes y telecomunicaciones",
        "description": "Equipos de red, telefonía, transmisión e instrumentación.",
        "subcategories": [
            "Switches",
            "Routers y módems",
            "Equipos de red",
            "Centrales telefónicas",
            "Antenas",
            "Repetidores",
            "Equipos de transmisión",
            "Equipos de telecomunicaciones",
            "Instrumentos de medición",
        ],
    },
    {
        "code": "AUDIO_VIDEO",
        "name": "Audio, video y entretenimiento",
        "description": "Recepción, reproducción y amplificación de audio y video.",
        "subcategories": [
            "Televisores",
            "Radios",
            "Videocámaras",
            "Proyectores",
            "Reproductores DVD/Blu-ray",
            "Amplificadores y ecualizadores",
            "Equipos de sonido",
            "Parlantes",
            "Consolas y videojuegos",
            "Instrumentos musicales",
            "Juguetes electrónicos",
            "Equipos deportivos electrónicos",
        ],
    },
    {
        "code": "ILUMINACION",
        "name": "Iluminación",
        "description": "Solo tecnología LED o halógena/incandescente tradicional. Se rechaza mercurio.",
        "subcategories": [
            "Lámparas LED",
            "Luminarias LED",
            "Lámparas halógenas e incandescentes",
            "Luminarias halógenas/incandescentes tradicionales",
            "Lámparas de descarga y sodio (sin mercurio)",
            "Otros aparatos para difundir o controlar la luz",
        ],
    },
    {
        "code": "REFRIGERACION_CLIMATIZACION",
        "name": "Refrigeración y climatización",
        "description": "Frío doméstico/comercial, aire acondicionado y ventilación.",
        "subcategories": [
            "Heladeras",
            "Freezers",
            "Cavas de vino",
            "Frigobares",
            "Aires acondicionados",
            "Deshumidificadores",
            "Ventiladores",
        ],
    },
    {
        "code": "COCINA_ELECTRO",
        "name": "Cocina y pequeños electrodomésticos",
        "description": "Electrodomésticos de cocina y cuidado personal.",
        "subcategories": [
            "Cafeteras",
            "Pavas eléctricas",
            "Tostadoras",
            "Licuadoras",
            "Batidoras",
            "Procesadoras de alimentos",
            "Freidoras de aire",
            "Microondas",
            "Balanzas digitales",
            "Planchas",
            "Secadores de pelo",
            "Planchitas",
        ],
    },
    {
        "code": "HOGAR_LAVADO",
        "name": "Limpieza, lavado y hogar",
        "description": "Limpieza, lavado de ropa y herramientas eléctricas.",
        "subcategories": [
            "Aspiradoras tradicionales",
            "Aspiradoras robot",
            "Lavarropas",
            "Secarropas",
            "Lavavajillas",
            "Cocinas y hornos eléctricos",
            "Estufas eléctricas",
            "Máquinas de coser",
            "Taladros y sierras",
            "Herramientas de jardín y similares",
        ],
    },
    {
        "code": "SEGURIDAD_CONTROL",
        "name": "Seguridad y control",
        "description": "Vigilancia, control de acceso y alarmas.",
        "subcategories": [
            "Cámaras de seguridad (CCTV)",
            "DVR",
            "Porteros eléctricos",
            "Alarmas",
            "Timbres",
        ],
    },
    {
        "code": "SALUD",
        "name": "Aparatos médicos y diagnóstico",
        "description": "Uso doméstico no invasivo y equipamiento de diagnóstico.",
        "subcategories": [
            "Tensiómetros digitales",
            "Balanzas electrónicas",
            "Nebulizadores",
            "Monitores de pacientes",
            "Electrocardiógrafos",
            "Equipos de diagnóstico",
            "Otros instrumentos electrónicos médicos",
        ],
    },
    {
        "code": "ENERGIA_POTENCIA",
        "name": "Energía, fuentes y potencia",
        "description": "Fuentes, transformadores, estabilizadores y generación solar.",
        "subcategories": [
            "Fuentes switching genéricas",
            "Fuentes ATX",
            "Fuentes TFX",
            "Fuentes redundantes",
            "Transformadores",
            "Cargadores y adaptadores",
            "Estabilizadores de tensión",
            "Paneles solares",
            "Inversores",
            "Controladores de carga",
            "Reguladores electrónicos",
        ],
    },
    {
        "code": "CABLES_ACCESORIOS",
        "name": "Cables y accesorios",
        "description": "Cables de conexión y de alimentación directa al tomacorriente.",
        "subcategories": [
            "Cables HDMI",
            "Cables VGA",
            "Cables DVI",
            "Cables de alimentación a tomacorriente",
            "Cables de conexión",
            "Accesorios electrónicos",
        ],
    },
    {
        "code": "VARIOS",
        "name": "Otros RAEE",
        "description": "Comodín para equipos y componentes no clasificados arriba.",
        "subcategories": [
            "Equipos electrónicos varios",
            "Componentes electrónicos sueltos",
        ],
    },
]

# ---------------------------------------------------------------------------
# Factores y equivalencias (valores orientativos, editables en el Bloque 2)
# ---------------------------------------------------------------------------

FACTORS: list[dict[str, Any]] = [
    {
        "key": "default_reuse",
        "label": "CO₂ evitado por reutilización / reacondicionamiento (general)",
        "value": 2.5,
        "unit": "kg CO₂e/kg",
        "mode": "reuse",
        "source": "Estimación paramétrica interna",
        "note": "Valor por defecto para equipos. Ajustable desde el Panel de Factores.",
    },
    {
        "key": "default_recycling",
        "label": "CO₂ evitado por reciclaje / valorización (general)",
        "value": 1.2,
        "unit": "kg CO₂e/kg",
        "mode": "recycling",
        "source": "Estimación paramétrica interna",
        "note": "Se aplica a fracciones materiales recuperadas.",
    },
    {
        "key": "default_no_recovery",
        "label": "Sin recuperación",
        "value": 0.0,
        "unit": "kg CO₂e/kg",
        "mode": "no_recovery",
        "source": "Convención metodológica",
        "note": "No contabiliza CO₂ evitado: evita doble contabilidad.",
    },
    {
        "key": "material_copper",
        "label": "Cobre recuperado",
        "value": 3.0,
        "unit": "kg CO₂e/kg",
        "mode": "material",
        "source": "Estimación paramétrica interna",
        "note": "Aplicar al peso de la fracción cobre.",
    },
    {
        "key": "material_aluminum",
        "label": "Aluminio recuperado",
        "value": 2.0,
        "unit": "kg CO₂e/kg",
        "mode": "material",
        "source": "Estimación paramétrica interna",
        "note": "Aplicar al peso de la fracción aluminio.",
    },
    {
        "key": "material_abs",
        "label": "Plástico ABS recuperado",
        "value": 1.0,
        "unit": "kg CO₂e/kg",
        "mode": "material",
        "source": "Estimación paramétrica interna",
        "note": "Aplicar al peso de la fracción ABS.",
    },
    {
        "key": "material_hips",
        "label": "Plástico HIPS recuperado",
        "value": 0.9,
        "unit": "kg CO₂e/kg",
        "mode": "material",
        "source": "Estimación paramétrica interna",
        "note": "Aplicar al peso de la fracción HIPS.",
    },
    {
        "key": "material_pp",
        "label": "Plástico PP recuperado",
        "value": 0.8,
        "unit": "kg CO₂e/kg",
        "mode": "material",
        "source": "Estimación paramétrica interna",
        "note": "Aplicar al peso de la fracción PP.",
    },
    {
        "key": "material_pc",
        "label": "Plástico PC recuperado",
        "value": 1.1,
        "unit": "kg CO₂e/kg",
        "mode": "material",
        "source": "Estimación paramétrica interna",
        "note": "Aplicar al peso de la fracción PC.",
    },
    {
        "key": "material_other_metals",
        "label": "Otros metales recuperados",
        "value": 1.5,
        "unit": "kg CO₂e/kg",
        "mode": "material",
        "source": "Estimación paramétrica interna",
        "note": "Aplicar al peso de la fracción otros metales.",
    },
    {
        "key": "material_others",
        "label": "Otros materiales (comodín)",
        "value": 0.4,
        "unit": "kg CO₂e/kg",
        "mode": "material",
        "source": "Estimación paramétrica interna",
        "note": "Fracción comodín: conviene desagregarla cuando sea posible.",
    },
    # Bloque 4: fracciones RAEE adicionales. Se insertan como filas nuevas;
    # _get_or_create respeta cualquier edición previa del usuario.
    {
        "key": "material_glass",
        "label": "Vidrio recuperado",
        "value": 0.35,
        "unit": "kg CO₂e/kg",
        "mode": "material",
        "source": "Estimación paramétrica interna",
        "note": "Aplicar al peso de vidrio de pantallas y luminarias. Manejo con precauciones según revestimiento.",
    },
    {
        "key": "material_steel",
        "label": "Hierro / acero recuperado",
        "value": 1.1,
        "unit": "kg CO₂e/kg",
        "mode": "material",
        "source": "Estimación paramétrica interna",
        "note": "Aplicar a chasis, carcasas y estructuras metálicas ferrosas.",
    },
    {
        "key": "material_lithium_battery",
        "label": "Baterías de litio recuperadas",
        "value": 4.5,
        "unit": "kg CO₂e/kg",
        "mode": "material",
        "source": "Estimación paramétrica interna",
        "note": "Incluye recuperación de materiales críticos. Exige manipulación segura y descarte conforme a normativa local.",
    },
    {
        "key": "material_pcb",
        "label": "Placas PCB recuperadas",
        "value": 2.5,
        "unit": "kg CO₂e/kg",
        "mode": "material",
        "source": "Estimación paramétrica interna",
        "note": "Aplicar a placas de circuito impreso; excluye baterías y componentes peligrosos adheridos.",
    },
    {
        "key": "material_precious_metals",
        "label": "Metales preciosos recuperados",
        "value": 8.0,
        "unit": "kg CO₂e/kg",
        "mode": "material",
        "source": "Estimación paramétrica interna",
        "note": "Oro, plata y paladio en contactos y conectores. Valor muy dependiente de la composición real.",
    },
    {
        "key": "equivalence_car_km",
        "label": "Auto promedio: km por kg CO₂e",
        "value": 5.0,
        "unit": "km/kg CO₂e",
        "mode": "equivalence",
        "source": "Referencia general ~0,2 kg CO₂/km",
        "note": "Equivalencia ilustrativa para demostraciones.",
    },
    {
        "key": "equivalence_phone_charges",
        "label": "Cargas de teléfono por kg CO₂e",
        "value": 100.0,
        "unit": "cargas/kg CO₂e",
        "mode": "equivalence",
        "source": "Referencia general ~0,01 kg CO₂e/carga",
        "note": "Carga completa de un smartphone promedio.",
    },
    {
        "key": "equivalence_tree_year",
        "label": "Absorción anual de un árbol",
        "value": 1 / 21,
        "unit": "árbol·año/kg CO₂e",
        "mode": "equivalence",
        "source": "Referencia general ~21 kg CO₂e/año por árbol",
        "note": "1 kg CO₂e evitado equivale a 1/21 de la absorción anual de un árbol. Varía según especie, edad y entorno.",
    },
]

EQUIVALENCES: list[dict[str, Any]] = [
    {
        "label": "Kilómetros en auto promedio",
        "value": 5.0,
        "unit": "km por kg CO₂e",
        "note": "Equivalente a dejar de recorrer esa distancia en un auto promedio.",
    },
    {
        "label": "Cargas de teléfono",
        "value": 100.0,
        "unit": "cargas por kg CO₂e",
        "note": "Cargas completas de un smartphone promedio.",
    },
    {
        "label": "Absorción anual de árboles",
        "value": 1 / 21,
        "unit": "árbol·año por kg CO₂e",
        "note": "Orientativo: 1 árbol absorbe ~21 kg CO₂e por año; la absorción real depende de especie, edad y entorno.",
    },
]

# Corrección aplicada al actualizar de seed v1 a v2 (la v1 guardaba 21 kg/año,
# que es la absorción del árbol y no el factor por kg CO₂e evitado).
FACTOR_FIXES_V2: dict[str, dict[str, Any]] = {
    "equivalence_tree_year": {
        "value": 1 / 21,
        "unit": "árbol·año/kg CO₂e",
        "source": "Referencia general ~21 kg CO₂e/año por árbol",
        "note": "1 kg CO₂e evitado equivale a 1/21 de la absorción anual de un árbol. Varía según especie, edad y entorno.",
    }
}
EQUIVALENCE_FIXES_V2: dict[str, dict[str, Any]] = {
    "Absorción anual de árboles": {
        "value": 1 / 21,
        "unit": "árbol·año por kg CO₂e",
        "note": "Orientativo: 1 árbol absorbe ~21 kg CO₂e por año; la absorción real depende de especie, edad y entorno.",
    }
}

# ---------------------------------------------------------------------------
# Fracciones, reglas de recepción y atributos dinámicos
# ---------------------------------------------------------------------------

FRACTIONS: list[dict[str, Any]] = [
    {"name": "Cobre", "type": "metal", "color": "#b87333", "factor_key": "material_copper"},
    {"name": "Aluminio", "type": "metal", "color": "#9ca3af", "factor_key": "material_aluminum"},
    {"name": "ABS", "type": "plastic", "color": "#d1d5db", "factor_key": "material_abs"},
    {"name": "HIPS", "type": "plastic", "color": "#f3f4f6", "factor_key": "material_hips"},
    {"name": "PP", "type": "plastic", "color": "#a7f3d0", "factor_key": "material_pp"},
    {"name": "PC", "type": "plastic", "color": "#bfdbfe", "factor_key": "material_pc"},
    {
        "name": "Otros metales",
        "type": "metal",
        "color": "#6b7280",
        "factor_key": "material_other_metals",
    },
    {"name": "Otros", "type": "other", "color": "#e5e7eb", "factor_key": "material_others"},
    # Bloque 4: materiales RAEE habituales que faltaban en la semilla inicial.
    {"name": "Vidrio", "type": "other", "color": "#a5f3fc", "factor_key": "material_glass"},
    {"name": "Hierro / acero", "type": "metal", "color": "#94a3b8", "factor_key": "material_steel"},
    {
        "name": "Baterías de litio",
        "type": "other",
        "color": "#fca5a5",
        "factor_key": "material_lithium_battery",
    },
    {"name": "Placas PCB", "type": "other", "color": "#86efac", "factor_key": "material_pcb"},
    {
        "name": "Metales preciosos",
        "type": "metal",
        "color": "#fcd34d",
        "factor_key": "material_precious_metals",
    },
]

ACCEPTANCE_RULES: list[dict[str, Any]] = [
    {
        "name": "Rechazo de tóner y cartuchos de tinta",
        "action": "reject",
        "pattern": "tóner|toner|cartucho de tinta|cartucho de impresora|ink cartridge|toner cartridge",
        "applies_to": "all",
        "message": "No se reciben tóneres ni cartuchos de tinta. Retirarlos antes de registrar la impresora o fotocopiadora.",
        "sort_order": 1,
    },
    {
        "name": "Rechazo de luminarias con mercurio",
        "action": "reject",
        "pattern": "mercurio|vapor de mercurio|alta presión|fluorescente|tubo fluorescente|cfl|compacta de bajo consumo",
        "applies_to": "ILUMINACION",
        "message": "No se reciben luminarias con mercurio (vapor de mercurio de alta presión de calle, tubos fluorescentes ni CFL tradicionales).",
        "sort_order": 2,
    },
    {
        "name": "Rechazo de residuos peligrosos no electrónicos",
        "action": "reject",
        "pattern": "residuo peligroso|residuos peligrosos|químico peligroso|reactivo|radioactivo",
        "applies_to": "all",
        "message": "Los residuos peligrosos no electrónicos no se reciben en este circuito de RAEE.",
        "sort_order": 3,
    },
    {
        "name": "Impresoras y fotocopiadoras sin cartuchos",
        "action": "warn",
        "pattern": "impresora|fotocopiadora",
        "applies_to": "INFORMATICA",
        "message": "Recibir impresoras y fotocopiadoras sin cartuchos de tinta ni tóners colocados.",
        "sort_order": 4,
    },
    {
        "name": "Iluminación admitida: LED o halógena/incandescente",
        "action": "warn",
        "pattern": "luminaria|lámpara|lampara",
        "applies_to": "ILUMINACION",
        "message": "Aceptar solo tecnología LED o luminarias halógenas/incandescentes tradicionales.",
        "sort_order": 5,
    },
    {
        "name": "LED admitido",
        "action": "accept",
        "pattern": "led",
        "applies_to": "ILUMINACION",
        "message": "Tecnología LED admitida.",
        "sort_order": 6,
    },
]

ATTRIBUTE_DEFS: list[dict[str, Any]] = [
    {
        "name": "Tipo de memoria",
        "data_type": "select",
        "unit": None,
        "options": ["SDRAM", "DDR3 SDRAM", "DDR4 8GB", "DDR4 16GB"],
        "scope": "component",
    },
    {
        "name": "Capacidad RAM (GB)",
        "data_type": "number",
        "unit": "GB",
        "options": [],
        "scope": "component",
    },
    {
        "name": "Formato de fuente",
        "data_type": "select",
        "unit": None,
        "options": ["Genérica", "ATX", "TFX", "Redundante"],
        "scope": "component",
    },
    {
        "name": "Potencia (W)",
        "data_type": "number",
        "unit": "W",
        "options": [],
        "scope": "component",
    },
    {
        "name": "Socket / generación",
        "data_type": "text",
        "unit": None,
        "options": [],
        "scope": "component",
    },
    {
        "name": "Capacidad de almacenamiento (GB)",
        "data_type": "number",
        "unit": "GB",
        "options": [],
        "scope": "component",
    },
    {
        "name": "Tipo de conector",
        "data_type": "text",
        "unit": None,
        "options": [],
        "scope": "component",
    },
    {
        "name": "Formato del chasis",
        "data_type": "select",
        "unit": None,
        "options": ["SFF", "Torre", "Mini ITX"],
        "scope": "component",
    },
    {
        "name": "Tecnología de iluminación",
        "data_type": "select",
        "unit": None,
        "options": ["LED", "Halógena", "Incandescente"],
        "scope": "equipment",
    },
]

# ---------------------------------------------------------------------------
# Ejemplo detallado: Lenovo ThinkCentre M82 SFF
# ---------------------------------------------------------------------------

THINKCENTRE_BOM: list[dict[str, Any]] = [
    {
        "name": "Chasis SFF (acero)",
        "fraction": "Otros metales",
        "weight_kg": 2.20,
        "notes": "Gabinete small form factor de chapa de acero.",
        "attributes": {"Formato del chasis": "SFF"},
    },
    {
        "name": "Fuente switching ATX/TFX 240 W",
        "fraction": "Otros metales",
        "weight_kg": 0.80,
        "notes": "Fuente conmutada interna; incluye cableado de cobre.",
        "attributes": {"Formato de fuente": "ATX", "Potencia (W)": "240"},
    },
    {
        "name": "Placa madre Intel Q75 (PCB)",
        "fraction": "Otros metales",
        "weight_kg": 0.35,
        "notes": "Placa electrónica con pistas de cobre y conectores.",
        "attributes": {"Socket / generación": "LGA1155 / Intel Q75"},
    },
    {
        "name": "Procesador Intel Core i5-3470",
        "fraction": "Otros metales",
        "weight_kg": 0.05,
        "notes": "CPU de 3ª generación, socket LGA1155.",
        "attributes": {"Socket / generación": "LGA1155 (3ª gen)"},
    },
    {
        "name": "Memoria RAM DDR3 SDRAM 4 GB",
        "fraction": "Otros metales",
        "weight_kg": 0.03,
        "notes": "Módulo SO-DIMM/DIMM DDR3; comparable con DDR4 16 GB.",
        "attributes": {"Tipo de memoria": "DDR3 SDRAM", "Capacidad RAM (GB)": "4"},
    },
    {
        "name": 'Disco rígido HDD 3.5" 500 GB',
        "fraction": "Aluminio",
        "weight_kg": 0.45,
        "notes": "Unidad mecánica: base de aluminio, imanes y platos.",
        "attributes": {"Capacidad de almacenamiento (GB)": "500"},
    },
    {
        "name": "Disipador y ventilador de CPU",
        "fraction": "Aluminio",
        "weight_kg": 0.18,
        "notes": "Disipador de aluminio con carcasa plástica.",
        "attributes": {},
    },
    {
        "name": "Cableado interno",
        "fraction": "Cobre",
        "weight_kg": 0.12,
        "notes": "Arnés SATA, ATX y conectores internos.",
        "attributes": {"Tipo de conector": "SATA / ATX interno"},
    },
    {
        "name": "Tapa frontal (ABS)",
        "fraction": "ABS",
        "weight_kg": 0.30,
        "notes": "Plástico ABS inyectado del frontal.",
        "attributes": {},
    },
    {
        "name": "Tornillería y soportes",
        "fraction": "Otros metales",
        "weight_kg": 0.10,
        "notes": "Tornillos, separadores y soportes internos.",
        "attributes": {},
    },
]

LOOSE_COMPONENTS: list[dict[str, Any]] = [
    {
        "name": "Memoria RAM DDR4 16 GB (suelta)",
        "fraction": "Otros metales",
        "weight_kg": 0.03,
        "notes": "Componente suelto: no pertenece a la BOM de ningún equipo.",
        "attributes": {"Tipo de memoria": "DDR4 16GB", "Capacidad RAM (GB)": "16"},
    },
    {
        "name": "Fuente ATX 500 W (suelta)",
        "fraction": "Otros metales",
        "weight_kg": 1.10,
        "notes": "Componente suelto recibido por separado.",
        "attributes": {"Formato de fuente": "ATX", "Potencia (W)": "500"},
    },
    {
        "name": "Cable HDMI (suelto)",
        "fraction": "Cobre",
        "weight_kg": 0.15,
        "notes": "Cable de conexión suelto.",
        "attributes": {"Tipo de conector": "HDMI"},
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_or_create(
    session: Session, model: type, lookup: dict[str, Any], defaults: dict[str, Any] | None = None
):
    """Busca por `lookup`; si no existe, crea la fila con `defaults`."""
    stmt = select(model)
    for key, value in lookup.items():
        stmt = stmt.where(getattr(model, key) == value)
    obj = session.scalar(stmt)
    if obj is not None:
        return obj, False
    obj = model(**{**lookup, **(defaults or {})})
    session.add(obj)
    return obj, True


def _create_component(
    session: Session,
    entry: dict[str, Any],
    fraction_map: dict[str, Fraction],
    equipment_model_id: int | None,
) -> Component:
    component, _ = _get_or_create(
        session,
        Component,
        {"equipment_model_id": equipment_model_id, "name": entry["name"]},
        {
            "fraction_id": fraction_map[entry["fraction"]].id,
            "weight_kg": entry["weight_kg"],
            "quantity": 1,
            "notes": entry["notes"],
        },
    )
    return component


def _apply_attributes(
    session: Session,
    entry: dict[str, Any],
    component: Component,
    definition_map: dict[str, AttributeDef],
) -> None:
    for name, value in entry.get("attributes", {}).items():
        definition = definition_map[name]
        _get_or_create(
            session,
            AttributeValue,
            {
                "definition_id": definition.id,
                "entity_type": "component",
                "entity_id": component.id,
            },
            {"value": str(value)},
        )


# ---------------------------------------------------------------------------
# Semilla
# ---------------------------------------------------------------------------


def seed_database(session: Session, current_version: int = 0) -> None:
    """Carga o actualiza los datos base. Idempotente por clave natural.

    ``current_version`` evita reaplicar correcciones históricas (v2) sobre una
    base que ya venía de esa versión: así se respetan las ediciones del usuario.
    """

    # Factores y equivalencias
    for item in FACTORS:
        _get_or_create(
            session,
            Factor,
            {"key": item["key"]},
            {
                "label": item["label"],
                "value": item["value"],
                "unit": item["unit"],
                "mode": item["mode"],
                "source": item["source"],
                "note": item["note"],
                "active": True,
            },
        )
    for item in EQUIVALENCES:
        _get_or_create(
            session,
            Equivalence,
            {"label": item["label"]},
            {
                "value": item["value"],
                "unit": item["unit"],
                "note": item["note"],
                "active": True,
            },
        )
    session.flush()
    factor_map = {factor.key: factor for factor in session.scalars(select(Factor)).all()}
    equivalence_map = {
        equivalence.label: equivalence
        for equivalence in session.scalars(select(Equivalence)).all()
    }
    if current_version < 2:
        for key, changes in FACTOR_FIXES_V2.items():
            for attribute, value in changes.items():
                setattr(factor_map[key], attribute, value)
        for label, changes in EQUIVALENCE_FIXES_V2.items():
            for attribute, value in changes.items():
                setattr(equivalence_map[label], attribute, value)

    # Categorías y subcategorías (con referencia al factor general de reutilización)
    for index, category_data in enumerate(CATEGORIES):
        category, _ = _get_or_create(
            session,
            Category,
            {"code": category_data["code"]},
            {
                "name": category_data["name"],
                "description": category_data["description"],
                "sort_order": index,
            },
        )
        # Necesitamos el id antes de crear las subcategorías vinculadas.
        session.flush()
        for sub_index, sub_name in enumerate(category_data["subcategories"]):
            _get_or_create(
                session,
                Subcategory,
                {"category_id": category.id, "name": sub_name},
                {
                    "factor_id": factor_map["default_reuse"].id,
                    "sort_order": sub_index,
                },
            )
    session.flush()

    # Marcas
    for brand_name in ("Lenovo", "Genérico"):
        _get_or_create(session, Brand, {"name": brand_name})
    session.flush()
    brand_map = {brand.name: brand for brand in session.scalars(select(Brand)).all()}
    subcategory_map = {
        sub.name: sub for sub in session.scalars(select(Subcategory)).all()
    }

    # Fracciones (incluye "Otros" como comodín)
    for index, item in enumerate(FRACTIONS):
        _get_or_create(
            session,
            Fraction,
            {"name": item["name"]},
            {
                "type": item["type"],
                "color": item["color"],
                "factor_id": factor_map[item["factor_key"]].id,
                "sort_order": index,
            },
        )
    session.flush()
    fraction_map = {
        fraction.name: fraction for fraction in session.scalars(select(Fraction)).all()
    }

    # Atributos dinámicos
    for item in ATTRIBUTE_DEFS:
        _get_or_create(
            session,
            AttributeDef,
            {"name": item["name"]},
            {
                "data_type": item["data_type"],
                "unit": item["unit"],
                "options_json": json.dumps(item["options"], ensure_ascii=False),
                "scope": item["scope"],
                "is_active": True,
            },
        )
    session.flush()
    definition_map = {
        definition.name: definition
        for definition in session.scalars(select(AttributeDef)).all()
    }

    # Equipo de ejemplo
    equipment, _ = _get_or_create(
        session,
        EquipmentModel,
        {"name": "ThinkCentre M82 SFF", "brand_id": brand_map["Lenovo"].id},
        {
            "subcategory_id": subcategory_map["Computadoras de escritorio"].id,
            "typical_weight_kg": 4.58,
            "notes": "Equipo de ejemplo con composición interna editable (BOM).",
        },
    )
    session.flush()

    # BOM del equipo + componentes sueltos
    for entry in THINKCENTRE_BOM:
        component = _create_component(session, entry, fraction_map, equipment.id)
        session.flush()
        _apply_attributes(session, entry, component, definition_map)

    for entry in LOOSE_COMPONENTS:
        component = _create_component(session, entry, fraction_map, None)
        session.flush()
        _apply_attributes(session, entry, component, definition_map)

    # Reglas de recepción
    for item in ACCEPTANCE_RULES:
        _get_or_create(
            session,
            AcceptanceRule,
            {"name": item["name"]},
            {
                "action": item["action"],
                "pattern": item["pattern"],
                "applies_to": item["applies_to"],
                "message": item["message"],
                "active": True,
                "sort_order": item["sort_order"],
            },
        )

    # Escenario de demostración: equipo, componente suelto y fracción por peso
    demo, _ = _get_or_create(
        session,
        Scenario,
        {"name": "Demo — recepción de planta"},
        {
            "default_mode": "reuse",
            "notes": "Escenario de ejemplo: verifica los tres modos de asociación de ítems.",
        },
    )
    session.flush()
    if not demo.items:
        loose_ram = session.scalar(
            select(Component).where(Component.name == "Memoria RAM DDR4 16 GB (suelta)")
        )
        session.add_all(
            [
                ScenarioItem(
                    scenario_id=demo.id,
                    equipment_model_id=equipment.id,
                    quantity=10,
                    weight_kg=equipment.typical_weight_kg,
                    mode="reuse",
                    attributes_json=json.dumps({"Estado": "Reacondicionable"}),
                ),
                ScenarioItem(
                    scenario_id=demo.id,
                    component_id=loose_ram.id,
                    quantity=5,
                    weight_kg=loose_ram.weight_kg,
                    mode="recycling",
                ),
                ScenarioItem(
                    scenario_id=demo.id,
                    fraction_id=fraction_map["Cobre"].id,
                    quantity=1,
                    weight_kg=2.5,
                    mode="recycling",
                ),
            ]
        )
    session.flush()


def seed_if_empty(session: Session | None = None) -> bool:
    """Aplica/actualiza la semilla si la versión instalada es menor. Devuelve True si la aplicó."""
    owns_session = session is None
    db = session or SessionLocal()
    try:
        current_version = db.scalar(select(func.max(SeedMeta.version))) or 0
        if current_version >= SEED_VERSION:
            return False
        seed_database(db, current_version=current_version)
        db.merge(SeedMeta(version=SEED_VERSION))
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        if owns_session:
            db.close()
