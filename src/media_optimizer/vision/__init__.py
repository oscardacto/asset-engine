"""Primitivas de visión compartidas: medir imágenes, no decidir sobre ellas.

En simple: aquí viven las funciones que convierten una foto en números —brillo,
sombras, luces—. Qué hacer con esos números (aprobar, descartar, corregir) lo
deciden otras capas con el criterio del perfil de negocio.
"""

from media_optimizer.vision.exposure import (
    Image,
    blown_highlights_ratio,
    crushed_shadows_ratio,
    decode_image,
    luminance,
    mean_brightness,
)

__all__ = [
    "Image",
    "blown_highlights_ratio",
    "crushed_shadows_ratio",
    "decode_image",
    "luminance",
    "mean_brightness",
]
