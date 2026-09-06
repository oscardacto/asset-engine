# Insumo — HU-102 en el backlog

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-102 | Score técnico por escena: nitidez, exposición, estabilidad (muestreo de frames) | HU-101, HU-029 | P2 | L |

## Estado real de las dependencias

| HU | Qué aporta | Estado |
|----|-----------|--------|
| HU-101 | Las escenas a puntuar | ✅ DONE |
| HU-029 | Score de exposición compuesto | ✅ DONE |
| **HU-023** | **`ADR`+impl. Métrica de nitidez (varianza de Laplaciano vs Tenengrad)** | ❌ **no iniciada** |
| HU-100 | Ingesta de clips con streaming | ❌ no iniciada |

## La dependencia que el backlog no declara

El enunciado pide **nitidez**, pero **HU-102 no declara depender de HU-023**, que es
justamente la HU que decide cómo se mide la nitidez — y es un `ADR`, o sea una decisión de
stack sin cerrar (varianza de Laplaciano frente a Tenengrad).

Implementar la nitidez aquí significaría **tomar esa decisión sin su ADR**, que es lo que la
gobernanza del proyecto prohíbe. El score se construye extensible para que la nitidez entre
como un componente más cuando HU-023 cierre, sin tocar el resto.

## Sobre el muestreo de frames

HU-100 (ingesta de clips con streaming) tampoco está. Aquí no hace falta la ingesta completa:
basta con leer unos pocos frames repartidos por la escena. El charter exige que el video vaya
en streaming y **nunca completo a RAM**, así que se salta a las posiciones concretas en vez
de recorrer el clip entero.

## Consumidores

| ID | HU | Qué le pide |
|----|----|-------------|
| HU-103 | Descarte de escenas malas con causas | El score y sus componentes, para explicar el descarte |
| HU-105 | Secuenciado narrativo | Escenas ordenadas por calidad |
