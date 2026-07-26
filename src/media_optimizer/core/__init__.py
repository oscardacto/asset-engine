"""Contratos del dominio: las piezas de datos que el resto del sistema intercambia.

En simple: aquí solo se definen estructuras de información — nunca se abren
archivos, ni se procesa imagen o video.
"""

from media_optimizer.core.errors import CorruptMediaError, InvalidInputError, MediaOptimizerError
from media_optimizer.core.media_asset import MediaAsset, MediaType, Orientation
from media_optimizer.core.quality_report import QualityReport, Verdict
from media_optimizer.core.transform import ParamValue, Transform, TransformHistory

__all__ = [
    "CorruptMediaError",
    "InvalidInputError",
    "MediaAsset",
    "MediaOptimizerError",
    "MediaType",
    "Orientation",
    "ParamValue",
    "QualityReport",
    "Transform",
    "TransformHistory",
    "Verdict",
]
