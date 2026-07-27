# HU-006 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/ingest/hashing.py` | `compute_content_hash(path)` (SHA-256 hex, lectura en bloques de 1 MiB), `HASH_ALGORITHM`, `DuplicateGroup` (frozen: hash + rutas) y `find_duplicate_groups(paths)` (solo grupos de 2+, ordenados) |
| `src/media_optimizer/ingest/__init__.py` | Re-exporta los 4 nombres nuevos (9 públicos en `ingest/`) |
| `tests/ingest/test_hashing.py` | 15 tests: identidad por contenido, vector conocido de SHA-256, agrupamiento, independencia del orden de entrada, lectura por bloques, ilegible, no-destructividad + capa secundaria |

Decisiones aplicadas de la spec: SHA-256 sin prefijo para que el usuario pueda verificar
el catálogo a mano con `Get-FileHash` (A-1); "duplicado exacto" = byte a byte, los
near-duplicates perceptuales quedan para HU-075 (A-2); sin pre-filtro por tamaño porque
todo asset necesita su hash igualmente para el catálogo (A-5).

Dos tests que valen más que su tamaño:
- **Vector conocido** (`e3b0c442…b855`, SHA-256 del contenido vacío): prueba que se computa
  el algoritmo estándar y no una variante propia — si alguien cambia el algoritmo sin
  querer, falla aquí y no al descubrir que un catálogo viejo ya no casa.
- **Independencia del orden de entrada**: la misma lista invertida produce idéntico
  resultado, que es la garantía real de "sin dependencia del orden del filesystem".

Evidencia DEV (2026-07-26): **128 tests passed (15 nuevos) · cobertura `ingest/` 100%**
(102/102 stmts, gate ≥80%) · ruff check/format limpios · mypy Success (12 archivos) —
todo verde en la primera ejecución, sin correcciones.
