"""Pruebas de las plantillas de reel: el guion como datos, reutilizable entre lotes.

En simple: comprueban que el guion se puede escribir para cualquier negocio sin
tocar el programa, que la misma plantilla sirve para dos lotes distintos, que
repartir los clips da siempre el mismo resultado, y que cuando falta material el
tramo queda como hueco — porque saber qué falta grabar es el dato útil.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from media_optimizer.core import InvalidInputError, Verdict
from media_optimizer.ranking import RankedAsset
from media_optimizer.video import (
    NarrativeSlot,
    ReelTemplate,
    assign_slots,
    template_from_data,
)

_GUION: dict[str, Any] = {
    "name": "recorrido",
    "slots": [
        {"name": "apertura", "duration_seconds": 3.0, "setting": "fachada"},
        {"name": "espacio", "duration_seconds": 4.0, "setting": "sala"},
        {"name": "cierre", "duration_seconds": 3.0, "setting": None},
    ],
}


def _clip(nombre: str, score: float) -> RankedAsset:
    return RankedAsset(
        content_hash=nombre,
        source=f"{nombre}.mp4",
        score=score,
        verdict=Verdict.PUBLISHABLE,
        flags=(),
        width=1920,
        height=1080,
    )


_MEJOR = _clip("a", 0.95)
_MEDIO = _clip("b", 0.80)
_PEOR = _clip("c", 0.60)
_CANDIDATOS = (_MEJOR, _MEDIO, _PEOR)


class TestGuionComoDatos:
    def test_se_construye_desde_los_datos_del_perfil(self) -> None:
        plantilla = template_from_data(_GUION)
        assert plantilla.name == "recorrido"
        assert [t.name for t in plantilla.slots] == ["apertura", "espacio", "cierre"]

    def test_suma_la_duracion_de_todos_los_tramos(self) -> None:
        assert template_from_data(_GUION).total_duration_seconds == pytest.approx(10.0)

    def test_declara_los_ambientes_que_espera(self) -> None:
        assert template_from_data(_GUION).expected_settings == ("fachada", "sala")

    def test_un_tramo_sin_ambiente_acepta_cualquiera(self) -> None:
        cierre = template_from_data(_GUION).slots[2]
        assert cierre.accepts_any_setting is True

    def test_sirve_para_un_negocio_completamente_distinto(self) -> None:
        """El charter exige que cambiar de vertical no toque el código."""
        bar = template_from_data(
            {
                "name": "noche_bar",
                "slots": [
                    {"name": "barra", "duration_seconds": 2.0, "setting": "barra"},
                    {"name": "pista", "duration_seconds": 5.0, "setting": "pista"},
                ],
            }
        )
        assert bar.expected_settings == ("barra", "pista")
        assert bar.total_duration_seconds == pytest.approx(7.0)

    def test_el_guion_del_perfil_real_es_valido(self) -> None:
        datos = json.loads(
            Path("profiles/hospedaje/reel_template.json").read_text(encoding="utf-8")
        )
        plantilla = template_from_data(datos)
        assert len(plantilla.slots) == 6
        assert plantilla.total_duration_seconds == pytest.approx(19.0)


class TestGuionesInvalidos:
    def test_un_guion_sin_tramos_falla(self) -> None:
        with pytest.raises(ValueError, match="ningún tramo"):
            ReelTemplate(name="vacio", slots=())

    def test_un_tramo_repetido_falla(self) -> None:
        tramo = NarrativeSlot(name="apertura", duration_seconds=1.0)
        with pytest.raises(ValueError, match="repetido"):
            ReelTemplate(name="x", slots=(tramo, tramo))

    def test_una_duracion_imposible_falla(self) -> None:
        with pytest.raises(ValueError, match="duración"):
            NarrativeSlot(name="apertura", duration_seconds=999.0)

    def test_un_tramo_sin_nombre_falla(self) -> None:
        with pytest.raises(ValueError, match="nombre no vacío"):
            NarrativeSlot(name="  ", duration_seconds=1.0)

    def test_una_plantilla_sin_nombre_falla(self) -> None:
        with pytest.raises(ValueError, match="nombre no vacío"):
            ReelTemplate(name=" ", slots=(NarrativeSlot(name="a", duration_seconds=1.0),))

    def test_un_guion_incompleto_da_un_mensaje_accionable(self) -> None:
        with pytest.raises(InvalidInputError, match="incompleto"):
            template_from_data({"slots": []})

    def test_un_valor_invalido_del_perfil_se_explica(self) -> None:
        malo = {"name": "x", "slots": [{"name": "a", "duration_seconds": 999.0}]}
        with pytest.raises(InvalidInputError, match="valor inválido"):
            template_from_data(malo)


class TestRepartoDeClips:
    def test_un_tramo_sin_ambiente_toma_el_mejor_libre(self) -> None:
        plantilla = ReelTemplate(name="x", slots=(NarrativeSlot("libre", 3.0),))
        linea = assign_slots(plantilla, _CANDIDATOS)
        assert linea.assignments[0].asset == _MEJOR

    def test_un_tramo_con_ambiente_solo_acepta_ese_ambiente(self) -> None:
        plantilla = ReelTemplate(name="x", slots=(NarrativeSlot("sala", 3.0, setting="sala"),))
        linea = assign_slots(plantilla, _CANDIDATOS, settings={"b": "sala"})
        assert linea.assignments[0].asset == _MEDIO

    def test_ningun_clip_se_usa_dos_veces(self) -> None:
        plantilla = ReelTemplate(
            name="x",
            slots=(
                NarrativeSlot("uno", 1.0),
                NarrativeSlot("dos", 1.0),
                NarrativeSlot("tres", 1.0),
            ),
        )
        usados = [a.asset for a in assign_slots(plantilla, _CANDIDATOS).assignments]
        assert usados == [_MEJOR, _MEDIO, _PEOR]
        assert len(set(usados)) == 3

    def test_sin_material_el_tramo_queda_como_hueco(self) -> None:
        """Saber qué falta grabar es más útil que rellenar con lo que sea."""
        plantilla = template_from_data(_GUION)
        linea = assign_slots(plantilla, _CANDIDATOS)

        assert linea.gaps == ("apertura", "espacio")
        assert linea.is_complete is False
        assert linea.assignments[2].asset == _MEJOR

    def test_sin_etiquetas_de_ambiente_todos_los_tramos_exigentes_son_huecos(self) -> None:
        plantilla = template_from_data(_GUION)
        assert len(assign_slots(plantilla, _CANDIDATOS).gaps) == 2

    def test_la_duracion_cuenta_solo_los_tramos_llenos(self) -> None:
        plantilla = template_from_data(_GUION)
        linea = assign_slots(plantilla, _CANDIDATOS)
        assert linea.duration_seconds == pytest.approx(3.0)

    def test_un_guion_completo_lo_declara(self) -> None:
        plantilla = template_from_data(_GUION)
        etiquetas = {"a": "fachada", "b": "sala"}
        linea = assign_slots(plantilla, _CANDIDATOS, settings=etiquetas)
        assert linea.is_complete is True
        assert linea.duration_seconds == pytest.approx(10.0)


class TestDeterminismo:
    def test_el_mismo_lote_y_guion_dan_el_mismo_reparto(self) -> None:
        plantilla = template_from_data(_GUION)
        etiquetas = {"a": "fachada", "b": "sala"}
        assert assign_slots(plantilla, _CANDIDATOS, settings=etiquetas) == assign_slots(
            plantilla, _CANDIDATOS, settings=etiquetas
        )

    def test_la_misma_plantilla_sirve_para_dos_lotes_distintos(self) -> None:
        """Reutilizable entre lotes: la plantilla no guarda nada del lote anterior."""
        plantilla = template_from_data(_GUION)
        otro_lote = (_clip("x", 0.9), _clip("y", 0.7))

        primero = assign_slots(plantilla, _CANDIDATOS)
        segundo = assign_slots(plantilla, otro_lote)

        assert primero.assignments[2].asset == _MEJOR
        assert segundo.assignments[2].asset == otro_lote[0]
        assert primero.template_name == segundo.template_name

    def test_un_lote_vacio_deja_todo_en_huecos(self) -> None:
        plantilla = template_from_data(_GUION)
        linea = assign_slots(plantilla, ())
        assert len(linea.gaps) == 3
        assert linea.duration_seconds == 0.0
