"""Contratos del dominio: las piezas de datos que el resto del sistema intercambia.

En simple: aquí solo se definen estructuras de información — nunca se abren
archivos, ni se procesa imagen o video.
"""

from media_optimizer.core.business_profile import (
    BusinessProfile,
    OutputFormat,
    OutputIntent,
    ScoringWeights,
)
from media_optimizer.core.determinism import (
    stable_order,
    stable_order_by,
    stable_text,
    stable_unique,
)
from media_optimizer.core.errors import CorruptMediaError, InvalidInputError, MediaOptimizerError
from media_optimizer.core.media_asset import MediaAsset, MediaType, Orientation
from media_optimizer.core.ports import SceneDetectorPort
from media_optimizer.core.quality_report import QualityReport, Verdict
from media_optimizer.core.scene import Scene
from media_optimizer.core.stage_report import ReproducibleStageSummary, StageReport
from media_optimizer.core.transform import ParamValue, Transform, TransformHistory

__all__ = [
    "BusinessProfile",
    "CorruptMediaError",
    "InvalidInputError",
    "MediaAsset",
    "MediaOptimizerError",
    "MediaType",
    "Orientation",
    "OutputFormat",
    "OutputIntent",
    "ParamValue",
    "QualityReport",
    "ReproducibleStageSummary",
    "Scene",
    "SceneDetectorPort",
    "ScoringWeights",
    "StageReport",
    "Transform",
    "TransformHistory",
    "Verdict",
    "stable_order",
    "stable_order_by",
    "stable_text",
    "stable_unique",
]
