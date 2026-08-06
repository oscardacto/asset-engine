# Feedback — HU-010

## Anti-patrones detectados
- **La capa que arreglaba el problema lo reintroducía.** Mi primera implementación normalizaba
  con `Path.resolve()`. Sobre un `CON.jpg` **que existe**, `resolve()` devuelve `…\CON` y
  `os.path.abspath()` devuelve `\\.\CON`: ambas consultan al sistema operativo, que
  reinterpreta el nombre. Es decir, destruían justo el nombre que el prefijo venía a
  rescatar. Solo `os.path.normpath` es seguro, por ser **puramente léxica**.
  **Lección: al escribir una capa de compatibilidad, cada primitiva que use debe verificarse
  contra el caso hostil, no solo contra el caso normal.** Mi verificación manual previa usó
  la ruta cruda, no la resuelta — por eso no lo detectó.
- **Verificar sobre rutas inexistentes da falsa confianza.** Comprobé que `resolve()`
  preservaba `CON.jpg`… sobre un archivo que no existía, donde la operación es puramente
  lexical. Con el archivo creado, el comportamiento cambia. **Los casos de prueba del
  filesystem deben usar archivos reales.**
- **Un detector de gobernanza necesita distinguir el receptor.** El test de cumplimiento
  marcó como infracción las llamadas *a través* de la capa (`filesystem.read_bytes`),
  porque solo miraba el nombre del método. Afinarlo para mirar el receptor fue la
  diferencia entre un test usable y uno que se desactivaría al primer falso positivo.

## Decisiones rechazadas
- **Lista negra de nombres reservados** — rechazada por la evidencia: con la ruta adaptada,
  las 70 combinaciones del stack funcionan. Una lista negra habría descartado material
  legítimo del usuario y repartido lógica de plataforma por todo el código.
- **Cuarentenar los nombres hostiles** — rechazada: el nombre no invalida al asset
  (ADR-004 §1). Cuarentenar habría reportado como problemática una foto perfectamente
  utilizable.
- **Activar `LongPathsEnabled` en el registro** — rechazada: es configuración de la máquina
  del usuario, exige privilegios de administrador, y la evidencia se obtuvo **con la opción
  desactivada**, o sea, el prefijo funciona sin ella.
- **`Path.resolve()` / `os.path.abspath()`** — rechazadas tras medirlas (ver arriba).
- **Property-based testing con `hypothesis`** — rechazada: dependencia nueva con ADR, y el
  espacio de entrada aquí es un catálogo conocido y enumerable, mejor cubierto con casos
  explícitos derivados de evidencia.

## Lecciones aprendidas
- **La hipótesis del ticket puede estar equivocada, y descubrirlo es parte del trabajo.**
  El título decía "nombres hostiles y colisiones"; la evidencia demostró que era la capa de
  acceso. Renombrar la HU en el backlog fue tan importante como el código: deja el
  diagnóstico correcto para quien lea el historial.
- **Un test de gobernanza vale más que la documentación de la regla.** La regla "todo IO
  pasa por la capa" está escrita en ADR-004 y en `python.md`, pero lo que impide la
  regresión es el test que falla. Debe seguir en CI para siempre.
- **La validación con datos reales cerró el ciclo:** el escaneo pasó de 107 a 109 archivos
  sobre el lote del cliente. Dos archivos que se perdían en silencio. Ninguna prueba
  sintética lo habría revelado, porque los fixtures se crean con nombres que uno elige.
- **Contribución al documento base de permisos:** la evidencia de que el matcher descompone
  comandos compuestos (0 de 52 reglas contienen `&&`) resuelve una incógnita que ese
  documento tenía marcada como inferencia.
