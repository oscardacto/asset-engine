# Spec Técnica `HU-104` — `Crop 9:16 de material horizontal`

> **Estado:** LISTA PARA DEV · **Fecha:** 2026-09-06 · **Confianza global:** 90%

---

## 1. Resumen ejecutivo

- **Qué se pide:** llevar un clip de cualquier forma al formato vertical que se ve en un
  teléfono, sin deformarlo y sin tocar el original.
- **Para quién:** HU-106 (recorte a duración), HU-107 (ensamblado), HU-109 (export).
- **Módulo:** `media_optimizer.video.framing`.
- **No obvio — la aritmética ya está resuelta y no es la parte difícil.**
  `frame_to_vertical` calcula el encuadre exacto desde la tanda de HU-135, verificado con
  valores literales para 4K, 1080p, 4:3 y vertical. **Lo que falta es todo lo que el cálculo
  puro no necesita:** averiguar cuánto mide el clip, entregarle la ruta en la forma que la
  herramienta sí abre, y producir el archivo sin rozar el original.
- **Segundo punto no obvio:** el desplazamiento configurable **tiene que quedar dentro del
  material**. Pedir un corrimiento mayor que el margen sobrante produciría un recorte fuera
  del cuadro, y la herramienta lo rechazaría a mitad de un lote. Se recorta al margen
  disponible en vez de fallar.

---

## 2. Alcance

### 2.1 IN
- `read_dimensions`: cuánto mide un clip, leyendo el archivo por la capa de acceso.
- `build_crop_command`: el comando completo de encuadre, **puro y verificable sin ejecutar**.
- `crop_to_vertical`: aplica el encuadre y produce el archivo.
- Desplazamiento configurable respecto del centro, acotado al margen real.

### 2.2 OUT
- **Encuadre inteligente** (detectar dónde está el sujeto) → no tiene HU en el backlog;
  exigiría detección de contenido.
- **Recorte a duración objetivo** → HU-106.
- **Ensamblado y transiciones** → HU-107.
- **Codec, bitrate y perfil de color** → HU-109. Aquí la salida es correcta pero no está
  afinada para plataforma.

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | Clip ya en 9:16 | El encuadre no recorta nada; se conserva íntegro |
| 2 | Desplazamiento mayor que el margen sobrante | Se acota al margen; no se sale del cuadro |
| 3 | Clip más alto que 9:16 | Se recorta alto en vez de ancho |
| 4 | Clip ilegible o inexistente | `CorruptMediaError`: se aparta ese clip, el lote sigue |
| 5 | Ruta larga o con nombre de dispositivo | Pasa por la capa de ADR-004 |

---

## 3. Diseño

```
read_dimensions(video)                      -> (ancho, alto)     lee el archivo
frame_to_vertical(ancho, alto)              -> VerticalFraming   ya existe, puro
build_crop_command(video, encuadre, salida) -> tuple[str, ...]   puro, testeable sin ejecutar
crop_to_vertical(video, salida, *, offset)  -> VerticalFraming   ejecuta y devuelve qué hizo
```

**La construcción del comando se separa de su ejecución.** Así el filtro `crop=w:h:x:y` se
verifica con valores literales, sin binario y en milisegundos — que es donde viven los
errores de encuadre. Es el mismo patrón que ya usa el ejecutor de video con su validación
silenciosa.

`crop_to_vertical` **devuelve el encuadre aplicado**, no solo un éxito: quien llama necesita
saber qué se recortó para poder explicarlo en el reporte de HU-110.

---

## 4. El desplazamiento configurable

Por defecto el recorte sale del centro. `offset` lo mueve: negativo hacia la izquierda o
arriba, positivo hacia la derecha o abajo, medido en píxeles del material ya escalado.

**Se acota al margen disponible.** Si el sobrante es de 1167 píxeles a cada lado y alguien
pide 2000, se aplica 1167. La alternativa —fallar— convertiría un parámetro mal puesto en un
lote interrumpido a la mitad, y el encuadre resultante sigue siendo válido.

---

## 5. Reglas de negocio

| # | Regla | Fuente | Implicación |
|---|-------|--------|-------------|
| RN-1 | No destructivo | charter §6.3 | El original nunca se modifica; la salida es un archivo nuevo |
| RN-2 | Todo acceso a disco por la capa | ADR-004 | Medido tres veces que las rutas largas fallan sin ella |
| RN-3 | Cinco banderas de reproducibilidad | ADR-006 | Las pone el ejecutor; el llamador no las escribe |
| RN-4 | Un medio corrupto degrada, no tumba | charter | `CorruptMediaError` por clip |
| RN-5 | `core/` sin IO | CLAUDE.md | Este módulo vive en `video/`, no toca el dominio |
| RN-6 | Cobertura 100% del módulo nuevo | Pre-Flight | Al cierre |

---

## 6. Criterios de aceptación en BDD

### CA-1 · El filtro lleva las coordenadas calculadas
```gherkin
DADO QUE el encuadre se calcula con aritmética exacta
CUANDO se construye el comando para un clip apaisado
ENTONCES el filtro de recorte trae ancho, alto y las dos coordenadas del origen
```

### CA-2 · Las rutas se entregan adaptadas
```gherkin
DADO QUE la herramienta abre los archivos por su cuenta
CUANDO se construye el comando de encuadre
ENTONCES la entrada y la salida aparecen en la forma que el sistema exige para abrirlas
```

### CA-3 · Un clip ya vertical no se recorta
```gherkin
DADO QUE un clip puede venir ya en el formato de destino
CUANDO se calcula su encuadre
ENTONCES no se recorta nada: el origen del recorte queda en la esquina
```

### CA-4 · El desplazamiento se queda dentro del cuadro
```gherkin
DADO QUE un desplazamiento excesivo produciría un recorte fuera del material
CUANDO se pide mover el encuadre más allá del margen sobrante
ENTONCES se aplica el margen disponible y el recorte sigue dentro del cuadro
```

### CA-5 · El original queda intacto
```gherkin
DADO QUE el programa nunca modifica los archivos del usuario
CUANDO se encuadra un clip
ENTONCES el archivo de origen conserva exactamente los mismos bytes
```

### CA-6 · La salida mide exactamente el formato vertical
```gherkin
DADO QUE el destino es el formato de un teléfono
CUANDO se encuadra un clip apaisado
ENTONCES el archivo producido mide 1080 por 1920
```

### CA-7 · Un clip ilegible aparta ese clip
```gherkin
DADO QUE un archivo puede estar dañado
CUANDO se intenta leer sus dimensiones o encuadrarlo
ENTONCES se levanta el error que aparta ese medio, y el lote continúa
```

### CA-8 · Funciona con rutas largas
```gherkin
DADO QUE está medido que la herramienta no abre rutas de más de 260 caracteres sin adaptar
CUANDO se encuadra un clip en una ruta así
ENTONCES el archivo se produce correctamente
```

---

## 7. Asunciones

| # | Asunción | Costo si se rompe |
|---|----------|-------------------|
| A-1 | Las dimensiones se pueden leer sin decodificar el clip entero | Ninguno: se lee la cabecera |
| A-2 | Acotar el desplazamiento es preferible a fallar | Cambiar dos líneas |
| A-3 | La salida por defecto sirve hasta que HU-109 afine el codec | Aditivo |

---

## 8. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|--------|-------|---------|------------|
| R-1 | Ruta larga sin adaptar | media | alto | Medido tres veces; CA-2 y CA-8 |
| R-2 | Un desplazamiento excesivo rompa el lote a la mitad | media | alto | CA-4: se acota, no falla |
| R-3 | Que se modifique el original | baja | **crítico** | CA-5 compara los bytes antes y después |
| R-4 | Medidas impares que el codificador rechace | baja | medio | `frame_to_vertical` ya fuerza pares |

---

## 9. Confianza global

- **Preguntas abiertas:** 0 — **0 bloqueantes**
- **Verificaciones cruzadas:**
  - [x] `frame_to_vertical` y `vertical_filter_chain` leídos en código y ya probados
  - [x] `build_command` del ejecutor leído: pone las banderas de reproducibilidad solo
  - [x] Patrón de rutas confirmado tres veces en el proyecto
  - [x] Consumidores (HU-106, 107, 109) revisados en el backlog
- **Recomendación:** ✅ **LISTA PARA DEV. Confianza 90%.** El 10% es A-3.

---

## 10. Dependencias
| ID | Relación | Estado |
|----|----------|--------|
| HU-101 | Escenas | DONE |
| HU-135 | La aritmética del encuadre llegó con esa tanda | DONE |
| ADR-006 | Habilita la cadena de video | Aceptado |
| HU-106, 107, 109 | La consumirán | backlog |

---

## 11. Historial de cambios
| Fecha | Cambio | Por |
|-------|--------|-----|
| 2026-09-06 | Creación | Claude (ejecutor) |
