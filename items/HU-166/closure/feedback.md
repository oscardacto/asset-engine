# Feedback — HU-166

## Anti-patrones detectados
- **`git add -A` arrastró configuración de sesión al commit de la HU.** El harness
  persiste las aprobaciones de permisos en `.claude/settings.json` (archivo compartido y
  versionado), y el `add -A` las metió en `a6339e7`; hubo que revertirlas en `f4afe97`.
  **Regla operativa a partir de ahora: usar rutas explícitas en `git add`** (`git add
  src/ tests/ items/<ID>/ ...`) y revisar `git status` antes de comitear. Fuera de alcance
  de esta HU, pero pendiente real: esas aprobaciones deberían vivir en
  `.claude/settings.local.json` (gitignorado).
- **El merge del PR se dio por hecho sin verificarlo.** Un turno se ejecutó creyendo que
  HU-166 estaba integrada cuando el PR ni siquiera existía en GitHub. Ahora el cierre
  arranca **verificando `origin/develop`** antes de tocar nada — barato y evita construir
  sobre una base inexistente.

## Decisiones rechazadas
- **Colocar el generador en `tests/support/`** — rechazado (A-1): lo consumirán también
  `benchmarks/` (HU-165) y el dataset E2E (HU-185); desde `tests/` no sería importable
  limpio ni quedaría bajo mypy estricto.
- **EXIF sintético en esta HU** — rechazado (A-2): cv2 no escribe EXIF y resolverlo
  implicaría una dependencia nueva sin HU que la justifique. Pregunta transferida
  formalmente a HU-004/005.
- **Un único helper `corrupt_image()` genérico** — rechazado: truncado, magic falso y
  vacío ejercitan ramas distintas de la ingesta (decodificador vs validador de formato vs
  tamaño); un helper único habría escondido esa distinción justo donde importa.
- **Afirmar "el truncado no decodifica"** — rechazado por honestidad técnica: libjpeg es
  tolerante y a veces reconstruye parcialmente. El criterio se formuló como "no
  reconstruye el original", que es lo verificable.

## Lecciones aprendidas
- **Un fixture debe tener exactitud conocida, no solo apariencia realista.** Separar
  `flat_image` (media exacta, para calibrar) de `textured_image` (media ± tolerancia
  declarada, para realismo) es lo que hará posible verificar la paridad ±2% del KPI: sin
  el caso exacto, un fallo de métrica sería indistinguible de ruido del fixture.
- **Las reglas propias se aplican al código propio:** ruff rechazó los literales 255/100
  por la regla de números mágicos que este mismo equipo añadió a `python.md` hace unas
  horas. La gobernanza funciona cuando muerde a quien la escribió.
- **La cobertura como detector de ramas olvidadas:** el 95% inicial señaló exactamente la
  validación de `mean_brightness` sin test. Correr `--cov` del módulo tocado antes del
  commit, no después.
