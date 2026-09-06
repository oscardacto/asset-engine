# Insumo — HU-104 en el backlog

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-104 | Crop 9:16 de material horizontal (encuadre centrado configurable) | HU-101 | P2 | M |

## Lo que ya existe y no hay que rehacer

`video/transforms.py` (entregado junto a HU-135) resuelve la **aritmética**:

- `frame_to_vertical(ancho, alto)` → cuánto agrandar y qué recortar, en enteros exactos y
  con medidas siempre pares.
- `vertical_filter_chain(encuadre)` → la cadena de filtros con el reinicio de marcas de
  tiempo por delante.

Verificado con valores literales para 4K, 1080p, 4:3, vertical y vertical alto.

## Lo que falta, y por qué no es trivial

Aplicarlo a un **clip real** exige tres cosas que el cálculo puro no necesita:

1. **Saber cuánto mide el clip.** El encuadre depende de las dimensiones del material, y hay
   que leerlas del archivo.
2. **Entregar la ruta adaptada.** Tanto la herramienta de video como la librería de escenas
   fallan con rutas largas si se les pasa tal cual — está medido tres veces en este proyecto.
3. **Producir el archivo sin tocar el original** (charter §6.3).

## Sobre "configurable"

El enunciado pide **encuadre centrado configurable**, no encuadre inteligente. Detectar dónde
está el sujeto para recortar alrededor exigiría detección de contenido, que no tiene HU en el
backlog. Lo configurable aquí es **cuánto desplazar el encuadre** respecto del centro: sirve
para el caso real de que lo interesante quede a un lado, sin inventar una capacidad que nadie
especificó.

## Consumidores

| ID | HU | Qué le pide |
|----|----|-------------|
| HU-106 | Recorte de clips a duración objetivo | Clips ya en formato vertical |
| HU-107 | Ensamblado del reel | Idem, todos con las mismas medidas |
| HU-109 | Export 1080×1920 | El material ya encuadrado |
