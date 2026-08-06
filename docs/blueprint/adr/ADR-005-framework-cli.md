# ADR-005 — Framework de la CLI: Typer vs argparse

- **Estado:** **Propuesto** — requiere decisión del equipo (implica aprobar dependencias nuevas)
- **Fecha:** 2026-08-06
- **Origen:** HU-162 (backlog E7) · bloquea HU-017, HU-037, HU-184 y toda la cadena de CLI
- **Decisores:** equipo técnico (@oscardacto) · análisis: Claude (orquestador-ejecutor ASDD)

---

## Contexto

El charter §2 define el producto como **"una CLI local"** y la tabla de stack de CLAUDE.md
propone `Typer` — con la salvedad explícita de que *"cada fila se confirma con su ADR antes
de escribir código que dependa de ella"*. HU-162 es ese código, así que la fila toca ahora.

Restricción de gobernanza aplicable (CLAUDE.md): *"No instalar dependencias nuevas sin
aprobación — y si son de stack, con su ADR."* **Este ADR no puede auto-aprobarse.**

### Superficie real de la CLI (contada sobre el backlog)

| Comando | HU | Argumentos previstos |
|---------|-----|---------------------|
| `ingest` | HU-017 | carpeta, `--workspace`, `--profile` |
| `analyze` | HU-037 | catálogo, `--workspace`, `--profile` |
| `develop` | E3 | catálogo, `--workspace`, `--profile` |
| `select` | E5 | catálogo, `--profile`, `--format` |
| `run` | HU-184 | carpeta, `--workspace`, `--profile` |

Son **5 comandos con 3–4 opciones cada uno**, todas de tipos simples (ruta, texto, enum).
No hay subcomandos anidados, ni parsing dinámico, ni flags mutuamente excluyentes.

### Quién la va a usar

No solo desarrolladores: el dueño del negocio es un usuario previsto. Eso hace que la
calidad de los mensajes de error y de la ayuda **sea funcionalidad**, no comodidad.

## Costo medido (2026-08-06, `uv pip compile`, Python 3.13)

No estimado — resuelto:

```
typer==0.27.1
├── annotated-doc==0.0.5
├── colorama==0.4.6
├── rich==15.0.0
│   ├── markdown-it-py==4.2.0
│   │   └── mdurl==0.1.2
│   └── pygments==2.20.0
└── shellingham==1.5.4
```

**7 paquetes transitivos.** Se verificó también `typer-slim`, que en esta versión **no
ahorra nada**: resuelve a `typer-slim==0.24.0` → `typer==0.27.1` con el mismo árbol
completo. No hay una vía intermedia.

Todos son puros Python, sin binarios ni descargas en tiempo de ejecución, y `uv.lock` los
fija con hash — la reproducibilidad del entorno (ADR-001) no se degrada.

## Opciones consideradas

### A — `argparse` (stdlib)
- ✅ **Cero dependencias nuevas**, cero superficie de suministro añadida. Alineado con el
  principio "local, sin nube" llevado al extremo. Estable desde hace 15 años.
- ⚠️ Más código repetitivo por comando (`add_parser` + `add_argument` + despacho manual).
  La firma tipada de la función y la definición del argumento son **dos declaraciones
  separadas que hay que mantener sincronizadas a mano** — justo el tipo de duplicación que
  mypy no puede vigilar. Ayuda y errores correctos pero secos. Sin autocompletado.
- 📊 ~20–30 líneas extra por comando · 5 comandos · mantenimiento manual del tipado.

### B — `Typer`
- ✅ El argumento de la CLI **es** la firma tipada de la función: una sola declaración, y
  mypy la verifica. Encaja con la convención dominante del proyecto (typing estricto +
  dataclasses en todos los contratos). Ayuda, errores y autocompletado de shell de serie.
- ⚠️ 7 paquetes transitivos. Trae `rich`, que **formatea según el ancho del terminal** —
  si alguna vez escribiera un reporte a archivo, rompería el determinismo de la salida.
- 📊 Menos código propio; una dependencia de terceros en la capa más externa.

### C — `click` directo (lo que Typer envolvía históricamente)
- ⚠️ Descartada: en `typer==0.27.1` **`click` ya no aparece en el árbol de dependencias**
  (medido arriba), así que "usar click a secas" ya no es la vía de menor huella que fue.
  Y frente a argparse, paga una dependencia sin la ventaja de la firma tipada.

## Decisión propuesta

**Opción B — Typer**, con dos restricciones de uso que este ADR fija:

1. **`rich` nunca toca una salida persistida.** Todo reporte que se escriba a archivo lo
   genera código propio, sin pasar por `rich`. `rich` solo puede pintar el terminal. Motivo:
   su formato depende del ancho de la ventana, y el charter §6.1 promete la misma salida
   ante la misma entrada.
2. **`cli/` sigue siendo capa delgada** (CLAUDE.md): parsea, invoca y formatea. Cero lógica
   de negocio. Un comando que crezca más allá de eso es la señal de que le falta un módulo.

La razón dominante no es ahorrar líneas: es que **la firma tipada y la interfaz de línea de
comandos sean el mismo dato**. En un proyecto donde `mypy --strict` es gate de cierre, una
CLI cuyos tipos se declaran dos veces es la única parte del sistema donde el tipado no
verifica lo que el usuario realmente escribe.

**El equipo puede razonablemente decidir A.** Con 5 comandos y flags simples, argparse
alcanza, y "cero dependencias" es un valor defendible en una herramienta que se precia de
correr sola y offline. Si esa es la decisión, HU-162 se implementa igual y sin retrasos:
lo que cambia es el módulo `cli/`, no el resto del sistema.

## Consecuencias

**Positivas**
- La cadena `HU-162 → HU-017 → HU-018` se desbloquea, que es lo que convierte el proyecto
  en algo ejecutable por el usuario y no solo por sus tests.
- Autocompletado y mensajes de error de calidad para un usuario no técnico.

**Negativas / mitigación**
- 7 paquetes más en el lock → todos mainstream y fijados con hash; `uv sync` sigue siendo
  offline y reproducible.
- Riesgo de que `rich` se filtre a la salida persistida → restricción 1, verificable con un
  test que compare un reporte generado con dos anchos de terminal distintos.

**Neutrales**
- Si algún día se quisiera volver a argparse, el cambio queda confinado a `cli/` por la
  restricción 2.

## Qué se necesita para pasar a *Aceptado*

1. Aprobación explícita del equipo para agregar `typer` a `dependencies` (o instrucción de
   usar argparse, que cierra este ADR como *Rechazado* y no requiere aprobación alguna).
2. `uv add typer` + `uv.lock` comiteado.
3. Actualizar la fila "Interfaz" de la tabla de stack de CLAUDE.md con la referencia a este ADR.
