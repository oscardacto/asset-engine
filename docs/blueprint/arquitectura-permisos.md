# Arquitectura de permisos — media-optimizer

> Adaptación de `docs/arquitectura-base-permisos-claude-code.md` (destilado de la auditoría de
> ClaudeCore SBS) al stack, los hooks y la evidencia **de este** proyecto.
>
> **Cada afirmación lleva su nivel de certeza:**
>
> | Marca | Significado |
> |-------|-------------|
> | **[MEDIDO-AQUÍ]** | Comprobado ejecutándolo en *este* repositorio, con resultado observado |
> | **[MEDIDO-SBS]** | Medido en la auditoría de origen, **no re-verificado aquí** |
> | **[DOCUMENTADO]** | Documentación oficial de Claude Code |
> | **[INFERENCIA]** | Deducción razonada, no comprobada |
> | **[NO VERIFICADO]** | Pendiente |
>
> Sin marca = criterio de diseño explícito, no un hecho.

---

## 1. Estado medido de este repositorio (2026-07-26)

| Hecho | Valor | Marca |
|---|---|---|
| Reglas totales en `.claude/settings.json` | **77** (crecieron 2 durante la propia investigación) | [MEDIDO-AQUÍ] |
| Reglas que hacen trabajo útil | **18 (23%)** | [MEDIDO-AQUÍ] |
| Reglas `deny` en los cuatro archivos | **0** | [MEDIDO-AQUÍ] |
| Reglas `ask` en los cuatro archivos | **0** | [MEDIDO-AQUÍ] |
| Reglas con rutas absolutas de esta máquina | **29** | [MEDIDO-AQUÍ] |
| Reglas PowerShell **sobre-escapadas** (imposible que casen) | **27 de 27** | [MEDIDO-AQUÍ] |
| Reglas `PowerShell(uv …)` muertas por prefijo | **5** | [MEDIDO-AQUÍ] |
| Reglas cubiertas por una genérica anterior que aun así generaron prompt | **17** | [MEDIDO-AQUÍ] |
| Reglas específicas que contienen `&&` | **0 de 52** | [MEDIDO-AQUÍ] |

### 1.1 El hallazgo principal: sobre-escapado silencioso

Es el error §8.8 del documento base, ocurriendo aquí:

```
patrón de la regla : $env:Path = "C:\\Users\\usuario\\.local\\bin    ← doble barra
comando real       : $env:Path = "C:\Users\usuario\.local\bin       ← barra simple
```

**El arnés generó reglas que no coinciden con los comandos de los que salieron.** Las 27 reglas de
PowerShell son peso muerto absoluto. Consecuencia operativa: **aprobar por clic nunca iba a reducir
los prompts de la batería de calidad**, por muchas veces que se hiciera. [MEDIDO-AQUÍ]

### 1.2 El matcher descompone comandos compuestos

El documento base lo dejó como [INFERENCIA] (§9). Aquí hay evidencia más fuerte: **ninguna de las 52
reglas específicas contiene `&&`**, y sin embargo todos mis comandos eran cadenas. El arnés registra
subcomandos individuales, luego descompone. [MEDIDO-AQUÍ] — *contribución de este proyecto al
documento base.*

### 1.3 El clasificador del runtime también actúa aquí

17 reglas específicas fueron creadas para comandos que **ya estaban cubiertos** por una regla
genérica anterior — 12 de ellas `git commit` bajo `Bash(git commit *)`. Coincide con la incógnita
registrada en §9 del documento base: existe una capa de decisión que produce prompts pese a que las
reglas cubran. **No es diagnosticable desde dentro.** [MEDIDO-AQUÍ el síntoma; el mecanismo,
NO VERIFICADO]

---

## 2. Capacidades de nuestros hooks

Los tres hooks de este proyecto, con sus contratos leídos del código:

| Hook | Códigos que emite | ¿Puede preguntar? | ¿Puede bloquear? |
|---|---|---|---|
| `command-write-protection.js` | 0, **2** | **No** | Sí |
| `pre-edit-protection.js` | 0, **2** | **No** | Sí |
| `rules-inject.js` | 0 + `permissionDecision: 'allow'` | No — **autoriza** | No |

[MEDIDO-AQUÍ]. Confirma §2.4 del documento base: **un hook no puede escalar a pregunta.**
`rules-inject` *reduce* prompts autorizando ediciones que casan con una regla de path.

**Falso positivo observado** (§6.11 del documento base): `command-write-protection` bloqueó un
comando que solo **leía**, porque la cadena `settings.local.json` aparecía en el texto. Detecta la
subcadena, no la operación. Ocurrió **1 vez** en esta sesión. [MEDIDO-AQUÍ]

---

## 3. Política por capacidades, adaptada al ciclo ASDD

Sustituye la tabla genérica del documento base por **nuestras** operaciones reales.

| Capacidad del ciclo ASDD | Decisión | Razón |
|---|---|---|
| Leer código, backlog, ADR, specs, gate-log | ALLOW | Sin efectos. Es ~40 operaciones por HU |
| Escribir en `src/`, `tests/`, `items/`, `docs/` | ALLOW | Versionado: `git diff` es el control real (§2.8 del base) |
| Batería de calidad (`pytest`, `ruff`, `mypy`) | ALLOW | Solo lectura por naturaleza; su propósito es fallar sin consecuencias |
| `uv sync` (instalar desde el lock) | ALLOW | El contenido ya pasó por ADR y revisión |
| `uv add` (dependencia nueva) | ASK | Introduce código no revisado. **Además exige ADR por constitución** |
| `uv run python <script>` | ASK | Código arbitrario: puede escribir donde quiera |
| Git en lectura (`status/log/diff/show/branch`) | ALLOW | Lista **acotada y estable** — se enumera (§2.7 del base) |
| `git add` / `git commit` | ALLOW | Local y reversible |
| `git checkout -b` / `branch -d` | ALLOW | Reversible vía reflog |
| `git merge` | ASK | Integra a `develop`: estado compartido |
| `git push` | ASK | **Sale de la máquina**; irreversible |
| Reescritura de historia (`--force`, `reset --hard`, `rebase`) | DENY | Destruye trabajo. Sin caso de uso legítimo aquí |
| Escribir en `.claude/` | ASK | Altera la propia gobernanza |
| Leer los medios del cliente (fuera del workspace) | ASK | **PII** (charter §6.6) |
| Escribir fuera del workspace | DENY | Sin caso de uso |
| Red (`curl`, `irm`, `pip install`) | DENY | Ejecuta código externo. El proyecto es local por charter §6.1 |

**Nota crítica heredada del documento base (§2.6):** `ask` se evalúa **antes** que `allow`, y la
especificidad no altera el orden [MEDIDO-SBS]. Por eso arriba **no hay ningún `ask` amplio sobre
`git`**: las lecturas se enumeran en `allow` y las escrituras peligrosas se nombran una a una. Un
`ask` genérico sobre git anularía todas nuestras reglas de lectura.

---

## 4. Qué versionar

| Archivo | Contenido | Regla |
|---|---|---|
| `.claude/settings.json` **(versionado)** | `deny`, `ask`, `allow` genéricas y relativas, **registro de hooks** | Sin registro los hooks no existen: no hay auto-discovery [MEDIDO-SBS] |
| `.claude/settings.local.json` (ignorado) | Rutas absolutas, adaptación de esta máquina | Ya está en `.gitignore` |
| `~/.claude/settings.json` | Preferencias transversales del desarrollador | Nunca reglas de este proyecto |

**Criterio único para clasificar cualquier regla:** *¿seguiría siendo cierta para otro desarrollador
en otra máquina?* Sí → política, versionada. No → configuración, local. Resuelve el 100% de los casos
encontrados aquí.

---

## 5. Reglas de higiene, con su detección

Adaptadas de §6 del documento base a lo que sí nos ocurrió:

| # | Error | Cómo detectarlo aquí | ¿Ocurrió? |
|---|---|---|---|
| 1 | Política acumulada por clics | Proporción de reglas sin comodín | **Sí: 68% específicas** |
| 2 | Reglas irrepetibles | Buscar rutas absolutas y variantes de un comando | **Sí: 29 con rutas de máquina** |
| 3 | Ausencia de capa `deny` | Contarlas | **Sí: 0 en los 4 archivos** |
| 4 | Sobre-escapado silencioso | Comparar el patrón des-escapado contra el comando real | **Sí: 27 de 27 PowerShell** |
| 5 | `ask` amplio que anula `allow` | Para cada `allow`, ver si un `ask` la cubre | No (no hay `ask` todavía) |
| 6 | Falso positivo del hook por análisis de texto | Ocurre solo | **Sí: 1 vez** |
| 7 | Protección que falla en silencio | Ejecutar el hook sin Node y observar | **[NO VERIFICADO] aquí** |

---

## 6. Nuestra causa raíz, corregida por la evidencia

| # | Causa | Reglas | Impacto | Marca |
|---|---|---|---|---|
| 1 | **Sobre-escapado de las reglas PowerShell** | 27/52 | **52%** | [MEDIDO-AQUÍ] |
| 2 | Clasificador del runtime sobre `git commit` | 17/52 | **33%** | síntoma [MEDIDO-AQUÍ], mecanismo [NO VERIFICADO] |
| 3 | Comandos únicos de una sola vez | 8/52 | **15%** | [MEDIDO-AQUÍ] |
| 4 | Hooks | 0 | **0%** | [MEDIDO-AQUÍ] |

Corrige mi diagnóstico anterior: atribuí el 52% al prefijo `$env:`. **El prefijo era secundario; la
causa es el escapado.** Un comando sin prefijo habría fallado igual.

---

## 7. Plan, en orden de valor demostrado

Sigue §7 del documento base, con nuestra intervención mínima primero (§8.7: *medir primero la
intervención mínima*):

1. **Reiniciar Claude Code** → uv queda en el PATH; desaparece el prefijo. Verificable en un comando.
2. **Cambiar mi estilo de invocación**: sin `&&` (el matcher descompone), comandos estables sin
   variantes de `Select-Object -Last N`, commits con `-F` en vez de `-m` multilínea. **No requiere
   tocar configuración.**
3. **Medir una HU completa** antes de reescribir nada. Si los prompts caen, el rediseño se simplifica.
4. Escribir `deny` y `ask` (hoy inexistentes) — **es el hueco de seguridad real**, independiente del ruido.
5. **Verificar que `deny` dispara** con un caso inocuo. Una regla de seguridad no verificada no cuenta
   (§8.6 del base).
6. Mover las 29 reglas de máquina a `settings.local.json`.
7. Validador que falle si una regla contiene rutas absolutas o escapado sospechoso.

---

## 8. Incertidumbres registradas

- **El clasificador del runtime.** Produce prompts pese a reglas que cubren. Límite superior de
  cualquier trabajo aquí. [NO VERIFICADO — coincide con §9 del base]
- **Por qué el arnés sobre-escapa al generar reglas.** Observado el efecto, no el mecanismo.
- **Si `deny` y `ask` funcionan en esta versión.** Documentados; **ningún archivo los usa**, así que
  no hay evidencia local. Se verifican en el paso 5.
- **Comportamiento de los hooks sin Node.** No probado aquí; el base lo midió como *falla abierta*.

> Los hechos **[MEDIDO-AQUÍ]** se verificaron el 26-jul-2026 sobre esta instalación. Los
> **[MEDIDO-SBS]** provienen de otra auditoría y **no fueron re-verificados**: antes de apoyarse en
> ellos conviene repetir el experimento, que cuesta minutos.
