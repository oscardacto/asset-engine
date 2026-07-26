// Hook: PreToolUse (Edit|Write) — bloquea escritura directa en archivos protegidos.
// Ver protected-patterns.json (fuente única, compartida con command-write-protection.js).

const fs = require('fs');
const path = require('path');

const PATTERNS = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'protected-patterns.json'), 'utf8')
);

let raw = '';
process.stdin.on('data', (c) => (raw += c));
process.stdin.on('end', () => {
  let filePath = '';
  try {
    const input = JSON.parse(raw);
    filePath = (input.tool_input && input.tool_input.file_path) || '';
  } catch (e) {
    process.exit(0);
  }
  if (!filePath) process.exit(0);

  const hit = PATTERNS.find((p) => new RegExp(p).test(filePath));
  if (hit) {
    process.stderr.write(`BLOCKED: '${filePath}' está en la lista de archivos protegidos (patrón: ${hit}).\n`);
    process.stderr.write('Este archivo no debe modificarse directamente. Consulta al usuario si necesitas hacer cambios en configuración sensible.\n');
    process.exit(2);
  }
  process.exit(0);
});
