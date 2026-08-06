# Spec Técnica `HU-016` — `Directorio de trabajo no destructivo`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Confianza global:** 89% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** dónde van las salidas, la garantía de que los originales no se tocan, y
  cómo convertir un nombre de entrada en un nombre de salida escribible.
- **Para quién:** HU-017 (CLI), HU-057 (sidecar), HU-061 (export), HU-036/181 (reportes).
- **Módulo:** `media_optimizer.workspace` — módulo nuevo de nivel superior (ver P-1).
- **No obvio:** es el **problema inverso de HU-010**. Allí el objetivo era poder leer
  cualquier nombre que el sistema de archivos admita; aquí es no *crear* nombres que luego
  nadie pueda abrir. La capa de acceso, al saltarse la normalización de Windows, permite
  escribir `foto.jpg.` — y ese archivo después solo es accesible con la forma extendida.
  Y hay un segundo caso medido en HU-010: **`Foto.jpg` y `foto.jpg` no coexisten en NTFS**,
  el segundo sobrescribe al primero en silencio. Dos assets distintos pueden pisarse sin
  dejar traza.

---

## 2. Alcance

### 2.1 IN
- `workspace.py`:
  - `Workspace` (frozen): `root` + las carpetas que hoy existen (`reports/`), con `ensure()`
    que las crea vía la capa de ADR-004.
  - `safe_output_name(name, taken)` — nombre escribible y **sin colisión**, determinista.
  - `fingerprint_sources(paths)` / `verify_unchanged(fingerprint)` — la garantía de que el
    origen quedó intacto, comprobable y no solo prometida.
- Saneamiento: caracteres prohibidos, nombres de dispositivo, punto/espacio final, longitud.
- Desambiguación por colisión **insensible a mayúsculas** (la que NTFS provoca).

### 2.2 OUT
- El **contenido** de cada salida → su propia HU (57, 61, 36, 181).
- Subcarpetas de revelados/reels → nacen con sus HUs; crearlas ahora sería inventar layout
  sin consumidor.
- Limpieza o rotación del directorio de trabajo → sin HU asignada; se anota.
- Copiar los originales al directorio de trabajo → **prohibido** (charter §6.3).

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|---|---|
| 1 | `Foto.jpg` y `foto.jpg` en el mismo lote | El segundo recibe sufijo determinista; no se pisan |
| 2 | Nombre que es un dispositivo (`CON.jpg`) | Se sanea al escribir, aunque al leer funcionara |
| 3 | Nombre vacío tras sanear | Se sustituye por un marcador estable |

---

## 3. Componentes

| Componente | Cambio | Verificado |
|---|---|---|
| `src/media_optimizer/workspace.py` | nuevo | ✅ no existe en `develop` (f2c0e79) |
| `tests/test_workspace.py` | nuevo | ✅ no existe |

### 3.1 Reutilizables
| Componente | ¿Reutilizar? | Justificación |
|---|---|---|
| `ingest.filesystem` (HU-010) | Sí, **obligatorio** | ADR-004: todo IO por la capa. El test de gobernanza lo verifica |
| `compute_content_hash` (HU-006) | Sí | La huella del origen es el hash que ya calculamos |
| Nombres de dispositivo de HU-010 | Sí (la lista) | Ya medidos empíricamente |

---

## 4. Modelo de datos
`Workspace` y `SourceFingerprint` en memoria. El layout es una convención de carpetas.

---

## 5. Reglas de negocio

| # | Regla | Fuente | Implicación |
|---|---|---|---|
| RN-1 | "originales intactos; toda salida a directorio de trabajo" | charter §6.3 | Nunca se escribe en la carpeta de origen; hay función que lo comprueba |
| RN-2 | "el nombre sí se normaliza al escribir" | ADR-004 §4 corolario | Saneamiento obligatorio en la salida |
| RN-3 | Todo IO por la capa | ADR-004 §2 | `workspace` no abre archivos por su cuenta |
| RN-4 | Determinismo | charter §6.1 | El mismo nombre de entrada produce siempre el mismo nombre de salida |
| RN-5 | Cobertura ≥80% | Pre-Flight | Evidencia al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | Un nombre saneado es escribible **y** releíble por ruta normal | test |
| V-2 | Dos nombres que colisionan por mayúsculas producen salidas distintas | test |
| V-3 | Tras escribir salidas, el hash de cada origen no cambió | test |

---

## 6. Preguntas abiertas

### P-1 — ¿Dónde vive el módulo?
- **Categoría:** IMPORTANTE (no bloqueante)
- **Mi mejor hipótesis:** módulo de nivel superior `media_optimizer/workspace.py`, no dentro
  de `ingest/`. El directorio de trabajo lo usan **todas** las etapas (análisis, revelado,
  reels), no solo la ingesta; anidarlo en `ingest` obligaría a que `photo/` y `video/`
  importen de la capa de entrada. **Si se acepta, CLAUDE.md debería sumar esa fila**, igual
  que se hizo con `ingest/`.
- **Costo si se asume mal:** mover un módulo de 2 archivos.
- **Estado:** ABIERTA (ratificable con la integración)

### P-2 — ¿Sufijo de desambiguación: numérico o hash?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** numérico corto y estable (`nombre_2.jpg`), asignado por orden
  determinista. Un sufijo de hash sería inequívoco pero ilegible, y estos nombres los va a
  leer una persona en su carpeta de salida.
- **Estado:** ABIERTA

---

## 7. Asunciones

| # | Asunción | Costo si se rompe |
|---|---|---|
| A-1 | `workspace` es módulo de nivel superior | Mover el módulo |
| A-2 | Sufijo numérico determinista | Cambiar una función |
| A-3 | Solo se crea `reports/` por ahora; el resto con sus HUs | Añadir carpetas (aditivo) |
| A-4 | La verificación de intocabilidad usa el hash de contenido, no `mtime` (que el SO puede alterar solo) | Ninguno: el hash es más estricto |

---

## 8. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|---|
| R-1 | Un consumidor escriba sin sanear y cree un archivo inaccesible | media | medio | La API de escritura pasa por `safe_output_name`; documentado en el docstring |
| R-2 | Colisión no detectada por comparar sensible a mayúsculas | media | **alto** (pérdida silenciosa) | La comparación es `casefold`; test explícito con el caso de NTFS |
| R-3 | Sanear tanto que dos nombres distintos colapsen en uno | media | alto | El desambiguador se aplica **después** de sanear, sobre el resultado |

---

## 9. Confianza global

- **Preguntas abiertas:** 2 — **0 bloqueantes**
- **Verificaciones cruzadas:**
  - [x] Codebase leído (`develop f2c0e79`, 274 tests verdes)
  - [x] Consumidores cruzados en el backlog (HU-017/036/057/061/181)
  - [x] Corolario de ADR-004 leído: leer y escribir son problemas distintos
  - [x] Evidencia de colisión por mayúsculas **medida en HU-010**, no supuesta
  - [x] Reutilizables verificados en código
- **Recomendación:** ✅ **LISTA PARA DEV**
- **Confianza: 89%.** El 11%: P-1 (ubicación, con implicación de gobernanza) y R-3.

---

## 10. Dependencias
| ID | Relación | Estado |
|---|---|---|
| HU-010, HU-012, HU-006 | Capa, catálogo, hash | DONE |
| HU-017, HU-036, HU-057, HU-061, HU-181 | Escribirán aquí | backlog |

---

## 11. Criterios de aceptación

- **CA-1** — `ensure()` crea el directorio de trabajo y `reports/` si no existen, y es idempotente.
- **CA-2** — Un nombre con caracteres prohibidos, punto o espacio final produce un nombre escribible **y releíble por ruta normal**.
- **CA-3** — Un nombre de dispositivo (`CON.jpg`) se sanea al escribir.
- **CA-4** — `Foto.jpg` y `foto.jpg` producen nombres de salida **distintos**.
- **CA-5** — El saneamiento es determinista: mismo nombre ⇒ mismo resultado.
- **CA-6** — Tras crear el directorio y escribir salidas, el hash de cada archivo de origen no cambió.
- **CA-7** — Un nombre que queda vacío tras sanear recibe un marcador estable.
- **CA-8** — El test de gobernanza sigue verde: `workspace` no toca disco fuera de la capa.
- **CA-9** — Cobertura ≥80% y batería verde.
- **CA-10** — Trazabilidad en el gate-log.

---

## 12. Historial de cambios
| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación; resuelve el lado de la escritura que ADR-004 delimitó | Claude (ejecutor) |
