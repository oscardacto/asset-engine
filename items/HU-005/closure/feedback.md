# Feedback — HU-005

## Anti-patrones detectados
- (Ninguno. Primera HU del proyecto que sale verde en la primera ejecución de la batería,
  sin una sola corrección de ruff, mypy o cobertura.)

## Decisiones rechazadas
- **Meter el EXIF en `core.Orientation`** para tener "una sola orientación" — rechazado:
  `core` es dominio puro sin IO ni metadatos (charter §6.4). El test de arquitectura ya
  impide que `core` importe `ingest`, así que el intento fallaría de forma ruidosa.
- **Devolver solo la orientación efectiva** — rechazado: sin la cruda al lado, nadie puede
  explicar por qué el archivo mide una cosa y se ve otra. HU-018 necesitará esa explicación
  cuando alguien mire el reporte y no le cuadre.
- **Exponer la discrepancia como flag de calidad** — rechazado: un flag sugiere problema, y
  una foto girada por EXIF es lo normal en cualquier móvil. Es una propiedad (`rotated`),
  no una advertencia.
- **Persistir la orientación efectiva en el catálogo** — rechazado por ahora: el catálogo
  guarda las medidas y la orientación se deriva; un campo redundante invita a que se
  desincronicen. Transferido a HU-018.

## Lecciones aprendidas
- **Una HU de 47 líneas es la mejor señal de que las anteriores se hicieron bien.** Esta no
  construyó nada: compuso `core.Orientation`, `oriented_size`, `swaps_axes` e `ImageSize`.
  Cuando una HU resulta trivial de implementar, conviene mirar hacia atrás y reconocer por
  qué — normalmente es que alguien dejó la superficie correcta.
- **Delegar una ambigüedad a una HU futura funciona si se escribe dónde.** HU-004 dejó
  literalmente "HU-005 decidirá cuál usa y por qué" en su spec y su feedback. Al llegar
  aquí, la decisión estaba enmarcada y solo faltaba tomarla — no hubo que reconstruir el
  contexto.
- **Ningún consumidor la declaraba como dependencia en el backlog.** Los tres (HU-018,
  HU-059, HU-074) la necesitan por texto pero no por la columna "Depende de". Vale la pena
  revisar si otras HUs tienen dependencias implícitas parecidas: el orden de arranque se
  calcula con esa columna.
