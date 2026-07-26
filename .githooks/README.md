# .githooks — protección agnóstica de herramienta

Los hooks de `.claude/hooks/` solo existen cuando quien edita es **Claude Code**. Si
mañana este repo se toca con Cursor, Copilot o un editor a mano, `pre-edit-protection` y
`command-write-protection` no corren y un `.env` puede terminar comiteado. Este
directorio mueve la última línea de defensa a **git**, el único punto por el que pasan
todos los commits.

## Activación (una vez por clon)

```
git config core.hooksPath .githooks
```

Sin este comando, git usa `.git/hooks/` (vacío) y esta protección **no existe** — está
documentado como paso de setup en el README raíz.

## Qué hace

`pre-commit` → `check-protected.js`: revisa los archivos **staged** contra
`.claude/hooks/protected-patterns.json` (la misma fuente de verdad que los hooks de
Claude Code) y aborta el commit si alguno matchea. Requiere Node en el PATH — la misma
dependencia que ya tienen los hooks del template.

## Escape consciente

`git commit --no-verify` salta el hook. Es deliberado: la protección existe para impedir
el accidente, no para impedir una decisión humana explícita.

## Límites conocidos

- No impide **editar** el archivo, solo comitearlo (la edición la cubren los hooks de
  Claude Code cuando la herramienta es Claude Code).
- `core.hooksPath` es configuración local por clon — un clon nuevo sin el paso de setup
  queda sin protección. Defensa en profundidad, no sandbox.
