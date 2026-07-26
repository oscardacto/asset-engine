# Spec Técnica `<ID>` — `<Nombre del WorkItem>`

> **Estado:** DRAFT
> **Fecha de generación:** `<YYYY-MM-DD>`
> **Última actualización:** `<YYYY-MM-DD>`
> **Confianza global:** `<NN>%` — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** `<1 frase>`
- **Para quién:** `<perfil de usuario>`
- **Módulo / dominio:** `<módulo>`
- **No obvio (lo crítico que el ticket no dice de frente):** `<1 frase>`

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- `<bullet>`

### 2.2 OUT — NO entra (delimitaciones)
- `<bullet>`

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 |   |   | ticket §X.Y |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- `<bullet>` → P-`<N>`

---

## 3. Componentes técnicos identificados

> Lectura desde la rama principal, no de feature branches. Si un componente NO existe aún, marcarlo como **pendiente**.

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `<módulo.Clase>` | nuevo / modif / elim | alto / medio / bajo | ✅ / ❌ / N/A |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación (read/insert/update/delete) | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [ ] No

---

## 5. Reglas de negocio

> Cada regla con su **fuente exacta** (ticket §, minuto:segundo del audio, fila del Excel).

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 |   | ticket §X.Y |   |   |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 |   |   |

---

## 6. Preguntas abiertas

> Estas preguntas **bloquean el inicio del desarrollo**. Cada una con dueño y mi mejor hipótesis.

### P-1 — `<pregunta literal>`
- **Importa porque:** `<decisión que bloquea>`
- **Va dirigida a:** `<rol>`
- **Mi mejor hipótesis:** `<respuesta tentativa a confirmar/refutar>`
- **Si se asume mal, costo:** rework / rollback / bloqueante en producción
- **Estado:** ABIERTA / RESUELTA

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 |   | P-`<N>` |   |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 |   | negocio / técnico / datos / seguridad / cronograma | alta / media / baja | alto / medio / bajo |   |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** `<N>` total — `<M>` bloqueantes
- **Asunciones tomadas:** `<K>`
- **Verificaciones cruzadas:**
  - [ ] Codebase actual leído y cruzado
  - [ ] Rama principal de los componentes relevantes leída
  - [ ] Esquema/API real cruzado (vía MCP o equivalente)
  - [ ] Componentes "reutilizables" en §3.1 buscados, no asumidos
- **Recomendación:**
  - [ ] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** `<NN>%`

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|

### 10.2 Datos/configuración previa requerida
- `<bullet>`

### 10.3 Servicios o equipos externos
- `<bullet>`

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — `<criterio original del ticket>`
- **Given:** `<estado inicial>`
- **When:** `<acción>`
- **Then:** `<resultado esperado>`

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| YYYY-MM-DD | Creación inicial | Claude |
