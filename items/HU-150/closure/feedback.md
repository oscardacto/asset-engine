# Feedback — HU-150

## Anti-patrones detectados
- **PATH stale tras instalar herramientas.** uv quedó en `%USERPROFILE%\.local\bin`, fuera
  del PATH de las sesiones ya abiertas (riesgo R-2, se materializó como se predijo). El
  patrón correcto quedó establecido: prepend explícito por sesión hasta reiniciar la shell —
  no asumir que "instalado" significa "invocable".
- (Proceso limpio en lo demás — sin rework, las 3 asunciones de la spec sobrevivieron a QA.)

## Decisiones rechazadas
- **Pre-crear los 9 módulos de la arquitectura como paquetes vacíos** — rechazado por la
  filosofía ADR-005 (ninguna abstracción sin implementación que la necesite): cada módulo
  nace con su primera HU. El esqueleto solo ancla distribución, versión y tooling.
- **Linter adicional para límites de líneas** (módulo≤300/clase≤200/función≤40 no tienen
  regla nativa en ruff) — rechazado: sería dependencia nueva sin ADR solo para contar
  líneas; quedan como disciplina de revisión, ampliable en HU-163 si duele.
- **mypy laxo "para empezar"** — rechazado: `strict = true` desde el día cero; activarlo
  después es rework garantizado sobre código ya escrito.

## Lecciones aprendidas
- **Los floors (`>=`) en dev-deps + lock funcionan:** el lock resolvió versiones muy
  posteriores a las conocidas (ruff 0.16, mypy 2.3, pytest 9.1) y todo pasó — el
  determinismo lo da `uv.lock`, no los floors. Re-sincronizar en develop resolvió en 1 ms:
  lock estable entre ramas.
- **Re-ejecutar la batería QA sobre develop post-merge** (no solo en la rama de feature)
  es barato y convierte "debería seguir verde" en evidencia. Mantener como práctica de
  cierre para HUs con código.
- **El merge del PR puede ratificar asunciones de spec, no solo ADRs:** P-1 (nombre del
  paquete) quedó resuelta implícitamente al mergear con `media_optimizer` visible en el
  diff. Señalar siempre en el resumen del PR qué asunciones ratifica el merge.
