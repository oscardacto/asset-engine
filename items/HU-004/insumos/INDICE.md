# Índice de insumos — HU-004

Lista los archivos entregados por el negocio/producto y su propósito.
Este directorio es **read-only mental**: no se editan los archivos originales.
Si hay correcciones, van a `closure/feedback.md`.

| Archivo | Qué es | Por qué importa |
|---------|--------|-----------------|
| hu-004-backlog.md | Extracto literal: HU del backlog + consumidores (HU-005 orientación, HU-015 sesiones, HU-018 reporte) + **hallazgo verificado sobre el stack real**: OpenCV 5 lee y escribe EXIF sin dependencias nuevas, y **aplica la rotación EXIF al decodificar** + reglas de entradas hostiles y PII | Es el ticket: el hallazgo cambia dos cosas — invalida la asunción de HU-166 de que haría falta una dependencia con ADR, y convierte la orientación en un dato **activo** que puede hacer discrepar las dimensiones de cabecera con las decodificadas |

Fuentes canónicas referenciadas: `docs/blueprint/backlog.md` (f10d05e) · `charter.md` §6.6 ·
`.claude/rules/python.md` · `documento-maestro.md` §8.2 · verificación empírica sobre
opencv-python-headless 5.0.0.93.
