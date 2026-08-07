# HU-051 (+052+055) — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `photo/develop.py` | El motor: `TransformSpec` (contrato), `build_plan` (valida todo antes de tocar fotos), `apply_pipeline` (aplica y deja historial) + `clahe`, `white_balance`, `saturation` |
| `tests/photo/test_develop.py` | 16 tests: contrato, validación previa, no-mutación, determinismo byte a byte, y el comportamiento de cada retoque |

**El contrato quedó demostrado, no prometido:** hay un test que registra un transform falso
y el motor lo ejecuta sin cambiar una línea de `apply_pipeline`. Agregar = registrar, igual
que etapas y reportes.

**El plan se valida entero antes de tocar la primera foto**: un parámetro mal escrito en el
perfil falla con el nombre del paso, no a mitad de un lote de 100 fotos.

**Trazabilidad**: cada aplicación produce el `Transform` de HU-159 y el pipeline devuelve el
`TransformHistory` — la evidencia auditable ya existía como contrato; ahora se llena.

**White balance con calidez solo en luces** (referencia revelado 25-jul): ganancia ponderada
por luminancia local — test con imagen mitad luces / mitad sombras que verifica la asimetría.

Evidencia: **577 tests (16 nuevos) · `develop.py` 100% · total 99%**.
