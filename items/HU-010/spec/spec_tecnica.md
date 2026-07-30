# Spec Técnica `HU-010` — `Acceso al filesystem: rutas y nombres que hoy detienen el pipeline`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 92% — ver sección 9
>
> **Nota de alcance:** el título del backlog ("Paths unicode, nombres hostiles y colisiones
> de nombre") describía la hipótesis inicial. La evidencia la refutó: no es un problema de
> nombres. Ver §13 (ajustes propuestos al backlog).

---

## 1. Resumen ejecutivo

- **Qué se pide:** que ningún archivo de la carpeta de entrada pueda bloquear, detener ni
  hacer desaparecer material del pipeline.
- **Para quién:** todo el pipeline. Es la HU que hace cumplir el invariante I-1 de ADR-004,
  hoy demostrablemente roto.
- **Módulo / dominio:** `media_optimizer.ingest` — módulo nuevo `filesystem.py` + migración
  de los seis módulos de `ingest/` que hoy tocan disco. Cobertura ≥80%.
- **No obvio:** la solución **no** es detectar nombres peligrosos. Con la ruta adaptada, los
  archivos "peligrosos" se leen perfectamente (70/70 operaciones correctas). Una lista negra
  habría descartado material legítimo del usuario y repartido lógica de plataforma por todo
  el código. **Esta HU no añade validación: elimina la necesidad de validar.**

---

## 2. Alcance

### 2.1 IN
- `ingest/filesystem.py`: capa única de acceso a disco (contratos en §5).
- **Migración** de `scanner.py`, `formats.py`, `hashing.py`, `quarantine.py`, `exif.py` y
  `dimensions.py` para que ninguno abra archivos ni consulte metadatos por su cuenta.
- Corrección del invariante I-2: el escaneo deja de perder rutas largas en silencio.
- Test de cumplimiento que detecta cualquier acceso directo a disco fuera de la capa.
- Test del bloqueo (`CON.jpg`) ejecutado con aislamiento y timeout.

### 2.2 OUT
- **Saneamiento de nombres al escribir salidas** → HU-016 (es el problema inverso: la ruta
  extendida permite *crear* nombres luego inaccesibles). ADR-004 §Decisión 4 lo delimita.
- Colisiones de nombre en el directorio de trabajo (`Foto.jpg` vs `foto.jpg`) → HU-016.
- Verificación de la cadena de video con rutas extendidas → **HU-154** (obligación fijada
  por ADR-004).
- Cambiar `LongPathsEnabled` en el registro de Windows → **descartado**, ver P-3.
- Detección de duplicados por nombres Unicode equivalentes → ya cubierto por HU-006, que
  compara contenido, no nombres.

### 2.3 Casos límite con evidencia
| # | Caso | Tratamiento | Fuente |
|---|---|---|---|
| 1 | `CON.jpg` bloquea el proceso | Se lee correctamente con la ruta adaptada | evidencia §1 |
| 2 | Ruta >260 caracteres omitida en silencio | Entra al lote como cualquier otra | evidencia §1 |
| 3 | `NUL.jpg` devuelve 0 bytes por ruta normal | Verificar con ruta adaptada en DEV (hueco declarado) | evidencia §5 |

---

## 3. Componentes técnicos

| Componente | Cambio | Riesgo | Verificado |
|---|---|---|---|
| `ingest/filesystem.py` | nuevo | bajo (superficie pequeña, muy testeable) | ✅ no existe |
| `ingest/scanner.py` | migrar `Path.walk`, `iterdir` | **medio** — toca el determinismo de HU-001 | ✅ leído |
| `ingest/formats.py`, `hashing.py`, `quarantine.py`, `exif.py`, `dimensions.py` | migrar `open`/`stat` | bajo | ✅ leídos |
| `tests/ingest/test_filesystem.py` | nuevo | bajo | ✅ no existe |

### 3.1 Reutilizables
| Componente | ¿Reutilizar? | Justificación |
|---|---|---|
| `core.InvalidInputError` | Sí | Ya cubre la raíz inválida; no cambia |
| Causas de cuarentena (HU-009/011) | Sí, **sin añadir ninguna** | Que un archivo entre o no deja de depender del nombre: no hace falta una causa nueva |
| Tests de determinismo de HU-001 | Sí, **como red de seguridad** | Son el contrato que la migración no puede romper |

---

## 4. Modelo de datos
Sin entidades nuevas ni persistencia. La forma prefijada es transporte, no dato (ADR-004 §2).

---

## 5. Contratos (sin implementación)

### 5.1 `ingest/filesystem.py` — API pública

```python
def system_path(path: Path) -> str
    """Ruta en la forma que exige la plataforma para acceso fiable.
    Windows: absoluta, resuelta y con prefijo extendido. POSIX: str(path).
    Único punto del sistema que conoce el prefijo. Idempotente."""

def open_binary(path: Path) -> IO[bytes]
def read_bytes(path: Path, offset: int = 0, count: int | None = None) -> bytes
def file_size(path: Path) -> int
def exists(path: Path) -> bool
def is_directory(path: Path) -> bool
def iter_files(root: Path, *, recursive: bool = True) -> Iterator[Path]
    """Archivos bajo root. No sigue enlaces de carpeta, omite ocultos.
    Devuelve rutas SIN prefijar: presentables y comparables."""

def replace_atomic(source: Path, target: Path) -> None
    """Reemplazo atómico en el mismo volumen (lo consume HU-012)."""
```

**Invariantes de la capa**
| # | Invariante |
|---|---|
| F-1 | `system_path` es idempotente: aplicarla dos veces da lo mismo |
| F-2 | Las rutas que **salen** de la capa nunca llevan prefijo |
| F-3 | En POSIX, `system_path(p) == str(p)` — sin ramas de plataforma fuera de aquí |
| F-4 | La capa no interpreta contenido ni traduce a errores de dominio: propaga `OSError` |

**Errores:** `OSError` sin envolver. La traducción a `CorruptMediaError` /
`InvalidInputError` sigue siendo de los módulos de dominio, que ya la hacen.

**Dependencias:** solo `pathlib`, `os`, `sys`. Ninguna hacia otros módulos de `ingest/`
(es la capa más baja).

### 5.2 Lo que NO se crea, y por qué
No hay `NameValidationResult`, `NameIssue`, `validate_path` ni `normalize_name`. La
evidencia mostró que no hay nada que validar en la lectura: **un contrato que no existe no
puede quedar obsoleto**. El saneamiento de nombres al escribir es de HU-016 y tendrá sus
propios contratos allí.

---

## 6. Preguntas abiertas — resueltas

### P-1 — ¿Scanner o validador aparte? → **Ninguno de los dos: adaptador de acceso**
- **Decisión:** capa de acceso a disco, no validador de nombres.
- **Justificación:** *responsabilidad única* — el scanner enumera, no negocia con el SO;
  un validador de nombres tampoco corresponde, porque la evidencia (70/70) demuestra que
  no hay nada que rechazar. *Resiliencia* — un validador deja el bloqueo vivo para quien
  abra el archivo sin pasar por él; el adaptador lo elimina en origen. *Evidencia* — con
  ruta adaptada no falla ninguna operación del stack.
- **Estado:** RESUELTA.

### P-2 — ¿Cuarentena u omisión para nombres peligrosos? → **Ninguna: se procesan**
- **Decisión:** entran al pipeline como cualquier otro archivo. La cuarentena queda para
  causas de contenido (ADR-004 §Decisión 4).
- **Justificación:** *identidad por contenido* (ADR-004 §1) — el nombre no invalida al
  asset. *Resiliencia* — omitir repetiría el anti-patrón de pérdida silenciosa (I-2), y
  cuarentenar reportaría como problemática una foto perfectamente utilizable del usuario.
- **Estado:** RESUELTA.

### P-3 — ¿`LongPathsEnabled` o prefijo? → **Prefijo, en la capa**
- **Decisión:** prefijo de ruta extendida dentro del adaptador. **No** se toca el registro.
- **Justificación:** *límites de autonomía* — `LongPathsEnabled` es configuración de la
  máquina del usuario, no del proyecto; exigirlo trasladaría a cada usuario un requisito de
  instalación con privilegios de administrador. *Portabilidad* — el prefijo funciona sin
  permisos y sin condicionar el entorno. *Evidencia* — se verificó con el registro en `0`,
  es decir, funciona **sin** esa opción activada.
- **Estado:** RESUELTA.

---

## 7. Asunciones explícitas

| # | Asunción | Costo si se rompe |
|---|---|---|
| A-1 | `NUL.jpg` con ruta adaptada se comporta como `CON.jpg` (hueco declarado en la evidencia §5) | Si no, una causa de cuarentena adicional |
| A-2 | Los seis módulos de `ingest/` cubren todo el acceso a disco actual | El test de cumplimiento (§8) lo detecta |
| A-3 | El prefijo no altera el orden determinista de HU-001, porque las rutas salen sin prefijar (F-2) | Los tests de HU-001 lo detectan |
| A-4 | En POSIX el adaptador es identidad y toda la suite pasa igual | CI en Linux lo detectaría (HU-185) |

---

## 8. Estrategia de pruebas

Organizada por lo que **demuestra**, no por tipo de test.

### 8.1 Que la capa hace lo que promete (unitarias)
- `system_path` idempotente (F-1) · resuelve relativas y `..` antes de prefijar ·
  identidad en POSIX (F-3) · las rutas devueltas por `iter_files` no llevan prefijo (F-2).

### 8.2 Que el invariante roto quedó cerrado (regresión sobre evidencia real)
Un test por caso documentado en la evidencia, escrito **desde el caso que hoy falla**:
`CON.jpg`, `NUL.jpg`, `COM1.jpg`, punto final, espacio final, ruta >260, ADS (`foto:a.jpg`).

**Diseño del test de bloqueo:** el caso `CON.jpg` no puede probarse en proceso —colgaría la
suite—. Se ejecuta en **subproceso con timeout**, con la aserción invertida: *la lectura
adaptada retorna antes del límite*. Si alguien revierte la capa, el test no falla con un
error: se agota el tiempo, que es la señal correcta. Marcado para Windows.

### 8.3 Que NO rompimos HU-001 (la garantía que más importa)
- **Los 15 tests de HU-001 se ejecutan sin modificación**: son el contrato.
- Test nuevo: el orden determinista se mantiene **con nombres hostiles mezclados** —
  dos escaneos consecutivos de una carpeta con reservados, punto/espacio final, gemelos
  NFC/NFD y ruta larga devuelven tuplas idénticas.
- Test nuevo: la ruta larga **aparece** en el resultado (hoy desaparece) — cierra I-2.

### 8.4 Que nadie puede reintroducir el problema (cumplimiento)
Test que recorre el código de `ingest/` y **falla si algún módulo distinto de
`filesystem.py` usa `open(`, `.stat(`, `.walk(`, `.iterdir(` o `.exists(` sobre rutas.
Es la única defensa real contra A-2: un módulo futuro que olvide la capa reintroduce el
cuelgue en silencio.

### 8.5 Unicode y equivalencia
- Gemelos NFC/NFD coexistentes: ambos se leen, el orden es estable, y HU-006 los reporta
  como duplicados **por contenido** (no por nombre) — verifica que la identidad de ADR-004
  §1 se sostiene.

### 8.6 No destructivo (I-3)
- Bytes y `mtime` de todos los casos hostiles intactos tras un escaneo + triaje completo.

### 8.7 Portabilidad
Los tests específicos de Windows se marcan con `skipif`; la suite debe pasar entera en
POSIX con la capa en modo identidad.

### 8.8 Lo que NO se hará
**Sin property-based testing.** `hypothesis` sería una dependencia nueva y requeriría su
ADR; además el espacio de entrada aquí no es aleatorio sino un catálogo **conocido y
enumerable** de comportamientos del SO, que se cubre mejor con casos explícitos derivados
de evidencia. Si más adelante aparece un dominio con espacio de entrada realmente amplio
(p. ej. parámetros de revelado), se re-evalúa con su ADR.

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 3 — **todas RESUELTAS**, 0 bloqueantes
- **Asunciones:** 4 (A-1 con hueco de evidencia declarado; A-2 y A-3 con test que las vigila)
- **Verificaciones cruzadas:**
  - [x] Evidencia **reproducida por mí**, no aceptada de terceros: 70 combinaciones del
        stack real, bloqueo demostrado con subproceso y timeout
  - [x] Codebase leído: los 6 módulos de `ingest/` y sus puntos de acceso a disco
  - [x] Contradicciones buscadas contra charter, CLAUDE.md, ADR-001/002/003, HU-001, HU-006,
        HU-009, HU-011, HU-012, HU-016 → **ninguna**; ADR-004 §1 refuerza HU-006 y HU-012
  - [x] Alternativas descartadas con razón documentada (lista negra, validador, registro)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (bloqueantes = 0 · confianza ≥ 85%)
- **Confianza: 92%.** El 8% restante, desglosado con honestidad:
  - A-1: `NUL.jpg` con prefijo no está verificado (se cierra en la primera hora de DEV).
  - La migración toca los 6 módulos existentes; el riesgo no es conceptual sino de omisión,
    y está cubierto por el test de §8.4.
  - El test de bloqueo por subproceso es la pieza de infraestructura de pruebas más
    delicada escrita hasta ahora.

> **No declaro 95%.** El listón del proyecto es 85% y la confianza es una estimación, no un
> objetivo: inflarla haría inútil la métrica que lleva 17 HUs prediciendo el resultado de QA.

---

## 10. Dependencias
| ID | Relación | Estado |
|---|---|---|
| HU-001 | Su determinismo es el contrato que no se puede romper | DONE |
| HU-006, HU-009, HU-011 | Consumen la capa tras la migración | DONE |
| ADR-004 | Fija identidad, acceso e invariantes | Propuesto |
| HU-012 | Usará `replace_atomic` | SPEC (gate pasado) |
| HU-016 | Hereda el saneamiento de nombres **al escribir** | backlog |
| HU-154 | **Obligada** a validar la cadena de video contra la matriz | backlog |

---

## 11. Criterios de aceptación

- **CA-1** — Un `CON.jpg` en la carpeta de entrada **no bloquea**: el escaneo y el triaje del lote completan en tiempo acotado (subproceso con timeout).
- **CA-2** — Los archivos con nombre de dispositivo, punto final y espacio final se **leen y procesan** como cualquier otro: aparecen en `accepted`, no en cuarentena.
- **CA-3** — Un archivo en ruta de más de 260 caracteres **aparece** en el resultado del escaneo (hoy desaparece).
- **CA-4** — Los 15 tests de HU-001 pasan **sin modificación**.
- **CA-5** — El orden es idéntico entre dos escaneos de una carpeta que mezcla reservados, punto/espacio final, gemelos NFC/NFD y ruta larga.
- **CA-6** — Ninguna ruta devuelta por la capa lleva prefijo (F-2), y `system_path` es idempotente (F-1).
- **CA-7** — El test de cumplimiento falla si se introduce un acceso directo a disco fuera de la capa (se verifica introduciéndolo a propósito y comprobando que el test lo detecta).
- **CA-8** — En POSIX la capa es identidad y la suite pasa completa (verificado con la rama de plataforma forzada).
- **CA-9** — Bytes y `mtime` de todos los casos hostiles quedan intactos (I-3).
- **CA-10** — Cobertura de `ingest/` ≥80%; batería completa verde.
- **CA-11** — Gate-log con `draft`, `gate_spec`, `dev`.

---

## 12. Historial de cambios
| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación tras reproducir la evidencia; hipótesis de "nombres" refutada y sustituida por capa de acceso | Claude (ejecutor) |

---

## 13. Ajustes propuestos al backlog (decide el equipo)

1. **Renombrar HU-010** a *"Capa de acceso al filesystem: rutas que hoy detienen el
   pipeline"*. El título actual describe una hipótesis que la evidencia refutó.
2. **Mover HU-010 al frente de la cola de E1.** Su naturaleza cambió de robustez a
   disponibilidad. **No propongo un nivel de prioridad nuevo**: el backlog usa P0–P3 más un
   orden de arranque, y crear un cuarto nivel para una sola fila es churn de esquema; el
   mecanismo para decir "esto va primero" ya existe.
3. **Añadir a HU-016** el saneamiento de nombres al escribir salidas, con la razón (la ruta
   extendida permite crear nombres luego inaccesibles).
4. **Añadir a HU-154** la obligación de validar ffmpeg/PySceneDetect contra la matriz de
   compatibilidad antes de adoptarlos.
5. **HU nueva propuesta (E7): histórico de auditoría de lotes.** Convertir en herramienta
   versionada el análisis que hoy es un script desechable, acumulando por lote: totales,
   duplicados, formatos, EXIF, resoluciones y causas de cuarentena. Permitiría responder si
   el pipeline mejora entre lotes y qué problemas son recurrentes. **No la meto en HU-010**:
   es capacidad nueva, merece su propio ciclo.
