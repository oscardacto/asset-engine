# Insumo — HU-106 en el backlog

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-106 | Recorte de clips a duración objetivo por segmento de la plantilla | HU-105 | P2 | M |

## Por qué se toma antes que su dependencia declarada

El backlog la cuelga de HU-105 (secuenciado narrativo), y HU-105 está **bloqueada por
HU-032** (etiquetado de ambientes): los 6 tramos del guion `hospedaje` declaran ambiente, así
que sin etiquetado la línea de tiempo saldría vacía.

Pero el núcleo de HU-106 —ajustar un conjunto de escenas a una duración— **no necesita el
guion**: opera sobre `Scene`, que ya existe desde HU-101, y sobre las escenas que sobreviven
al descarte de HU-103. Cuando HU-105 llegue, solo tiene que llamarlo con los tramos ya
repartidos.

Se toma ahora para no dejar la épica parada esperando a HU-032.

## La medición que condiciona el diseño

El enunciado del trabajo pide cumplir **exactamente** la duración objetivo. Medido en esta
máquina:

```
recorte proporcional de tres escenas a 15 s  ->  15.000000000000002
```

**«Exacto» y «coma flotante» no conviven.** Sumar duraciones escaladas acumula error, y un
reel que dice durar 15 s y dura 15.000000000000002 falla cualquier comparación exacta — que
es justo lo que el charter §6.1 promete verificar.

La aritmética del recorte va en **milisegundos enteros**, con el residuo asignado a una sola
escena. Así la suma cierra al milisegundo, siempre.

## Consumidores

| ID | HU | Qué le pide |
|----|----|-------------|
| HU-105 | Secuenciado narrativo | Ajustar cada tramo del guion a su duración |
| HU-107 | Ensamblado del reel | Escenas ya con la duración final |
