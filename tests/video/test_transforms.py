"""Pruebas del encuadre vertical: la aritmética exacta del recorte 9:16.

En simple: comprueban que un clip de cualquier forma —4K apaisado, 1080p, 4:3, ya
vertical— acaba midiendo exactamente 1080x1920 sin deformarse, que lo que se
recorta sale del centro, y que las medidas intermedias son pares, porque los
codificadores de video rechazan un cuadro de ancho impar.
"""

import pytest

from media_optimizer.video import (
    ALTO_VERTICAL,
    ANCHO_VERTICAL,
    frame_to_vertical,
    vertical_filter_chain,
)


class TestCoordenadasExactas:
    @pytest.mark.parametrize(
        ("ancho", "alto", "escala_esperada", "recorte_esperado"),
        [
            (3840, 2160, (3414, 1920), (1167, 0)),  # 4K 16:9
            (1920, 1080, (3414, 1920), (1167, 0)),  # 1080p 16:9
            (1600, 1200, (2560, 1920), (740, 0)),  # 4:3
            (1080, 1920, (1080, 1920), (0, 0)),  # ya es 9:16
            (1080, 2400, (1080, 2400), (0, 240)),  # más alto que 9:16
        ],
    )
    def test_el_calculo_es_exacto_para_cada_resolucion(
        self,
        ancho: int,
        alto: int,
        escala_esperada: tuple[int, int],
        recorte_esperado: tuple[int, int],
    ) -> None:
        encuadre = frame_to_vertical(ancho, alto)

        assert (encuadre.scaled_width, encuadre.scaled_height) == escala_esperada
        assert (encuadre.crop.x, encuadre.crop.y) == recorte_esperado

    @pytest.mark.parametrize(
        ("ancho", "alto"), [(3840, 2160), (1920, 1080), (1600, 1200), (1080, 1920), (640, 480)]
    )
    def test_la_salida_siempre_mide_exactamente_el_destino(self, ancho: int, alto: int) -> None:
        recorte = frame_to_vertical(ancho, alto).crop
        assert (recorte.width, recorte.height) == (ANCHO_VERTICAL, ALTO_VERTICAL)

    @pytest.mark.parametrize(
        ("ancho", "alto"), [(3840, 2160), (1920, 1080), (1600, 1200), (1333, 1000), (999, 777)]
    )
    def test_nunca_deforma_la_imagen(self, ancho: int, alto: int) -> None:
        """La proporción tras escalar es la original, con el error de un píxel par."""
        encuadre = frame_to_vertical(ancho, alto)
        original = ancho / alto
        escalada = encuadre.scaled_width / encuadre.scaled_height
        assert escalada == pytest.approx(original, rel=0.005)

    @pytest.mark.parametrize(("ancho", "alto"), [(1333, 1000), (999, 777), (1921, 1081)])
    def test_las_medidas_intermedias_son_pares(self, ancho: int, alto: int) -> None:
        """Un ancho impar hace que el codificador rechace el cuadro."""
        encuadre = frame_to_vertical(ancho, alto)
        assert encuadre.scaled_width % 2 == 0
        assert encuadre.scaled_height % 2 == 0

    def test_el_recorte_sale_del_centro(self) -> None:
        encuadre = frame_to_vertical(3840, 2160)
        sobrante = encuadre.scaled_width - encuadre.crop.width
        assert encuadre.crop.x == sobrante // 2

    def test_un_clip_apaisado_recorta_ancho_no_alto(self) -> None:
        assert frame_to_vertical(1920, 1080).crops_width is True

    def test_un_clip_mas_alto_recorta_alto_no_ancho(self) -> None:
        assert frame_to_vertical(1080, 2400).crops_width is False


class TestMedidasImposibles:
    @pytest.mark.parametrize(("ancho", "alto"), [(0, 1080), (1920, 0), (-1, 100), (100, -1)])
    def test_una_medida_no_positiva_falla(self, ancho: int, alto: int) -> None:
        with pytest.raises(ValueError, match="px"):
            frame_to_vertical(ancho, alto)

    def test_un_destino_imposible_tambien_falla(self) -> None:
        with pytest.raises(ValueError, match="target_width"):
            frame_to_vertical(1920, 1080, target_width=0)


class TestCadenaDeFiltros:
    def test_reinicia_los_tiempos_antes_de_cualquier_filtro(self) -> None:
        """Sin el reinicio, al encadenar clips el tiempo salta hacia atrás."""
        cadena = vertical_filter_chain(frame_to_vertical(1920, 1080))
        assert cadena.startswith("setpts=PTS-STARTPTS")

    def test_escala_antes_de_recortar(self) -> None:
        cadena = vertical_filter_chain(frame_to_vertical(1920, 1080))
        assert cadena.index("scale=") < cadena.index("crop=")

    def test_lleva_las_coordenadas_calculadas(self) -> None:
        encuadre = frame_to_vertical(3840, 2160)
        cadena = vertical_filter_chain(encuadre)
        assert "scale=3414:1920" in cadena
        assert "crop=1080:1920:1167:0" in cadena

    def test_fija_los_cuadros_por_segundo_y_el_formato_de_color(self) -> None:
        cadena = vertical_filter_chain(frame_to_vertical(1920, 1080), fps=30)
        assert "fps=30" in cadena
        assert "format=yuv420p" in cadena

    def test_es_determinista(self) -> None:
        encuadre = frame_to_vertical(3840, 2160)
        assert vertical_filter_chain(encuadre) == vertical_filter_chain(encuadre)
