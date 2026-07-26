"""Tests del contrato ``MediaAsset`` (HU-157), organizados por criterio de aceptación (spec §11).

``TestCapaSecundaria`` agrupa los boundary values adicionales — capa secundaria
del ciclo ASDD, separada a propósito de la cobertura de criterios de aceptación.
"""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from media_optimizer.core import MediaAsset, MediaType, Orientation


def _foto(width: int = 1080, height: int = 1920) -> MediaAsset:
    return MediaAsset(
        media_type=MediaType.PHOTO,
        width=width,
        height=height,
        content_hash="a3f5c9",
        source=Path("originales/foto_001.jpg"),
    )


class TestCA1Construccion:
    def test_foto_expone_los_cuatro_conceptos_del_ticket(self) -> None:
        asset = _foto()
        assert asset.media_type is MediaType.PHOTO
        assert (asset.width, asset.height) == (1080, 1920)
        assert asset.content_hash == "a3f5c9"
        assert asset.source == Path("originales/foto_001.jpg")

    def test_video_se_construye_con_el_mismo_contrato(self) -> None:
        asset = MediaAsset(
            media_type=MediaType.VIDEO,
            width=1920,
            height=1080,
            content_hash="b7e2d1",
            source=Path("originales/clip_001.mp4"),
        )
        assert asset.media_type is MediaType.VIDEO


class TestCA2Inmutabilidad:
    def test_asignar_un_campo_lanza_frozen_error(self) -> None:
        asset = _foto()
        with pytest.raises(FrozenInstanceError):
            asset.width = 9999  # type: ignore[misc]


class TestCA3InvariantesFailFast:
    def test_width_cero_falla_nombrando_campo_y_valor(self) -> None:
        with pytest.raises(ValueError, match=r"width.*0"):
            _foto(width=0)

    def test_height_negativo_falla_nombrando_campo_y_valor(self) -> None:
        with pytest.raises(ValueError, match=r"height.*-1"):
            _foto(height=-1)

    def test_hash_vacio_falla(self) -> None:
        with pytest.raises(ValueError, match="content_hash"):
            MediaAsset(
                media_type=MediaType.PHOTO,
                width=100,
                height=100,
                content_hash="",
                source=Path("x.jpg"),
            )


class TestCA4Orientacion:
    @pytest.mark.parametrize(
        ("width", "height", "esperada"),
        [
            (1080, 1920, Orientation.VERTICAL),
            (1920, 1080, Orientation.HORIZONTAL),
            (1000, 1000, Orientation.SQUARE),
        ],
    )
    def test_orientacion_derivada_de_dimensiones(
        self, width: int, height: int, esperada: Orientation
    ) -> None:
        assert _foto(width=width, height=height).orientation is esperada


class TestCA5IgualdadPorValor:
    def test_mismos_campos_son_iguales_y_comparten_hash(self) -> None:
        a, b = _foto(), _foto()
        assert a == b
        assert hash(a) == hash(b)

    def test_un_campo_distinto_rompe_la_igualdad(self) -> None:
        assert _foto() != _foto(width=1081)


class TestCapaSecundaria:
    """Boundary values adicionales — NO son criterios de aceptación."""

    def test_dimension_minima_1x1_es_valida_y_cuadrada(self) -> None:
        asset = _foto(width=1, height=1)
        assert asset.orientation is Orientation.SQUARE

    def test_hash_de_solo_espacios_cuenta_como_vacio(self) -> None:
        with pytest.raises(ValueError, match="content_hash"):
            MediaAsset(
                media_type=MediaType.PHOTO,
                width=100,
                height=100,
                content_hash="   ",
                source=Path("x.jpg"),
            )

    def test_enums_serializan_a_string_plano(self) -> None:
        assert str(MediaType.PHOTO) == "photo"
        assert str(Orientation.VERTICAL) == "vertical"
