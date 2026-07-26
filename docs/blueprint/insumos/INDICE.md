# Índice de insumos — cliente 0 (LIVING POP / LIVING 42)

Insumos de negocio del cliente 0. Read-only mental: si un insumo tiene un error, se
anota en el feedback del WorkItem que lo detecte — el archivo original no se edita.

**Fuente canónica:** `D:\Proyectos\Bacano (Parcela)\Living\Claude\` (copias del 26-jul-2026).
La copia en `Marca\claude v1\insumos\` es anterior y queda descartada.

| Archivo | Qué es | Por qué importa para media-optimizer |
|---------|--------|--------------------------------------|
| `documento-maestro.md` | **Fuente única de verdad** v1.2 · 25-jul-2026: identidad, activo, precios, canales, inventario de activos digitales, decisiones pendientes y vacíos | El insumo rector. Su §8 es la spec de facto de los módulos de análisis y revelado: métricas usadas (brillo medio, % píxeles negros, orientación V/H), detección de compresión WhatsApp (techo 1288×952, prefijo `WA`), criterios de descarte (subexposición, sombras aplastadas), y el revelado por lotes ya aplicado una vez a mano (sombras por máscara de luminancia, protección de altas luces, calidez solo en luces, saturación ≤6%) que el software debe reproducir de forma determinista |
| `sistema-contenido-redes-v1.1.md` | Documento operativo de contenido para redes (IG/TikTok/FB) v1.1 · 25-jul-2026 | Formatos de salida (9:16 video, 4:5 foto, nunca 1:1), ambientes esperados por pieza, guiones R1–R5, cobertura de activos por calendario, KPIs de contenido |
| `plan-crecimiento-reservas.md` | Hoja de ruta a 90 días: ocupación 45% → 65% | Prioridades de negocio que ordenan el backlog (portada primero, originales, estancia media); métricas de control |
| `anuncio-airbnb.md` | Copia campo por campo del anuncio vivo + auditoría de configuración | Requisitos del "perfil de salida Airbnb": portada, orden de fotos, exactitud ≥4,9 |
| `brandbook-definitivo.md` | ⚠️ No es el brandbook: es el **prompt maestro** del comité ejecutivo de LIVING POP (el Maestro §0 lo declara absorbido en sus §2 y §7) | Criterio estético vigente vive en Maestro §2; este archivo queda como referencia del marco de evaluación (5 ejes) |

## Insumos referenciados, disponibles fuera del repo (no se versionan)

- **Archivo fotográfico real** — `D:\...\Living\Fotos\` (45 archivos). Dataset de
  validación del cliente 0; no se comitea (PII + peso). Su inventario técnico completo
  está en Maestro §8.2.
- **`Proyeccion_Living_POP_2026.pdf`**, **`Data airbinb Living POP 302.docx`**,
  **`Brief_Living42_Cauce.docx`** — respaldo ejecutivo, absorbidos por el Maestro (§0).
- `livingpop_fotos_reveladas.zip` · `livingpop_9piezas.zip` — entregables del revelado
  manual del 25-jul; referencia de salida esperada.

## Nota de confidencialidad

Estos documentos contienen cifras de negocio reales (tarifas, márgenes, presupuestos)
y el Maestro §10 incluye la clave WiFi del apartamento. El repo es privado y local; si
algún día se publica o comparte, esta carpeta debe excluirse o anonimizarse antes.
