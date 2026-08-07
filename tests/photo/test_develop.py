"""Pruebas del motor de revelado y su primera tanda de retoques.

En simple: verifican que el plan se valida entero antes de tocar una foto, que
cada retoque hace lo que promete —el contraste local sube, la calidez entra más
en las luces que en las sombras, la saturación respeta el tope del negocio—, que
nada muta la imagen de entrada, y que registrar un retoque nuevo no exige tocar
el motor: ese es el contrato que las transformaciones futuras heredan.
"""

import cv2
import numpy as np
import pytest

from media_optimizer.core import InvalidInputError, Transform
from media_optimizer.photo.develop import TRANSFORMS, TransformSpec, apply_pipeline, build_plan
from media_optimizer.testing import textured_image
from media_optimizer.vision import luminance, mean_brightness

_FOTO = textured_image(48, 48, 110, seed=9, spread=40)
_CLAHE = Transform(name="clahe", params={"clip_limit": 2.0, "tile_size": 8})
_WB = Transform(name="white_balance", params={"warmth": 0.1})
_SAT = Transform(name="saturation", params={"factor": 1.06, "max_factor": 1.06})


class TestContrato:
    def test_registrar_un_retoque_nuevo_no_toca_el_motor(self) -> None:
        """El contrato: agregar = registrar. El pipeline lo ejecuta sin cambios."""
        TRANSFORMS["invertir"] = TransformSpec(
            apply=lambda imagen, _params: 255 - imagen, validate=lambda _params: None
        )
        try:
            salida, historial = apply_pipeline(_FOTO, (Transform(name="invertir", params={}),))
            assert np.array_equal(salida, 255 - _FOTO)
            assert [paso.name for paso in historial] == ["invertir"]
        finally:
            del TRANSFORMS["invertir"]

    def test_un_plan_con_retoque_desconocido_falla_antes_de_procesar(self) -> None:
        with pytest.raises(InvalidInputError, match="no existe"):
            build_plan((Transform(name="vintage", params={}),))

    @pytest.mark.parametrize(
        "paso",
        [
            Transform(name="clahe", params={"clip_limit": 99, "tile_size": 8}),
            Transform(name="white_balance", params={"warmth": 0.9}),
            Transform(name="saturation", params={"factor": 1.5, "max_factor": 1.06}),
            Transform(name="clahe", params={"tile_size": 8}),
        ],
    )
    def test_parametros_invalidos_fallan_al_armar_el_plan(self, paso: Transform) -> None:
        with pytest.raises(InvalidInputError, match=paso.name):
            build_plan((paso,))

    def test_la_entrada_no_se_muta(self) -> None:
        copia = _FOTO.copy()
        apply_pipeline(_FOTO, (_CLAHE, _WB, _SAT))
        assert np.array_equal(_FOTO, copia)

    def test_el_historial_es_la_secuencia_exacta(self) -> None:
        _, historial = apply_pipeline(_FOTO, (_CLAHE, _WB, _SAT))
        assert [paso.name for paso in historial] == ["clahe", "white_balance", "saturation"]

    def test_es_determinista_byte_a_byte(self) -> None:
        primera, _ = apply_pipeline(_FOTO, (_CLAHE, _WB, _SAT))
        segunda, _ = apply_pipeline(_FOTO, (_CLAHE, _WB, _SAT))
        assert np.array_equal(primera, segunda)

    def test_la_salida_conserva_tipo_y_forma(self) -> None:
        salida, _ = apply_pipeline(_FOTO, (_CLAHE, _WB, _SAT))
        assert salida.dtype == np.uint8
        assert salida.shape == _FOTO.shape


class TestClahe:
    def test_sube_el_contraste_local(self) -> None:
        plana = textured_image(48, 48, 110, seed=9, spread=8)
        salida, _ = apply_pipeline(plana, (_CLAHE,))
        assert float(luminance(salida).std()) > float(luminance(plana).std())


class TestWhiteBalance:
    def test_la_calidez_entra_mas_en_las_luces_que_en_las_sombras(self) -> None:
        mitad = np.zeros((20, 20, 3), dtype=np.uint8)
        mitad[:10] = 220  # luces arriba
        mitad[10:] = 40  # sombras abajo
        salida, _ = apply_pipeline(mitad, (_WB,))
        ganancia_luces = int(salida[:10, :, 2].mean()) - 220
        ganancia_sombras = int(salida[10:, :, 2].mean()) - 40
        assert ganancia_luces > ganancia_sombras >= 0

    def test_calidez_negativa_enfria(self) -> None:
        frio = Transform(name="white_balance", params={"warmth": -0.1})
        salida, _ = apply_pipeline(np.full((8, 8, 3), 200, dtype=np.uint8), (frio,))
        assert float(salida[:, :, 0].mean()) > float(salida[:, :, 2].mean())


class TestSaturation:
    def test_satura_dentro_del_tope(self) -> None:
        salida, _ = apply_pipeline(_FOTO, (_SAT,))
        antes = cv2.cvtColor(_FOTO, cv2.COLOR_BGR2HSV)[:, :, 1].mean()
        despues = cv2.cvtColor(salida, cv2.COLOR_BGR2HSV)[:, :, 1].mean()
        assert despues >= antes

    def test_factor_uno_deja_el_color_casi_igual(self) -> None:
        neutro = Transform(name="saturation", params={"factor": 1.0, "max_factor": 1.06})
        salida, _ = apply_pipeline(_FOTO, (neutro,))
        assert abs(mean_brightness(salida) - mean_brightness(_FOTO)) < 3


class TestCapaSecundaria:
    def test_un_plan_vacio_devuelve_la_imagen_intacta(self) -> None:
        salida, historial = apply_pipeline(_FOTO, ())
        assert np.array_equal(salida, _FOTO)
        assert len(historial) == 0


class TestShadows:
    def test_sube_las_sombras_mas_que_las_luces(self) -> None:
        mitad = np.zeros((20, 20, 3), dtype=np.uint8)
        mitad[:10] = 30
        mitad[10:] = 220
        paso = Transform(name="shadows", params={"amount": 0.5})
        salida, _ = apply_pipeline(mitad, (paso,))
        subida_sombras = float(salida[:10].mean()) - 30
        subida_luces = float(salida[10:].mean()) - 220
        assert subida_sombras > 5
        assert subida_sombras > subida_luces >= 0

    def test_amount_cero_no_cambia_nada(self) -> None:
        paso = Transform(name="shadows", params={"amount": 0.0})
        salida, _ = apply_pipeline(_FOTO, (paso,))
        assert np.array_equal(salida, _FOTO)


class TestExposure:
    def test_acerca_el_brillo_al_objetivo(self) -> None:
        oscura = textured_image(48, 48, 60, seed=3)
        paso = Transform(name="exposure", params={"target_brightness": 128})
        salida, _ = apply_pipeline(oscura, (paso,))
        assert abs(mean_brightness(salida) - 128) < abs(mean_brightness(oscura) - 128)

    def test_una_foto_ya_en_objetivo_queda_casi_igual(self) -> None:
        justa = textured_image(48, 48, 128, seed=4)
        paso = Transform(name="exposure", params={"target_brightness": 128})
        salida, _ = apply_pipeline(justa, (paso,))
        assert abs(mean_brightness(salida) - mean_brightness(justa)) < 3

    def test_las_altas_luces_no_se_queman_al_subir(self) -> None:
        mitad = np.zeros((20, 20, 3), dtype=np.uint8)
        mitad[:10] = 40
        mitad[10:] = 250
        paso = Transform(name="exposure", params={"target_brightness": 150})
        salida, _ = apply_pipeline(mitad, (paso,))
        assert float(salida[10:].mean()) <= 255
        assert float(salida[10:].mean()) - 250 < 5


class TestCrop:
    def test_produce_el_aspecto_exacto_centrado(self) -> None:
        imagen = textured_image(100, 60, 100, seed=5)
        paso = Transform(name="crop", params={"aspect_width": 4, "aspect_height": 5})
        salida, _ = apply_pipeline(imagen, (paso,))
        alto, ancho = salida.shape[:2]
        assert ancho / alto == pytest.approx(0.8, abs=0.02)
        assert alto == 60  # solo se recorta el eje sobrante

    def test_no_escala_solo_recorta(self) -> None:
        imagen = textured_image(80, 100, 100, seed=6)  # ya es 4:5
        paso = Transform(name="crop", params={"aspect_width": 4, "aspect_height": 5})
        salida, _ = apply_pipeline(imagen, (paso,))
        assert np.array_equal(salida, imagen)


class TestResize:
    def test_respeta_las_medidas_exactas(self) -> None:
        paso = Transform(name="resize", params={"width": 24, "height": 30})
        salida, _ = apply_pipeline(_FOTO, (paso,))
        assert salida.shape == (30, 24, 3)
