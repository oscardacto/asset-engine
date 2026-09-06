# HU-104 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `video/framing.py` | `read_dimensions`, `build_crop_command`, `crop_to_vertical` |
| `tests/video/test_frame_cropping.py` | 23 tests |

**La aritmética no se rehízo.** `frame_to_vertical` y `vertical_filter_chain` ya existían y
estaban probados con valores literales. Lo que esta HU añade es todo lo que el cálculo puro
no necesita: medir el clip, entregar la ruta adaptada y producir el archivo.

**Construir el comando se separa de ejecutarlo.** Así el filtro `crop=w:h:x:y` se verifica
con valores literales, sin renderizar y en milisegundos — que es donde viven los errores de
encuadre. 12 de los 23 tests no tocan el binario.

**El desplazamiento se acota, no falla.** Pedir mover el encuadre más allá del margen
sobrante produciría un recorte fuera del cuadro y la herramienta rechazaría el clip a mitad
del lote. Se aplica el margen disponible; el encuadre sigue siendo válido.

**`crop_to_vertical` devuelve el encuadre aplicado**, no solo un éxito: quien llama necesita
saber qué se recortó para poder explicarlo en el reporte de HU-110.

## Validación con material real

```
2026-07-15-154529102.mp4   720x1280  -> 1080x1920   original intacto ✅
VID_20260726_165801.mp4   1080x1920  -> 1080x1920   original intacto ✅
VID_20260726_165817.mp4   1080x1920  -> 1080x1920   original intacto ✅
VID_20260726_165840.mp4   1080x1920  -> 1080x1920   original intacto ✅
```

Dato del dominio que conviene saber: **el material del cliente ya viene vertical** — el
celular graba en 9:16. Ninguno recortó ancho; el encuadre solo escala. El recorte de material
apaisado está implementado y probado con clips sintéticos, pero hoy no se ejercita con el
cliente 0.

Evidencia: **803 tests · `framing.py` 100% · total 99%**.
