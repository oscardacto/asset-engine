# Spec Técnica `HU-101` — `Detección de escenas`

> **Estado:** LISTA PARA DEV · **Fecha:** 2026-09-06
> **Confianza global:** 89% — ver sección 9
> **Habilitada por:** [ADR-006](../../../docs/blueprint/adr/ADR-006-stack-video.md), Aceptado el 2026-09-06

---

## 1. Resumen ejecutivo

- **Qué se pide:** partir un clip en sus tomas, con umbrales que vienen del perfil.
- **Para quién:** HU-102 (score por escena), HU-103 (descarte), HU-105 (secuenciado), HU-110 (reel).
- **Módulos:** `core.scene` + `core.ports.scene_detector` (dominio puro) ·
  `video.scenedetect_adapter` (la única parte que conoce la librería).
- **No obvio — la librería trae un conflicto de empaquetado que rompe una decisión ya
  tomada.** `scenedetect` declara `opencv-python` (con interfaz gráfica), y ADR-002 eligió
  deliberadamente `opencv-python-headless`. **Los dos instalan el mismo módulo `cv2` en el
  mismo directorio**, así que cuál queda depende del orden de instalación. No es teórico: al
  medirlo, el entorno de prueba acabó con `cv2` inservible (*missing configuration file*).

---

## 2. Hallazgos medidos antes de escribir código

### H-1 · Conflicto de `cv2` — resuelto con override

Resolución conjunta de las dependencias del proyecto más `scenedetect`:

```
opencv-python==5.0.0.93            ← con interfaz gráfica, la trae scenedetect
opencv-python-headless==5.0.0.93   ← la que ADR-002 eligió
```

**Ambas presentes.** Los extras `[opencv-headless]` y `[headless]` no cambian nada en la
versión 0.7.1. La solución medida y aplicada es dejar la variante con interfaz fuera con un
marcador de plataforma que nunca se cumple. Verificado en el proyecto real: queda solo
`opencv-python-headless`, y `scenedetect` importa y expone su detector sin problema.

### H-2 · La librería no encuentra videos en rutas largas

Con un clip generado en una ruta de 384 caracteres:

| Ruta entregada a la librería | Resultado |
|---|---|
| Tal cual | ❌ `OSError: Video file not found.` |
| Adaptada por la capa de ADR-004 | ✅ abre y analiza |

Es el tercer caso del mismo patrón en este proyecto: el manejador de archivos de la
biblioteca estándar, la herramienta de video, y ahora esta librería. **Toda ruta que se le
entregue pasa por la capa.**

---

## 3. Alcance

### 3.1 IN
- `Scene`: contrato de dominio — índice, inicio y fin en segundos.
- `SceneDetectorPort`: qué se le pide a un detector, sin decir quién lo hace.
- `PySceneDetectAdapter`: la implementación real.
- Umbral como parámetro; su valor por perfil llega con HU-133.

### 3.2 OUT
- **Score técnico por escena** → HU-102.
- **Descarte de escenas malas** → HU-103.
- **El umbral como dato del perfil** → HU-133; aquí es un parámetro con valor por defecto.
- **Etapa `reel` del pipeline** → HU-110.

### 3.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | Clip sin cortes | Una sola escena que cubre todo |
| 2 | Ruta larga | Pasa por la capa (H-2) |
| 3 | Clip ilegible o inexistente | `CorruptMediaError`: degrada ese asset, no el lote |
| 4 | Umbral muy alto | Menos cortes, nunca más que con uno bajo |

---

## 4. Estrategia de pruebas (TDD)

**Los videos de prueba se generan en el momento con la herramienta externa** — un clip de
negro a blanco produce un corte inequívoco. Así no entra ni un medio real al repositorio
(charter §6.6) y el fixture es reproducible en cualquier máquina con el binario.

Las pruebas se escribieron **antes** que la implementación y están marcadas como fallo
esperado en modo estricto. Eso consigue las dos cosas a la vez: quedan en rojo declarado —
describen lo que aún no existe— y la batería global sigue verde, así que la cobertura no se
degrada mientras tanto. El día que alguien implemente el detector, esas pruebas **fallarán
por pasar**, avisando de que hay que desmarcarlas. Un `skip` no daría ese aviso.

| Grupo | Estado |
|---|---|
| Contrato del puerto (4 tests) | ✅ verdes ya: no necesitan implementación |
| Detección sobre clips reales (8 tests) | 🔴 fallo esperado, hasta implementar |

---

## 5. Reglas de negocio

| # | Regla | Fuente | Implicación |
|---|-------|--------|-------------|
| RN-1 | `core/` sin IO ni terceros | CLAUDE.md | El puerto solo usa `Path` y `Scene` |
| RN-2 | **Ningún tipo de la librería sale de `video/`** | hexagonal | El adaptador devuelve `Scene`, nunca estructuras ajenas |
| RN-3 | Todo acceso a disco por la capa | ADR-004 · H-2 | Rutas adaptadas antes de entregarlas |
| RN-4 | Un medio corrupto degrada, no tumba | charter | `CorruptMediaError` por clip |
| RN-5 | Determinismo | charter §6.1 | Mismo clip y umbral ⇒ mismas escenas |
| RN-6 | Cobertura ≥80% del módulo | Pre-Flight | Al cierre de DEV |

---

## 6. Preguntas abiertas

### P-1 — ¿El override de la dependencia es la solución definitiva?
- **Categoría:** IMPORTANTE (no bloqueante)
- **Mi mejor hipótesis:** sí mientras `scenedetect` no publique un extra headless que
  funcione. Está medido que el proyecto queda solo con la variante sin interfaz y que la
  librería opera con ella. Si una versión futura lo arregla, el override se quita y nada más
  cambia.
- **Estado:** ABIERTA

### P-2 — ¿Qué umbral por defecto?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** 27.0, el valor de referencia de la propia librería, hasta que
  HU-133 lo calibre con material real del cliente.
- **Estado:** ABIERTA

---

## 7. Asunciones

| # | Asunción | Costo si se rompe |
|---|----------|-------------------|
| A-1 | El override sobrevive a futuras versiones (P-1) | Revisar una línea de configuración |
| A-2 | El detector por contenido basta; no hacen falta otros modos | Añadir un parámetro, aditivo |
| A-3 | Las escenas caben en memoria como tupla | Ninguno: son decenas, no millones |

---

## 8. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|--------|-------|---------|------------|
| R-1 | Que vuelva a colarse la variante con interfaz | media | **alto** (deja `cv2` inservible) | Override + comentario en la configuración |
| R-2 | Que un tipo de la librería se filtre al dominio | media | alto | Test que lo comprueba; el puerto solo habla de `Scene` |
| R-3 | Ruta larga sin adaptar | media | alto | Medido en H-2; test dedicado |
| R-4 | Umbral mal calibrado para material de celular | alta | medio | Es parámetro; HU-133 lo calibra con material real |

---

## 9. Confianza global

- **Preguntas abiertas:** 2 — **0 bloqueantes**
- **Verificaciones cruzadas:**
  - [x] **Conflicto de `cv2` medido** y la solución verificada en el proyecto real
  - [x] **Comportamiento con rutas largas medido**, no supuesto
  - [x] ADR-002 leído: la elección de la variante sin interfaz es deliberada
  - [x] ADR-006 Aceptado, con la cadena de video validada
  - [x] Consumidores (HU-102, 103, 105, 110) revisados en el backlog
- **Recomendación:** ✅ **LISTA PARA DEV. Confianza 89%.** El 11% es P-1 y R-4.

---

## 10. Nota sobre la estructura

`core/ports/` es un subpaquete nuevo, no contemplado en el mapa de módulos de CLAUDE.md.
Se crea porque el puerto tiene un consumidor real —permite que el pipeline y las pruebas
pidan escenas sin conocer la librería— y porque es puro: solo `Path`, `Protocol` y `Scene`.
**Si el equipo prefiere mantener el mapa tal cual**, el puerto cabe igual en `core/scene.py`
junto al dato, y mover el archivo es todo el cambio.

---

## 11. Dependencias
| ID | Relación | Estado |
|----|----------|--------|
| HU-154 / ADR-006 | Habilita la cadena de video | DONE / Aceptado |
| HU-100 | Ingesta de clips | backlog |
| HU-102, 103, 105, 110 | La consumirán | backlog |

---

## 12. Historial de cambios
| Fecha | Cambio | Por |
|-------|--------|-----|
| 2026-09-06 | Creación, tras medir el conflicto de empaquetado y el comportamiento con rutas | Claude (ejecutor) |
