# Simulador de CO₂ Evitado RAEE

Aplicación web local para estimar el CO₂ evitado en la gestión de Residuos de Aparatos
Eléctricos y Electrónicos (RAEE). Permite administrar un catálogo extensible con
composición (BOM) y atributos, armar escenarios de simulación, comparar modos de
recuperación y editar los factores paramétricos que alimentan el cálculo.

> **Estimación paramétrica.** Los resultados son orientativos y se basan en factores
> editables; no constituyen un inventario oficial de emisiones.

## Requisitos

- **Python 3.10, 3.11 o 3.12** (no se recomienda 3.13+; con versiones muy nuevas,
  `pydantic-core` puede fallar al instalar).
- Git (para clonar el proyecto).
- Navegador moderno con conexión a internet la primera vez (Tailwind CSS, Alpine.js y
  Chart.js se cargan desde CDN).

## Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO> simulador-co2-raee
cd simulador-co2-raee
```

Si trabajás con el proyecto ya descargado, simplemente ubicate en la carpeta raíz:

```powershell
cd C:\Users\grise\Desktop\simulador-co2-raee
```

### 2. Crear y activar el entorno virtual

**Windows (PowerShell):**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación, habilitá scripts para la sesión:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> En este entorno de Windows, si el `python` suelto apunta a una versión no soportada,
> usá directamente `.\.venv\Scripts\python.exe` en lugar de `python`.

### 4. Configuración opcional

Copiá `.env.example` a `.env` y ajustá los valores según la planta u organización:

```powershell
Copy-Item .env.example .env
```

| Variable | Valor por defecto | Uso |
| --- | --- | --- |
| `APP_TITLE` | `Simulador de CO₂ Evitado RAEE` | Título de la aplicación. |
| `ORG_NAME` | `Electrogreem S.R.L.` | Organización visible en el encabezado (dato configurable, independiente de la autoría del código). |
| `DB_PATH` | `data/simulador_co2.db` | Ruta de la base SQLite local. |
| `DEBUG` | `false` | Habilita el log SQL de SQLAlchemy. |

No hace falta editar nada para arrancar: si no existe `.env`, se usan los valores por defecto.

### 5. Iniciar la aplicación

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

En Linux/macOS, con el entorno activado:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

Al iniciar se crean automáticamente la carpeta `data/`, la base `simulador_co2.db` y la
semilla inicial (categorías RAEE, fracciones, factores, equivalencias, reglas de recepción,
el equipo de ejemplo *Lenovo ThinkCentre M82 SFF* y un escenario de demostración).
La base de datos está ignorada por Git: no se versiona.

Para recargar automáticamente durante el desarrollo, agregá `--reload`.

### 6. Verificar que funciona

Abrí <http://127.0.0.1:8002/> en el navegador. También podés comprobar el estado con:

- <http://127.0.0.1:8002/health> — respuesta JSON con versión de semilla y configuración.
- <http://127.0.0.1:8002/docs> — documentación interactiva de la API (Swagger).

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

## Estructura del proyecto

```text
simulador-co2-raee/
├── app/
│   ├── main.py                 # FastAPI, rutas del favicon y /health
│   ├── core/                   # Configuración y base de datos (SQLite + migración mínima)
│   ├── models/                 # Modelos SQLAlchemy (factores, fracciones, escenarios, etc.)
│   ├── schemas/                # Esquemas Pydantic de entrada/salida
│   ├── routes/                 # API REST, catálogo, escenarios y vistas HTML
│   ├── seed/                   # Semilla idempotente y versionada (SEED_VERSION)
│   ├── services/               # Motor de cálculo y formateo de equivalencias
│   └── templates/              # Plantillas Jinja2 (base, catálogo, calculadora, simulador, factores, manual)
├── docs/
│   └── MANUAL_USUARIO.md       # Manual en Markdown
├── data/                       # Base SQLite local (ignorada por Git)
├── co2-favicon.jpg             # Favicon servido en /favicon.jpg y /favicon.ico
├── requirements.txt
├── .env.example
└── README.md
```

## Notas sobre cambios y actualizaciones

- La semilla es **idempotente y versionada**: al iniciar, solo aplica cambios cuando la
  versión guardada es menor que `SEED_VERSION`. Las ediciones del usuario (por ejemplo,
  valores de factores) no se sobrescriben.
- Las fracciones y los factores usan **baja lógica**: desactivarlos los quita del alta y de
  las opciones nuevas, pero no borra escenarios ni cálculos históricos. El botón ↺ los reactiva.
- Para actualizar una instalación existente: `git pull`, reiniciar uvicorn. La migración de
  columnas nuevas se aplica automáticamente al arrancar.

## Autoría

La autoría del código consta únicamente en metaetiquetas y comentarios del código
(`Leandro Damian Chumbita — Técnico Superior en Programación`). No se muestra como texto
visible en la interfaz. La organización indicada en pantalla es un dato de configuración
(`ORG_NAME`).
