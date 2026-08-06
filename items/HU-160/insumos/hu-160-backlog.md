# Insumo — HU-160 en el backlog

> Copia literal de `docs/blueprint/backlog.md`, épica **E7 · Plataforma**.

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-160 | Contrato `BusinessProfile` en `core/` (solo estructura; datos en E6) | HU-150 | P0 | S |

## Regla de generalización que esta HU materializa

> Charter §3 — *"todo criterio específico del cliente (pesos de score, ambientes
> esperados, estética del revelado, formatos de salida) entra como **datos** del perfil
> de negocio (`profiles/`), nunca como código. El primer perfil es `hospedaje`; la
> arquitectura no asume que sea el único."*

Y el riesgo que mitiga, del mismo charter:

> *"Un solo cliente real — riesgo de sobreajuste al caso LIVING POP → Regla 'perfiles como
> datos' + revisión de generalización en cada gate de spec."*

## Consumidores declarados en el backlog

| ID | HU | Qué le pide al perfil |
|----|----|----------------------|
| HU-008 | Flag "bajo el nativo": resolución insuficiente por formato de salida del perfil (1080/1350/1920) | Las dimensiones objetivo de cada formato |
| HU-029 | Score de exposición compuesto (fórmula = datos del perfil) | Umbrales de exposición |
| HU-033 | Cobertura de ambientes del lote vs esperados por el perfil | La lista de ambientes esperados |
| HU-070 | Score global por asset: combinación ponderada según pesos del perfil | Pesos por métrica |
| HU-130 | Esquema del perfil: estructura, tipos y validación (carga falla rápido y claro) | **La estructura que esta HU define** |
| HU-132 | Perfil `hospedaje` v1: ambientes, estética (sat ≤6%, sin HDR), formatos (4:5, 9:16, nunca 1:1) | Todo lo anterior, con datos reales |
| HU-133 | Umbrales técnicos por perfil: descarte, flags, objetivos de exposición | Umbrales por nombre |
| HU-134 | Pesos del score por perfil (portada vs feed vs story) | Pesos **por intención de salida** |

## Frontera explícita con E6

El enunciado dice *"solo estructura; datos en E6"*. La carga desde archivo, los mensajes de
error accionables y los defaults del sistema son **HU-130, HU-131 y HU-136** — no esta HU.
