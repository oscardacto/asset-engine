"""Pruebas de la calificación de una escena: sus límites y la nota que la resume.

En simple: verifican que una nota imposible —fuera del rango, sin cuadros
mirados— falla al construirse, y que la nota general es la media de lo que sí se
midió, de modo que añadir una métrica nueva no cambie el contrato.
"""

import pytest

from media_optimizer.core import SceneScore


def _nota(**cambios: object) -> SceneScore:
    base: dict[str, object] = {
        "scene_index": 0,
        "exposure": 0.8,
        "stability": 0.6,
        "sampled_frames": 5,
    }
    return SceneScore(**{**base, **cambios})  # type: ignore[arg-type]


class TestNotaGeneral:
    def test_promedia_los_componentes_medidos(self) -> None:
        assert _nota().overall == pytest.approx(0.7)

    def test_los_componentes_salen_en_orden_estable(self) -> None:
        assert _nota().components == (0.8, 0.6)

    def test_una_escena_perfecta_saca_uno(self) -> None:
        assert _nota(exposure=1.0, stability=1.0).overall == pytest.approx(1.0)


class TestValoresImposibles:
    def test_un_indice_negativo_falla(self) -> None:
        with pytest.raises(ValueError, match="scene_index"):
            _nota(scene_index=-1)

    def test_no_mirar_ningun_cuadro_falla(self) -> None:
        with pytest.raises(ValueError, match="al menos un cuadro"):
            _nota(sampled_frames=0)

    @pytest.mark.parametrize("componente", ["exposure", "stability"])
    @pytest.mark.parametrize("valor", [-0.1, 1.1])
    def test_un_componente_fuera_de_rango_falla(self, componente: str, valor: float) -> None:
        with pytest.raises(ValueError, match=componente):
            _nota(**{componente: valor})


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_la_nota_no_se_puede_alterar(self) -> None:
        with pytest.raises(AttributeError):
            _nota().exposure = 1.0  # type: ignore[misc]

    def test_dos_notas_iguales_son_iguales(self) -> None:
        assert _nota() == _nota()

    def test_los_extremos_del_rango_son_validos(self) -> None:
        assert _nota(exposure=0.0, stability=1.0).overall == pytest.approx(0.5)
