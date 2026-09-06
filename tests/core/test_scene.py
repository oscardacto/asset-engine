"""Pruebas del contrato de escena: un tramo de video entre dos cortes.

En simple: verifican que una escena imposible —que termina antes de empezar, o
con posición negativa— falla al construirse en vez de propagarse hasta un reel
mal cortado, y que la duración se calcula sola.
"""

import pytest

from media_optimizer.core import Scene


class TestConstruccion:
    def test_guarda_su_posicion_y_sus_limites(self) -> None:
        escena = Scene(index=2, start_seconds=4.5, end_seconds=9.25)
        assert escena.index == 2
        assert escena.start_seconds == pytest.approx(4.5)
        assert escena.end_seconds == pytest.approx(9.25)

    def test_calcula_su_duracion(self) -> None:
        assert Scene(index=0, start_seconds=1.0, end_seconds=4.5).duration_seconds == pytest.approx(
            3.5
        )

    def test_una_escena_que_empieza_en_cero_es_valida(self) -> None:
        assert Scene(index=0, start_seconds=0.0, end_seconds=1.0).duration_seconds == pytest.approx(
            1.0
        )


class TestValoresImposibles:
    def test_un_indice_negativo_falla(self) -> None:
        with pytest.raises(ValueError, match="index"):
            Scene(index=-1, start_seconds=0.0, end_seconds=1.0)

    def test_un_inicio_negativo_falla(self) -> None:
        with pytest.raises(ValueError, match="start_seconds"):
            Scene(index=0, start_seconds=-0.5, end_seconds=1.0)

    @pytest.mark.parametrize("fin", [1.0, 0.5])
    def test_terminar_antes_o_a_la_vez_que_empezar_falla(self, fin: float) -> None:
        with pytest.raises(ValueError, match="termina antes de empezar"):
            Scene(index=3, start_seconds=1.0, end_seconds=fin)


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_la_escena_no_se_puede_alterar(self) -> None:
        with pytest.raises(AttributeError):
            Scene(index=0, start_seconds=0.0, end_seconds=1.0).index = 1  # type: ignore[misc]

    def test_dos_escenas_iguales_son_iguales(self) -> None:
        assert Scene(index=1, start_seconds=0.0, end_seconds=2.0) == Scene(
            index=1, start_seconds=0.0, end_seconds=2.0
        )

    def test_una_escena_muy_corta_sigue_siendo_valida(self) -> None:
        """Un corte rápido es material legítimo; descartarlo es de otra etapa."""
        assert Scene(index=0, start_seconds=1.0, end_seconds=1.04).duration_seconds > 0
