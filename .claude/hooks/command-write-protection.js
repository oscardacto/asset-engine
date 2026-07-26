// Hook: PreToolUse (Bash|PowerShell) — bloquea comandos que escriben sobre archivos protegidos.
//
// Corrige un gap real (hallado y verificado empíricamente en la auditoría ARB 2026-07-23):
// pre-edit-protection.js solo cubre las herramientas Edit/Write. Bash y PowerShell escriben
// archivos por su cuenta (redirección, sed -i, Set-Content, etc.) y evadían por completo la
// protección. Best-effort por diseño: analiza el texto del comando, no un parser de shell
// completo — un comando suficientemente ofuscado (indirección de variables, etc.) puede
// evadirlo. Ceremonia proporcional: cierra el caso obvio y frecuente, no pretende ser
// una sandbox de seguridad exhaustiva.

const fs = require('fs');
const path = require('path');

const PATTERNS = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'protected-patterns.json'), 'utf8')
);

// Verbos/operadores que indican que el comando ESCRIBE un archivo (no solo lo lee).
const WRITE_INDICATORS = [
  />>?(?!=)/, // > o >> (no >=)
  /\bsed\b[^\n]*-i\b/i,
  /\btee\b/i,
  /\bcp\b/i,
  /\bmv\b/i,
  /\bdd\b/i,
  /\btruncate\b/i,
  /Set-Content/i,
  /Out-File/i,
  /Add-Content/i,
  /New-Item/i,
  /Copy-Item/i,
  /Move-Item/i,
  /Rename-Item/i,
];

let raw = '';
process.stdin.on('data', (c) => (raw += c));
process.stdin.on('end', () => {
  let command = '';
  try {
    const input = JSON.parse(raw);
    command = (input.tool_input && input.tool_input.command) || '';
  } catch (e) {
    process.exit(0);
  }
  if (!command) process.exit(0);

  const looksLikeWrite = WRITE_INDICATORS.some((re) => re.test(command));
  if (!looksLikeWrite) process.exit(0);

  const hit = PATTERNS.find((p) => new RegExp(p).test(command));
  if (hit) {
    process.stderr.write(`BLOCKED: el comando parece escribir sobre un archivo protegido (patrón: ${hit}).\n`);
    process.stderr.write('Comando: ' + command.slice(0, 300) + '\n');
    process.stderr.write('No uses Bash/PowerShell para modificar configuración sensible. Consulta al usuario si de verdad hace falta.\n');
    process.exit(2);
  }
  process.exit(0);
});
