# Hooks de Claude Code

Este directorio contiene los scripts de hooks del framework. Los hooks se configuran en
`.claude/settings.json` — **no hay auto-discovery por nombre de archivo**: un script aquí
que no esté registrado bajo la clave `"hooks"` de `settings.json` nunca se ejecuta.

Probados de forma aislada (payload JSON simulado por stdin) antes de incorporarse a este
template — ver §"Mecanismo probado" del `README.md` raíz.

## Hooks activos (registrados en `settings.json`)

| Script | Evento | Matcher | Descripción |
|--------|--------|---------|-------------|
| `pre-edit-protection.sh` (→ `.js`) | `PreToolUse` | `Edit\|Write` | Bloquea edición de archivos sensibles según `protected-patterns.json` |
| `rules-inject.sh` (→ `.js`) | `PreToolUse` | `Edit\|Write` | Mecanismo real de carga de `.claude/rules/*.md`: matchea el `file_path` contra el frontmatter `paths:` de cada rule y, si matchea, inyecta su contenido vía `hookSpecificOutput.additionalContext`. No bloquea nada — el frontmatter `paths:` no tiene ningún mecanismo de carga nativo en Claude Code sin este hook. |
| `command-write-protection.sh` (→ `.js`) | `PreToolUse` | `Bash\|PowerShell` | Bloquea comandos que escriben (`>`, `sed -i`, `Set-Content`, etc.) sobre un patrón protegido (mismo `protected-patterns.json` que `pre-edit-protection.js`). `Edit`/`Write` no cubren escritura vía shell — sin este hook, `Bash`/`PowerShell` evaden la protección por completo. |

## Nota técnica — parseo de JSON y patrones compartidos

Los hooks `.js` parsean el JSON de entrada con **Node** (garantizar que `node` esté en el
`PATH` del entorno donde corre Claude Code — es la única dependencia real de este mecanismo).

El payload real de `PreToolUse` está **anidado**: `{ tool_name, tool_input: { file_path,
command, ... }, ... }`, no `{ file_path, ... }` en la raíz. `Edit`/`Write` traen
`tool_input.file_path`; `Bash`/`PowerShell` traen `tool_input.command`.

`protected-patterns.json` es la fuente única de patrones protegidos — la leen tanto
`pre-edit-protection.js` (contra `file_path`) como `command-write-protection.js` (contra el
texto del comando). Agregar un patrón ahí lo aplica a ambas vías de escritura sin duplicar
la lista. Trae un set neutral de partida (`.env`, `secrets/`, `.git/`, `node_modules/`,
`settings.local.json`, claves privadas) — súmale lo que sea sensible en tu proyecto.

## Control de flujo de hooks

| Exit code | Efecto |
|-----------|--------|
| `exit 0` | La operación procede normalmente |
| `exit 2` | La operación es BLOQUEADA — stderr se muestra a Claude como razón |
| `exit 1` | Error del hook — no bloquea la operación |

## Agregar un nuevo hook

1. Crear el script en este directorio (ej. `mi-hook.sh`)
2. Darle permisos de ejecución: `chmod +x .claude/hooks/mi-hook.sh`
3. Registrarlo en `.claude/settings.json`:

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Edit|Write",
      "hooks": [
        { "type": "command", "command": ".claude/hooks/mi-hook.sh" }
      ]
    }
  ]
}
```

## Eventos disponibles

- `PreToolUse` — antes de ejecutar una herramienta (puede bloquear con exit 2)
- `PostToolUse` — después de que una herramienta termina
- `UserPromptSubmit` — cuando el usuario envía un prompt
- `Stop` — cuando Claude termina de responder
- `SubagentStart` / `SubagentStop` — ciclo de vida de subagentes
- `Notification` — cuando Claude necesita atención
- `SessionStart` / `SessionEnd` — ciclo de vida de sesión
