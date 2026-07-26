"""Contratos del dominio: las piezas de datos que el resto del sistema intercambia.

En simple: aquí solo se definen estructuras de información — nunca se abren
archivos, ni se procesa imagen o video.
"""

from media_optimizer.core.media_asset import MediaAsset, MediaType, Orientation
from media_optimizer.core.quality_report import QualityReport, Verdict

__all__ = ["MediaAsset", "MediaType", "Orientation", "QualityReport", "Verdict"]
