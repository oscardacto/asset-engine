# Insumo — HU-169 en el backlog

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-169 | Utilidades de determinismo: semillas fijas, orden estable, test de reproducibilidad E2E | HU-150 | P0 | S |

## El KPI que sostiene

Charter §7: **"Reproducibilidad · Meta v1: 100% — misma entrada+perfil ⇒ misma salida
(verificado en CI con golden tests)"**. Y §6.1: *"misma salida, **byte a byte** donde el
formato lo permita"*.

Es el KPI número uno del producto. Esta HU es la que lo hace verificable en vez de
declarativo.

## Dos defectos medidos antes de escribir la spec (2026-08-06)

### 1. El orden de un conjunto cambia en cada ejecución

Python aleatoriza `PYTHONHASHSEED` en cada proceso, y de ahí depende el orden en que se
recorre un `set`/`frozenset` de textos. `QualityReport.flags` (HU-158, ya integrado) es un
`frozenset[str]`:

```
PYTHONHASHSEED=0    -> ['borrosa', 'bajo_nativo', 'ruidosa', 'subexpuesta', 'comprimida']
PYTHONHASHSEED=1    -> ['subexpuesta', 'comprimida', 'bajo_nativo', 'ruidosa', 'borrosa']
PYTHONHASHSEED=42   -> ['borrosa', 'ruidosa', 'bajo_nativo', 'subexpuesta', 'comprimida']
PYTHONHASHSEED=7777 -> ['borrosa', 'bajo_nativo', 'ruidosa', 'comprimida', 'subexpuesta']
```

Cuatro ejecuciones, cuatro órdenes. Hoy no rompe nada porque nadie serializa los flags
todavía — **pero HU-036 y HU-181 van a escribirlos en un reporte**, y ahí el KPI se cae.

### 2. La misma carpeta ordena distinto según el sistema que entregue los nombres

Un nombre acentuado tiene dos representaciones válidas: macOS entrega `café.jpg` en NFD
(`cafe` + tilde combinante), Windows y Linux en NFC (`caf` + `é`). Ordenan distinto:

```
si el nombre llega NFC: ['cafz.jpg', 'café.jpg']
si el nombre llega NFD: ['café.jpg', 'cafz.jpg']
```

Mismos archivos, mismo contenido, orden invertido. El cliente 0 sincroniza fotos desde el
celular; basta que un lote pase por un Mac para que el catálogo salga en otro orden.

## Consumidores

| ID | HU | Qué le pide |
|----|----|-------------|
| HU-164 | Framework de golden tests | Que lo comparado sea estable entre corridas |
| HU-185 | Smoke test E2E en CI local | El arnés de "corre dos veces y compara" |
| HU-036, HU-181 | Reportes que escriben flags | Orden estable de los flags |
