// Hook: PreToolUse — inyecta el contenido de .claude/rules/*.md cuyo frontmatter `paths:`
// matchee el archivo que se va a Editar/Escribir. No bloquea nada — solo agrega contexto
// (o nada, si ninguna regla matchea). Ver .claude/rules/README-mecanismo.md.
//
// Corrige C1: el frontmatter `paths:` de rules/*.md no tenía ningún mecanismo real de
// carga en Claude Code (era metadata inerte, heredada de la convención `globs:` de
// .cursor/rules/*.mdc que Claude Code no replica). Este hook es el mecanismo real.

const fs = require('fs');
const path = require('path');

function globToRegex(glob) {
  let re = '';
  let i = 0;
  while (i < glob.length) {
    if (glob.startsWith('**/', i)) {
      re += '(?:.*/)?';
      i += 3;
    } else if (glob.startsWith('**', i)) {
      re += '.*';
      i += 2;
    } else if (glob[i] === '*') {
      re += '[^/]*';
      i += 1;
    } else {
      re += glob[i].replace(/[-/\\^$+?.()|[\]{}]/g, '\\$&');
      i += 1;
    }
  }
  return new RegExp('^' + re + '$');
}

function parseRuleFile(fullPath) {
  const content = fs.readFileSync(fullPath, 'utf8');
  const fmMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!fmMatch) return null;
  const [, frontmatter, body] = fmMatch;
  const pathsBlock = frontmatter.match(/paths:\n((?:\s*-\s*.*\n?)+)/);
  if (!pathsBlock) return null;
  const globs = [];
  const globRe = /-\s*"([^"]+)"/g;
  let m;
  while ((m = globRe.exec(pathsBlock[1])) !== null) globs.push(m[1]);
  return { globs, body: body.trim() };
}

function main() {
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

    const normalized = filePath.replace(/\\/g, '/');
    const rulesDir = path.join('.claude', 'rules');

    let files = [];
    try {
      files = fs.readdirSync(rulesDir).filter((f) => f.endsWith('.md'));
    } catch (e) {
      process.exit(0);
    }

    const hits = [];
    for (const f of files) {
      const parsed = parseRuleFile(path.join(rulesDir, f));
      if (!parsed) continue;
      const matched = parsed.globs.some((g) => globToRegex(g).test(normalized));
      if (matched) hits.push({ file: f, body: parsed.body });
    }

    if (hits.length === 0) process.exit(0);

    const context = hits
      .map((h) => `## Regla activada por path: ${h.file}\n\n${h.body}`)
      .join('\n\n---\n\n');

    process.stdout.write(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'allow',
          additionalContext: context,
        },
      })
    );
    process.exit(0);
  });
}

main();
