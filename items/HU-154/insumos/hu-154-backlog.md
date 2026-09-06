# Insumo — HU-154 en el backlog

> Copia literal de `docs/blueprint/backlog.md`, épica **E7 · Plataforma**.

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-154 | `ADR` Stack de video: ffmpeg + PySceneDetect (y PyAV sí/no). **Obligatorio: validar la cadena contra la matriz de compatibilidad de rutas de ADR-004 antes de adoptarla** | HU-150 | P2 | S |

## La condición obligatoria, y por qué no es retórica

El enunciado exige validar la cadena contra la matriz de rutas **antes** de adoptarla. Hay un
precedente medido que la justifica.

En HU-156 se midió el manejador de archivos de la biblioteca estándar contra esa misma
matriz, en la máquina de referencia:

| Ruta | Comportamiento |
|------|----------------|
| Larga (383 caracteres) | ❌ falla |
| `CON.log` | ❌ error incomprensible |
| `NUL.log` | ⚠️ **no protesta y descarta todos los registros** |
| `COM1.log` | ❌ falla |

Una dependencia que recibe rutas y las abre por dentro puede fallar en silencio. ffmpeg es
exactamente ese tipo de dependencia: recibe rutas como argumentos y abre los archivos por su
cuenta, sin pasar por la capa de adaptación del proyecto.

## Lo que E5 depende de esta HU

13 HUs: HU-100 a HU-112 (ingesta de clips, escenas, score, crop, secuenciado, ensamblado,
export, reel), más HU-003 (validación de formatos de video), HU-014 (metadatos de video) y
HU-167 (fixtures sintéticos de video).

## Estado de la máquina de referencia (2026-09-05)

`ffmpeg -version` no responde: **el binario no está instalado**. La validación que el
enunciado exige no se puede ejecutar hoy.
