# Feedback — HU-157

## Anti-patrones detectados
- **Referencias a HUs/specs dentro del código.** Los docstrings originales citaban
  "(HU-157)", "spec §11", "charter §6.3", "ciclo ASDD". Corrección del equipo (26-jul):
  los docstrings explican **qué hace** el código en lenguaje simple ("en simple: …");
  la trazabilidad vive en git e `items/`, no en el código. Regla nueva codificada en
  `.claude/rules/python.md` y aplicada retroactivamente a todo el código (`c4c52cb`).
  Esta es la lección más importante del cierre: **el código habla del dominio, el
  proceso habla del proceso.**

## Decisiones rechazadas
- **Validar existencia de `source` en disco** — rechazado: sería IO en `core/`; esa
  verificación pertenece a la ingesta.
- **Validar formato/longitud del hash** — rechazado: el algoritmo aún no está decidido;
  sobre-validar acoplaría el contrato a una decisión inexistente (P-2 de la spec).
- **Campos extra "por si acaso"** (duración de video, EXIF, score) — rechazado: el
  alcance quedó clavado a los 4 conceptos literales del ticket; los contratos siguientes
  componen, no engordan este.

## Lecciones aprendidas
- **El feedback de estilo llega mejor con código real en la mesa:** la convención de
  docstrings surgió al revisar el primer PR con código de dominio — imposible haberla
  descubierto en HUs documentales. Los primeros PRs de cada tipo de artefacto son
  detectores de convenciones implícitas del equipo.
- **Organizar tests por criterio de aceptación (clases `TestCA_N…`) hace la evidencia de
  cierre casi automática:** la tabla de entregables se mapea 1:1 con la salida de pytest.
  Mantener el patrón (sin mencionar "CA" en docstrings del código — la clase de test
  nombra el comportamiento, la spec mapea).
- **`StrEnum` para los enums del dominio** paga de inmediato: serialización JSON natural
  para el catálogo futuro sin código extra.
