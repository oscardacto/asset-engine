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
from media_optimizer.core.scene_score import SceneScore
from media_optimizer.core.scene_selection import (
    UMBRALES_POR_DEFECTO,
    DiscardReason,
    SceneThresholds,
    SceneVerdict,
    judge_scene,
    kept_scenes,
    select_scenes,
)
from media_optimizer.core.scene_trimmer import (
    MINIMO_POR_ESCENA,
    TrimPlan,
    TrimStrategy,
    trim_to_target,
)
from media_optimizer.core.stage_report import ReproducibleStageSummary, StageReport
from media_optimizer.core.transform import ParamValue, Transform, TransformHistory

__all__ = [
    "MINIMO_POR_ESCENA",
    "UMBRALES_POR_DEFECTO",
    "BusinessProfile",
    "CorruptMediaError",
    "DiscardReason",
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
    "SceneScore",
    "SceneThresholds",
    "SceneVerdict",
    "ScoringWeights",
    "StageReport",
    "Transform",
    "TransformHistory",
    "TrimPlan",
    "TrimStrategy",
    "Verdict",
    "judge_scene",
    "kept_scenes",
    "select_scenes",
    "stable_order",
    "stable_order_by",
    "stable_text",
    "stable_unique",
    "trim_to_target",
]
