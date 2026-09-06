# Feedback — HU-101

> La evidencia de pruebas está en `qa_report.md`. Aquí solo van las lecciones, los
> anti-patrones y las decisiones rechazadas, como pide la regla de oro nº 3.

## Lecciones aprendidas

- **Medir la dependencia antes de declararla evitó un fallo intermitente.** `scenedetect`
  arrastra la variante de OpenCV con interfaz gráfica, que instala el mismo módulo que la
  variante sin interfaz elegida en ADR-002. Al resolverlo en un entorno de prueba, el módulo
  quedó inservible con un error de configuración. Declararlo sin medir habría producido un
  fallo de importación aparentemente aleatorio, y nadie lo habría atribuido a esta HU.
  **La regla que ya lleva tres casos: toda dependencia nueva se resuelve en un entorno
  desechable antes de tocar la configuración del proyecto.**

- **`xfail(strict=True)` es lo que convierte el TDD en evidencia y no en relato.** Los tests
  se escribieron antes del código y quedaron en fallo esperado. Al implementar, el modo
  estricto **obligó** a desmarcarlos: si se hubieran dejado, habrían fallado por pasar. Eso
  deja constancia verificable de que el ciclo rojo → verde ocurrió, algo que un `skip` no
  daría y que escribir los tests después del código no podría demostrar.

- **La ausencia de resultado no siempre significa cero.** La librería devuelve lista vacía
  cuando un clip no tiene cortes. Interpretarlo literalmente habría hecho que un clip
  continuo produjera cero escenas y desapareciera del reel sin error ni aviso. Un clip sin
  cortes es una escena, no ninguna. **Generalizable: cuando una librería externa devuelve
  vacío, hay que preguntarse si significa "nada" o "todo en una pieza".**

- **Tercer caso del mismo patrón de rutas.** El manejador de archivos de la biblioteca
  estándar, la herramienta de video y ahora esta librería: las tres reciben rutas y las abren
  por dentro, y las tres fallan sin la adaptación de ADR-004. Ya no es una precaución: es lo
  que hay que medir en cualquier dependencia que reciba una ruta.

## Decisiones rechazadas

- **Usar los extras `[opencv-headless]` / `[headless]` de la librería** — medido: en la
  versión 0.7.1 no cambian el árbol resuelto. Habrían dado una falsa sensación de solución.
- **Instalar ambas variantes de OpenCV y confiar en el orden** — cuál gana depende del orden
  de instalación; es exactamente el tipo de no-determinismo que el charter §6.1 prohíbe.
- **Devolver cero escenas para un clip sin cortes** — fallo silencioso; ver arriba.
- **Silenciar los tipos de forma global en mypy** — el silencio se acotó a la librería que no
  publica tipos. Ampliarlo habría desactivado la verificación en código propio.
- **Que el adaptador expusiera los objetos de la librería** — habría hecho que el dominio
  dependiera de ella; el puerto solo habla de `Scene`, y hay un test que lo comprueba.

## Anotado, sin acción

`core/ports/` es un subpaquete nuevo con un solo puerto y una sola implementación. Se creó a
petición explícita y es puro, pero sigue siendo una abstracción con un único consumidor: si
al llegar HU-102 y HU-105 no aporta desacoplamiento real, el puerto cabe en `core/scene.py`
junto al dato y mover el archivo es todo el cambio.
