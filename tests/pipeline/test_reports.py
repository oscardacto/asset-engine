"""Pruebas del reporte de inventario generado desde un catálogo real.

En simple: ingieren un lote pequeño, piden el reporte y comprueban que la tabla
trae una fila por foto con sus medidas y su orientación, que la cuarentena aparece
con su causa, y que generar dos veces el mismo reporte da exactamente los mismos
bytes — porque el reporte es una salida persistida y la promesa de reproducibilidad
lo cubre.
"""

from pathlib import Path

import pytest

from media_optimizer.core import InvalidInputError
from media_optimizer.ingest import filesystem
from media_optimizer.pipeline import REPORTS, find_report
from media_optimizer.pipeline.reports import (
    ReportRequest,
    ReportResult,
    available_reports,
    generate_report,
)
from media_optimizer.pipeline.stages import StageRequest, execute_stage
from media_optimizer.testing import encode_jpeg, not_an_image, textured_image

_VERTICAL = encode_jpeg(textured_image(48, 64, 100, seed=3))
_HORIZONTAL = encode_jpeg(textured_image(64, 48, 140, seed=4))


@pytest.fixture
def workspace_con_catalogo(tmp_path: Path) -> Path:
    lote = tmp_path / "lote"
    lote.mkdir()
    (lote / "vertical.jpg").write_bytes(_VERTICAL)
    (lote / "horizontal.jpg").write_bytes(_HORIZONTAL)
    (lote / "rota.jpg").write_bytes(not_an_image())
    salidas = tmp_path / "salidas"
    execute_stage("ingest", StageRequest(workspace=salidas, profile="hospedaje", source=lote))
    return salidas


def _peticion(workspace: Path, formato: str = "markdown") -> ReportRequest:
    return ReportRequest(workspace=workspace, output_format=formato)


class TestInventario:
    def test_una_fila_por_asset_con_medidas_y_orientacion(
        self, workspace_con_catalogo: Path
    ) -> None:
        resultado = generate_report("inventory", _peticion(workspace_con_catalogo))

        assert "| vertical.jpg | 48x64 | vertical |" in resultado.content
        assert "| horizontal.jpg | 64x48 | horizontal |" in resultado.content

    def test_la_cuarentena_aparece_con_su_causa(self, workspace_con_catalogo: Path) -> None:
        contenido = generate_report("inventory", _peticion(workspace_con_catalogo)).content
        assert "Cuarentena" in contenido
        assert "rota.jpg" in contenido
        assert "unknown_format" in contenido

    def test_el_reporte_queda_escrito_en_reports(self, workspace_con_catalogo: Path) -> None:
        resultado = generate_report("inventory", _peticion(workspace_con_catalogo))

        assert resultado.written_to == workspace_con_catalogo / "reports" / "inventory.md"
        en_disco = filesystem.read_bytes(resultado.written_to).decode("utf-8")
        assert en_disco == resultado.content

    def test_dos_generaciones_producen_los_mismos_bytes(self, workspace_con_catalogo: Path) -> None:
        """El reporte es salida persistida: la promesa byte a byte lo cubre."""
        primero = generate_report("inventory", _peticion(workspace_con_catalogo))
        segundo = generate_report("inventory", _peticion(workspace_con_catalogo))
        assert primero.content == segundo.content
        assert filesystem.read_bytes(primero.written_to) == filesystem.read_bytes(
            segundo.written_to
        )

    def test_el_formato_texto_trae_lo_mismo_sin_tabla(self, workspace_con_catalogo: Path) -> None:
        resultado = generate_report("inventory", _peticion(workspace_con_catalogo, "texto"))
        assert resultado.written_to.suffix == ".txt"
        assert "vertical.jpg" in resultado.content
        assert "|" not in resultado.content.split("INVENTARIO")[1].splitlines()[0]


class TestEntradasInvalidas:
    def test_sin_catalogo_dice_que_falta_la_ingesta(self, tmp_path: Path) -> None:
        with pytest.raises(InvalidInputError, match="catálogo"):
            generate_report("inventory", _peticion(tmp_path / "vacio"))

    def test_un_reporte_sin_generador_falla_con_claridad(
        self, workspace_con_catalogo: Path
    ) -> None:
        with pytest.raises(InvalidInputError, match="no está disponible"):
            generate_report("analysis", _peticion(workspace_con_catalogo))

    def test_el_formato_jsonl_no_aplica_al_inventario(self, workspace_con_catalogo: Path) -> None:
        with pytest.raises(InvalidInputError, match="jsonl"):
            generate_report("inventory", _peticion(workspace_con_catalogo, "jsonl"))


class TestDisponibilidadDerivada:
    def test_la_disponibilidad_del_registro_sale_de_los_generadores(self) -> None:
        for reporte in REPORTS:
            assert reporte.available == (reporte.name in available_reports())

    def test_inventory_esta_disponible_y_el_resto_todavia_no(self) -> None:
        entrada = find_report("inventory")
        assert entrada is not None
        assert entrada.available is True
        assert available_reports() == frozenset({"inventory"})


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_un_catalogo_vacio_produce_un_reporte_valido(self, tmp_path: Path) -> None:
        lote = tmp_path / "lote"
        lote.mkdir()
        salidas = tmp_path / "salidas"
        execute_stage("ingest", StageRequest(workspace=salidas, profile="h", source=lote))

        resultado = generate_report("inventory", _peticion(salidas))

        assert "Aceptados: **0**" in resultado.content
        assert isinstance(resultado, ReportResult)

    def test_el_reporte_no_contiene_fecha_ni_hora(self, workspace_con_catalogo: Path) -> None:
        """Un timestamp rompería la comparación byte a byte entre corridas."""
        contenido = generate_report("inventory", _peticion(workspace_con_catalogo)).content
        assert "2026" not in contenido
