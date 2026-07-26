"""Pruebas de ``Transform`` y ``TransformHistory``: declaración, inmutabilidad y orden.

En simple: verifican que cada retoque se declara bien con sus parámetros, que
nada se puede modificar después, y que el historial crece sin alterar sus
versiones anteriores ni el orden de aplicación.
"""

import math
from dataclasses import FrozenInstanceError

import pytest

from media_optimizer.core import Transform, TransformHistory


def _clahe() -> Transform:
    return Transform("clahe", {"clip_limit": 2.0, "tiles_x": 8, "tiles_y": 8})


class TestDeclaracion:
    def test_expone_nombre_y_parametros(self) -> None:
        retoque = _clahe()
        assert retoque.name == "clahe"
        assert retoque.params["clip_limit"] == 2.0
        assert retoque.params["tiles_x"] == 8

    def test_sin_parametros_es_valido(self) -> None:
        assert len(Transform("auto_rotate", {}).params) == 0


class TestInmutabilidad:
    def test_asignar_un_campo_lanza_frozen_error(self) -> None:
        with pytest.raises(FrozenInstanceError):
            _clahe().name = "otro"  # type: ignore[misc]

    def test_los_parametros_son_de_solo_lectura(self) -> None:
        retoque = _clahe()
        with pytest.raises(TypeError):
            retoque.params["clip_limit"] = 9.0  # type: ignore[index]

    def test_mutar_el_dict_original_no_afecta_al_transform(self) -> None:
        original: dict[str, float] = {"angle": 1.5}
        retoque = Transform("rotate", original)
        original["intruso"] = 0.0
        assert "intruso" not in retoque.params


class TestInvariantesFailFast:
    def test_nombre_vacio_falla(self) -> None:
        with pytest.raises(ValueError, match="nombre"):
            Transform("   ", {})

    def test_parametro_sin_nombre_falla(self) -> None:
        with pytest.raises(ValueError, match="sin nombre"):
            Transform("rotate", {" ": 1.0})

    def test_parametro_nan_falla_nombrando_parametro(self) -> None:
        with pytest.raises(ValueError, match="clip_limit"):
            Transform("clahe", {"clip_limit": math.nan})


class TestHistorial:
    def test_nace_vacio_por_defecto(self) -> None:
        assert len(TransformHistory()) == 0

    def test_append_devuelve_historial_nuevo_sin_mutar_el_anterior(self) -> None:
        vacio = TransformHistory()
        con_uno = vacio.append(_clahe())
        assert len(vacio) == 0
        assert len(con_uno) == 1

    def test_los_pasos_conservan_el_orden_de_aplicacion(self) -> None:
        historial = (
            TransformHistory().append(Transform("b_paso", {})).append(Transform("a_paso", {}))
        )
        assert [paso.name for paso in historial] == ["b_paso", "a_paso"]


class TestIgualdadPorValor:
    def test_mismo_nombre_y_parametros_son_iguales(self) -> None:
        assert _clahe() == _clahe()

    def test_historiales_con_distinto_orden_no_son_iguales(self) -> None:
        a, b = Transform("a_paso", {}), Transform("b_paso", {})
        assert TransformHistory((a, b)) != TransformHistory((b, a))


class TestDeterminismo:
    def test_orden_de_insercion_de_parametros_es_irrelevante(self) -> None:
        x = Transform("wb", {"warmth": 0.3, "target": 128.0})
        y = Transform("wb", {"target": 128.0, "warmth": 0.3})
        assert x == y
        assert list(x.params) == list(y.params) == ["target", "warmth"]


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_bool_e_int_no_pasan_por_el_filtro_de_floats(self) -> None:
        retoque = Transform("flip", {"horizontal": True, "veces": 2})
        assert retoque.params["horizontal"] is True

    def test_el_mismo_retoque_puede_aplicarse_dos_veces(self) -> None:
        historial = TransformHistory().append(_clahe()).append(_clahe())
        assert len(historial) == 2

    def test_transforms_iguales_comparten_hash(self) -> None:
        assert hash(_clahe()) == hash(_clahe())
