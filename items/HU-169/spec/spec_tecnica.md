# Spec Técnica `HU-169` — `Utilidades de determinismo`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-08-06
> **Confianza global:** 91% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** lo que hace verificable el KPI número uno del producto — misma entrada,
  misma salida byte a byte.
- **Para quién:** HU-164 (golden tests), HU-185 (smoke E2E), HU-036/181 (reportes).
- **Módulo:** `media_optimizer.core.determinism` — puro, sin IO (ver P-1).
- **No obvio — de las tres fuentes clásicas de no-determinismo, la que este proyecto tiene
  no es la que se espera.** Lo primero que suena al decir "determinismo" son las semillas
  aleatorias; pero `testing/synthetic.py` ya usa `np.random.default_rng(seed)`, que es un
  generador propio con semilla explícita, y **no hay aleatoriedad global en ninguna parte**.
  Construir un gestor de semillas sería resolver un problema que no existe. Las dos fuentes
  que sí existen se midieron y ninguna se ve a simple vista:
  **el orden de un conjunto cambia en cada proceso**, y **el mismo nombre de archivo ordena
  distinto según el sistema que lo entregue**.

---

## 2. Alcance

### 2.1 IN
- `stable_text(value)`: la forma canónica de un texto (NFC), para que dos representaciones
  del mismo nombre visible sean el mismo dato.
- `stable_order(items)` / `stable_order_by(items, key)`: orden que no depende de la
  plataforma que entregó los nombres.
- **Arreglo del defecto medido en `QualityReport.flags`** (HU-158): pasa de `frozenset` a
  colección ordenada. Conserva las semánticas de conjunto que importan —sin duplicados,
  pertenencia con `in`— y gana orden estable.
- Arnés de reproducibilidad: comprobar que una operación produce **los mismos bytes en dos
  procesos con semillas de hash distintas**.

### 2.2 OUT
- **Gestor de semillas aleatorias** → **no se construye**: no hay aleatoriedad global que
  gestionar. `default_rng(seed)` ya es el patrón correcto y está en uso. Si algún día entra
  una dependencia con estado aleatorio global, entra con su HU.
- **Golden tests** (comparación de imágenes con tolerancia) → HU-164.
- **Smoke E2E del pipeline completo** → HU-185; aquí nace el arnés que usará.
- **Normalizar nombres al escribir** → ya resuelto en HU-016 (`workspace._sanear` hace NFC).

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | El mismo nombre en NFC y en NFD | Se consideran **el mismo texto**; ordenan igual |
| 2 | Flags repetidos al construir un reporte | Se descartan los duplicados, como haría un conjunto |
| 3 | Textos que solo difieren en mayúsculas | Ordenan por código de carácter, sin `casefold`: dos nombres distintos siguen siendo distintos (a diferencia de HU-016, donde el problema era el sistema de archivos) |
| 4 | Colección vacía | Devuelve vacío; no es un error |

---

## 3. Componentes

| Componente | Cambio | Verificado |
|---|---|---|
| `src/media_optimizer/core/determinism.py` | nuevo | ✅ no existe en `develop` |
| `src/media_optimizer/core/quality_report.py` | **arregla el defecto de orden** | ✅ leído: `flags: frozenset[str]` |
| `src/media_optimizer/core/__init__.py` | exporta las utilidades | ✅ leído |
| `tests/core/test_determinism.py` | nuevo | ✅ no existe |
| `tests/core/test_quality_report.py` | ajusta 1 aserción de igualdad | ✅ leído: 2 consumidores de `.flags`, ambos triviales |

### 3.1 Reutilizables
| Componente | ¿Reutilizar? | Justificación |
|---|---|---|
| `unicodedata.normalize` | Sí | Es la operación exacta; `workspace._sanear` ya la usa para lo mismo |
| Patrón de normalización en `__post_init__` | Sí | Cinco contratos del proyecto ya ordenan al construir |

---

## 4. Modelo de datos

No hay estructuras nuevas: son funciones puras y un cambio de tipo en un contrato existente.

```
QualityReport.flags:  frozenset[str]  ──▶  tuple[str, ...]  (ordenado, sin duplicados)
```

**Por qué se cambia el tipo en vez de ordenar al serializar.** Ordenar en cada serializador
funciona hasta que alguien escribe uno nuevo y lo olvida; el fallo aparecería como un golden
test que falla 1 de cada N corridas mostrando los mismos flags en otro orden — indistinguible
del ruido. Es el mismo razonamiento que en HU-168: **la disciplina la sostiene el tipo, no la
memoria de quien escribe el siguiente módulo.**

Lo que se pierde: pertenencia en O(1). Con menos de diez flags por asset, es irrelevante.

---

## 5. Reglas de negocio

| # | Regla | Fuente | Implicación |
|---|-------|--------|-------------|
| RN-1 | Misma entrada ⇒ misma salida byte a byte | charter §6.1 · KPI §7 | Ninguna salida puede depender del orden de un conjunto |
| RN-2 | Sin dependencia del orden del filesystem | `python.md` | Ya cubierto por el scanner; se complementa con NFC |
| RN-3 | `core/` puro, sin IO | CLAUDE.md | Solo `unicodedata` de la stdlib |
| RN-4 | Cobertura ≥95% en dominio puro | Pre-Flight | Evidencia al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|-----------|----------|
| V-1 | Dos procesos con semillas de hash distintas producen los mismos bytes | test con subprocesos |
| V-2 | Un nombre en NFD y el mismo en NFC ordenan igual | test |
| V-3 | Los flags de un reporte iteran siempre en el mismo orden | test |
| V-4 | Los flags duplicados se descartan | test |

---

## 6. Preguntas abiertas

### P-1 — ¿`core/determinism.py` o módulo de nivel superior?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** dentro de `core/`. Es puro —solo `unicodedata`— y **lo consumen
  los propios contratos de `core/`**. Ponerlo arriba obligaría a que el dominio importara
  un módulo externo a él, que es justo lo que la regla de hexagonal ligera evita. Distinto
  de `workspace` y `logs`, que sí tocan disco y por eso no pueden vivir en `core/`.
- **Estado:** ABIERTA (ratificable con la integración)

### P-2 — ¿Cambiar `QualityReport.flags` cuenta como rework de HU-158?
- **Categoría:** IMPORTANTE (no bloqueante) — es de gobernanza, no técnica
- **Mi mejor hipótesis:** **sí**, y se registra como tal en el gate-log contra HU-158. El
  contrato se cerró con un defecto latente de reproducibilidad; que no rompiera nada
  todavía no lo vuelve correcto. Registrarlo como rework mantiene honesta la métrica de
  calidad — sería fácil disimularlo como "mejora" de HU-169.
- **Estado:** ABIERTA

---

## 7. Asunciones

| # | Asunción | Costo si se rompe |
|---|----------|-------------------|
| A-1 | `determinism` vive en `core/` (P-1) | Mover un archivo |
| A-2 | No hace falta gestor de semillas: no hay aleatoriedad global | Añadir el gestor con su HU cuando exista el problema |
| A-3 | Perder pertenencia O(1) en flags es irrelevante (<10 por asset) | Volver a `frozenset` + accesor ordenado |
| A-4 | NFC es la forma canónica correcta (no NFD) | Cambiar una constante; NFC es lo que ya usa HU-016 |

---

## 8. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|--------|-------|---------|------------|
| R-1 | Aparezcan más colecciones sin orden en contratos futuros | **alta** | alto | Test que recorre los contratos de `core/` y falla si alguno expone un `set`/`frozenset` |
| R-2 | El arnés de subprocesos sea lento y estorbe la batería | media | bajo | Un único test con dos subprocesos; se mide el tiempo al cierre |
| R-3 | Cambiar el tipo de `flags` rompa un consumidor | baja | bajo | **Verificado**: solo 2 consumidores, ambos en tests |

---

## 9. Confianza global

- **Preguntas abiertas:** 2 — **0 bloqueantes**
- **Verificaciones cruzadas:**
  - [x] **Los dos defectos se midieron**, no se supusieron: 4 semillas de hash con 4 órdenes
        distintos, y la divergencia NFC/NFD con un caso concreto
  - [x] Verificado que **no hay aleatoriedad global**: `synthetic.py` usa `default_rng(seed)`
  - [x] Consumidores de `.flags` contados en código: 2, ambos en tests
  - [x] `workspace._sanear` leído: ya normaliza a NFC, la elección es consistente
  - [x] Charter §6.1 y KPI §7 leídos
- **Recomendación:** ✅ **LISTA PARA DEV**
- **Confianza: 91%.** El 9% es P-2 (gobernanza) y R-1.

---

## 10. Dependencias
| ID | Relación | Estado |
|----|----------|--------|
| HU-150, HU-158, HU-166 | Esqueleto, `QualityReport`, fixtures sintéticos | DONE |
| HU-164, HU-185, HU-036, HU-181 | Lo consumirán | backlog |

---

## 11. Criterios de aceptación

- **CA-1** — Un texto en NFD y el mismo en NFC se consideran iguales tras `stable_text`.
- **CA-2** — Una lista de nombres ordena igual llegue en NFC o en NFD.
- **CA-3** — `QualityReport.flags` itera siempre en el mismo orden.
- **CA-4** — Dos procesos con `PYTHONHASHSEED` distinto producen **los mismos bytes** para el mismo reporte.
- **CA-5** — Los flags duplicados se descartan; la pertenencia con `in` sigue funcionando.
- **CA-6** — Ningún contrato de `core/` expone un `set`/`frozenset` en su API pública.
- **CA-7** — `stable_order_by` ordena objetos por una clave textual, con la misma garantía.
- **CA-8** — Una colección vacía no es un error.
- **CA-9** — `core/` sigue sin IO y sin importar infraestructura.
- **CA-10** — Cobertura ≥95% y batería verde.
- **CA-11** — El rework de HU-158 queda registrado en el gate-log.

---

## 12. Historial de cambios
| Fecha | Cambio | Por |
|-------|--------|-----|
| 2026-08-06 | Creación, sobre dos defectos de determinismo medidos en código integrado | Claude (ejecutor) |
