"""Ingesta: encuentra, valida y cataloga los medios crudos del usuario.

En simple: la puerta de entrada del pipeline — de una carpeta del usuario a una
lista ordenada de archivos, sin tocar jamás los originales.
"""

from media_optimizer.ingest.formats import (
    SUPPORTED_FORMATS,
    ImageFormat,
    detect_image_format,
    is_supported_image,
)
from media_optimizer.ingest.hashing import (
    HASH_ALGORITHM,
    DuplicateGroup,
    compute_content_hash,
    find_duplicate_groups,
)
from media_optimizer.ingest.scanner import scan_input_folder

__all__ = [
    "HASH_ALGORITHM",
    "SUPPORTED_FORMATS",
    "DuplicateGroup",
    "ImageFormat",
    "compute_content_hash",
    "detect_image_format",
    "find_duplicate_groups",
    "is_supported_image",
    "scan_input_folder",
]
