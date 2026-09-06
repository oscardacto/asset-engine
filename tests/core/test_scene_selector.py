"""Pruebas del descarte de escenas: qué se conserva y, sobre todo, por qué no.

En simple: comprueban que una toma buena pasa, que una corta o temblorosa se
descarta diciendo cuál fue el problema, que si falla por varias razones se
enumeran todas —porque eso es lo que le dice al usuario qué grabar mejor—, y que
el juicio mira cada componente por separado en vez de la nota general, que va a
cambiar de valor cuando se añada una métrica nueva.
"""

from dataclasses import fields

import pytest

from media_optimizer.core import Scene, SceneScore
from media_optimizer.core.scene_selection import (
    UMBRALES_POR_DEFECTO,
    DiscardReason,
    SceneThresholds,
    judge_scene,
    kept_scenes,
    select_scenes,
)

_CRITERIOS = SceneThresholds(min_duration_seconds=1.5, min_exposure=0.6, min_stability=0.15)


def _escena(index: int = 0, duracion: float = 4.0) -> Scene:
    return Scene(index=index, start_seconds=0.0, end_seconds=duracion)


def _nota(index: int = 0, exposicion: float = 0.9, estabilidad: float = 0.4) -> SceneScore:
    return SceneScore(
        scene_index=index, exposure=exposicion, stability=estabilidad, sampled_frames=5
    )


class TestEscenaQueSeConserva:
    def test_una_escena_buena_pasa_sin_causas(self) -> None:
        veredicto = judge_scene(_escena(), _nota(), _CRITERIOS)
        assert veredicto.keep is True
        assert veredicto.reasons == ()

    def test_el_veredicto_conserva_el_indice_de_la_escena(self) -> None:
        assert judge_scene(_escena(index=7), _nota(index=7), _CRITERIOS).scene_index == 7

    def test_el_umbral_es_el_minimo_aceptable_no_el_primer_rechazo(self) -> None:
        """Un valor justo en el límite cumple el criterio."""
        justa = judge_scene(
            _escena(duracion=1.5), _nota(exposicion=0.6, estabilidad=0.15), _CRITERIOS
        )
        assert justa.keep is True


class TestCausasDeDescarte:
    def test_una_escena_corta_se_descarta_por_duracion(self) -> None:
        veredicto = judge_scene(_escena(duracion=0.8), _nota(), _CRITERIOS)
        assert veredicto.keep is False
        assert veredicto.reasons == (DiscardReason.TOO_SHORT,)

    def test_una_escena_temblorosa_se_descarta_por_estabilidad(self) -> None:
        veredicto = judge_scene(_escena(), _nota(estabilidad=0.05), _CRITERIOS)
        assert veredicto.reasons == (DiscardReason.UNSTABLE,)

    def test_una_escena_mal_expuesta_se_descarta_por_exposicion(self) -> None:
        veredicto = judge_scene(_escena(), _nota(exposicion=0.3), _CRITERIOS)
        assert veredicto.reasons == (DiscardReason.POOR_EXPOSURE,)

    def test_se_reportan_todas_las_causas_no_la_primera(self) -> None:
        """Saber qué corregir es el valor del descarte, y puede haber varias cosas."""
        veredicto = judge_scene(
            _escena(duracion=0.5), _nota(exposicion=0.2, estabilidad=0.01), _CRITERIOS
        )
        assert set(veredicto.reasons) == {
            DiscardReason.TOO_SHORT,
            DiscardReason.POOR_EXPOSURE,
            DiscardReason.UNSTABLE,
        }

    def test_las_causas_salen_siempre_en_el_mismo_orden(self) -> None:
        mala = judge_scene(
            _escena(duracion=0.5), _nota(exposicion=0.2, estabilidad=0.01), _CRITERIOS
        )
        assert (
            mala.reasons
            == judge_scene(
                _escena(duracion=0.5), _nota(exposicion=0.2, estabilidad=0.01), _CRITERIOS
            ).reasons
        )
        assert list(mala.reasons) == sorted(mala.reasons, key=lambda causa: causa.value)


class TestIndependenciaDeLaNotaGeneral:
    def test_dos_escenas_con_la_misma_nota_pueden_tener_veredictos_distintos(self) -> None:
        """La nota general cambiará al entrar la nitidez; el juicio no puede colgar de ella."""
        equilibrada = _nota(exposicion=0.65, estabilidad=0.65)
        desequilibrada = _nota(exposicion=1.0, estabilidad=0.30)
        assert equilibrada.overall == pytest.approx(desequilibrada.overall, abs=0.01)

        assert judge_scene(_escena(), equilibrada, _CRITERIOS).keep is True
        floja = judge_scene(_escena(), _nota(exposicion=1.0, estabilidad=0.10), _CRITERIOS)
        assert floja.keep is False

    def test_una_nota_general_alta_no_salva_un_componente_hundido(self) -> None:
        buena_nota = _nota(exposicion=1.0, estabilidad=0.10)
        assert buena_nota.overall > 0.5
        assert judge_scene(_escena(), buena_nota, _CRITERIOS).keep is False


class TestLote:
    def test_juzga_todas_las_escenas_en_orden(self) -> None:
        escenas = (_escena(0), _escena(1, duracion=0.5), _escena(2))
        notas = (_nota(0), _nota(1), _nota(2, estabilidad=0.02))

        veredictos = select_scenes(escenas, notas, _CRITERIOS)

        assert [v.scene_index for v in veredictos] == [0, 1, 2]
        assert [v.keep for v in veredictos] == [True, False, False]

    def test_devuelve_solo_las_que_sobreviven(self) -> None:
        escenas = (_escena(0), _escena(1, duracion=0.5))
        notas = (_nota(0), _nota(1))
        assert [e.index for e in kept_scenes(escenas, notas, _CRITERIOS)] == [0]

    def test_un_lote_entero_descartado_es_un_resultado_valido(self) -> None:
        """Un lote mal grabado no es un error: dice que hay que volver a grabar."""
        escenas = (_escena(0, duracion=0.4), _escena(1, duracion=0.3))
        notas = (_nota(0), _nota(1))

        veredictos = select_scenes(escenas, notas, _CRITERIOS)

        assert all(not v.keep for v in veredictos)
        assert kept_scenes(escenas, notas, _CRITERIOS) == ()

    def test_un_lote_vacio_no_es_un_error(self) -> None:
        assert select_scenes((), (), _CRITERIOS) == ()

    def test_escenas_y_notas_descuadradas_fallan(self) -> None:
        with pytest.raises(ValueError, match="misma cantidad"):
            select_scenes((_escena(0), _escena(1)), (_nota(0),), _CRITERIOS)


class TestUmbralesPorDefecto:
    def test_no_vacian_el_material_real_del_cliente(self) -> None:
        """La estabilidad real llega a 0.404: un umbral de 0.5 descartaría las 19 escenas."""
        mejor_real = judge_scene(
            _escena(duracion=13.7),
            _nota(exposicion=0.928, estabilidad=0.404),
            UMBRALES_POR_DEFECTO,
        )
        assert mejor_real.keep is True

    def test_apartan_las_peores_del_material_real(self) -> None:
        peor_real = judge_scene(
            _escena(duracion=0.93),
            _nota(exposicion=0.799, estabilidad=0.0),
            UMBRALES_POR_DEFECTO,
        )
        assert peor_real.keep is False
        assert DiscardReason.UNSTABLE in peor_real.reasons
        assert DiscardReason.TOO_SHORT in peor_real.reasons

    def test_la_exposicion_real_del_cliente_nunca_se_descarta(self) -> None:
        """El material va de 0.799 a 0.976: el problema del cliente no es la luz."""
        for exposicion in (0.799, 0.928, 0.976):
            veredicto = judge_scene(
                _escena(), _nota(exposicion=exposicion, estabilidad=0.4), UMBRALES_POR_DEFECTO
            )
            assert DiscardReason.POOR_EXPOSURE not in veredicto.reasons


class TestUmbralesInvalidos:
    @pytest.mark.parametrize("campo", ["min_exposure", "min_stability"])
    @pytest.mark.parametrize("valor", [-0.1, 1.1])
    def test_un_umbral_fuera_de_rango_falla(self, campo: str, valor: float) -> None:
        base = {"min_duration_seconds": 1.5, "min_exposure": 0.6, "min_stability": 0.15}
        with pytest.raises(ValueError, match=campo):
            SceneThresholds(**{**base, campo: valor})  # type: ignore[arg-type]

    @pytest.mark.parametrize("duracion", [0.0, -1.0])
    def test_una_duracion_minima_no_positiva_falla(self, duracion: float) -> None:
        with pytest.raises(ValueError, match="min_duration_seconds"):
            SceneThresholds(min_duration_seconds=duracion, min_exposure=0.6, min_stability=0.15)


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_el_veredicto_es_inmutable(self) -> None:
        with pytest.raises(AttributeError):
            judge_scene(_escena(), _nota(), _CRITERIOS).reasons = ()  # type: ignore[misc]

    def test_conservar_no_existe_como_campo_asignable(self) -> None:
        """Es derivado: no hay forma de marcar como buena una escena con causas."""
        veredicto = judge_scene(_escena(duracion=0.1), _nota(), _CRITERIOS)
        assert "keep" not in {campo.name for campo in fields(veredicto)}
        assert veredicto.keep is False

    def test_los_umbrales_son_inmutables(self) -> None:
        with pytest.raises(AttributeError):
            _CRITERIOS.min_stability = 0.9  # type: ignore[misc]

    def test_conservar_se_deriva_de_no_tener_causas(self) -> None:
        """No puede existir una escena conservada que traiga causas de descarte."""
        buena = judge_scene(_escena(), _nota(), _CRITERIOS)
        mala = judge_scene(_escena(duracion=0.1), _nota(), _CRITERIOS)
        assert buena.keep == (buena.reasons == ())
        assert mala.keep == (mala.reasons == ())
