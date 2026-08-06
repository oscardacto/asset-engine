"""Pruebas de la orientación: cuál manda cuando el archivo y la pantalla difieren.

En simple: comprueban que una foto guardada en horizontal pero marcada como
girada se reporta como vertical —que es como se ve—, que sin esa marca no pasa
nada raro, y que una foto cuadrada sigue cuadrada aunque el metadato diga que
gira.
"""

import pytest

from media_optimizer.core import Orientation
from media_optimizer.ingest import AssetOrientation, ExifOrientation, ImageSize, detect_orientation

_HORIZONTAL = ImageSize(width=1920, height=1080)
_VERTICAL = ImageSize(width=1080, height=1920)
_CUADRADA = ImageSize(width=1000, height=1000)

_NO_GIRAN = [
    ExifOrientation.NORMAL,
    ExifOrientation.MIRROR_HORIZONTAL,
    ExifOrientation.ROTATE_180,
    ExifOrientation.MIRROR_VERTICAL,
]
_GIRAN = [
    ExifOrientation.MIRROR_HORIZONTAL_ROTATE_270,
    ExifOrientation.ROTATE_90,
    ExifOrientation.MIRROR_HORIZONTAL_ROTATE_90,
    ExifOrientation.ROTATE_270,
]


class TestSinMetadato:
    def test_sin_exif_manda_lo_que_miden_los_pixeles(self) -> None:
        resultado = detect_orientation(_VERTICAL)
        assert resultado.raw is Orientation.VERTICAL
        assert resultado.effective is Orientation.VERTICAL
        assert not resultado.rotated

    @pytest.mark.parametrize(
        ("medidas", "esperada"),
        [
            (_VERTICAL, Orientation.VERTICAL),
            (_HORIZONTAL, Orientation.HORIZONTAL),
            (_CUADRADA, Orientation.SQUARE),
        ],
    )
    def test_clasifica_los_tres_casos(self, medidas: ImageSize, esperada: Orientation) -> None:
        assert detect_orientation(medidas).effective is esperada


class TestMetadatoQueNoGira:
    @pytest.mark.parametrize("valor", _NO_GIRAN)
    def test_la_orientacion_no_cambia(self, valor: ExifOrientation) -> None:
        resultado = detect_orientation(_HORIZONTAL, valor)
        assert resultado.effective is Orientation.HORIZONTAL
        assert not resultado.rotated


class TestMetadatoQueGira:
    @pytest.mark.parametrize("valor", _GIRAN)
    def test_una_horizontal_marcada_como_girada_se_ve_vertical(
        self, valor: ExifOrientation
    ) -> None:
        resultado = detect_orientation(_HORIZONTAL, valor)
        assert resultado.raw is Orientation.HORIZONTAL
        assert resultado.effective is Orientation.VERTICAL
        assert resultado.rotated

    @pytest.mark.parametrize("valor", _GIRAN)
    def test_y_al_reves_tambien(self, valor: ExifOrientation) -> None:
        resultado = detect_orientation(_VERTICAL, valor)
        assert resultado.effective is Orientation.HORIZONTAL
        assert resultado.rotated


class TestCuadradas:
    @pytest.mark.parametrize("valor", _GIRAN)
    def test_una_cuadrada_girada_sigue_siendo_cuadrada(self, valor: ExifOrientation) -> None:
        resultado = detect_orientation(_CUADRADA, valor)
        assert resultado.effective is Orientation.SQUARE
        assert not resultado.rotated


class TestDeterminismo:
    def test_dos_llamadas_iguales_dan_lo_mismo(self) -> None:
        primera = detect_orientation(_HORIZONTAL, ExifOrientation.ROTATE_90)
        segunda = detect_orientation(_HORIZONTAL, ExifOrientation.ROTATE_90)
        assert primera == segunda


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_el_resultado_es_inmutable(self) -> None:
        with pytest.raises(AttributeError):
            detect_orientation(_VERTICAL).effective = Orientation.HORIZONTAL  # type: ignore[misc]

    def test_una_imagen_de_un_pixel_es_cuadrada(self) -> None:
        assert detect_orientation(ImageSize(1, 1)).effective is Orientation.SQUARE

    def test_conserva_ambas_lecturas_para_poder_explicar_la_diferencia(self) -> None:
        resultado = detect_orientation(_HORIZONTAL, ExifOrientation.ROTATE_90)
        assert isinstance(resultado, AssetOrientation)
        assert (resultado.raw, resultado.effective) == (
            Orientation.HORIZONTAL,
            Orientation.VERTICAL,
        )
