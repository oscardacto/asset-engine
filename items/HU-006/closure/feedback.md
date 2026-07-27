# Feedback — HU-006

## Anti-patrones detectados
- **Permisos hiper-específicos acumulándose en `settings.json`.** Detectado al cerrar esta
  HU: el archivo tenía 25 reglas, una por cada mensaje de commit y una por cada variación
  de la batería (`--cov=…testing` vs `…ingest`, `-Last 7` vs `-Last 8`). Cada variación
  pedía permiso de nuevo. **Corregido**: se sustituyeron por ~20 patrones genéricos
  (`Bash(git commit *)`, `PowerShell(uv run *)`). Causa raíz del prefijo `$env:Path`: la
  sesión de Claude Code heredó el entorno de **antes** de instalar uv; el PATH persistente
  del usuario ya lo tiene, así que reiniciar la sesión elimina el prefijo por completo.

## Decisiones rechazadas
- **Pre-filtro por tamaño antes de hashear** (optimización clásica de deduplicación) —
  rechazado con razón medible: todo asset necesita su hash igualmente para el catálogo y
  la re-ingesta idempotente, así que el pre-filtro no ahorraría **ni una** lectura. Es el
  caso raro donde la optimización de libro no aplica al problema concreto.
- **BLAKE2b** (más rápido) — rechazado: el hashing está limitado por IO, no por CPU, y
  SHA-256 es verificable a mano con `Get-FileHash`/`sha256sum`, lo que importa en una
  herramienta local y auditable donde el usuario debe poder comprobar el catálogo sin
  ejecutar nuestro código.
- **Prefijo de algoritmo en el hash** (`sha256:abc…`) — rechazado: rompería la comparación
  directa con las herramientas del sistema; el nombre del algoritmo se publica aparte en
  `HASH_ALGORITHM`.
- **Devolver el índice completo hash→rutas** — rechazado: el ticket pide *duplicados*; un
  grupo de un solo archivo no es un duplicado y devolverlo obligaría a filtrar a cada
  llamador.

## Lecciones aprendidas
- **Un vector conocido vale por diez tests de consistencia interna.** Comparar contra
  `e3b0c442…b855` prueba que computamos SHA-256 estándar y no una variante propia; los
  tests que solo comparan nuestra salida consigo misma pasarían igual con un algoritmo
  equivocado. Usar vectores públicos siempre que se implemente algo estandarizado.
- **La HU más rápida hasta ahora fue la que más reutilizó**: verde a la primera, sin una
  sola corrección de ruff/mypy. Cuatro HUs de plataforma después, el patrón de la capa
  `ingest/` (errores, fixtures, estilo de tests) ya no requiere decisiones.
- **Primer merge integrado por Claude:** la condición autoimpuesta —verificar la batería
  *sobre la rama fusionada*, no sobre la rama de feature— es lo que hace defendible la
  delegación; detectaría un conflicto semántico que el merge textual no ve.
