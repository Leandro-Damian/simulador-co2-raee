# Simulador de CO₂ Evitado RAEE

Aplicación web local para estimar el CO₂ evitado en la gestión de Residuos de Aparatos
Eléctricos y Electrónicos (RAEE). Permite administrar un catálogo extensible con
composición (BOM) y atributos, armar escenarios de simulación, comparar modos de
recuperación y editar los factores paramétricos que alimentan el cálculo.

> **Estimación paramétrica.** Los resultados son orientativos y se basan en factores
> editables; no constituyen un inventario oficial de emisiones.

## Vistas disponibles

| Ruta | Qué hace |
| --- | --- |
| `/` | Inicio y resumen del proyecto. |
| `/manual` | Manual de Usuario dentro de la aplicación. |
| `/catalogo` | Alta/edición de equipos, componentes, fracciones, marcas, categorías, atributos y BOM. |
| `/calculadora` | Cálculo rápido sin guardar. |
| `/simulador` | Escenarios guardables con gráficos comparativos. |
| `/factores` | Edición de factores y equivalencias; alta, baja y reactivación. |

## Flujo recomendado

1. Revisar los factores en `/factores` y ajustarlos a la operación real.
2. Cargar equipos y su BOM en `/catalogo`, o usar el ejemplo precargado.
3. Probar un cálculo puntual en `/calculadora`.
4. Armar y guardar escenarios en `/simulador` para comparar reutilización, reciclaje y sin recuperación.
5. Compartir valores y equivalencias usando `/manual` o `docs/MANUAL_USUARIO.md`.
