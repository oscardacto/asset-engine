"""Pruebas del ajuste de escenas a una duración objetivo.

En simple: comprueban que un conjunto de tomas se recorta hasta sumar
**exactamente** lo que pide el formato —al milisegundo, no «casi»—, que el
material más corto que la meta no se estira, y que ninguna escena queda tan breve
que sea un parpadeo en vez de un plano.

El caso que más importa es el primero: sumar duraciones escaladas en coma
flotante da 15.000000000000002 en vez de 15, y un reel que promete 15 s tiene que
durar 15 s.
"""

import pytest

from media_optimizer.core import Scene
from media_optimizer.core.scene_trimmer import (
    MINIMO_POR_ESCENA,
    TrimStrategy,
    trim_to_target,
)


def _escenas(*duraciones: float) -> tuple[Scene, ...]:
    """Escenas consecutivas con las duraciones pedidas."""
    escenas: list[Scene] = []
    inicio = 0.0
    for posicion, duracion in enumerate(duraciones):
        escenas.append(Scene(index=posicion, start_seconds=inicio, end_seconds=inicio + duracion))
        inicio += duracion
    return tuple(escenas)


class TestPrecisionExacta:
    """Lo que motivó el diseño: en coma flotante la suma no cierra."""

    def test_el_recorte_proporcional_cierra_al_milisegundo(self) -> None:
        plan = trim_to_target(_escenas(12.4, 20.1, 14.8), 15.0, strategy=TrimStrategy.PROPORTIONAL)

        assert plan.total_seconds == 15.0
        assert plan.is_exact is True

    def test_el_calculo_ingenuo_en_coma_flotante_no_habria_cerrado(self) -> None:
        """Demuestra el problema que la aritmética entera evita."""
        factor = 15.0 / 47.3
        ingenuo = sum(duracion * factor for duracion in (12.4, 20.1, 14.8))
        assert ingenuo != 15.0

    @pytest.mark.parametrize("meta", [15.0, 30.0, 60.0, 7.5, 22.333])
    def test_cierra_exacto_para_cualquier_meta(self, meta: float) -> None:
        plan = trim_to_target(
            _escenas(30.0, 25.0, 40.0, 12.0), meta, strategy=TrimStrategy.PROPORTIONAL
        )
        assert plan.total_seconds == meta

    def test_quitar_del_final_tambien_cierra_exacto(self) -> None:
        plan = trim_to_target(_escenas(6.0, 6.0, 6.0), 15.0, strategy=TrimStrategy.DROP_TAIL)
        assert plan.total_seconds == 15.0
        assert plan.is_exact is True


class TestRecorteProporcional:
    def test_todas_las_escenas_encogen(self) -> None:
        original = _escenas(10.0, 20.0, 10.0)
        plan = trim_to_target(original, 20.0, strategy=TrimStrategy.PROPORTIONAL)

        assert len(plan.scenes) == 3
        for antes, despues in zip(original, plan.scenes, strict=True):
            assert despues.duration_seconds < antes.duration_seconds

    def test_conserva_la_proporcion_entre_escenas(self) -> None:
        plan = trim_to_target(_escenas(10.0, 20.0), 15.0, strategy=TrimStrategy.PROPORTIONAL)
        corta, larga = plan.scenes
        assert larga.duration_seconds == pytest.approx(2 * corta.duration_seconds, abs=0.01)

    def test_conserva_todas_las_escenas_del_recorrido(self) -> None:
        """El objetivo de esta estrategia: que aparezcan todos los ambientes."""
        plan = trim_to_target(
            _escenas(8.0, 8.0, 8.0, 8.0), 20.0, strategy=TrimStrategy.PROPORTIONAL
        )
        assert [e.index for e in plan.scenes] == [0, 1, 2, 3]
        assert plan.dropped == ()


class TestQuitarDelFinal:
    def test_las_primeras_conservan_su_duracion_natural(self) -> None:
        """El objetivo de esta estrategia: que las mejores salgan enteras."""
        plan = trim_to_target(_escenas(6.0, 6.0, 6.0), 15.0, strategy=TrimStrategy.DROP_TAIL)

        assert plan.scenes[0].duration_seconds == 6.0
        assert plan.scenes[1].duration_seconds == 6.0
        assert plan.scenes[2].duration_seconds == 3.0

    def test_las_que_sobran_se_descartan(self) -> None:
        plan = trim_to_target(
            _escenas(6.0, 6.0, 6.0, 6.0, 6.0), 12.0, strategy=TrimStrategy.DROP_TAIL
        )
        assert [e.index for e in plan.scenes] == [0, 1]
        assert plan.dropped == (2, 3, 4)

    def test_si_la_primera_ya_pasa_la_meta_se_recorta_sola(self) -> None:
        plan = trim_to_target(_escenas(40.0, 10.0), 15.0, strategy=TrimStrategy.DROP_TAIL)
        assert len(plan.scenes) == 1
        assert plan.scenes[0].duration_seconds == 15.0
        assert plan.dropped == (1,)


class TestMaterialInsuficiente:
    def test_no_se_alarga_lo_que_no_llega(self) -> None:
        """Alargar exigiría repetir cuadros o ralentizar: eso cambia lo que se ve."""
        original = _escenas(4.0, 5.0)
        plan = trim_to_target(original, 15.0, strategy=TrimStrategy.PROPORTIONAL)

        assert plan.scenes == original
        assert plan.total_seconds == 9.0
        assert plan.is_exact is False

    def test_tampoco_al_quitar_del_final(self) -> None:
        original = _escenas(4.0, 5.0)
        plan = trim_to_target(original, 15.0, strategy=TrimStrategy.DROP_TAIL)
        assert plan.scenes == original
        assert plan.is_exact is False

    def test_material_que_ya_suma_la_meta_no_se_toca(self) -> None:
        original = _escenas(5.0, 10.0)
        plan = trim_to_target(original, 15.0, strategy=TrimStrategy.PROPORTIONAL)

        assert plan.scenes == original
        assert plan.is_exact is True


class TestMinimoPorEscena:
    def test_una_escena_que_quedaria_un_parpadeo_se_descarta(self) -> None:
        """Recortar mucho convierte una toma breve en un destello inútil."""
        plan = trim_to_target(
            _escenas(60.0, 1.0), 20.0, strategy=TrimStrategy.PROPORTIONAL, min_scene_seconds=1.0
        )

        assert plan.dropped == (1,)
        assert [e.index for e in plan.scenes] == [0]
        assert plan.total_seconds == 20.0

    def test_el_tiempo_de_la_descartada_se_reparte(self) -> None:
        plan = trim_to_target(
            _escenas(60.0, 60.0, 1.0),
            30.0,
            strategy=TrimStrategy.PROPORTIONAL,
            min_scene_seconds=1.0,
        )
        assert plan.dropped == (2,)
        assert [(e.index, e.duration_seconds) for e in plan.scenes] == [(0, 15.0), (1, 15.0)]
        assert plan.total_seconds == 30.0

    def test_ninguna_escena_conservada_queda_bajo_el_minimo(self) -> None:
        plan = trim_to_target(
            _escenas(20.0, 20.0, 20.0, 20.0),
            8.0,
            strategy=TrimStrategy.PROPORTIONAL,
            min_scene_seconds=2.5,
        )
        for escena in plan.scenes:
            assert escena.duration_seconds >= 2.5

    def test_si_ni_una_cabe_entera_se_devuelve_lo_que_quepa(self) -> None:
        """Meta muy pequeña frente al mínimo: no se fuerza un resultado imposible."""
        plan = trim_to_target(
            _escenas(10.0, 10.0), 1.0, strategy=TrimStrategy.PROPORTIONAL, min_scene_seconds=5.0
        )
        assert plan.total_seconds <= 10.0

    def test_el_minimo_por_defecto_esta_declarado(self) -> None:
        assert MINIMO_POR_ESCENA > 0


class TestPlan:
    def test_informa_que_escenas_quedaron_fuera(self) -> None:
        plan = trim_to_target(_escenas(6.0, 6.0, 6.0), 6.0, strategy=TrimStrategy.DROP_TAIL)
        assert plan.dropped == (1, 2)

    def test_recuerda_la_meta_y_la_estrategia(self) -> None:
        plan = trim_to_target(_escenas(10.0), 5.0, strategy=TrimStrategy.DROP_TAIL)
        assert plan.target_seconds == 5.0
        assert plan.strategy is TrimStrategy.DROP_TAIL

    def test_el_plan_es_inmutable(self) -> None:
        plan = trim_to_target(_escenas(10.0), 5.0, strategy=TrimStrategy.PROPORTIONAL)
        with pytest.raises(AttributeError):
            plan.scenes = ()  # type: ignore[misc]

    def test_las_escenas_conservan_su_indice_original(self) -> None:
        plan = trim_to_target(_escenas(10.0, 10.0, 10.0), 15.0, strategy=TrimStrategy.DROP_TAIL)
        assert [e.index for e in plan.scenes] == [0, 1]


class TestDeterminismo:
    def test_el_mismo_lote_y_meta_dan_el_mismo_plan(self) -> None:
        escenas = _escenas(12.4, 20.1, 14.8)
        assert trim_to_target(escenas, 15.0, strategy=TrimStrategy.PROPORTIONAL) == trim_to_target(
            escenas, 15.0, strategy=TrimStrategy.PROPORTIONAL
        )

    def test_las_dos_estrategias_dan_resultados_distintos(self) -> None:
        escenas = _escenas(6.0, 6.0, 6.0)
        proporcional = trim_to_target(escenas, 15.0, strategy=TrimStrategy.PROPORTIONAL)
        del_final = trim_to_target(escenas, 15.0, strategy=TrimStrategy.DROP_TAIL)
        assert proporcional.scenes != del_final.scenes
        assert proporcional.total_seconds == del_final.total_seconds == 15.0


class TestEntradasInvalidas:
    @pytest.mark.parametrize("meta", [0.0, -1.0])
    def test_una_meta_no_positiva_falla(self, meta: float) -> None:
        with pytest.raises(ValueError, match="target_seconds"):
            trim_to_target(_escenas(10.0), meta, strategy=TrimStrategy.PROPORTIONAL)

    def test_un_minimo_no_positivo_falla(self) -> None:
        with pytest.raises(ValueError, match="min_scene_seconds"):
            trim_to_target(
                _escenas(10.0), 5.0, strategy=TrimStrategy.PROPORTIONAL, min_scene_seconds=0.0
            )

    def test_un_lote_vacio_no_es_un_error(self) -> None:
        plan = trim_to_target((), 15.0, strategy=TrimStrategy.PROPORTIONAL)
        assert plan.scenes == ()
        assert plan.total_seconds == 0.0
        assert plan.is_exact is False
