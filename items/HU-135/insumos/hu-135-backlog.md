# Insumo — HU-135 en el backlog

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-135 | Plantillas narrativas como datos: orden de galería y guiones de reel | HU-132 | P1 | M |

## La regla que la gobierna

Charter §3:

> *"todo criterio específico del cliente (pesos de score, ambientes esperados, estética del
> revelado, formatos de salida) entra como **datos** del perfil de negocio, nunca como
> código. El primer perfil es `hospedaje`; la arquitectura no asume que sea el único."*

**Esta HU es el caso más tentador de romper esa regla.** Un guion de reel tiene tramos con
nombres concretos —fachada, umbral, cocina— y escribirlos como constantes del programa se
siente natural. Pero un bar abre con la barra y un restaurante con el plato: si los nombres
vivieran en el código, cambiar de vertical exigiría cambiar el programa.

## Consumidores

| ID | HU | Qué le pide |
|----|----|-------------|
| HU-105 | Secuenciado narrativo del reel según plantilla del perfil | El guion y el reparto de clips |
| HU-072 | Orden narrativo de galería | La misma estructura, aplicada a fotos |
| HU-033 | Cobertura de ambientes: qué falta grabar | Los huecos del guion |

## Frontera con E6

Los **datos** del guion `hospedaje` y su calibración son HU-132. Esta HU define la forma y el
reparto; el archivo de ejemplo que la acompaña sirve para verificar que la forma admite un
guion real, no para fijar el criterio definitivo del cliente.
