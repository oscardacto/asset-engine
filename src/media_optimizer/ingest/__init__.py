"""Ingesta: encuentra, valida y cataloga los medios crudos del usuario.

En simple: la puerta de entrada del pipeline — de una carpeta del usuario a una
lista ordenada de archivos, sin tocar jamás los originales.
"""

from media_optimizer.ingest.dimensions import (
    MAX_DECODED_BYTES,
    MAX_SIDE,
    ImageSize,
    read_image_size,
    read_image_size_from_path,
)
from media_optimizer.ingest.exif import (
    ExifData,
    ExifOrientation,
    oriented_size,
    read_exif,
    read_exif_from_header,
)
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
from media_optimizer.ingest.quarantine import (
    QuarantinedAsset,
    QuarantineReason,
    TriageResult,
    triage_media,
)
from media_optimizer.ingest.scanner import scan_input_folder

__all__ = [
    "HASH_ALGORITHM",
    "MAX_DECODED_BYTES",
    "MAX_SIDE",
    "SUPPORTED_FORMATS",
    "DuplicateGroup",
    "ExifData",
    "ExifOrientation",
    "ImageFormat",
    "ImageSize",
    "QuarantineReason",
    "QuarantinedAsset",
    "TriageResult",
    "compute_content_hash",
    "detect_image_format",
    "find_duplicate_groups",
    "is_supported_image",
    "oriented_size",
    "read_exif",
    "read_exif_from_header",
    "read_image_size",
    "read_image_size_from_path",
    "scan_input_folder",
    "triage_media",
]
