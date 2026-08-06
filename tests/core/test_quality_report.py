"""Pruebas de ``QualityReport``: construcción, inmutabilidad, validación y determinismo.

En simple: verifican que la boleta de calidad se crea bien, rechaza números
inválidos (NaN/inf), no se puede modificar y siempre itera en el mismo orden.
"""

import math
from dataclasses import FrozenInstanceError

import pytest

from media_optimizer.core import QualityReport, Verdict


def _reporte(
    metrics: dict[str, float] | None = None,
    flags: tuple[str, ...] | None = None,
    verdict: Verdict = Verdict.SUPPORT,
) -> QualityReport:
    if metrics is None:
        metrics = {"mean_brightness": 118.4, "sharpness": 0.72}
    if flags is None:
        flags = ()
    return QualityReport(metrics=metrics, flags=flags, verdict=verdict)


class TestConstruccion:
    def test_expone_metricas_flags_y_veredicto(self) -> None:
        reporte = _reporte(flags=("whatsapp_compressed",))
        assert reporte.metrics["mean_brightness"] == 118.4
        assert "whatsapp_compressed" in reporte.flags
        assert reporte.verdict is Verdict.SUPPORT

    def test_reporte_sin_metricas_ni_flags_es_valido(self) -> None:
        reporte = _reporte(metrics={}, flags=())
        assert len(reporte.metrics) == 0
        assert reporte.flags == ()


class TestInmutabilidad:
    def test_asignar_un_campo_lanza_frozen_error(self) -> None:
        with pytest.raises(FrozenInstanceError):
            _reporte().verdict = Verdict.DISCARD  # type: ignore[misc]

    def test_las_metricas_son_de_solo_lectura(self) -> None:
        reporte = _reporte()
        with pytest.raises(TypeError):
            reporte.metrics["sharpness"] = 1.0  # type: ignore[index]

    def test_mutar_el_dict_original_no_afecta_al_reporte(self) -> None:
        original = {"mean_brightness": 100.0}
        reporte = _reporte(metrics=original)
        original["intrusa"] = 1.0
        assert "intrusa" not in reporte.metrics


class TestInvariantesFailFast:
    def test_metrica_nan_falla_nombrando_la_metrica(self) -> None:
        with pytest.raises(ValueError, match="sharpness"):
            _reporte(metrics={"sharpness": math.nan})

    def test_metrica_infinita_falla(self) -> None:
        with pytest.raises(ValueError, match="finito"):
            _reporte(metrics={"noise": math.inf})

    def test_nombre_de_metrica_vacio_falla(self) -> None:
        with pytest.raises(ValueError, match="nombre"):
            _reporte(metrics={"  ": 1.0})

    def test_flag_vacio_falla(self) -> None:
        with pytest.raises(ValueError, match="flags"):
            _reporte(flags=("   ",))


class TestVeredicto:
    def test_tiene_exactamente_los_tres_destinos(self) -> None:
        assert [v.value for v in Verdict] == ["publishable", "support", "discard"]

    def test_serializa_a_string_plano(self) -> None:
        assert str(Verdict.PUBLISHABLE) == "publishable"


class TestDeterminismo:
    def test_orden_de_insercion_no_altera_igualdad_ni_iteracion(self) -> None:
        a = _reporte(metrics={"b_metric": 2.0, "a_metric": 1.0})
        b = _reporte(metrics={"a_metric": 1.0, "b_metric": 2.0})
        assert a == b
        assert list(a.metrics) == list(b.metrics) == ["a_metric", "b_metric"]


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_valores_cero_y_negativos_son_finitos_validos(self) -> None:
        reporte = _reporte(metrics={"delta": -3.5, "zero": 0.0})
        assert reporte.metrics["delta"] == -3.5

    def test_reportes_iguales_comparten_hash(self) -> None:
        assert hash(_reporte()) == hash(_reporte())
