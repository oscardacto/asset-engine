# Feedback — HU-151

## Anti-patrones detectados
- **Comandos aspiracionales en docs de gobernanza.** CLAUDE.md documentaba `python -m venv …`
  que falla en la máquina de referencia (`python` no está en PATH; solo `py`). Ningún comando
  entra a la documentación sin ejecutarlo o verificar sus precondiciones en el entorno real.
- **Primer push sin verificar identidad de la credencial.** El credential manager de Windows
  tenía la cuenta de otro usuario (`mipressyasta`) → 403. En el primer push de todo repo
  nuevo: verificar `git config user.*` **y** qué credencial va a usar el helper.
- **Comitear `items/<ID>/` sin recordar la lista blanca.** `.gitignore` ignora `items/*` por
  defecto (defensa PII) y el skill `/new-item` no menciona el paso de aprobar la carpeta con
  `!items/<ID>`. Candidato a añadirse al skill como paso explícito de FASE 1.

## Decisiones rechazadas
- **venv+pip puro** — sin lockfile con hashes; deja el KPI de reproducibilidad 100% en
  "mejor esfuerzo". Descartado en ADR-001 §Opción A.
- **venv+pip+pip-tools** — paga el mismo costo de aprobación de herramienta que uv sin dar
  lockfile multiplataforma ni gestión de versiones de Python. Descartado en ADR-001 §Opción B.
- **Mega-prompt externo ("Principal Software Architect", propuesta ChatGPT)** como segunda
  constitución — rechazado íntegro: ~70% duplicaba CLAUDE.md/rules con números divergentes,
  proponía a la IA como Product Owner (contra los límites de autonomía) y traía stack ajeno
  (MoviePy, Pillow, FastAPI). Se rescataron 4 deltas puntuales a `.claude/rules/python.md`
  (complejidad ≤10, clase ≤200, checklist de seguridad, TODOs trazables).

## Lecciones aprendidas
- **Las HUs tipo ADR encajan limpias en el ciclo ASDD** si "verificar el esquema real" se
  traduce a "verificar el entorno real de la máquina" (`py -0p`, PATH, gestores presentes).
  La spec distinguió verificado vs asumido y eso sostuvo la confianza del 92%.
- **El flujo de ramas cambió con el PR #1:** `feature → develop (integración) → main
  (estable)`. CLAUDE.md aún dice "rama de feature desde main" y el ciclo dice "DONE = merge
  a main". Propuesta de gobernanza pendiente (decide el equipo): actualizar CLAUDE.md para
  reflejar develop como rama de integración y redefinir DONE = merge a develop aceptado.
- **Ratificar ADRs con el merge del PR funciona** como acto humano de aprobación con
  evidencia (URL del PR) — mantener el patrón: ADR nace `Propuesto`, el merge lo vuelve
  `Aceptado`, y el flip de estado se comitea en la rama de integración al cerrar.
