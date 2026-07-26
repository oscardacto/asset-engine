"""Utilidades de prueba: datos sintéticos con propiedades controladas.

En simple: aquí vive lo que los tests y benchmarks necesitan fabricar (imágenes
falsas, archivos rotos) para no depender jamás de medios reales del cliente.
"""

from media_optimizer.testing.synthetic import (
    Image,
    encode_jpeg,
    flat_image,
    not_an_image,
    textured_image,
    truncated_jpeg,
    write_jpeg,
)

__all__ = [
    "Image",
    "encode_jpeg",
    "flat_image",
    "not_an_image",
    "textured_image",
    "truncated_jpeg",
    "write_jpeg",
]
