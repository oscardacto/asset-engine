# Feedback — HU-159

## Anti-patrones detectados
- (Ninguno en ejecución — ruff atrapó localmente 1 línea >100 columnas antes del commit,
  que es exactamente el trabajo esperado de la batería local.)

## Decisiones rechazadas
- **Enum cerrado de nombres de transform** — rechazado (A-1): el conjunto es abierto y el
  perfil referencia transforms *por nombre como dato*; un enum en `core/` habría que
  tocarlo en cada HU de revelado — el mismo churn que se evitó con las métricas de HU-158.
- **Params anidados (listas/dicts)** — rechazado (A-2): los consumidores conocidos usan
  escalares; lo compuesto se aplana. Mantiene trivial la serialización del sidecar.
- **Timestamps/duración dentro del Transform** — rechazado: eso es observabilidad y
  pertenece a `StageReport` (HU-168); el transform es declarativo puro.
- **Historial como `tuple` pelada** — rechazado (A-3): `append` puro + iteración le dan
  la semántica de auditoría que el sidecar necesita, por ~10 líneas.

## Lecciones aprendidas
- **Distinguir colecciones semánticas de colecciones de datos:** los *params* se ordenan
  (son datos, el orden no significa nada) pero los *steps* jamás (el orden ES el
  significado). La pregunta "¿el orden de esta colección significa algo?" debería hacerse
  en cada contrato futuro con secuencias.
- **Los patrones de `core/` ya son biblioteca:** mapping congelado + copia defensiva +
  anti-NaN se reutilizaron de HU-158 sin re-diseño. Cuatro contratos después, el costo
  marginal de un contrato nuevo es ~1 hora con calidad constante.
- **`typing.Self` + `type(self)(...)`** para métodos que devuelven la propia clase evita
  forward-refs entre comillas y sobrevive a subclases.
