"""Video: encuadre vertical, guiones de reel y la puerta hacia el binario externo."""

from media_optimizer.video.ffmpeg_executor import (
    NORMALIZAR_TIEMPOS_AUDIO,
    NORMALIZAR_TIEMPOS_VIDEO,
    FfmpegResult,
    build_command,
    build_probe_command,
    degrade,
    detect_version,
    is_available,
    log_version,
    normalized_segment,
    probe_filtergraph,
    run,
)
from media_optimizer.video.framing import (
    build_crop_command,
    crop_to_vertical,
    read_dimensions,
)
from media_optimizer.video.scene_scoring import (
    MUESTRAS_POR_ESCENA,
    score_scene,
    score_scenes,
)
from media_optimizer.video.scenedetect_adapter import (
    UMBRAL_POR_DEFECTO,
    PySceneDetectAdapter,
)
from media_optimizer.video.templates import (
    NarrativeSlot,
    ReelTemplate,
    SlotAssignment,
    Timeline,
    assign_slots,
    template_from_data,
)
from media_optimizer.video.transforms import (
    ALTO_VERTICAL,
    ANCHO_VERTICAL,
    CUADROS_POR_SEGUNDO,
    CropBox,
    VerticalFraming,
    frame_to_vertical,
    vertical_filter_chain,
)

__all__ = [
    "ALTO_VERTICAL",
    "ANCHO_VERTICAL",
    "CUADROS_POR_SEGUNDO",
    "MUESTRAS_POR_ESCENA",
    "NORMALIZAR_TIEMPOS_AUDIO",
    "NORMALIZAR_TIEMPOS_VIDEO",
    "UMBRAL_POR_DEFECTO",
    "CropBox",
    "FfmpegResult",
    "NarrativeSlot",
    "PySceneDetectAdapter",
    "ReelTemplate",
    "SlotAssignment",
    "Timeline",
    "VerticalFraming",
    "assign_slots",
    "build_command",
    "build_crop_command",
    "build_probe_command",
    "crop_to_vertical",
    "degrade",
    "detect_version",
    "frame_to_vertical",
    "is_available",
    "log_version",
    "normalized_segment",
    "probe_filtergraph",
    "read_dimensions",
    "run",
    "score_scene",
    "score_scenes",
    "template_from_data",
    "vertical_filter_chain",
]
