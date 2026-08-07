# Entregables — HU-020 + HU-021 + HU-022

| CA | Resultado | Evidencia |
|----|-----------|-----------|
| CA-1 Paridad ±2% sobre fixtures de brillo conocido | ✅ | parametrizado en 4 objetivos, tolerancia 255·2% |
| CA-2 Luminancia perceptual con orden BGR (rojo≈76, azul≈29, verde≈150) | ✅ | 2 tests de colores puros |
| CA-3 Ratios exactos sobre proporciones conocidas | ✅ | mitad negra ⇒ 0.5; franja quemada ⇒ 0.2 |
| CA-4 Negra: crushed=1.0/blown=0.0; blanca al revés | ✅ | 4 tests |
| CA-5 Umbrales como parámetros | ✅ | ninguna constante de umbral en el módulo; `ValueError` fuera de rango |
| CA-6 `decode_image` por la capa; ruta larga; corrupto degrada | ✅ | 3 tests |
| CA-7 Determinismo exacto | ✅ | 2 tests |
| CA-8 Gobernanza + cobertura + gate-log por HU | ✅ | 100% del módulo; eventos 020/021/022 |

**Resultado: 8/8 · 0 fallidos · sin rework.**

## Validación con medios reales
Fotos editadas (`Anuncio/`): brillo 126–144, negro <1–8%. Crudas del celular: brillo 65–97,
negro hasta 24%. Coherente con el patrón de la auditoría manual del Maestro §8.2.
