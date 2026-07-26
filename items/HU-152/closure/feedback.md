# Feedback — HU-152

## Anti-patrones detectados
- **Floors sin techo pueden traer una versión mayor sin avisar:** `>=4.10` resolvió
  OpenCV **5.0** (mayor nueva) en el primer `uv add`. No fue un problema (el lock congela
  y el humo verificó), pero la lección es explícita: al agregar una dependencia, mirar
  **qué versión resolvió realmente** el lock antes de dar el paso por bueno — no asumir
  que caerá la rama conocida.

## Decisiones rechazadas
- **`opencv-python` (full)** — GUI/Qt sin consumidor en una CLI; peso y superficie extra.
- **`opencv-contrib-python(-headless)`** — nada del inventario de operaciones del backlog
  usa contrib (YAGNI); las variantes son excluyentes y el swap posterior es barato.
- **Techo de versión (`<6`)** en los floors — rechazado: el lock ya da el control exacto y
  un techo genera conflictos de resolución futuros; los upgrades de mayor son re-locks
  deliberados vigilados por el test de humo y los golden tests.

## Lecciones aprendidas
- **El patrón "ADR + dependencia en la misma rama" funciona:** el merge ratifica decisión
  e instalación de una vez, y `uv.lock` deja la evidencia exacta. Reusar para HU-153
  (catálogo) y HU-154 (video) si deciden agregar dependencias.
- **Convertir la verificación empírica del ADR en test permanente** (`test_stack_vision`)
  hace que futuros re-locks se auto-verifiquen — el costo fue 20 líneas. Patrón a repetir
  con ffmpeg/PySceneDetect en HU-154.
- **Los riesgos heredados deben nombrarse en la spec siguiente:** R-1 nació en HU-151,
  se verificó en HU-152 y quedó cerrado con evidencia — el hilo entre specs (§8 → §2.3)
  evitó que se perdiera.
