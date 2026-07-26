#!/usr/bin/env node
// Bloquea el commit si hay archivos protegidos en el staging area.
//
// Cierra un riesgo aceptado del template original: los hooks de .claude/hooks/ solo
// existen para Claude Code — si el repo se toca con Cursor, Copilot o un editor a mano,
// esa protección no corre. Este hook corre en GIT, el único punto por el que pasan
// todos los commits sin importar qué herramienta editó los archivos.
//
// Fuente única de verdad: .claude/hooks/protected-patterns.json (el mismo JSON que usan
// los hooks de Claude Code) — un patrón nuevo protege en ambas capas a la vez.

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const PATTERNS = JSON.parse(
  fs.readFileSync(
    path.join(__dirname, '..', '.claude', 'hooks', 'protected-patterns.json'),
    'utf8'
  )
);

const staged = execSync('git diff --cached --name-only --diff-filter=ACMR', {
  encoding: 'utf8',
})
  .split('\n')
  .filter(Boolean);

const hits = staged.filter((f) => PATTERNS.some((p) => new RegExp(p).test(f)));

if (hits.length > 0) {
  console.error('BLOCKED: intento de comitear archivos protegidos:');
  hits.forEach((f) => console.error('  - ' + f));
  console.error('Patrones: .claude/hooks/protected-patterns.json');
  console.error(
    'Si es realmente intencional: git commit --no-verify (decisión humana explícita).'
  );
  process.exit(1);
}
process.exit(0);
