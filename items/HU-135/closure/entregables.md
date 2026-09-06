# Entregables — HU-135 (+HU-154 / ADR-006) + encuadre vertical

## Módulos creados

| Archivo | Qué es | HU |
|---|---|-----|
| `docs/blueprint/adr/ADR-006-stack-video.md` | Decisión del stack de video · **Propuesto**, no Aceptado | HU-154 |
| `src/media_optimizer/video/ffmpeg_executor.py` | Puerta única hacia el binario: banderas de reproducibilidad, validación silenciosa, degradación | HU-154 |
| `src/media_optimizer/video/templates.py` | `ReelTemplate`, `NarrativeSlot`, `Timeline` y el reparto de clips a tramos | HU-135 |
| `src/media_optimizer/video/transforms.py` | Encuadre 9:16: aritmética exacta de escala y recorte + cadena de filtros | HU-104 (parcial) |
| `profiles/hospedaje/reel_template.json` | El guion del cliente 0 como **datos**, 6 tramos, 19 s | HU-135 |

## Evidencia de pruebas

| Criterio | Resultado |
|----------|-----------|
| Coordenadas exactas para 4K, 1080p, 4:3, 9:16 y vertical alto | ✅ 5 casos parametrizados con valores literales |
| La salida mide siempre 1080x1920 | ✅ 5 resoluciones de origen |
| Nunca deforma (proporción conservada) | ✅ 5 casos, incluidos tamaños impares |
| Medidas intermedias pares | ✅ 3 casos impares (1333x1000, 999x777, 1921x1081) |
| El recorte sale del centro | ✅ |
| Reinicio de marcas de tiempo antes de todo filtro | ✅ |
| Guion reutilizable entre lotes del mismo negocio | ✅ dos lotes distintos, misma plantilla |
| Guion válido para una vertical distinta (bar) sin tocar código | ✅ |
| El guion real del perfil carga y valida | ✅ 6 tramos, 19 s |
| Reparto determinista y sin repetir clips | ✅ |
| Falta de material ⇒ hueco conservado, no relleno | ✅ 4 tests |
| Banderas de reproducibilidad siempre presentes | ✅ 4 tests |
| Rutas traducidas por la capa antes de entregarlas al binario | ✅ 2 tests |
| Fallo del binario degrada sin lanzar excepción | ✅ 7 tests con simulación |
| Validación de grafo sin renderizar | ✅ |
| Integración con el binario real | ⏭️ **3 tests omitidos**: el binario no está instalado |

### Cobertura

```
src/media_optimizer/video/__init__.py              4   0   100%
src/media_optimizer/video/ffmpeg_executor.py      58   0   100%
src/media_optimizer/video/templates.py            88   0   100%
src/media_optimizer/video/transforms.py           39   0   100%
TOTAL                                            189   0   100%
```

**100% en `video/`**, sobre el 85% exigido. Batería completa: **689 passed, 4 skipped**.
`ruff check`, `ruff format --check` y `mypy src/` limpios.

## Defecto encontrado y corregido

El guardián de ADR-004 detectó `shutil.which()` en el ejecutor recién escrito: buscar un
ejecutable recorre carpetas del sistema, así que es acceso a disco y debía pasar por la capa.
Se añadió `filesystem.find_executable()` y el ejecutor lo usa. **La regla funcionó sobre
código escrito en esta misma sesión.**

## Hueco de gobernanza cerrado

`subprocess` no estaba vigilado por el test de arquitectura — el mismo patrón que en HU-156
con el manejador de archivos de la biblioteca estándar: algo que recibe rutas y las abre por
dentro. Ahora solo la capa de video puede lanzar procesos, `core/` tiene prohibido importar
`subprocess` y `media_optimizer.video`, y hay un test que comprueba que la regla ve lo que
debe ver.

## ⚠️ Estado del ADR: Propuesto, no Aceptado

HU-154 exige literalmente *"validar la cadena contra la matriz de compatibilidad de rutas de
ADR-004 antes de adoptarla"*. **El binario no está instalado en la máquina de referencia**
(`ffmpeg -version` no responde), así que esa validación no se ha podido ejecutar.

El test de integración que la realiza ya está escrito y se activa solo en cuanto el binario
exista. Hasta entonces, ninguna HU de E5 que **ejecute** video puede cerrarse: se estaría
construyendo sobre una suposición de compatibilidad de rutas que el propio backlog prohíbe
asumir.

Lo entregado aquí —plantillas, encuadre y construcción de comandos— es aritmética y datos
puros: se implementa y se verifica sin el binario, y por eso sí se cierra.
