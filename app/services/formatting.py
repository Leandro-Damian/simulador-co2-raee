from __future__ import annotations


def friendly_number(value: float) -> str:
    """Número legible en español con escalado automático (mil / millones)."""
    value = abs(value)
    if value >= 1_000_000:
        scaled = value / 1_000_000
        text = f"{scaled:.1f}".rstrip("0").rstrip(".") if scaled < 100 else f"{scaled:.0f}"
        return f"{text} millones"
    if value >= 1_000:
        scaled = value / 1_000
        text = f"{scaled:.1f}".rstrip("0").rstrip(".") if scaled < 100 else f"{scaled:.0f}"
        return f"{text} mil"
    if value >= 10:
        return f"{value:,.0f}".replace(",", ".")
    return f"{value:,.1f}".replace(",", ".")


def format_equivalence(label: str, raw_value: float) -> str:
    """Texto listo para mostrar al cliente, con escala y sentido comprehensible."""
    lowered = label.lower()
    if "árbol" in lowered or "arbol" in lowered:
        # El factor es árbol·año por kg CO₂e: raw_value ya son árbol·año equivalentes.
        if raw_value < 1:
            days = raw_value * 365
            return f"≈ {friendly_number(days)} días de absorción de un árbol"
        return f"≈ {friendly_number(raw_value)} árbol·año"
    if "kilómetro" in lowered or "kilometro" in lowered:
        return f"≈ {friendly_number(raw_value)} km en auto promedio"
    if "carga" in lowered:
        return f"≈ {friendly_number(raw_value)} cargas de teléfono"
    return f"≈ {friendly_number(raw_value)} {label.lower()}"
