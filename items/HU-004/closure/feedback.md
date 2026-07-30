# Feedback — HU-004

## Anti-patrones detectados
- **Una asunción sobre el stack escrita sin verificar sobrevivió dos HUs.** HU-166 documentó
  que "cv2 no escribe EXIF; hará falta una dependencia con su ADR" — era cierto en OpenCV 4
  y falso en el OpenCV 5 que tenemos lockeado desde HU-152. La asunción viajó como pregunta
  transferida hasta que alguien la ejecutó. **Las capacidades del stack se comprueban contra
  la versión instalada, no contra lo que uno recuerda de la librería.**
- **Casi resuelvo el problema con la herramienta cómoda en vez de la correcta.** La primera
  implementación usaba `cv2.imreadWithMetadata`, que funciona… **decodificando la imagen
  entera**: ~600 MB en una foto de 200 MP, solo para leer una fecha. Contradecía la política
  explícita de la capa (HU-002 y HU-011 evitan decodificar). Se sustituyó por un recorrido
  propio del APP1 sobre la cabecera que ya se lee. **Que una API exista no significa que su
  coste encaje con la capa donde se usa.**
- **Un resto de depuración estuvo a punto de colarse**: `return ..., True and False` en lugar
  de `, False`. Lo habría atrapado un test, pero es señal de que conviene releer el diff de
  una función binaria antes de ejecutar nada.

## Defecto detectado tras el cierre (validación con el lote real, 2026-07-26)
- **`Orientation = 0` se trataba como valor corrupto.** Al correr la ingesta sobre el
  archivo real del cliente (100 JPEG), **72 de las 82 fotos con EXIF quedaron marcadas como
  `is_malformed`** — un 88% de falsos positivos. La causa: la etiqueta Orientation existe
  pero vale `0`, que en la práctica significa "sin declarar" y que muchas cámaras escriben
  así. Mi parser solo aceptaba 1–8 y consideraba corrupto todo lo demás.
- **Impacto si no se detecta:** HU-018 habría reportado al usuario que casi todo su archivo
  tiene metadatos corruptos, que es falso y erosiona la confianza en el resto de flags.
- **Corrección:** `0` se trata igual que la ausencia de la etiqueta (sin dato, sin marcar
  malformado); solo los valores fuera de 0–8 indican corrupción real. Test de regresión
  añadido con el caso literal encontrado. Verificado sobre el mismo lote: **72 → 0**.
- **Lección:** los tests sintéticos cubrían "válido" y "absurdo" (99), pero no el valor que
  la realidad usa para decir "no sé". **Un generador de fixtures escribe lo que el
  programador imagina; el archivo real trae lo que el fabricante decidió.** Correr sobre
  datos reales en cuanto haya una pieza ejecutable, aunque no exista aún la CLI.

## Decisiones rechazadas
- **`cv2.imreadWithMetadata` para leer EXIF en producción** — rechazado por coste (ver
  arriba). Se conserva `imencodeWithMetadata` **solo en fixtures de test**, donde las
  imágenes son diminutas y el coste es irrelevante.
- **Lanzar `CorruptMediaError` ante EXIF inválido** — rechazado: un bloque de metadatos roto
  no invalida la foto. La excepción se reserva al archivo ilegible; el EXIF roto degrada el
  dato y lo marca. Distinguirlo es exactamente lo que pide el ticket.
- **Leer GPS** — rechazado deliberadamente pese a estar disponible: recolectar coordenadas
  sin una política de tratamiento sería acumular PII sin necesidad. El campo pertenece a
  HU-034, que sí define qué hacer con él.
- **Soportar EXIF en PNG y WebP** — rechazado por YAGNI: el dominio es fotografía de móvil
  (JPEG) y ningún consumidor lo pide; el módulo devuelve "sin EXIF" para esos formatos, que
  es honesto y no bloquea nada.

## Lecciones aprendidas
- **Un metadato puede ser una transformación disfrazada.** La orientación EXIF no es
  información sobre la foto: es una instrucción que OpenCV **ejecuta** al abrirla, de modo
  que las medidas de cabecera y las decodificadas discrepan. Exponer esa diferencia
  (`oriented_size`) en vez de esconderla evita que HU-005 y HU-018 se contradigan entre sí.
- **Corregir el feedback de una HU cerrada es parte del ciclo, no una excepción.** La
  anotación en `HU-166/closure/feedback.md` deja el error donde alguien que relea esa HU lo
  va a encontrar, en vez de enterrado en la HU que lo descubrió.
- **Los parsers binarios se prueban con entrada hostil, no solo con entrada válida.** De los
  26 tests, 8 alimentan bloques rotos, punteros fuera de rango o contadores absurdos —
  y son los que justifican que el módulo pueda llamarse "lectura *segura*".
