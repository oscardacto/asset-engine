# Feedback — HU-160

## Lecciones aprendidas

- **Una prueba de arquitectura que no se ha visto fallar no vale nada.** El guardián de
  generalización se escribió, pasó a la primera, y eso era exactamente la señal de alarma:
  podía estar pasando por no mirar nada. Se le inyectó al módulo un
  `AMBIENTES_HOSPEDAJE = ("cocina", "alcoba")` y falló en 3 casos. **Es el mismo método que
  ya se usó en HU-010 con las rutas: comprobar, no suponer** — y en este proyecto ya lleva
  dos hallazgos que la intuición había dado por resueltos.

- **La primera versión del guardián marcaba la explicación de la regla como violación.**
  Buscaba texto en el archivo completo, así que el docstring "el programa no sabe qué es un
  *hospedaje* ni qué es un bar" —que enuncia la regla— la incumplía. Se pasó a mirar el
  árbol sintáctico descartando docstrings. **Generalizable: un test que analiza código
  fuente tiene que distinguir lo que el código hace de lo que documenta**; es el segundo
  caso en el proyecto (el primero fue el inventario de HU-010, donde un grep marcó
  "paráme**tros.**" como acceso a `os.`).

- **La pregunta útil al diseñar un contrato extensible no es "cuántos campos" sino "quién
  sabe la respuesta".** Es el criterio que separó `OutputIntent` (cerrado: existe porque hay
  una etapa que lo produce) de los ambientes (abiertos: solo el negocio sabe qué espera
  ver). Sirve para los contratos que faltan.

## Decisiones rechazadas
- **`dict[str, Any]` como perfil** — no contrata nada y traslada el problema entero a HU-130.
- **Declarar el aspecto junto a las dimensiones** — dos fuentes de verdad que pueden
  contradecirse, y una validación de coherencia que mantener.
- **Exigir que los pesos sumen 1** — haría que ajustar un peso obligue a recalcular los
  demás a mano; normalizar es del algoritmo de score (HU-070).
- **Añadir ya estilo de revelado y plantillas narrativas** — sin consumidor. Mismo criterio
  que con las subcarpetas de HU-016: nacen con su HU y entran de forma aditiva.
- **Mirar los insumos del cliente 0 para diseñar la estructura** — era la vía más directa al
  sobreajuste que el charter §4 pide vigilar. Esos documentos son insumo de HU-132.

## Fricción operativa (no bloqueante)
`.gitignore` lleva una línea por HU (`!items/HU-XXX`), y ya van 21. Es una molestia real en
cada HU, **pero el default correcto es el seguro**: una carpeta de WorkItem nueva es
invisible para git hasta que alguien la habilita a mano, y esas carpetas pueden recibir
insumos del cliente. Se deja como está a propósito; si algún día molesta lo suficiente, la
alternativa es ignorar por tipo de archivo (binarios/medios) en vez de por carpeta — pero
eso cambia el default de "seguro salvo permiso" a "permitido salvo prohibición", que es
justo la dirección equivocada para un repo con PII potencial.
