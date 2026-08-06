# HU-016 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/workspace.py` | `Workspace` (raíz + `reports/` + `ensure()`), `safe_output_name(name, taken)`, `fingerprint_sources` / `find_modified_sources` |
| `src/media_optimizer/ingest/filesystem.py` | Se añade `make_directory` a la capa: crear carpetas también es IO |
| `tests/test_workspace.py` | 20 tests: layout, nombres escribibles, dispositivos, colisiones, determinismo, originales intactos + capa secundaria |

**Es el problema inverso de HU-010.** Allí había que poder *leer* cualquier nombre que el
sistema admita; aquí hay que evitar *crear* nombres que después nadie pueda abrir — porque
la capa de acceso, al saltarse la normalización, permite escribir `foto.jpg.` y ese archivo
solo sería accesible con la forma extendida.

**La colisión que importa:** en NTFS `Foto.jpg` y `foto.jpg` no coexisten; el segundo pisa
al primero **en silencio**. La comparación de nombres ya usados es `casefold`, y hay test
específico. Sin eso, dos fotos distintas del usuario podrían acabar en el mismo archivo.

**"No destructivo" pasa de promesa a comprobación:** `fingerprint_sources` toma el hash de
cada original antes de escribir y `find_modified_sources` los vuelve a comparar después.
Usa el contenido, no la fecha — hay test que lo demuestra tocando el `mtime` sin alterar
los bytes.

Evidencia DEV: **302 tests passed (20 nuevos) · `workspace.py` 100%** · ruff y mypy limpios.
