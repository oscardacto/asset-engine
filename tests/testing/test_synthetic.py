"""Pruebas del generador sintético: exposición, orientación, corrupción y determinismo.

En simple: el generador también se prueba — que el brillo pedido sea el brillo
real, que los archivos rotos estén rotos de verdad y que la misma semilla
produzca siempre los mismos bytes.
"""

from pathlib import Path

import cv2
import numpy as np
import pytest

from media_optimizer.testing import (
    encode_jpeg,
    flat_image,
    not_an_image,
    textured_image,
    truncated_jpeg,
    write_jpeg,
)


def _decodificar(data: bytes) -> np.ndarray | None:
    return cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)


class TestExposiciones:
    def test_imagen_plana_tiene_el_brillo_exacto(self) -> None:
        assert float(flat_image(100, 100, brightness=40).mean()) == 40.0

    def test_extremos_negro_y_blanco_exactos(self) -> None:
        assert float(flat_image(50, 50, brightness=0).mean()) == 0.0
        assert float(flat_image(50, 50, brightness=255).mean()) == 255.0

    def test_imagen_texturizada_respeta_el_brillo_objetivo(self) -> None:
        media = float(textured_image(256, 256, mean_brightness=120, seed=7).mean())
        assert abs(media - 120.0) <= 2.0


class TestOrientaciones:
    @pytest.mark.parametrize(
        ("width", "height"),
        [(1080, 1920), (1920, 1080), (1000, 1000)],
    )
    def test_las_dimensiones_pedidas_son_las_generadas(self, width: int, height: int) -> None:
        imagen = textured_image(width, height, mean_brightness=120, seed=1)
        assert imagen.shape == (height, width, 3)


class TestCorruptos:
    def test_un_jpeg_valido_decodifica_a_sus_dimensiones(self) -> None:
        decodificada = _decodificar(encode_jpeg(textured_image(64, 48, 120, seed=3)))
        assert decodificada is not None
        assert decodificada.shape == (48, 64, 3)

    def test_el_truncado_no_reconstruye_el_original(self) -> None:
        imagen = textured_image(64, 64, 120, seed=3)
        original = _decodificar(encode_jpeg(imagen))
        recortada = _decodificar(truncated_jpeg(imagen, keep_fraction=0.5))
        assert recortada is None or not np.array_equal(recortada, original)

    def test_los_magic_bytes_falsos_no_decodifican(self) -> None:
        assert _decodificar(not_an_image()) is None


class TestDeterminismo:
    def test_misma_semilla_produce_los_mismos_bytes(self) -> None:
        a = encode_jpeg(textured_image(64, 64, 120, seed=42))
        b = encode_jpeg(textured_image(64, 64, 120, seed=42))
        assert a == b

    def test_semillas_distintas_producen_bytes_distintos(self) -> None:
        a = encode_jpeg(textured_image(64, 64, 120, seed=1))
        b = encode_jpeg(textured_image(64, 64, 120, seed=2))
        assert a != b


class TestValidaciones:
    def test_brillo_fuera_de_rango_falla(self) -> None:
        with pytest.raises(ValueError, match="300"):
            flat_image(10, 10, brightness=300)

    def test_brillo_objetivo_fuera_de_rango_falla(self) -> None:
        with pytest.raises(ValueError, match="mean_brightness"):
            textured_image(10, 10, mean_brightness=300, seed=1)

    def test_calidad_fuera_de_rango_falla(self) -> None:
        with pytest.raises(ValueError, match="quality"):
            encode_jpeg(flat_image(10, 10, 100), quality=0)

    def test_fraccion_de_recorte_invalida_falla(self) -> None:
        with pytest.raises(ValueError, match="keep_fraction"):
            truncated_jpeg(flat_image(10, 10, 100), keep_fraction=1.0)

    def test_dimensiones_cero_fallan(self) -> None:
        with pytest.raises(ValueError, match="dimensiones"):
            flat_image(0, 10, brightness=100)

    def test_size_cero_falla(self) -> None:
        with pytest.raises(ValueError, match="size"):
            not_an_image(size=0)


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_write_jpeg_produce_un_archivo_decodificable(self, tmp_path: Path) -> None:
        ruta = write_jpeg(tmp_path / "fixture.jpg", flat_image(32, 32, 128))
        decodificada = _decodificar(ruta.read_bytes())
        assert decodificada is not None
        assert decodificada.shape == (32, 32, 3)

    def test_not_an_image_respeta_el_tamano_pedido(self) -> None:
        assert len(not_an_image(size=100)) == 100

    def test_un_recorte_minimo_tampoco_reconstruye(self) -> None:
        imagen = textured_image(64, 64, 120, seed=3)
        original = _decodificar(encode_jpeg(imagen))
        minima = _decodificar(truncated_jpeg(imagen, keep_fraction=0.05))
        assert minima is None or not np.array_equal(minima, original)
