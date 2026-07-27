# Feedback — HU-009

## Anti-patrones detectados
- **Guarda defensiva inalcanzable.** El primer diseño validaba que la cabecera WebP tuviera
  ≥12 bytes antes de leer el tamaño declarado — pero un archivo solo se identifica como
  WebP *después* de haber leído esos 12 bytes, así que la rama no podía ejecutarse nunca.
  La cobertura lo delató (84%). Se eliminó en vez de taparla con un test artificial:
  **código que no se puede alcanzar no se testea, se borra.**
- **Dos lectores de bytes casi idénticos** (`_read_head` y `_read_tail`, con su propio
  manejo de error cada uno). Se unificaron en `_read_bytes(path, offset, count)`: menos
  superficie, un único punto de conversión a `CorruptMediaError`.

## Decisiones rechazadas
- **Mover los archivos apartados a una carpeta `quarantine/`** — rechazado por el charter
  §6.3: tocaría los originales. La palabra del ticket sugiere movimiento físico; el
  principio del proyecto lo prohíbe, y el principio manda.
- **Copiar los apartados a la carpeta de trabajo** — rechazado: duplicaría gigabytes de
  video para no aportar nada que la ruta + el motivo no digan ya.
- **Exigir que la marca de cierre sean los últimos bytes exactos** — rechazado (R-1): hay
  móviles que añaden relleno tras el cierre, y esa exigencia habría descartado material
  bueno del cliente. Se busca en los últimos 64 bytes; hay un test que fija el caso.
- **Decodificar para validar integridad real** — rechazado: cerraría la puerta al rechazo
  previo de imágenes-bomba (HU-011) y duplicaría el trabajo de la etapa de análisis. La
  validación aquí es estructural y está documentada como tal.
- **Un motivo genérico `INVALID`** — rechazado: cinco motivos tipados permiten agrupar el
  resumen de fallos (HU-180) y dar mensajes distintos; uno solo obligaría a parsear texto.

## Lecciones aprendidas
- **Cuando el ticket usa una metáfora, verificarla contra los principios antes de
  diseñar.** "Cuarentena" evoca mover archivos a un cuarto oscuro; en un sistema no
  destructivo solo puede ser una lista. Ese cruce (ticket vs charter) se hizo en el insumo,
  antes de la spec, y evitó construir lo contrario de lo que el proyecto exige.
- **La cobertura como detector de diseño, no solo de tests faltantes.** El 84% inicial no
  significaba "faltan tests": significaba "hay código que no hace falta" y "hay una rama
  real (WebP) que nadie probó". Las dos lecturas llevaron a un módulo más pequeño.
- **Se puede detectar mucho sin decodificar.** Firma + marca de cierre atrapan el archivo a
  medio descargar leyendo ~80 bytes. Vale la pena preguntarse qué se puede saber barato
  antes de pagar el coste completo — sobre todo con videos por delante.
