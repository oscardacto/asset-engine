# Insumo — HU-101 en el backlog

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-101 | Detección de escenas (PySceneDetect, umbrales por perfil) | HU-100, HU-154 | P2 | M |

## Lo que las dos mediciones previas cambiaron del diseño

**El conflicto de empaquetado.** La librería declara la variante de OpenCV con interfaz
gráfica; ADR-002 eligió la variante sin interfaz. Las dos instalan el mismo módulo en el
mismo sitio. Medido: el entorno de prueba acabó con ese módulo inservible. Sin esta
medición, el conflicto habría aparecido como un fallo intermitente de importación.

**Las rutas largas.** La librería no encuentra un video cuya ruta supera los 260 caracteres
si se le entrega tal cual, y sí lo abre en la forma adaptada. Es lo mismo que ya pasó con el
manejador de archivos de la biblioteca estándar y con la herramienta de video.

## Consumidores

| ID | HU | Qué le pide |
|----|----|-------------|
| HU-102 | Score técnico por escena | Los tramos que hay que puntuar |
| HU-103 | Descarte de escenas malas | Idem, para filtrar |
| HU-105 | Secuenciado narrativo | Las escenas candidatas a cada tramo del guion |
| HU-110 | Reel 9:16 | El material ya partido |
