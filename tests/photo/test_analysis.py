"""Pruebas del score de exposición y el veredicto, con umbrales de prueba explícitos.

En simple: verifican que la calificación es 1 en el objetivo y baja al alejarse en
cualquier dirección, que las zonas hundidas y quemadas restan según su peso, y que
el veredicto explica siempre sus causas — incluida la regla de que lo que pasó por
WhatsApp nunca es publicable.
"""

import pytest

from media_optimizer.core import Verdict
from media_optimizer.photo import ExposureThresholds, exposure_score, verdict_for

_UMBRALES = ExposureThresholds(
    brightness_target=128.0,
    crushed_shadows_weight=1.0,
    blown_highlights_weight=2.0,
    publishable_min_score=0.8,
    support_min_score=0.5,
)


def _score(brillo: float = 128.0, negro: float = 0.0, quemado: float = 0.0) -> float:
    return exposure_score(brillo, negro, quemado, _UMBRALES)


class TestScore:
    def test_en_el_objetivo_exacto_y_limpia_vale_uno(self) -> None:
        assert _score() == 1.0

    def test_decrece_al_alejarse_del_objetivo_en_ambas_direcciones(self) -> None:
        assert _score(brillo=128) > _score(brillo=100) > _score(brillo=60)
        assert _score(brillo=128) > _score(brillo=160) > _score(brillo=220)

    def test_mas_brillante_no_es_mejor(self) -> None:
        """El error clásico: premiar brillo absoluto en vez de castigar distancia."""
        assert _score(brillo=200) < _score(brillo=128)

    def test_el_negro_y_el_quemado_restan_segun_su_peso(self) -> None:
        assert _score(negro=0.1) == pytest.approx(0.9)
        assert _score(quemado=0.1) == pytest.approx(0.8)  # pesa el doble

    def test_queda_acotado_a_cero(self) -> None:
        assert _score(brillo=0, negro=1.0, quemado=1.0) == 0.0

    def test_es_determinista(self) -> None:
        assert _score(90, 0.2, 0.05) == _score(90, 0.2, 0.05)


class TestVeredicto:
    def test_score_alto_es_publicable_sin_causas(self) -> None:
        assert verdict_for(0.9, (), _UMBRALES) == (Verdict.PUBLISHABLE, ())

    def test_score_medio_es_apoyo_y_dice_por_que(self) -> None:
        veredicto, causas = verdict_for(0.6, (), _UMBRALES)
        assert veredicto is Verdict.SUPPORT
        assert "0.60" in causas[0] and "0.8" in causas[0]

    def test_score_bajo_se_descarta_y_dice_por_que(self) -> None:
        veredicto, causas = verdict_for(0.3, (), _UMBRALES)
        assert veredicto is Verdict.DISCARD
        assert "0.30" in causas[0]

    def test_whatsapp_nunca_es_publicable(self) -> None:
        veredicto, causas = verdict_for(0.95, ("whatsapp_compressed",), _UMBRALES)
        assert veredicto is Verdict.SUPPORT
        assert any("WhatsApp" in causa for causa in causas)

    def test_whatsapp_no_salva_a_una_descartada(self) -> None:
        veredicto, _ = verdict_for(0.2, ("whatsapp_compressed",), _UMBRALES)
        assert veredicto is Verdict.DISCARD

    def test_en_el_corte_exacto_es_publicable(self) -> None:
        assert verdict_for(0.8, (), _UMBRALES)[0] is Verdict.PUBLISHABLE


class TestUmbralesInvalidos:
    def test_objetivo_fuera_de_rango(self) -> None:
        with pytest.raises(ValueError, match="brightness_target"):
            ExposureThresholds(300, 1, 1, 0.8, 0.5)

    def test_peso_negativo(self) -> None:
        with pytest.raises(ValueError, match="weight"):
            ExposureThresholds(128, -1, 1, 0.8, 0.5)

    def test_cortes_invertidos(self) -> None:
        with pytest.raises(ValueError, match="cortes"):
            ExposureThresholds(128, 1, 1, 0.5, 0.8)
