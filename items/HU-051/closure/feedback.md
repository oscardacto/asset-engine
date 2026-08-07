# Feedback — HU-051+052+055

## Lecciones
- **El contrato se probó con un transform falso registrado en el test** — séptima HU
  consecutiva donde el guardián se verifica en ambas direcciones. Es lo que garantiza que
  las 5 transforms restantes de E3 (sombras, exposición, crop, resize, export) entren sin
  tocar el motor.
- **Validar el plan completo antes de procesar** convierte el error de perfil en un fallo
  inmediato y nombrado, no en un lote a medias.

## Decisiones rechazadas
- **Una clase base abstracta por transform** — un dataclass con dos funciones basta; la
  herencia no aporta nada que el registro no dé.
- **Medir tiempo por transform ya** — es de HU-165 (benchmarks con presupuesto); medir sin
  presupuesto es ruido.
