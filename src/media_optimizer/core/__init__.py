"""Contratos del dominio — puros, sin IO (hexagonal ligera).

Cada contrato nace con su HU: ``MediaAsset`` (HU-157); ``QualityReport`` (HU-158),
``Transform`` (HU-159) y ``BusinessProfile`` (HU-160) llegarán con las suyas.
"""

from media_optimizer.core.media_asset import MediaAsset, MediaType, Orientation

__all__ = ["MediaAsset", "MediaType", "Orientation"]
