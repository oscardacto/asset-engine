# Feedback — HU-169

## Lecciones aprendidas

- **La HU se llamaba "semillas fijas" y no hacía falta ninguna semilla.** Lo primero que se
  hizo fue buscar aleatoriedad global; no hay: `synthetic.py` ya usa `default_rng(seed)`,
  que es el patrón correcto. Construir el gestor de semillas que el título sugería habría
  añadido código permanente para un problema inexistente. **El enunciado de una HU describe
  la preocupación, no necesariamente el defecto**: conviene medir antes de implementar lo
  que el título insinúa.

- **Los defectos de reproducibilidad son invisibles mientras nadie serialice.** El
  `frozenset` de los flags llevaba varias HUs cerrado y con cobertura al 100%. Ninguna
  prueba lo detectaba porque todas corrían en un solo proceso, y **el fallo vivía entre
  procesos**. Se necesitó un arnés con subprocesos para verlo. Generalizable: **una promesa
  de "misma entrada, misma salida" no se puede verificar dentro de una sola ejecución.**

- **Cuarta HU seguida en que el guardián se verifica por inyección** (HU-160, HU-168,
  HU-156, HU-169). Aquí además reveló algo distinto: no un guardián defectuoso, sino la
  confirmación de que el arnés detecta el defecto real que motivó la HU.

- **Un guardián que recorre los contratos es mejor que uno que revisa uno.** El de esta HU
  itera sobre `core.__all__`: cualquier contrato futuro con un `set` en su API falla solo,
  sin que nadie tenga que acordarse de añadir un test. El defecto que originó la HU tardó
  varias HUs en aparecer justamente porque no había nada así.

## Decisiones rechazadas
- **Construir un gestor de semillas aleatorias** — sin aleatoriedad global que gestionar.
- **Ordenar los flags al serializar en vez de cambiar el tipo** — funciona hasta que alguien
  escribe un serializador nuevo y lo olvida; el fallo sería intermitente e indistinguible
  del ruido. La disciplina la sostiene el tipo.
- **Aplicar `casefold` al ordenar** — en HU-016 sí, porque el problema era que el sistema de
  archivos considera iguales dos nombres; aquí son textos distintos y deben seguir siéndolo.
- **Normalizar a NFD** — NFC es lo que ya usa `workspace._sanear`; dos formas canónicas
  distintas en el mismo proyecto sería el mismo defecto con otro nombre.

## Deuda anotada
El guardián de contratos vigila `set` y `frozenset` en los campos de los contratos de
`core/`. **No vigila** un `dict` sin ordenar ni una colección dentro de un contrato de otra
capa. Ambos casos están cubiertos hoy por convención (los cinco contratos ordenan al
construir), no por prueba. Si aparece un contrato fuera de `core/`, conviene ampliar el
alcance del guardián.
