"""Pruebas de la etapa de ingesta ejecutada de punta a punta.

En simple: siembran una carpeta con fotos buenas, dañadas y repetidas, corren la
etapa como lo haría el usuario, y comprueban que el catálogo aparece en el
directorio de trabajo, que lo dañado se aparta llevando su causa, que los
originales quedan byte a byte intactos y que dos corridas producen exactamente el
mismo catálogo.
"""

import json
from pathlib import Path

import pytest

import media_optimizer.pipeline.stages as stages_module
from media_optimizer.core import InvalidInputError, MediaOptimizerError, StageReport
from media_optimizer.ingest import CATALOG_FILENAME, filesystem, load_catalog, read_exif
from media_optimizer.pipeline import STAGES, find_stage
from media_optimizer.pipeline.stages import (
    StageRequest,
    available_stages,
    execute_stage,
)
from media_optimizer.testing import (
    encode_jpeg,
    exif_block,
    flat_image,
    jpeg_with_exif,
    not_an_image,
    textured_image,
    truncated_jpeg,
)

_FOTO_A = encode_jpeg(textured_image(64, 48, 100, seed=1))
_FOTO_B = encode_jpeg(textured_image(48, 64, 140, seed=2))


def _sembrar_lote(carpeta: Path) -> None:
    carpeta.mkdir()
    (carpeta / "a.jpg").write_bytes(_FOTO_A)
    (carpeta / "b.jpg").write_bytes(_FOTO_B)
    (carpeta / "copia_de_a.jpg").write_bytes(_FOTO_A)


def _peticion(tmp_path: Path, origen: str = "lote") -> StageRequest:
    return StageRequest(
        workspace=tmp_path / "salidas", profile="hospedaje", source=tmp_path / origen
    )


class TestIngestaCompleta:
    def test_produce_el_catalogo_en_el_workspace(self, tmp_path: Path) -> None:
        _sembrar_lote(tmp_path / "lote")

        resultado = execute_stage("ingest", _peticion(tmp_path))

        inventario = load_catalog(tmp_path / "salidas")
        assert len(inventario.entries) == 3
        assert resultado.partial is False

    def test_el_resumen_cuenta_lo_que_paso(self, tmp_path: Path) -> None:
        _sembrar_lote(tmp_path / "lote")

        resultado = execute_stage("ingest", _peticion(tmp_path))

        texto = "\n".join(resultado.summary)
        assert "Archivos encontrados: 3" in texto
        assert "Aceptados al catálogo: 3" in texto
        assert "Contenido repetido: 1 copias en 1 grupos" in texto
        assert CATALOG_FILENAME in texto

    def test_lo_danado_se_aparta_y_la_etapa_termina_parcial(self, tmp_path: Path) -> None:
        """Una foto rota degrada esa foto, no tumba el lote (charter)."""
        lote = tmp_path / "lote"
        _sembrar_lote(lote)
        (lote / "rota.jpg").write_bytes(truncated_jpeg(flat_image(64, 64, 90)))
        (lote / "no_es_foto.jpg").write_bytes(not_an_image())

        resultado = execute_stage("ingest", _peticion(tmp_path))

        assert resultado.partial is True
        inventario = load_catalog(tmp_path / "salidas")
        assert len(inventario.entries) == 3
        assert len(inventario.quarantined) == 2
        assert "Apartados a cuarentena: 2" in "\n".join(resultado.summary)

    def test_los_originales_quedan_byte_a_byte_intactos(self, tmp_path: Path) -> None:
        lote = tmp_path / "lote"
        _sembrar_lote(lote)

        execute_stage("ingest", _peticion(tmp_path))

        assert (lote / "a.jpg").read_bytes() == _FOTO_A
        assert (lote / "b.jpg").read_bytes() == _FOTO_B

    def test_dos_corridas_producen_el_mismo_catalogo_byte_a_byte(self, tmp_path: Path) -> None:
        _sembrar_lote(tmp_path / "lote")

        execute_stage("ingest", _peticion(tmp_path))
        primero = filesystem.read_bytes(tmp_path / "salidas" / CATALOG_FILENAME)
        execute_stage("ingest", _peticion(tmp_path))
        segundo = filesystem.read_bytes(tmp_path / "salidas" / CATALOG_FILENAME)

        assert primero == segundo

    def test_las_medidas_del_catalogo_son_las_orientadas(self, tmp_path: Path) -> None:
        """Una foto girada por EXIF entra al catálogo ya enderezada."""
        lote = tmp_path / "lote"
        lote.mkdir()
        girada = jpeg_with_exif(flat_image(64, 48, 100), exif_block(orientation=6))
        (lote / "girada.jpg").write_bytes(girada)

        execute_stage("ingest", _peticion(tmp_path))

        (entrada,) = load_catalog(tmp_path / "salidas").entries
        assert (entrada.width, entrada.height) == (48, 64)


class TestEntradasInvalidas:
    def test_sin_carpeta_de_origen_falla_con_mensaje_accionable(self, tmp_path: Path) -> None:
        peticion = StageRequest(workspace=tmp_path / "salidas", profile="hospedaje", source=None)
        with pytest.raises(InvalidInputError, match="run ingest"):
            execute_stage("ingest", peticion)

    def test_una_carpeta_inexistente_falla_con_su_causa(self, tmp_path: Path) -> None:
        with pytest.raises(InvalidInputError, match="no existe"):
            execute_stage("ingest", _peticion(tmp_path, origen="no_esta"))

    def test_una_etapa_sin_ejecutor_falla_con_claridad(self, tmp_path: Path) -> None:
        with pytest.raises(InvalidInputError, match="no está disponible"):
            execute_stage("reel", _peticion(tmp_path))


class TestIntegridad:
    def test_si_un_original_cambia_durante_la_ingesta_la_etapa_falla_y_lo_nombra(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """El caso de riesgo de datos: la verificación no puede ser decorativa."""

        _sembrar_lote(tmp_path / "lote")
        monkeypatch.setattr(stages_module, "find_modified_sources", lambda _huella: ("a.jpg",))

        with pytest.raises(MediaOptimizerError, match="cambiaron durante la ingesta"):
            execute_stage("ingest", _peticion(tmp_path))


class TestObservabilidad:
    def test_la_etapa_deja_su_ficha_medida(self, tmp_path: Path) -> None:
        _sembrar_lote(tmp_path / "lote")

        resultado = execute_stage("ingest", _peticion(tmp_path))

        assert isinstance(resultado.report, StageReport)
        assert resultado.report.stage == "ingest"
        assert resultado.report.duration_seconds >= 0.0
        assert resultado.report.peak_memory_bytes > 0


class TestDisponibilidadDerivada:
    def test_la_disponibilidad_del_registro_sale_de_los_ejecutores(self) -> None:
        """El registro no puede decir 'disponible' sin que el código exista, ni al revés."""
        for etapa in STAGES:
            assert etapa.available == (etapa.name in available_stages())

    def test_las_etapas_disponibles_son_exactamente_las_con_ejecutor(self) -> None:
        assert find_stage("ingest") is not None
        assert find_stage("ingest").available is True  # type: ignore[union-attr]
        assert available_stages() == frozenset({"ingest", "analyze", "develop", "select", "all"})


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_una_carpeta_vacia_produce_un_catalogo_vacio_y_termina_bien(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "lote").mkdir()
        resultado = execute_stage("ingest", _peticion(tmp_path))
        assert resultado.partial is False
        assert load_catalog(tmp_path / "salidas").entries == ()

    def test_el_workspace_se_crea_si_no_existe(self, tmp_path: Path) -> None:
        _sembrar_lote(tmp_path / "lote")
        peticion = StageRequest(
            workspace=tmp_path / "sin" / "crear", profile="hospedaje", source=tmp_path / "lote"
        )
        execute_stage("ingest", peticion)
        assert filesystem.exists(tmp_path / "sin" / "crear" / CATALOG_FILENAME)


class TestEtapaAnalyze:
    """La etapa completa: catálogo → análisis con veredictos, determinista."""

    def test_produce_el_analisis_con_veredicto_por_foto(self, tmp_path: Path) -> None:
        _sembrar_lote(tmp_path / "lote")
        execute_stage("ingest", _peticion(tmp_path))

        resultado = execute_stage("analyze", _peticion(tmp_path))

        datos = json.loads(
            filesystem.read_bytes(tmp_path / "salidas" / "analysis.json").decode("utf-8")
        )
        assert len(datos["assets"]) == 2  # 3 archivos, 2 contenidos distintos
        for ficha in datos["assets"].values():
            assert ficha["verdict"] in {"publishable", "support", "discard"}
            assert "exposure_score" in ficha["metrics"]
        assert "Fotos analizadas: 2" in "\n".join(resultado.summary)

    def test_dos_corridas_dan_el_mismo_analisis_byte_a_byte(self, tmp_path: Path) -> None:
        _sembrar_lote(tmp_path / "lote")
        execute_stage("ingest", _peticion(tmp_path))

        execute_stage("analyze", _peticion(tmp_path))
        primero = filesystem.read_bytes(tmp_path / "salidas" / "analysis.json")
        execute_stage("analyze", _peticion(tmp_path))
        segundo = filesystem.read_bytes(tmp_path / "salidas" / "analysis.json")

        assert primero == segundo

    def test_sin_catalogo_dice_que_falta_la_ingesta(self, tmp_path: Path) -> None:
        with pytest.raises(InvalidInputError, match="catálogo"):
            execute_stage(
                "analyze",
                StageRequest(workspace=tmp_path / "vacio", profile="h", source=None),
            )


class TestEtapaDevelop:
    def _preparar(self, tmp_path: Path) -> None:
        _sembrar_lote(tmp_path / "lote")
        execute_stage("ingest", _peticion(tmp_path))
        execute_stage("analyze", _peticion(tmp_path))

    def test_produce_reveladas_con_historial_y_antes_despues(self, tmp_path: Path) -> None:
        self._preparar(tmp_path)

        resultado = execute_stage("develop", _peticion(tmp_path))

        datos = json.loads(
            filesystem.read_bytes(tmp_path / "salidas" / "develop.json").decode("utf-8")
        )
        assert len(datos["assets"]) == 2  # una por contenido, no por copia
        for ficha in datos["assets"].values():
            assert filesystem.exists(tmp_path / "salidas" / "derived" / ficha["output"])
            assert [p["name"] for p in ficha["history"]] == [
                "clahe",
                "shadows",
                "exposure",
                "white_balance",
                "saturation",
            ]
            assert "brightness_before" in ficha and "brightness_after" in ficha
        assert "Fotos reveladas: 2" in "\n".join(resultado.summary)

    def test_dos_corridas_dan_el_mismo_develop_json(self, tmp_path: Path) -> None:
        self._preparar(tmp_path)
        execute_stage("develop", _peticion(tmp_path))
        primero = filesystem.read_bytes(tmp_path / "salidas" / "develop.json")
        execute_stage("develop", _peticion(tmp_path))
        segundo = filesystem.read_bytes(tmp_path / "salidas" / "develop.json")
        assert primero == segundo

    def test_los_originales_siguen_intactos_tras_revelar(self, tmp_path: Path) -> None:
        self._preparar(tmp_path)
        execute_stage("develop", _peticion(tmp_path))
        assert (tmp_path / "lote" / "a.jpg").read_bytes() == _FOTO_A

    def test_la_salida_no_lleva_exif(self, tmp_path: Path) -> None:
        """El export nace limpio: sin GPS ni metadatos personales."""

        self._preparar(tmp_path)
        execute_stage("develop", _peticion(tmp_path))
        derivadas = list(filesystem.iter_files(tmp_path / "salidas" / "derived"))
        assert derivadas
        for derivada in derivadas:
            assert read_exif(derivada).is_present is False

    def test_sin_analisis_dice_que_ejecutar(self, tmp_path: Path) -> None:
        _sembrar_lote(tmp_path / "lote")
        execute_stage("ingest", _peticion(tmp_path))
        with pytest.raises(InvalidInputError, match="run analyze"):
            execute_stage("develop", _peticion(tmp_path))


class TestEtapaSelectYRunAll:
    def test_run_all_ejecuta_la_secuencia_completa(self, tmp_path: Path) -> None:
        _sembrar_lote(tmp_path / "lote")

        resultado = execute_stage("all", _peticion(tmp_path))

        for archivo in ("catalog.json", "analysis.json", "develop.json", "selection.json"):
            assert filesystem.exists(tmp_path / "salidas" / archivo), archivo
        texto = "\n".join(resultado.summary)
        for etapa in ("ingest", "analyze", "develop", "select"):
            assert f"── {etapa} ──" in texto

    def test_la_seleccion_es_determinista_y_sin_descartes(self, tmp_path: Path) -> None:
        _sembrar_lote(tmp_path / "lote")
        execute_stage("all", _peticion(tmp_path))
        primero = filesystem.read_bytes(tmp_path / "salidas" / "selection.json")
        execute_stage("select", _peticion(tmp_path))
        segundo = filesystem.read_bytes(tmp_path / "salidas" / "selection.json")
        assert primero == segundo

        datos = json.loads(primero.decode("utf-8"))
        assert set(datos["by_format"]) == {"cover", "feed", "story"}
        assert datos["gallery"], "la galería no puede salir vacía con fotos publicables"

    def test_select_sin_analisis_dice_que_ejecutar(self, tmp_path: Path) -> None:
        _sembrar_lote(tmp_path / "lote")
        execute_stage("ingest", _peticion(tmp_path))
        with pytest.raises(InvalidInputError, match="run analyze"):
            execute_stage("select", _peticion(tmp_path))

    def test_run_all_con_fotos_rotas_termina_parcial(self, tmp_path: Path) -> None:
        lote = tmp_path / "lote"
        _sembrar_lote(lote)
        (lote / "rota.jpg").write_bytes(not_an_image())
        resultado = execute_stage("all", _peticion(tmp_path))
        assert resultado.partial is True
