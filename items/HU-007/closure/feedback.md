# Feedback — HU-007 + HU-008

## Lecciones aprendidas
- **Una señal de detección envejece; la medición previa lo detectó antes de codificarla.**
  El techo 1288×952 era cierto cuando se escribió el backlog y hoy da 16/16 falsos
  negativos. Es el mismo método de HU-010/156/169: medir antes de implementar la hipótesis
  del enunciado. Cuarta vez que invalida una suposición escrita.
- **El mejor discriminador no fue uno sino la conjunción de dos débiles**: EXIF ausente
  (3 FP por sí solo) ∧ bpp bajo (solapa por sí solo) → juntos, margen 0.114–0.234 sin
  ningún caso ambiguo en 102 assets.

## Decisiones rechazadas
- **Techo de dimensiones** — refutado por medición.
- **Solo el nombre** — una renombrada lo pierde; la física no se pierde.
- **Decodificar la imagen para estimar calidad JPEG** — caro y innecesario: los metadatos
  del triaje ya bastan para 0 FP.
