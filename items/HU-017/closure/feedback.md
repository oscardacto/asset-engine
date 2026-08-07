# Feedback — HU-017

## Rework generado (contra HU-162)
`report.py` tenía su propia constante `"catalogo.json"` ≠ `"catalog.json"` real: el reporte
nunca habría encontrado el catálogo. **Causa raíz: duplicar un nombre en vez de importar su
constante.** Lo destapó el primer test E2E que cruzó las dos capas — los tests de HU-162
usaban la misma constante equivocada, así que pasaban. Lección: **un nombre compartido entre
capas se importa, nunca se reescribe**; y un test que reutiliza la constante del código que
prueba no verifica el nombre, solo la coherencia interna.

## Lecciones aprendidas
- **La disponibilidad derivada eliminó una clase entera de inconsistencia**: el registro no
  puede decir "disponible" sin que el ejecutor exista, ni al revés, porque es la misma cosa.
- **La verificación de integridad se probó por inyección** (sexta HU consecutiva): con
  `find_modified_sources` forzado a reportar un cambio, la etapa falla y nombra el archivo.

## Decisiones rechazadas
- **Re-hashear todos los originales para verificar** — los hashes ya estaban calculados
  para el catálogo; la verificación los reutiliza y solo re-lee para comparar.
- **Conectar `--force`/`--resume` ya** — su efecto real es de HU-182; hoy se aceptan sin
  romper la sincronía parser↔contrato.
