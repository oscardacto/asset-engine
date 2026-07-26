# Feedback — HU-001

## Anti-patrones detectados
- (Ninguno nuevo en ejecución. Las dos reglas heredadas de HU-166 se aplicaron y
  funcionaron: `git add` con rutas explícitas dejó `settings.json` fuera del commit, y
  verificar `origin/develop` antes de cerrar confirmó el merge real.)

## Decisiones rechazadas
- **Devolver `MediaAsset` en vez de rutas** — rechazado: el contrato exige dimensiones y
  hash, que solo se conocen tras decodificar (HU-002) y hashear (HU-006); construirlo aquí
  obligaría a leer cada archivo dos veces y acoplaría el escaneo a la decodificación.
- **Filtrar por extensión en el escaneo** — rechazado: el backlog pide explícitamente
  "magic bytes, no extensión"; filtrar aquí produciría falsos negativos que HU-002 nunca
  llegaría a ver (una foto renombrada a `.txt` desaparecería en silencio).
- **Inventar una estructura de reporte para subcarpetas ilegibles** — rechazado: sería un
  contrato sin consumidor; el resumen de fallos pertenece a `StageReport` (HU-168) y al
  orquestador (HU-180). Transferido como nota de dependencia.
- **Seguir enlaces simbólicos de carpeta** — rechazado: una carpeta que se apunta a sí
  misma colgaría el escaneo indefinidamente.

## Lecciones aprendidas
- **"Ordenar alfabéticamente" no es determinismo.** La clave necesitó tres componentes:
  forma Unicode fija (NFC), insensibilidad a mayúsculas para que el orden sea legible en
  el reporte de inventario, y la ruta cruda como último desempate — porque dos nombres
  distintos pueden normalizar al mismo NFC y NTFS los deja coexistir. Sin ese tercer
  componente el orden volvía a depender del filesystem, que es exactamente lo prohibido.
  Aplicar el mismo escrutinio a cualquier orden que el pipeline declare estable.
- **Las HUs de plataforma empiezan a pagar.** Esta HU no escribió ni una línea de utilidad
  propia: usó `InvalidInputError` (HU-161) y el generador sintético (HU-166) tal cual.
  La inversión en contratos y fixtures se recupera desde el primer consumidor.
- **El primer código de una épica revela huecos de la constitución:** la tabla de módulos
  de CLAUDE.md no contemplaba la ingesta. Vale la pena preguntarse "¿dónde vive esto?"
  contra la constitución al arrancar cada épica nueva, no al tercer módulo.
