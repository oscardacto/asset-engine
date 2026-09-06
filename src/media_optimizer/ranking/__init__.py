"""Ranking y selección: decidir cuáles fotos se usan y en qué orden — dominio puro."""

from media_optimizer.ranking.selection import (
    RankedAsset,
    cover_candidates,
    gallery_order,
    global_score,
    rank,
    select_by_format,
)

__all__ = [
    "RankedAsset",
    "cover_candidates",
    "gallery_order",
    "global_score",
    "rank",
    "select_by_format",
]
