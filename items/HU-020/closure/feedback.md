# Feedback — HU-020 + HU-021 + HU-022

## Lecciones aprendidas
- **"Brillo" tenía una respuesta correcta y varias incorrectas**, y la diferencia no era
  académica: promediar canales rompería el KPI de paridad ±2% sobre las fotos cálidas del
  cliente. El test de colores puros fija los coeficientes para siempre.
- **La frontera exacta de un umbral no existe en aritmética flotante.** Sobre una imagen
  BGR uniforme, la luminancia de 10 da 9.9999…; solo en escala de grises el valor es
  exacto. El semántico "estrictamente bajo el umbral" se prueba donde puede ser verdad.
- **Tres HUs, un histograma:** implementarlas juntas evitó decodificar tres veces la misma
  imagen y les dio una superficie de API coherente. Cada una conservó su CA y su cierre.

## Decisiones rechazadas
- **`cv2.imread(ruta)`** — se salta la capa de ADR-004 y muere en rutas hostiles; se leen
  bytes y se decodifica en memoria.
- **Umbrales por defecto en las funciones** — serían criterio de negocio en código.
- **Redondear los ratios** — la presentación es de los reportes; el dato viaja completo.
