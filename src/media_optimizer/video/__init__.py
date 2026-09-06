"""Video: encuadre vertical, guiones de reel y la puerta hacia el binario externo."""

from media_optimizer.video.ffmpeg_executor import (
    NORMALIZAR_TIEMPOS_AUDIO,
    NORMALIZAR_TIEMPOS_VIDEO,
    FfmpegResult,
    build_command,
    build_probe_command,
    degrade,
    is_available,
    normalized_segment,
    probe_filtergraph,
    run,
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
    "NORMALIZAR_TIEMPOS_AUDIO",
    "NORMALIZAR_TIEMPOS_VIDEO",
    "CropBox",
    "FfmpegResult",
    "NarrativeSlot",
    "ReelTemplate",
    "SlotAssignment",
    "Timeline",
    "VerticalFraming",
    "assign_slots",
    "build_command",
    "build_probe_command",
    "degrade",
    "frame_to_vertical",
    "is_available",
    "normalized_segment",
    "probe_filtergraph",
    "run",
    "template_from_data",
    "vertical_filter_chain",
]
