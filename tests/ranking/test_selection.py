"""Pruebas de la selección: portada, galería y formatos, deterministas hasta el desempate.

En simple: verifican que la portada solo admite publicables que llenan su formato,
que la galería arranca con la mejor foto y alterna orientaciones, que una foto
corta de píxeles queda fuera del formato que no llena, y que los descartes no
entran nunca en nada.
"""

import pytest

from media_optimizer.core import Verdict
from media_optimizer.ranking import (
    RankedAsset,
    cover_candidates,
    gallery_order,
    global_score,
    rank,
    select_by_format,
)


def _foto(  # noqa: PLR0913 - fabrica de fixtures con defaults, no API
    nombre: str,
    score: float,
    veredicto: Verdict = Verdict.PUBLISHABLE,
    *,
    flags: tuple[str, ...] = (),
    ancho: int = 4080,
    alto: int = 3060,
) -> RankedAsset:
    return RankedAsset(
        content_hash=nombre,
        source=nombre,
        score=score,
        verdict=veredicto,
        flags=flags,
        width=ancho,
        height=alto,
    )


_MEJOR = _foto("mejor.jpg", 0.95)
_VERTICAL = _foto("vertical.jpg", 0.90, ancho=3060, alto=4080)
_APOYO = _foto("apoyo.jpg", 0.85, Verdict.SUPPORT)
_CORTA = _foto("corta.jpg", 0.80, flags=("below_native_story",))
_DESCARTE = _foto("descarte.jpg", 0.99, Verdict.DISCARD)
_LOTE = (_DESCARTE, _CORTA, _APOYO, _VERTICAL, _MEJOR)


class TestScoreGlobal:
    def test_combina_ponderado_y_normaliza(self) -> None:
        valor = global_score(
            {"exposure_score": 0.8, "sharpness": 0.6}, {"exposure_score": 3, "sharpness": 1}
        )
        assert valor == pytest.approx(0.75)

    def test_una_metrica_ausente_cuenta_cero(self) -> None:
        assert global_score(
            {"exposure_score": 0.8}, {"exposure_score": 1, "sharpness": 1}
        ) == pytest.approx(0.4)

    def test_pesos_vacios_dan_cero(self) -> None:
        assert global_score({"x": 1.0}, {}) == 0.0


class TestRank:
    def test_ordena_por_score_con_desempate_por_nombre(self) -> None:
        a, b = _foto("b.jpg", 0.5), _foto("a.jpg", 0.5)
        assert rank((a, b)) == (b, a)


class TestPortada:
    def test_solo_publicables_que_llenan_el_formato(self) -> None:
        corta_cover = _foto("corta_cover.jpg", 0.99, flags=("below_native_cover",))
        candidatas = cover_candidates((*_LOTE, corta_cover), top=3)
        assert [c.source for c in candidatas] == ["mejor.jpg", "vertical.jpg", "corta.jpg"]

    def test_respeta_el_top(self) -> None:
        assert len(cover_candidates(_LOTE, top=1)) == 1


class TestGaleria:
    def test_arranca_con_el_gancho_y_alterna_orientacion(self) -> None:
        orden = gallery_order(_LOTE)
        assert orden[0].source == "mejor.jpg"  # el gancho
        assert orden[1].source == "vertical.jpg"  # alterna a vertical
        assert orden[1].is_vertical != orden[0].is_vertical

    def test_los_descartes_no_entran(self) -> None:
        assert all(a.verdict is not Verdict.DISCARD for a in gallery_order(_LOTE))

    def test_es_deterministaa_reproducible(self) -> None:
        assert gallery_order(_LOTE) == gallery_order(_LOTE)

    def test_lote_vacio_da_galeria_vacia(self) -> None:
        assert gallery_order(()) == ()


class TestPorFormato:
    def test_una_corta_queda_fuera_solo_de_su_formato(self) -> None:
        seleccion = select_by_format(_LOTE, ("story", "feed"))
        assert "corta.jpg" not in [a.source for a in seleccion["story"]]
        assert "corta.jpg" in [a.source for a in seleccion["feed"]]

    def test_los_descartes_no_entran_en_ningun_formato(self) -> None:
        seleccion = select_by_format(_LOTE, ("story", "feed", "cover"))
        for fotos in seleccion.values():
            assert "descarte.jpg" not in [a.source for a in fotos]

    def test_el_apoyo_entra_detras_por_su_score(self) -> None:
        seleccion = select_by_format(_LOTE, ("feed",))
        assert "apoyo.jpg" in [a.source for a in seleccion["feed"]]
