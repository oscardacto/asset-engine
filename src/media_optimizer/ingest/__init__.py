"""Ingesta: encuentra, valida y cataloga los medios crudos del usuario.

En simple: la puerta de entrada del pipeline — de una carpeta del usuario a una
lista ordenada de archivos, sin tocar jamás los originales.
"""

from media_optimizer.ingest.catalog import (
    CATALOG_FILENAME,
    CATALOG_VERSION,
    Catalog,
    CatalogEntry,
    QuarantineRecord,
    catalog_from_triage,
    load_catalog,
    save_catalog,
)
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
    "CATALOG_FILENAME",
    "CATALOG_VERSION",
    "HASH_ALGORITHM",
    "MAX_DECODED_BYTES",
    "MAX_SIDE",
    "SUPPORTED_FORMATS",
    "Catalog",
    "CatalogEntry",
    "DuplicateGroup",
    "ExifData",
    "ExifOrientation",
    "ImageFormat",
    "ImageSize",
    "QuarantineReason",
    "QuarantineRecord",
    "QuarantinedAsset",
    "TriageResult",
    "catalog_from_triage",
    "compute_content_hash",
    "detect_image_format",
    "find_duplicate_groups",
    "is_supported_image",
    "load_catalog",
    "oriented_size",
    "read_exif",
    "read_exif_from_header",
    "read_image_size",
    "read_image_size_from_path",
    "save_catalog",
    "scan_input_folder",
    "triage_media",
]
