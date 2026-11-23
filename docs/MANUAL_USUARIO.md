# Manual de Usuario — Simulador de CO₂ Evitado RAEE

> **Estimación paramétrica.** Todas las cifras de esta aplicación se calculan con factores
> editables y sirven para orientar decisiones; no constituyen un inventario oficial de
> emisiones. Organización configurada: `ORG_NAME` (por defecto, *Electrogreem S.R.L.*).

Este manual también está disponible dentro de la aplicación en la ruta `/manual` (menú
**Manual**).

## Índice

1. [Primeros pasos](#1-primeros-pasos)
2. [Catálogo, BOM y atributos](#2-catálogo-bom-y-atributos)
3. [Simulación y guardado](#3-simulación-y-guardado)
4. [Calculadora rápida](#4-calculadora-rápida)
5. [Factores y equivalencias](#5-factores-y-equivalencias)
6. [Lectura ante clientes o recorridos en planta](#6-lectura-ante-clientes-o-recorridos-en-planta)

---

## 1. Primeros pasos

1. Ingresá a la aplicación desde `http://127.0.0.1:8002/`.
2. Usá el menú superior (o el botón **Menú** en el celular) para ir a **Catálogo**,
   **Calculadora**, **Simulador**, **Factores** o **Manual**.
3. Antes de operar, revisá los factores vigentes en `/factores`: son la base de todas
   las estimaciones.

## 2. Catálogo, BOM y atributos

En `/catalogo` se administran equipos, componentes sueltos, fracciones materiales, marcas,
categorías y atributos dinámicos.

### Cargar un equipo con su BOM

Abrí **Modelos de equipo** y elegí **Nuevo modelo**. Completá nombre, marca y peso. En la
lista de componentes agregá cada pieza indicando fracción, peso unitario y cantidad; esa
combinación es la lista de materiales (BOM). El peso total del equipo se obtiene de la suma
de la BOM cuando se indica.

### Componentes sueltos

Para piezas que no pertenecen a un equipo (por ejemplo un cable suelto), cargalas desde
**Componentes sueltos**. También podés asignarles atributos como conector, capacidad o
estado, según las definiciones disponibles.

### Fracciones y materiales

Las fracciones clasifican el peso por material: cobre, aluminio, plásticos (ABS, HIPS, PP,
PC), vidrio, hierro/acero, baterías de litio, placas PCB, metales preciosos, otros metales
y la fracción comodín «Otros». Cada una puede asociarse a un factor editable.

- **Agregar:** en **Fracciones**, completá nombre, tipo, color, factor y orden, y guardá.
- **Quitar:** el botón **✕** desactiva la fracción. No la borra: los componentes y escenarios
  que ya la usaban siguen calculando igual y su nombre se conserva en el historial.
- **Reactivar:** el botón **↺** vuelve a ponerla disponible para nuevas cargas.

Lo mismo aplica a los factores en `/factores`: se pueden dar de baja y reactivar sin perder
el valor editado.

### Atributos dinámicos

En **Atributos** definí campos extra (por ejemplo «Tipo de conector», «Capacidad», «Estado»)
y sus opciones. Luego cargá los valores en cada equipo o componente. Así el catálogo se
adapta a tu procedimiento de recepción sin cambiar el código.

## 3. Simulación y guardado

El simulador (`/simulador`) permite armar lotes de trabajo comparables y guardarlos como
escenarios.

1. Presioná **Nuevo escenario** y poné un nombre, un modo por defecto y, si querés, notas.
2. Agregá ítems de tres formas: un **equipo** del catálogo, un **componente suelto** o una
   **fracción por peso**.
3. Ajustá cantidad, peso (cuando corresponde) y modo: reutilización, reciclaje o sin
   recuperación.
4. Presioná **Calcular** para ver el total, el desglose por ítem y los gráficos comparativos
   por modo.
5. Presioná **Guardar escenario** para conservarlo. Podés volver a abrirlo, editarlo,
   recalcularlo o borrarlo desde la lista.

Los escenarios guardan el nombre de cada entidad al momento del cálculo: si después
desactivás una fracción o un factor, el escenario histórico sigue siendo legible y
calculable.

## 4. Calculadora rápida

La calculadora (`/calculadora`) es una herramienta de uso puntual: elegí tipo de ítem
(equipo, componente o fracción), cantidad, peso y modo, agregalo a la lista y presioná
**Calcular estimación**. Muestra el total, el desglose y equivalencias en unidades
cotidianas. No guarda nada: para conservar el trabajo usá el Simulador.

## 5. Factores y equivalencias

### Factores

Cada factor tiene clave, etiqueta, valor, unidad, modo (reutilización, reciclaje, sin
recuperación, material o equivalencia), fuente y nota. Podés crear nuevos, editarlos y
desactivarlos; el botón **↺** los reactiva sin cambiar el valor que ajustaste. Los cambios
impactan de inmediato en nuevas estimaciones.

Entre los factores materiales editables se incluyen vidrio, hierro/acero, baterías de
litio, placas PCB y metales preciosos, además de cobre, aluminio y plásticos.

### Equivalencias

Las equivalencias traducen kg CO₂e a kilómetros en auto, cargas de teléfono o días de
absorción de un árbol. Se editan en la pestaña **Equivalencias** del mismo panel y se
muestran al final de cada cálculo para facilitar la comunicación del resultado.

## 6. Lectura ante clientes o recorridos en planta

Para una visita o una reunión rápida, seguí este recorrido sugerido:

1. Abrí **Calculadora** en el celular: agregá el equipo que se está recepcionando y mostrá
   el total con sus equivalencias.
2. Si el cliente pregunta por el origen del número, abrí **Factores** y mostrá el factor
   aplicado, su unidad y su nota.
3. Si necesitás comparar destinos, abrí un escenario en **Simulador** y mostrá los gráficos
   por modo de recuperación.
4. Recordá siempre la aclaración: son **estimaciones paramétricas**, no un inventario oficial.

En un recorrido de planta podés usar el menú **Menú** del encabezado para cambiar de vista
sin volver al inicio. La interfaz se adapta al ancho del celular o de la pantalla de la sala.

---

Para instrucciones de instalación y configuración, consultá el `README.md` en la raíz del
proyecto.
