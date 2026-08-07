"""Pruebas de las métricas de exposición sobre imágenes de valores conocidos.

En simple: construyen imágenes donde el resultado correcto se sabe de antemano
—brillo exacto, mitad negra, colores puros— y comprueban que las funciones lo
devuelven. El caso más importante es el de los colores puros: distingue la
luminosidad percibida del promedio de canales, que es justo el error que rompería
la paridad con la auditoría manual del cliente.
"""

import os
import sys
from pathlib import Path

import numpy as np
import pytest

from media_optimizer.core import CorruptMediaError
from media_optimizer.testing import encode_jpeg, flat_image, not_an_image, textured_image
from media_optimizer.vision import (
    blown_highlights_ratio,
    crushed_shadows_ratio,
    decode_image,
    luminance,
    mean_brightness,
)


def _bgr(azul: int, verde: int, rojo: int, alto: int = 8, ancho: int = 8) -> np.ndarray:
    imagen = np.zeros((alto, ancho, 3), dtype=np.uint8)
    imagen[:, :] = (azul, verde, rojo)
    return imagen


class TestBrilloMedio:
    @pytest.mark.parametrize("brillo", [0, 60, 128, 200, 255])
    def test_una_imagen_uniforme_da_su_brillo_exacto(self, brillo: int) -> None:
        assert mean_brightness(flat_image(16, 16, brillo)) == pytest.approx(brillo, abs=0.01)

    @pytest.mark.parametrize("objetivo", [60, 100, 128, 180])
    def test_la_paridad_del_kpi_sobre_fixtures_texturados(self, objetivo: int) -> None:
        """El KPI del charter: reproducir la auditoría manual dentro de ±2%."""
        imagen = textured_image(64, 64, objetivo, seed=11)
        tolerancia = 255 * 0.02
        assert mean_brightness(imagen) == pytest.approx(objetivo, abs=tolerancia)

    def test_mide_luminosidad_percibida_no_promedio_de_canales(self) -> None:
        """Rojo y azul puros promedian igual (85), pero el ojo no los ve igual."""
        rojo = mean_brightness(_bgr(0, 0, 255))
        azul = mean_brightness(_bgr(255, 0, 0))
        verde = mean_brightness(_bgr(0, 255, 0))

        assert rojo == pytest.approx(255 * 0.299, abs=0.5)  # ~76
        assert azul == pytest.approx(255 * 0.114, abs=0.5)  # ~29
        assert verde == pytest.approx(255 * 0.587, abs=0.5)  # ~150
        assert rojo != pytest.approx(azul, abs=1)

    def test_el_orden_de_canales_es_el_de_opencv(self) -> None:
        """Si alguien invirtiera BGR/RGB, el rojo y el azul intercambiarían valores."""
        assert mean_brightness(_bgr(0, 0, 255)) > mean_brightness(_bgr(255, 0, 0))

    def test_una_imagen_en_grises_se_mide_tal_cual(self) -> None:
        gris = np.full((8, 8), 77, dtype=np.uint8)
        assert mean_brightness(gris) == pytest.approx(77.0)


class TestSombrasAplastadas:
    def test_una_mitad_negra_da_exactamente_la_mitad(self) -> None:
        imagen = np.zeros((10, 10), dtype=np.uint8)
        imagen[:5, :] = 200
        assert crushed_shadows_ratio(imagen, threshold=10) == pytest.approx(0.5)

    def test_una_imagen_negra_esta_toda_aplastada(self) -> None:
        assert crushed_shadows_ratio(flat_image(8, 8, 0), threshold=10) == 1.0

    def test_una_imagen_clara_no_tiene_nada_aplastado(self) -> None:
        assert crushed_shadows_ratio(flat_image(8, 8, 200), threshold=10) == 0.0

    def test_el_umbral_es_estricto(self) -> None:
        """Un píxel exactamente en el umbral no cuenta como aplastado.

        Se comprueba sobre una imagen en grises, donde la luminancia es el valor
        exacto del píxel; en color, la suma ponderada cae a fracciones de una
        milésima del entero y la frontera exacta deja de existir.
        """
        exacta = np.full((8, 8), 10, dtype=np.uint8)
        assert crushed_shadows_ratio(exacta, threshold=10) == 0.0


class TestLucesQuemadas:
    def test_una_franja_quemada_da_su_proporcion_exacta(self) -> None:
        imagen = np.full((10, 10), 128, dtype=np.uint8)
        imagen[:2, :] = 255
        assert blown_highlights_ratio(imagen, threshold=250) == pytest.approx(0.2)

    def test_una_imagen_blanca_esta_toda_quemada(self) -> None:
        assert blown_highlights_ratio(flat_image(8, 8, 255), threshold=250) == 1.0

    def test_una_imagen_negra_no_tiene_nada_quemado(self) -> None:
        assert blown_highlights_ratio(flat_image(8, 8, 0), threshold=250) == 0.0


class TestUmbralesComoParametros:
    @pytest.mark.parametrize("umbral", [-1, 256, 999.0])
    def test_un_umbral_imposible_es_contrato_roto(self, umbral: float) -> None:
        with pytest.raises(ValueError, match="umbral"):
            crushed_shadows_ratio(flat_image(4, 4, 0), threshold=umbral)
        with pytest.raises(ValueError, match="umbral"):
            blown_highlights_ratio(flat_image(4, 4, 0), threshold=umbral)


class TestDecodificacion:
    def test_decodifica_una_foto_leyendo_por_la_capa(self, tmp_path: Path) -> None:
        destino = tmp_path / "foto.jpg"
        destino.write_bytes(encode_jpeg(flat_image(32, 24, 120)))
        imagen = decode_image(destino)
        assert imagen.shape == (24, 32, 3)

    @pytest.mark.skipif(sys.platform != "win32", reason="rutas largas de Windows")
    def test_funciona_en_una_ruta_larga(self, tmp_path: Path) -> None:
        """cv2.imread moriría aquí; leer bytes por la capa y decodificar en memoria no."""
        profunda = tmp_path.joinpath(*(("v" * 40,) * 8))
        os.makedirs(f"\\\\?\\{profunda}", exist_ok=True)  # noqa: PTH103 - sembrar exige el prefijo
        destino = profunda / "foto.jpg"
        assert len(str(destino)) > 260
        with open(f"\\\\?\\{destino}", "wb") as archivo:  # noqa: PTH123 - sembrar exige el prefijo
            archivo.write(encode_jpeg(flat_image(16, 16, 90)))

        assert mean_brightness(decode_image(destino)) == pytest.approx(90, abs=2)

    def test_un_contenido_corrupto_degrada_con_su_causa(self, tmp_path: Path) -> None:
        destino = tmp_path / "rota.jpg"
        destino.write_bytes(not_an_image())
        with pytest.raises(CorruptMediaError, match=r"rota\.jpg"):
            decode_image(destino)


class TestDeterminismo:
    def test_la_misma_imagen_da_los_mismos_valores_exactos(self) -> None:
        imagen = textured_image(32, 32, 100, seed=5)
        assert mean_brightness(imagen) == mean_brightness(imagen)
        assert crushed_shadows_ratio(imagen, 30) == crushed_shadows_ratio(imagen, 30)

    def test_decodificar_dos_veces_da_la_misma_imagen(self, tmp_path: Path) -> None:
        destino = tmp_path / "foto.jpg"
        destino.write_bytes(encode_jpeg(textured_image(32, 32, 100, seed=5)))
        assert np.array_equal(decode_image(destino), decode_image(destino))


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_la_luminancia_conserva_las_dimensiones(self) -> None:
        assert luminance(_bgr(10, 20, 30, alto=6, ancho=9)).shape == (6, 9)

    def test_umbral_cero_no_aplasta_nada(self) -> None:
        """Nada puede estar estrictamente bajo cero."""
        assert crushed_shadows_ratio(flat_image(4, 4, 0), threshold=0) == 0.0

    def test_los_ratios_son_floats_nativos(self) -> None:
        """Un float de NumPy serializado a JSON daría otro texto que uno nativo."""
        valor = crushed_shadows_ratio(flat_image(4, 4, 0), threshold=10)
        assert type(valor) is float
