"""Pruebas del perfil de negocio: la forma que tiene el criterio de un negocio.

En simple: verifican que el perfil no se puede alterar, que siempre se recorre en
el mismo orden —de eso depende que el programa dé el mismo resultado dos veces—,
que los valores imposibles fallan al construirlo y no más tarde, y sobre todo que
un negocio con criterios opuestos al del cliente actual cabe sin tocar el código.
"""

import ast
import math
from pathlib import Path
from types import ModuleType

import pytest

from media_optimizer.core import (
    BusinessProfile,
    OutputFormat,
    OutputIntent,
    ScoringWeights,
    business_profile,
)


def _vocabulario_del_codigo(modulo: ModuleType) -> str:
    """Todo lo que el módulo nombra o escribe como dato, sin la documentación.

    Recoge identificadores y textos literales del árbol sintáctico y descarta los
    docstrings, que son prosa explicativa y no criterio grabado en el código.
    """
    arbol = ast.parse(Path(modulo.__file__ or "").read_text(encoding="utf-8"))
    docstrings = {
        ast.get_docstring(nodo, clean=False)
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Module | ast.ClassDef | ast.FunctionDef)
    }
    piezas: list[str] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Name | ast.Attribute | ast.arg):
            piezas.append(getattr(nodo, "id", None) or getattr(nodo, "attr", None) or nodo.arg)
        elif isinstance(nodo, ast.ClassDef | ast.FunctionDef):
            piezas.append(nodo.name)
        elif (
            isinstance(nodo, ast.Constant)
            and isinstance(nodo.value, str)
            and nodo.value not in docstrings
        ):
            piezas.append(nodo.value)
    return " ".join(piezas).lower()


_FEED = OutputFormat(intent=OutputIntent.FEED, width=1080, height=1350)
_STORY = OutputFormat(intent=OutputIntent.STORY, width=1080, height=1920)
_COVER = OutputFormat(intent=OutputIntent.COVER, width=1920, height=1080)


def _perfil(**cambios: object) -> BusinessProfile:
    base: dict[str, object] = {"name": "generico", "version": "1.0"}
    return BusinessProfile(**{**base, **cambios})  # type: ignore[arg-type]


class TestFormatos:
    def test_el_aspecto_se_deduce_de_las_dimensiones(self) -> None:
        assert _FEED.aspect_ratio == pytest.approx(0.8)
        assert _STORY.aspect_ratio == pytest.approx(0.5625)

    @pytest.mark.parametrize(
        ("ancho", "alto", "cabe"),
        [(1080, 1350, True), (2000, 2500, True), (1079, 1350, False), (1080, 1349, False)],
    )
    def test_dice_si_una_imagen_alcanza_para_el_formato(
        self, ancho: int, alto: int, cabe: bool
    ) -> None:
        assert _FEED.accepts(ancho, alto) is cabe

    @pytest.mark.parametrize(("ancho", "alto"), [(0, 1350), (1080, 0), (-1, 100)])
    def test_una_dimension_imposible_falla_al_construir(self, ancho: int, alto: int) -> None:
        with pytest.raises(ValueError, match="px"):
            OutputFormat(intent=OutputIntent.FEED, width=ancho, height=alto)

    def test_el_perfil_devuelve_el_formato_de_una_intencion(self) -> None:
        perfil = _perfil(formats=(_FEED, _STORY))
        assert perfil.format_for(OutputIntent.STORY) == _STORY

    def test_una_intencion_que_el_perfil_no_produce_devuelve_nada(self) -> None:
        """Un negocio puede no querer portada; eso no es un error."""
        assert _perfil(formats=(_FEED,)).format_for(OutputIntent.COVER) is None

    def test_dos_formatos_para_la_misma_intencion_no_se_permiten(self) -> None:
        repetido = OutputFormat(intent=OutputIntent.FEED, width=1080, height=1080)
        with pytest.raises(ValueError, match="más de un formato"):
            _perfil(formats=(_FEED, repetido))


class TestPesos:
    def test_devuelve_el_peso_de_una_metrica(self) -> None:
        pesos = ScoringWeights(intent=OutputIntent.COVER, weights={"nitidez": 0.6})
        assert pesos.weight_for("nitidez") == pytest.approx(0.6)

    def test_una_metrica_que_el_perfil_no_menciona_no_cuenta(self) -> None:
        pesos = ScoringWeights(intent=OutputIntent.COVER, weights={"nitidez": 0.6})
        assert pesos.weight_for("ruido") == 0.0

    def test_un_peso_en_cero_es_valido(self) -> None:
        """Decir 'esta métrica no cuenta aquí' es criterio legítimo del negocio."""
        pesos = ScoringWeights(intent=OutputIntent.STORY, weights={"nitidez": 0.0})
        assert pesos.weight_for("nitidez") == 0.0

    @pytest.mark.parametrize("peso", [-0.1, math.nan, math.inf])
    def test_un_peso_imposible_falla_al_construir(self, peso: float) -> None:
        with pytest.raises(ValueError, match="peso"):
            ScoringWeights(intent=OutputIntent.FEED, weights={"nitidez": peso})

    def test_una_metrica_sin_nombre_falla(self) -> None:
        with pytest.raises(ValueError, match="nombre no vacío"):
            ScoringWeights(intent=OutputIntent.FEED, weights={"  ": 1.0})

    def test_el_perfil_devuelve_los_pesos_de_una_intencion(self) -> None:
        pesos = ScoringWeights(intent=OutputIntent.FEED, weights={"nitidez": 0.5})
        assert _perfil(scoring=(pesos,)).weights_for(OutputIntent.FEED) is pesos

    def test_una_intencion_sin_pesos_devuelve_un_grupo_vacio(self) -> None:
        vacio = _perfil().weights_for(OutputIntent.COVER)
        assert vacio.intent is OutputIntent.COVER
        assert vacio.weight_for("nitidez") == 0.0

    def test_dos_grupos_de_pesos_para_la_misma_intencion_no_se_permiten(self) -> None:
        uno = ScoringWeights(intent=OutputIntent.FEED, weights={"nitidez": 0.5})
        otro = ScoringWeights(intent=OutputIntent.FEED, weights={"ruido": 0.5})
        with pytest.raises(ValueError, match="más de un grupo de pesos"):
            _perfil(scoring=(uno, otro))

    def test_los_pesos_no_tienen_que_sumar_uno(self) -> None:
        """Normalizar es del algoritmo de score, no del contrato."""
        pesos = ScoringWeights(intent=OutputIntent.FEED, weights={"a": 3.0, "b": 7.0})
        assert sum(pesos.weights.values()) == pytest.approx(10.0)


class TestUmbrales:
    def test_devuelve_el_umbral_por_nombre(self) -> None:
        perfil = _perfil(thresholds={"nitidez_minima": 120.0})
        assert perfil.threshold("nitidez_minima") == pytest.approx(120.0)

    def test_un_umbral_ausente_devuelve_el_valor_indicado(self) -> None:
        assert _perfil().threshold("nitidez_minima", default=0.0) == 0.0
        assert _perfil().threshold("nitidez_minima") is None

    @pytest.mark.parametrize("valor", [math.nan, math.inf, -math.inf])
    def test_un_umbral_no_finito_falla(self, valor: float) -> None:
        with pytest.raises(ValueError, match="número finito"):
            _perfil(thresholds={"nitidez_minima": valor})

    def test_un_umbral_negativo_si_es_valido(self) -> None:
        """Hay métricas centradas en cero: un objetivo de exposición puede ser negativo."""
        assert _perfil(thresholds={"exposicion_objetivo": -0.3}).threshold(
            "exposicion_objetivo"
        ) == pytest.approx(-0.3)

    def test_un_umbral_sin_nombre_falla(self) -> None:
        with pytest.raises(ValueError, match="nombre no vacío"):
            _perfil(thresholds={"": 1.0})


class TestAmbientes:
    def test_los_ambientes_son_texto_libre_del_negocio(self) -> None:
        perfil = _perfil(environments=("cocina", "balcon", "bano"))
        assert set(perfil.environments) == {"cocina", "balcon", "bano"}

    def test_un_ambiente_repetido_falla(self) -> None:
        with pytest.raises(ValueError, match="repetido"):
            _perfil(environments=("cocina", "cocina"))

    def test_un_ambiente_vacio_falla(self) -> None:
        with pytest.raises(ValueError, match="no pueden estar vacíos"):
            _perfil(environments=("cocina", "   "))


class TestIdentidad:
    @pytest.mark.parametrize("campo", ["name", "version"])
    def test_nombre_o_version_vacios_fallan(self, campo: str) -> None:
        with pytest.raises(ValueError, match="no puede estar vacío"):
            _perfil(**{campo: "  "})


class TestDeterminismo:
    def test_los_ambientes_quedan_ordenados(self) -> None:
        perfil = _perfil(environments=("terraza", "alcoba", "cocina"))
        assert perfil.environments == ("alcoba", "cocina", "terraza")

    def test_los_formatos_quedan_ordenados_por_intencion(self) -> None:
        directo = _perfil(formats=(_STORY, _COVER, _FEED))
        inverso = _perfil(formats=(_FEED, _COVER, _STORY))
        assert directo.formats == inverso.formats

    def test_los_umbrales_iteran_siempre_igual(self) -> None:
        directo = _perfil(thresholds={"z": 1.0, "a": 2.0})
        inverso = _perfil(thresholds={"a": 2.0, "z": 1.0})
        assert list(directo.thresholds) == list(inverso.thresholds) == ["a", "z"]

    def test_el_orden_de_construccion_no_cambia_el_perfil(self) -> None:
        directo = _perfil(environments=("b", "a"), formats=(_STORY, _FEED))
        inverso = _perfil(environments=("a", "b"), formats=(_FEED, _STORY))
        assert directo == inverso


class TestInmutabilidad:
    def test_el_perfil_no_se_puede_alterar(self) -> None:
        with pytest.raises(AttributeError):
            _perfil().name = "otro"  # type: ignore[misc]

    def test_los_umbrales_son_de_solo_lectura(self) -> None:
        perfil = _perfil(thresholds={"nitidez_minima": 120.0})
        with pytest.raises(TypeError):
            perfil.thresholds["nitidez_minima"] = 0.0  # type: ignore[index]

    def test_mutar_el_dict_original_no_afecta_al_perfil(self) -> None:
        original = {"nitidez_minima": 120.0}
        perfil = _perfil(thresholds=original)
        original["nitidez_minima"] = 0.0
        assert perfil.threshold("nitidez_minima") == pytest.approx(120.0)


class TestGeneralizacion:
    """El charter §3 prohíbe que el criterio del cliente 0 viva en el código."""

    def test_un_negocio_con_criterios_opuestos_cabe_sin_tocar_el_modulo(self) -> None:
        bar_nocturno = BusinessProfile(
            name="bar_nocturno",
            version="0.1",
            environments=("barra", "pista", "tarima"),
            formats=(OutputFormat(intent=OutputIntent.STORY, width=1080, height=1920),),
            scoring=(
                ScoringWeights(
                    intent=OutputIntent.STORY,
                    weights={"movimiento": 0.7, "nitidez": 0.1, "saturacion": 0.2},
                ),
            ),
            thresholds={"exposicion_objetivo": -1.2, "saturacion_maxima": 0.45},
        )

        assert bar_nocturno.format_for(OutputIntent.FEED) is None
        assert bar_nocturno.weights_for(OutputIntent.STORY).weight_for("movimiento") > (
            bar_nocturno.weights_for(OutputIntent.STORY).weight_for("nitidez")
        )
        assert bar_nocturno.threshold("exposicion_objetivo") == pytest.approx(-1.2)

    @pytest.mark.parametrize(
        "vocabulario",
        ["living", "hospedaje", "airbnb", "cocina", "alcoba", "nitidez", "portada"],
    )
    def test_el_codigo_no_nombra_ambientes_metricas_ni_clientes(self, vocabulario: str) -> None:
        """El día que alguien escriba aquí un ambiente o una métrica, esto falla.

        Mira lo que el módulo *hace*, no lo que explica: los textos de
        documentación quedan fuera, porque describir la regla no es violarla.
        """
        assert vocabulario not in _vocabulario_del_codigo(business_profile)


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_un_perfil_sin_nada_configurado_es_valido(self) -> None:
        """Que sea útil lo juzga quien lo carga; estructuralmente no está roto."""
        minimo = BusinessProfile(name="vacio", version="0.0")
        assert minimo.environments == ()
        assert minimo.formats == ()
        assert minimo.threshold("lo_que_sea") is None

    def test_dos_perfiles_iguales_son_iguales(self) -> None:
        assert _perfil(formats=(_FEED,)) == _perfil(formats=(_FEED,))

    def test_el_formato_cuadrado_tambien_es_representable(self) -> None:
        """El cliente 0 no quiere 1:1, pero el contrato no puede prohibirlo."""
        cuadrado = OutputFormat(intent=OutputIntent.FEED, width=1080, height=1080)
        assert cuadrado.aspect_ratio == pytest.approx(1.0)
