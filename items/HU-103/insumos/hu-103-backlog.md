# Insumo — HU-103 en el backlog

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-103 | Descarte de escenas malas con causas | HU-102 | P2 | S |

## Lo que HU-102 dejó medido, y que condiciona los umbrales

Sobre los 7 videos del cliente (19 escenas):

| Métrica | Rango observado | Consecuencia |
|---------|-----------------|--------------|
| Estabilidad | **0.000 – 0.404** | Un umbral de 0.5 descartaría **las 19 escenas**. La escala es estricta para video de celular a pulso |
| Exposición | 0.799 – 0.976 | El material del cliente está bien expuesto; el problema no es la luz |
| Duración | 5 escenas de menos de 1,5 s en el video largo | Probablemente paneo cruzando el umbral de detección, no cortes reales |

## El aviso que cambia el diseño

HU-102 dejó anotado que **la nota general promedia solo los componentes disponibles**, y que
cuando entre la nitidez (HU-023) ese promedio cambiará de valor sin cambiar de contrato.

Consecuencia directa: **un umbral sobre la nota general se comportaría distinto ese día**, sin
que nadie tocara nada. Los umbrales tienen que ir por componente.

## Consumidores

| ID | HU | Qué le pide |
|----|----|-------------|
| HU-105 | Secuenciado narrativo | Solo las escenas que sobreviven al descarte |
| HU-110 | Reel 9:16 | El reporte de escenas usadas y descartadas, con sus causas |
