# Product Charter — media-optimizer

**Versión 0.1 (borrador para aprobación) · 26 de julio de 2026**
Fuentes: `insumos/documento-maestro.md` (v1.2), `insumos/sistema-contenido-redes-v1.1.md`,
`insumos/plan-crecimiento-reservas.md`. Ante discrepancia, manda el Documento Maestro.

---

## 1. Problema

Un negocio de hospedaje pequeño produce fotos y videos crudos con el celular y necesita
convertirlos en contenido comercial (portada de Airbnb, feed 4:5, reels 9:16). Hoy ese
trabajo se hace a mano y de forma no reproducible. El caso del cliente 0 lo demuestra:

- La auditoría técnica de 43 fotos (brillo, % de negro, orientación, resolución) se hizo
  manualmente y quedó documentada en tablas de un `.md` (Maestro §8.2).
- El revelado por lotes del 25-jul (recuperación de sombras, protección de altas luces,
  saturación ≤6%) se aplicó una vez, sin código versionado ni parámetros reproducibles
  (Maestro §8.4).
- 14 fotos siguen "[POR IDENTIFICAR]" y la serie más valiosa del archivo (4 de abril,
  verticales luminosas) estuvo meses sin asignar porque nadie documentó qué muestra
  (Maestro §8.2).
- Todo el archivo está degradado por compresión de WhatsApp (techo 1288×952 px) y nadie
  lo detectó hasta la auditoría manual (Maestro §8.1).

**media-optimizer industrializa ese trabajo:** lo vuelve repetible, determinista, local
y auditable, para este cliente y para cualquier negocio con un perfil equivalente.

## 2. Visión

Una CLI local que recibe una carpeta de medios crudos y un perfil de negocio, y devuelve
un directorio de trabajo con: análisis técnico por asset, versiones reveladas según el
criterio estético del perfil, ranking y selección por formato de salida (portada,
feed 4:5, reel 9:16), y reporte de cobertura de ambientes — sin tocar jamás los
originales y produciendo la misma salida ante la misma entrada.

## 3. Cliente 0 y generalización

- **Cliente 0:** LIVING POP — Apartaestudio 302, Edificio Living 42, Popayán.
  Hospedaje boutique (Airbnb + estancias medias). Insumos en `insumos/`.
- **Generalización:** todo criterio específico del cliente (pesos de score, ambientes
  esperados, estética del revelado, formatos de salida) entra como **datos** del perfil
  de negocio (`profiles/`), nunca como código. El primer perfil es `hospedaje`; la
  arquitectura no asume que sea el único.

## 4. Objetivos de negocio que el software sirve (v1)

Derivados del Plan de Crecimiento (ocupación 45% → 65% en Q4) y del Maestro §11:

| # | Objetivo de negocio | Cómo contribuye media-optimizer |
|---|--------------------|--------------------------------|
| 1 | CTR de portada en Airbnb | Ranking de candidatas a portada con criterios técnicos (brillo, nitidez, orientación, resolución nativa) |
| 2 | Exactitud ≥ 4,9 en reseñas | Selección que prioriza fidelidad al espacio real: revelado sobrio (sin HDR/saturación), cobertura honesta de ambientes |
| 3 | Contenido para redes sostenible (4 piezas/semana) | Pipeline de reels 9:16 y crops 4:5 desde clips y fotos crudas, con detección de escenas y descarte |
| 4 | Detección temprana de activos inservibles | Flags automáticos: compresión WhatsApp, subexposición, sombras aplastadas, resolución bajo el nativo de la plataforma |

## 5. Alcance v1

**Dentro:** ingesta con validación hostil → análisis (nitidez, exposición, ruido,
perspectiva, ambientes) → revelado (verticales, CLAHE, white balance, según perfil) →
ranking y selección (score, portada, orden narrativo, cobertura) → video (escenas,
descarte, secuencia, reel 9:16) → reportes de observabilidad. CLI con argparse (ADR-005).

**Fuera de v1:** GUI · generación de placas/piezas de diseño con texto (el generador
editorial del Maestro §8.6 es prior art de otro proyecto; se evaluará como epic propio)
· publicación automática en plataformas · nube · entrenamiento de modelos ML ·
inferencia LLM.

## 6. Restricciones y principios

1. **Local y determinista** — sin nube, sin APIs remotas; misma entrada + mismo perfil
   ⇒ misma salida, byte a byte donde el formato lo permita.
2. **CPU-only** — sin dependencia de GPU. Presupuestos de rendimiento por etapa en
   `benchmarks/`.
3. **No destructivo** — originales intactos; toda salida a directorio de trabajo con
   historial de transformaciones.
4. **Dominio sin IO** — `core/` y `ranking/` puros (hexagonal ligera).
5. **Perfiles como datos** — cero `if`s por cliente en el código.
6. **PII local** — los medios del cliente jamás salen de la máquina ni entran al repo;
   fixtures de test sintéticos o libres.
7. **Dispositivo de captura de referencia:** celular gama media (cliente 0: Redmi
   Note 13 Pro+). El pipeline asume medios de celular, no de cámara profesional.

## 7. KPIs del producto

| KPI | Meta v1 |
|-----|---------|
| Reproducibilidad | 100% — misma entrada+perfil ⇒ misma salida (verificado en CI con golden tests) |
| Concordancia con la auditoría manual del cliente 0 | Las métricas de análisis reproducen las tablas del Maestro §8.2 (brillo medio, % negro) dentro de ±2% |
| Detección de degradación | 100% de las 43 fotos WA del cliente 0 flageadas como comprimidas; 0 falsos positivos en la serie del 4 de abril |
| Cobertura de tests | ≥95% dominio puro · ≥80% módulo tocado |
| Rendimiento | Presupuesto por etapa definido en su HU; medido en `benchmarks/` sobre hardware de referencia |

*KPIs de negocio (CTR, ocupación, Exactitud) son north stars del cliente — el software
los sirve pero no los mide; viven en los insumos.*

## 8. Riesgos principales

| Riesgo | Mitigación |
|--------|------------|
| Criterio estético "sobrio" difícil de objetivar en métricas | El revelado manual del 25-jul (Maestro §8.4) es el golden reference: sus antes/después calibran los parámetros del perfil |
| ADRs de stack pendientes (OpenCV, ffmpeg/PySceneDetect, catálogo JSON vs SQLite) | Cada ADR se cierra antes de la primera HU que dependa de él |
| Dataset real con PII y de baja calidad (compresión WA) | Fixtures sintéticos para tests; el dataset real solo para validación local manual |
| Un solo cliente real — riesgo de sobreajuste al caso LIVING POP | Regla "perfiles como datos" + revisión de generalización en cada gate de spec |

## 9. Decisión pendiente del charter

- **Marca/alcance multi-vertical:** el Maestro §9 tiene abierta la arquitectura de marca
  del cliente (Living POP vs Cauce). No bloquea a media-optimizer: el software es
  agnóstico de la marca; solo afecta textos de ejemplo en fixtures.

---

*Siguiente artefacto del blueprint: `backlog.md` — épicas + ~100–150 HUs de una línea,
priorizadas por los objetivos del §4.*
