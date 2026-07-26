# asdd-framework

Template de gobernanza **ASDD** (Agentic Spec-Driven Development) para Claude Code —
extraído y generalizado de `ClaudeCore SBS`, el framework en producción para el
ecosistema de seguros SBS Colombia. Este repo se queda con la capa que es 100%
independiente del dominio: el ciclo de vida con gates, la capa de gobernanza del agente,
y el mecanismo de hooks. Todo lo que era negocio de seguros (esquemas de BD, procesos
críticos, stack Java/Vue específico) se quedó afuera a propósito.

## Qué resuelve

Sin este framework, un agente como Claude Code escribe código apenas se lo pedís, con
la ambigüedad que traiga el ticket. Con este framework, un WorkItem no llega a `dev/`
hasta que pasa un **gate duro**: cero preguntas bloqueantes y ≥85% de confianza en una
spec técnica escrita y verificada contra el codebase real. El agente además opera bajo
una capa de gobernanza explícita (anti-sycophancy, divulgación progresiva, comparación de
enfoques antes de codear) en vez de la conducta por defecto del modelo.

## Qué incluye

```
.claude/
├── CLAUDE.md              ← contexto maestro (template con {{ASI}} a completar)
├── settings.json          ← wiring de hooks (limpio, sin secretos ni historial de permisos)
├── hooks/                 ← protección de archivos/comandos + inyección de reglas por path
├── rules/                 ← convención de reglas cargadas por path (arranca vacío)
└── skills/
    ├── new-item/           ← DRAFT→SPEC→DEV con el gate duro
    └── close-item/         ← evidencia de pruebas + feedback + entregables
items/
└── _template/              ← esqueleto de carpeta por WorkItem
```

## Mecanismo probado, no solo diseñado

Los 3 hooks (`pre-edit-protection`, `command-write-protection`, `rules-inject`) se
validaron de forma aislada antes de incorporarse aquí: se copiaron sin modificar a un
proyecto de prueba en un dominio distinto y se les mandó el mismo payload JSON que les
manda Claude Code en producción, vía stdin.

| Prueba | Resultado |
|---|---|
| `rules-inject` inyecta una regla cuando el path matchea su `paths:` | ✅ |
| `rules-inject` no inyecta nada cuando ningún path matchea | ✅ |
| `pre-edit-protection` bloquea `Edit`/`Write` sobre un archivo protegido | ✅ |
| `pre-edit-protection` permite editar un archivo normal | ✅ |
| `command-write-protection` bloquea un comando que escribe sobre un archivo protegido | ✅ |
| `command-write-protection` permite un comando de solo lectura sobre el mismo archivo | ✅ |

Los tres scripts usan solo rutas relativas al proyecto (`.claude/hooks/`,
`.claude/rules/`) y a su propio directorio (`__dirname`) — cero paths absolutos, cero
referencia a SBS. Node es la única dependencia real (no `python3`/`python`).

## Cómo adoptarlo en un proyecto nuevo

1. Copia este repo (o usa `degit`/`git clone` + borra el historial) como base de tu
   proyecto nuevo.
2. Completa los placeholders `{{ASI}}` de `.claude/CLAUDE.md`: stack real, componentes,
   convenciones de tu dominio.
3. Agrega tus propias reglas en `.claude/rules/` (ver `.claude/rules/README.md`) — el
   directorio arranca vacío a propósito.
4. Si tu proyecto tiene un esquema de datos grande (BD, contrato OpenAPI extenso),
   conéctalo vía un MCP server propio de solo lectura en vez de volcarlo al contexto —
   ver la sección "Esquema de Datos" de `CLAUDE.md`.
5. Personaliza `.claude/skills/new-item/templates/spec_template.md` si tu dominio necesita
   secciones adicionales (la sección de confianza/gate del final **no la toques** — es el
   corazón del framework).
6. Ajusta el Checklist Pre-Flight de `CLAUDE.md` con las reglas reales de tu equipo
   (linters, cobertura mínima, convención de ramas).

## Qué NO se trajo de `ClaudeCore SBS` (y por qué)

| Elemento | Por qué se quedó afuera |
|---|---|
| `context/` completo (procesos de seguros, esquemas `syli`/`apihub`/`intake`) | Contenido de dominio, no framework |
| Stack fijado (Java/Spring, Vue 2, Flyway, GitFlow `publish/Sofka-SOF-XXXX`) | Asume el ecosistema SBS — se reemplaza por placeholders `{{ASI}}` |
| `mcp-db` (servidor MCP completo) | Implementación Java/Gradle apuntada a PostgreSQL de SBS — el *patrón* (MCP de solo lectura bajo demanda) sí quedó documentado en `CLAUDE.md` |
| `references/contexto-sbs/` de `refinamiento-sbs-preguntas` | Dumps de BD y `AGENTS.md` por microservicio — contenido de negocio puro |
| Generador `.docx` de `evidencias-hu` | Portable en teoría, pero es ceremonia de más para un template base — referenciado en `close-item/SKILL.md` por si se necesita después |
| `settings.json` original (historial de permisos aprobados) | Contenía rutas absolutas de un usuario/máquina y tokens/credenciales de sesiones de desarrollo real (nunca comiteados — estaba en `.gitignore` del repo origen) |

## Filosofía (heredada de ADR-005 de `ClaudeCore SBS`)

Ninguna abstracción nueva entra a este framework sin que primero falle una
implementación real que la necesite. Este template mismo es prueba de esa regla: nació
de ~decenas de WorkItems reales cerrados en producción, no de una especulación sobre
"cómo debería verse" un framework ASDD.
