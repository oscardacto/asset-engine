# Entregables — HU-070+071+072+074+078+180+184

| CA | Resultado |
|----|-----------|
| CA-1 Score ponderado normalizado, determinista | ✅ 3 tests |
| CA-2 Portada: solo publicables elegibles, top-N | ✅ 2 tests |
| CA-3 Galería: gancho primero, orden estable | ✅ 4 tests |
| CA-4 Elegibilidad por formato: la corta cae solo de su intención | ✅ 3 tests |
| CA-5 Los descartes no entran en nada | ✅ 2 tests |
| CA-6 selection.json byte-idéntico; `run select` y `report selection` funcionan | ✅ |
| CA-7 Sin analysis ⇒ mensaje accionable; cobertura dominio 100% | ✅ |
| CA-8 `run all` ejecuta las 4 etapas y propaga `partial` | ✅ 2 tests |

**7 HUs · 0 fallidos · sin rework.**

## Evidencia con el lote real (`sala/`, 16 fotos)
```
run all               → catalog + analysis + develop + selection en 2m31s
report selection      → 5 candidatas a portada, galería de 16 con gancho
originales            → huella SHA-256 idéntica antes y después (fb1e874ea3450dcb)
dos corridas          → los 4 JSON y las 16 derivadas, byte a byte idénticos
```
