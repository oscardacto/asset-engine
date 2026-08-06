"""Pruebas de la ficha de etapa: qué se puede comparar entre corridas y qué no.

En simple: verifican que la ficha guarda los cuatro datos obligatorios, que los
valores imposibles fallan al construirla, y sobre todo que la parte comparable de
dos corridas de la misma etapa sale idéntica aunque los tiempos difieran — que es
lo que impide que una prueba de reproducibilidad falle por el reloj.
"""

import math

import pytest

from media_optimizer.core import (
    ReproducibleStageSummary,
    StageReport,
    Transform,
    TransformHistory,
)

_RECORTE = Transform(name="recorte", params={"alto": 1350, "ancho": 1080})
_HISTORIAL = TransformHistory().append(_RECORTE)


def _reporte(**cambios: object) -> StageReport:
    base: dict[str, object] = {
        "stage": "analisis",
        "duration_seconds": 0.031,
        "peak_memory_bytes": 4_194_304,
    }
    return StageReport(**{**base, **cambios})  # type: ignore[arg-type]


class TestLosCuatroCamposObligatorios:
    def test_la_ficha_guarda_tiempo_memoria_transformaciones_y_scores(self) -> None:
        reporte = _reporte(transforms=_HISTORIAL, scores={"nitidez": 0.82})

        assert reporte.stage == "analisis"
        assert reporte.duration_seconds == pytest.approx(0.031)
        assert reporte.peak_memory_bytes == 4_194_304
        assert list(reporte.transforms) == [_RECORTE]
        assert reporte.scores["nitidez"] == pytest.approx(0.82)

    def test_una_etapa_que_no_transforma_ni_puntua_es_valida(self) -> None:
        """Leer una carpeta no retoca nada; su ficha sigue siendo obligatoria."""
        reporte = _reporte(stage="ingesta")
        assert len(reporte.transforms) == 0
        assert dict(reporte.scores) == {}


class TestSeparacionDeLoMedido:
    def test_la_parte_reproducible_no_trae_tiempo_ni_memoria(self) -> None:
        parte = _reporte().reproducible_part()
        assert not hasattr(parte, "duration_seconds")
        assert not hasattr(parte, "peak_memory_bytes")
        assert isinstance(parte, ReproducibleStageSummary)

    def test_dos_corridas_con_tiempos_distintos_comparan_igual(self) -> None:
        """El caso que, sin esta separación, haría fallar un golden test al azar."""
        rapida = _reporte(
            duration_seconds=0.029, peak_memory_bytes=4_000_000, transforms=_HISTORIAL
        )
        lenta = _reporte(duration_seconds=1.842, peak_memory_bytes=9_900_000, transforms=_HISTORIAL)

        assert rapida != lenta
        assert rapida.reproducible_part() == lenta.reproducible_part()

    def test_si_cambia_lo_que_la_etapa_hizo_la_parte_reproducible_si_difiere(self) -> None:
        """La separación no puede volverse ciega a las diferencias que sí importan."""
        con_recorte = _reporte(transforms=_HISTORIAL)
        sin_recorte = _reporte(transforms=TransformHistory())
        assert con_recorte.reproducible_part() != sin_recorte.reproducible_part()

    def test_un_score_distinto_tambien_diferencia_la_parte_reproducible(self) -> None:
        assert (
            _reporte(scores={"nitidez": 0.82}).reproducible_part()
            != _reporte(scores={"nitidez": 0.81}).reproducible_part()
        )


class TestValoresImposibles:
    @pytest.mark.parametrize("duracion", [-0.001, -1.0, math.nan, math.inf])
    def test_una_duracion_imposible_falla_al_construir(self, duracion: float) -> None:
        with pytest.raises(ValueError, match="duration_seconds"):
            _reporte(duration_seconds=duracion)

    def test_una_memoria_negativa_falla(self) -> None:
        with pytest.raises(ValueError, match="peak_memory_bytes"):
            _reporte(peak_memory_bytes=-1)

    def test_duracion_y_memoria_en_cero_son_validas(self) -> None:
        """Una etapa puede ser más rápida que la resolución del reloj."""
        reporte = _reporte(duration_seconds=0.0, peak_memory_bytes=0)
        assert reporte.duration_seconds == 0.0

    def test_una_etapa_sin_nombre_falla(self) -> None:
        with pytest.raises(ValueError, match="nombre no vacío"):
            _reporte(stage="   ")

    @pytest.mark.parametrize("valor", [math.nan, math.inf, -math.inf])
    def test_un_score_no_finito_falla(self, valor: float) -> None:
        with pytest.raises(ValueError, match="finito"):
            _reporte(scores={"nitidez": valor})

    def test_un_score_sin_nombre_falla(self) -> None:
        with pytest.raises(ValueError, match="score sin nombre"):
            _reporte(scores={"  ": 1.0})

    def test_un_score_negativo_si_es_valido(self) -> None:
        """Hay métricas centradas en cero; el signo lo interpreta quien puntúa."""
        assert _reporte(scores={"desviacion": -0.4}).scores["desviacion"] == pytest.approx(-0.4)


class TestDeterminismoEInmutabilidad:
    def test_los_scores_iteran_siempre_en_el_mismo_orden(self) -> None:
        directo = _reporte(scores={"z": 1.0, "a": 2.0})
        inverso = _reporte(scores={"a": 2.0, "z": 1.0})
        assert list(directo.scores) == list(inverso.scores) == ["a", "z"]

    def test_la_ficha_no_se_puede_alterar(self) -> None:
        with pytest.raises(AttributeError):
            _reporte().duration_seconds = 0.0  # type: ignore[misc]

    def test_los_scores_son_de_solo_lectura(self) -> None:
        with pytest.raises(TypeError):
            _reporte(scores={"nitidez": 0.8}).scores["nitidez"] = 0.0  # type: ignore[index]

    def test_mutar_el_dict_original_no_afecta_la_ficha(self) -> None:
        original = {"nitidez": 0.8}
        reporte = _reporte(scores=original)
        original["nitidez"] = 0.0
        assert reporte.scores["nitidez"] == pytest.approx(0.8)


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_dos_fichas_identicas_son_iguales(self) -> None:
        assert _reporte() == _reporte()

    def test_el_historial_conserva_el_orden_de_los_retoques(self) -> None:
        blancos = Transform(name="balance_blancos", params={"temperatura": 5600})
        historial = TransformHistory().append(_RECORTE).append(blancos)
        assert [paso.name for paso in _reporte(transforms=historial).transforms] == [
            "recorte",
            "balance_blancos",
        ]

    def test_la_parte_reproducible_conserva_los_tres_datos_auditables(self) -> None:
        parte = _reporte(transforms=_HISTORIAL, scores={"nitidez": 0.82}).reproducible_part()
        assert parte.stage == "analisis"
        assert list(parte.transforms) == [_RECORTE]
        assert parte.scores["nitidez"] == pytest.approx(0.82)
