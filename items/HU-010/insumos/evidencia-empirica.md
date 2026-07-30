# HU-010 — Evidencia empírica reproducible

> Todo lo de este documento se **ejecutó** en la máquina de referencia el 2026-07-26.
> Ningún dato proviene de documentación de terceros ni de suposición.
>
> **Entorno:** Windows 10 Pro 19045 · NTFS · `LongPathsEnabled=0` · CPython 3.13.2 ·
> opencv-python-headless 5.0.0.93 · numpy 2.5.1.
> **Scripts:** `verificar_nombres.py`, `verificar_prefijo_cv2.py`, `matriz_fs.py`
> (temporales de sesión; reproducibles desde los procedimientos descritos abajo).

## 1. Comportamiento por caso, ruta normal vs ruta extendida

Procedimiento: crear cada archivo con prefijo `\\?\` (para saltar la normalización Win32
al escribir), listarlo con `iterdir`, e intentar leerlo. **Las lecturas peligrosas corren
en un subproceso con timeout de 6 s**, para que un bloqueo real quede demostrado sin colgar
al proceso que verifica.

| Caso | ¿Se lista? | Lectura con ruta normal | Lectura con `\\?\` |
|---|---|---|---|
| `CON.jpg` | sí | **BLOQUEO: sin retorno en 6 s, proceso matado** | ✅ 14 bytes |
| `NUL.jpg` | sí | Devuelve **0 bytes** (el contenido real, 14 B, es inaccesible) | *no probado — ver §5* |
| `COM1.jpg` | sí | `FileNotFoundError` | ✅ 14 bytes |
| `punto.jpg.` | sí | `FileNotFoundError` | ✅ 14 bytes |
| `espacio.jpg ` | sí | `FileNotFoundError` | ✅ 14 bytes |
| ruta de 368 caracteres | **no** | — | se crea y se lee correctamente |
| `normal.jpg` (control) | sí | ✅ 14 bytes | ✅ 14 bytes |

**Confirmado además:** `scan_input_folder` devolvió 7 rutas y **omitió en silencio** el
archivo de la ruta de 368 caracteres — sin excepción y sin aviso.

## 2. Matriz de compatibilidad del stack real

14 operaciones × 5 casos × 2 formas de ruta. Las celdas muestran `ruta normal / ruta extendida`.

| Operación | normal | punto final | espacio final | COM1 | ruta >260 |
|---|---|---|---|---|---|
| `pathlib` read | ok / ok | **X** / ok | **X** / ok | **X** / ok | **X** / ok |
| `pathlib` stat | ok / ok | **X** / ok | **X** / ok | **X** / ok | **X** / ok |
| `pathlib` exists | ok / ok | **X** / ok | **X** / ok | **X** / ok | **X** / ok |
| `pathlib` write | ok / ok | ok / ok | ok / ok | ok / ok | **X** / ok |
| `os.stat` | ok / ok | **X** / ok | **X** / ok | **X** / ok | **X** / ok |
| `os.rename` | ok / ok | ok / ok | ok / ok | ok / ok | **X** / ok |
| `os.remove` | ok / ok | ok / ok | ok / ok | ok / ok | **X** / ok |
| `shutil.copy2` | ok / ok | **X** / ok | **X** / ok | **X** / ok | **X** / ok |
| `shutil.move` | ok / ok | **X** / ok | **X** / ok | **X** / ok | **X** / ok |
| `hashlib` (sobre lectura) | ok / ok | **X** / ok | **X** / ok | **X** / ok | **X** / ok |
| `json` ida y vuelta | ok / ok | ok / ok | ok / ok | ok / ok | **X** / ok |
| **`cv2.imread`** | ok / ok | **X** / ok | **X** / ok | **X** / ok | **X** / ok |
| **`cv2.imwrite`** | ok / ok | ok / ok | ok / ok | ok / ok | **X** / ok |
| `open` + `cv2.imdecode` | ok / ok | **X** / ok | **X** / ok | **X** / ok | **X** / ok |

**Totales: con ruta extendida, 70/70 combinaciones correctas — cero fallos.**
**Con ruta normal, 41 de 70 fallan.**

Los fallos con ruta normal se reparten en dos formas: `FileNotFoundError` (la mayoría) y
retorno silencioso de `None`/`False` (`cv2.imread`, `cv2.imwrite`, `Path.exists`) — este
segundo grupo es el peligroso, porque **no hay excepción que capturar**.

## 3. La mejora es transparente

En la columna de control (`normal.jpg`) **las 14 operaciones dan `ok / ok`**: usar la ruta
extendida no degrada ni cambia el comportamiento de los archivos corrientes. No hay
compromiso entre robustez y normalidad.

## 4. Limitaciones conocidas del prefijo (verificadas o documentadas)

- Exige ruta **absoluta y ya resuelta**: no admite `..`, ni `.`, ni separadores `/`.
  ⇒ el adaptador debe resolver antes de prefijar.
- Es **específico de Windows**. En POSIX no existe y el adaptador debe ser identidad.
- Al saltarse la normalización Win32, permite *crear* nombres que luego son inaccesibles
  por ruta normal (así se sembraron los casos de prueba). ⇒ **al escribir salidas hay que
  seguir normalizando el nombre**, no solo prefijar la ruta.

## 5. Huecos declarados de esta evidencia

- **`NUL.jpg` con prefijo no fue probado.** Con ruta normal devuelve 0 bytes. Por analogía
  con `CON.jpg` debería funcionar, pero **no está verificado** y se cierra en las pruebas
  de DEV.
- **ffmpeg, PySceneDetect, Pillow y exifread NO están instalados** (verificado). No se
  probaron porque instalarlos solo para la prueba violaría la regla de "ninguna dependencia
  de stack sin ADR". ⇒ requisito trasladado a **HU-154** (ADR de video): validar esa cadena
  contra esta misma matriz **antes** de adoptarla.
- Un solo sistema de archivos (NTFS) y una sola máquina. No se probó FAT32, exFAT, unidad
  de red ni WSL.
