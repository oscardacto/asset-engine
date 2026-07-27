# Feedback — HU-002

## Anti-patrones detectados
- (Ninguno nuevo. Las tres reglas heredadas se aplicaron sin fricción: `git add` con rutas
  explícitas, verificación de `origin/develop` antes de cerrar, y docstrings sin
  referencias al proceso.)

## Decisiones rechazadas
- **Usar la extensión como pista rápida antes de leer bytes** — rechazado: el ticket dice
  "magic bytes, no extensión" y cualquier atajo por extensión reintroduce el error que la
  HU existe para eliminar (el archivo del cliente 0 llegó por WhatsApp, con renombrados).
- **Tratar el formato desconocido como excepción** — rechazado (A-4): no reconocer un
  archivo no es un fallo, es una clasificación; `None` es dato y deja a HU-009 decidir.
  Reservar las excepciones para lo que de verdad salió mal (archivo ilegible).
- **Incluir TIFF entre los soportados** — rechazado (P-1) pese a que el build lo decodifica:
  ningún celular lo produce y el charter fija el dispositivo de referencia. Añadirlo es
  una fila si algún día aparece.
- **Soportar HEIC ya** — rechazado: exige dependencia nueva con ADR. Reconocerlo cuesta
  3 líneas y da el 80% del valor (mensaje accionable en vez de "no es imagen").
- **Verificar integridad además de la firma** — rechazado: son cosas distintas y mezclarlas
  obligaría a decodificar aquí, cerrando la puerta al rechazo previo de imágenes-bomba
  (HU-011). Se documentó explícitamente con un test que lo fija.

## Lecciones aprendidas
- **Verificar las capacidades del stack antes de diseñar cambió el diseño.** La spec iba a
  tener dos categorías (soportado / no soportado); ejecutar `cv2.getBuildInformation()`
  reveló `AVIF: NO` y ausencia de HEIF, y de ahí salió la tercera categoría —reconocido
  pero no soportado— que es la que produce un mensaje útil para el usuario de iPhone.
  Cinco minutos de verificación empírica valieron más que la intuición sobre OpenCV.
- **Un test puede vigilar una dependencia externa:** `TestCoherenciaConElStack` recorre el
  conjunto declarado soportado y exige que cv2 abra cada formato. Convierte una suposición
  sobre el wheel en un chequeo automático que se re-evalúa en cada re-lock. Patrón
  reutilizable para HU-154 (ffmpeg) y cualquier capacidad que dependa de un binario.
- **Documentar lo que una función NO garantiza vale tanto como lo que garantiza:** el test
  "firma válida con basura detrás sigue siendo JPEG" evita que alguien confunda esta
  validación con un chequeo de integridad y salte HU-011.
