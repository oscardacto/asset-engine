"""Pruebas del esqueleto de la línea de comandos.

En simple: comprueban que la herramienta responde a `--version`, que sin comando
enseña la ayuda en vez de un error críptico, que cada código de salida sale cuando
debe, y —lo que más importa a futuro— que los argumentos declarados en el parser y
los campos del contrato de cada comando **no se desincronizan**, porque el
verificador de tipos no puede detectar esa diferencia.
"""

import argparse
import io
from dataclasses import fields, replace
from pathlib import Path

import pytest

from media_optimizer.cli import ExitCode
from media_optimizer.cli import main as cli_main
from media_optimizer.cli.commands import COMMANDS, Command
from media_optimizer.cli.console import Console
from media_optimizer.cli.context import (
    NIVEL_POR_DEFECTO,
    PERFIL_POR_DEFECTO,
    WORKSPACE_POR_DEFECTO,
    parse_context,
)
from media_optimizer.cli.errors import translate
from media_optimizer.cli.main import build_parser, main
from media_optimizer.core.errors import CorruptMediaError, InvalidInputError, MediaOptimizerError
from media_optimizer.ingest import CATALOG_FILENAME, filesystem
from media_optimizer.pipeline import report_names, stage_names
from media_optimizer.testing import encode_jpeg, not_an_image, textured_image

_ACCIONES_INTERNAS = frozenset({"help", "version", "command"})


def _destinos_del_subparser(comando: Command) -> set[str]:
    parser = argparse.ArgumentParser()
    comando.configure(parser)
    return {accion.dest for accion in parser._actions if accion.dest not in _ACCIONES_INTERNAS}


class TestSincroniaEntreParserYContrato:
    """El único riesgo real de usar argparse: el verificador no ve dentro del Namespace."""

    @pytest.mark.parametrize("comando", COMMANDS, ids=lambda c: c.name)
    def test_los_argumentos_declarados_coinciden_con_los_campos_del_contrato(
        self, comando: Command
    ) -> None:
        del_parser = _destinos_del_subparser(comando)
        del_contrato = {campo.name for campo in fields(comando.args_contract)}
        assert del_parser == del_contrato, (
            f"'{comando.name}': el parser declara {sorted(del_parser)} "
            f"y el contrato {sorted(del_contrato)}"
        )

    @pytest.mark.parametrize("comando", COMMANDS, ids=lambda c: c.name)
    def test_la_lista_declarada_de_destinos_tambien_coincide(self, comando: Command) -> None:
        assert set(comando.arg_destinations) == _destinos_del_subparser(comando)


class TestVersionYAyuda:
    def test_version_imprime_y_sale_con_cero(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as salida:
            main(["--version"])
        assert salida.value.code == 0
        assert "media-optimizer" in capsys.readouterr().out

    def test_sin_comando_muestra_la_ayuda_y_no_una_traza(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert main([]) == ExitCode.USAGE
        salida = capsys.readouterr().out
        assert "COMANDO" in salida
        assert "Traceback" not in salida

    def test_un_comando_inexistente_sale_con_error_de_uso(self) -> None:
        with pytest.raises(SystemExit) as salida:
            main(["inventar"])
        assert salida.value.code == ExitCode.USAGE

    @pytest.mark.parametrize("comando", ["run", "report", "label"])
    def test_cada_comando_tiene_su_propia_ayuda(
        self, comando: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit):
            main([comando, "--help"])
        assert capsys.readouterr().out.strip()


class TestContextoGlobal:
    def test_las_opciones_globales_producen_un_contexto_tipado(self) -> None:
        namespace = build_parser().parse_args(
            ["--workspace", "salida_x", "--profile", "bar", "--quiet", "run", "ingest"]
        )
        contexto = parse_context(namespace)

        assert contexto.workspace == Path("salida_x")
        assert contexto.profile == "bar"
        assert contexto.quiet is True

    def test_lo_que_no_se_indica_se_resuelve_al_convertir_no_en_el_parser(self) -> None:
        """El parser deja 'sin indicar' para que un archivo de configuración pueda entrar."""
        namespace = build_parser().parse_args(["run", "ingest"])
        assert namespace.workspace is None
        assert namespace.profile is None

        contexto = parse_context(namespace)
        assert contexto.workspace == WORKSPACE_POR_DEFECTO
        assert contexto.profile == PERFIL_POR_DEFECTO
        assert contexto.log_level == NIVEL_POR_DEFECTO

    def test_el_contexto_no_se_puede_alterar(self) -> None:
        contexto = parse_context(build_parser().parse_args(["run", "ingest"]))
        with pytest.raises(AttributeError):
            contexto.profile = "otro"  # type: ignore[misc]


class TestCodigosDeSalida:
    def test_una_etapa_todavia_no_disponible_sale_con_fallo(self) -> None:
        assert main(["run", "reel"]) == ExitCode.FAILURE

    def test_la_ingesta_sin_carpeta_sale_con_entrada_invalida(self, tmp_path: Path) -> None:
        assert main(["--workspace", str(tmp_path), "run", "ingest"]) == ExitCode.INVALID_INPUT

    def test_pedir_un_reporte_sin_haber_ingerido_sale_con_entrada_invalida(
        self, tmp_path: Path
    ) -> None:
        assert main(["--workspace", str(tmp_path), "report", "inventory"]) == ExitCode.INVALID_INPUT

    def test_el_mensaje_de_entrada_invalida_dice_que_hacer(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        main(["--workspace", str(tmp_path), "report", "inventory"])
        error = capsys.readouterr().err
        assert "run ingest" in error
        assert "Traceback" not in error

    def test_el_etiquetado_todavia_no_esta_disponible(self) -> None:
        assert main(["label"]) == ExitCode.FAILURE


class TestTraduccionDeErrores:
    @pytest.mark.parametrize(
        ("error", "codigo"),
        [
            (InvalidInputError("perfil vacío"), ExitCode.INVALID_INPUT),
            (CorruptMediaError(Path("foto.jpg"), "truncada"), ExitCode.PARTIAL),
            (MediaOptimizerError("algo del dominio"), ExitCode.FAILURE),
        ],
    )
    def test_cada_fallo_esperable_tiene_su_codigo(
        self, error: MediaOptimizerError, codigo: ExitCode
    ) -> None:
        mensaje, obtenido = translate(error)
        assert obtenido is codigo
        assert mensaje

    def test_una_excepcion_inesperada_propaga_su_traza(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Disfrazar un defecto del programa lo escondería entre los avisos del lote."""

        def revienta(
            _namespace: argparse.Namespace, _context: object, _console: Console
        ) -> ExitCode:
            raise RuntimeError("defecto del programa")

        defectuoso = replace(COMMANDS[0], execute=revienta)
        monkeypatch.setattr(cli_main, "find_command", lambda _nombre: defectuoso)

        with pytest.raises(RuntimeError, match="defecto del programa"):
            main(["run", "ingest"])


class TestLaSuperficieSaleDelRegistro:
    def test_las_etapas_validas_son_las_del_registro(self) -> None:
        for etapa in stage_names():
            assert build_parser().parse_args(["run", etapa]).stage == etapa

    def test_los_reportes_validos_son_los_del_registro(self) -> None:
        for tipo in report_names():
            assert build_parser().parse_args(["report", tipo]).kind == tipo

    def test_una_etapa_que_no_esta_en_el_registro_se_rechaza(self) -> None:
        with pytest.raises(SystemExit) as salida:
            main(["run", "inventada"])
        assert salida.value.code == ExitCode.USAGE

    def test_la_ayuda_de_run_enumera_las_etapas_del_registro(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit):
            main(["run", "--help"])
        ayuda = capsys.readouterr().out
        for etapa in stage_names():
            assert etapa in ayuda


class TestLaIngestaDePuntaAPunta:
    """El flujo real del usuario: de la terminal al catálogo, sin atajos."""

    def test_un_lote_limpio_sale_con_cero_y_deja_catalogo(self, tmp_path: Path) -> None:
        lote = tmp_path / "lote"
        lote.mkdir()
        (lote / "foto.jpg").write_bytes(encode_jpeg(textured_image(64, 48, 100, seed=7)))

        codigo = main(["--workspace", str(tmp_path / "salidas"), "run", "ingest", str(lote)])

        assert codigo == ExitCode.OK
        assert filesystem.exists(tmp_path / "salidas" / CATALOG_FILENAME)

    def test_un_lote_con_fotos_rotas_sale_parcial(self, tmp_path: Path) -> None:
        lote = tmp_path / "lote"
        lote.mkdir()
        (lote / "buena.jpg").write_bytes(encode_jpeg(textured_image(64, 48, 100, seed=7)))
        (lote / "rota.jpg").write_bytes(not_an_image())

        codigo = main(["--workspace", str(tmp_path / "salidas"), "run", "ingest", str(lote)])

        assert codigo == ExitCode.PARTIAL

    def test_el_resumen_llega_a_la_consola(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        lote = tmp_path / "lote"
        lote.mkdir()
        (lote / "foto.jpg").write_bytes(encode_jpeg(textured_image(64, 48, 100, seed=7)))

        main(["--workspace", str(tmp_path / "salidas"), "run", "ingest", str(lote)])

        salida = capsys.readouterr().out
        assert "Archivos encontrados: 1" in salida
        assert "Aceptados al catálogo: 1" in salida

    def test_un_reporte_aun_no_disponible_sale_con_fallo_no_con_entrada_invalida(
        self, tmp_path: Path
    ) -> None:
        """Ya hay catálogo: el problema es el reporte, no lo que el usuario escribió."""
        filesystem.write_bytes(tmp_path / CATALOG_FILENAME, b"{}")
        assert main(["--workspace", str(tmp_path), "report", "selection"]) == ExitCode.FAILURE

    def test_el_reporte_de_inventario_llega_a_consola_y_a_disco(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        lote = tmp_path / "lote"
        lote.mkdir()
        (lote / "foto.jpg").write_bytes(encode_jpeg(textured_image(64, 48, 100, seed=7)))
        salidas = tmp_path / "salidas"
        main(["--workspace", str(salidas), "run", "ingest", str(lote)])

        codigo = main(["--workspace", str(salidas), "report", "inventory", "--format", "markdown"])

        assert codigo == ExitCode.OK
        assert "| foto.jpg | 64x48 | horizontal |" in capsys.readouterr().out
        assert filesystem.exists(salidas / "reports" / "inventory.md")


class TestConsola:
    def test_los_avisos_normales_se_escriben(self) -> None:
        salida, errores = io.StringIO(), io.StringIO()
        Console(out=salida, err=errores).say("hola")
        assert salida.getvalue() == "hola\n"

    def test_los_avisos_normales_se_callan_con_quiet(self) -> None:
        salida, errores = io.StringIO(), io.StringIO()
        Console(out=salida, err=errores, quiet=True).say("hola")
        assert salida.getvalue() == ""

    def test_los_fallos_se_escriben_aunque_se_pida_silencio(self) -> None:
        salida, errores = io.StringIO(), io.StringIO()
        Console(out=salida, err=errores, quiet=True).fail("algo falló")
        assert "algo falló" in errores.getvalue()

    def test_los_fallos_van_por_la_salida_de_errores(self) -> None:
        salida, errores = io.StringIO(), io.StringIO()
        Console(out=salida, err=errores).fail("algo falló")
        assert salida.getvalue() == ""


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_el_rastro_a_archivo_funciona_en_una_ruta_larga(self, tmp_path: Path) -> None:
        destino = tmp_path.joinpath(*(("z" * 40,) * 8)) / "run.log"
        assert len(str(destino)) > 260

        main(["--workspace", str(tmp_path), "--log-file", str(destino), "run", "ingest"])

        assert b"carpeta de origen" in filesystem.read_bytes(destino)

    def test_los_tres_comandos_estan_registrados_y_sin_repetir(self) -> None:
        nombres = [comando.name for comando in COMMANDS]
        assert nombres == ["run", "report", "label"]
        assert len(set(nombres)) == len(nombres)

    def test_el_origen_es_opcional_porque_solo_lo_usa_la_ingesta(self) -> None:
        assert build_parser().parse_args(["run", "analyze"]).source is None
        assert build_parser().parse_args(["run", "ingest", "fotos"]).source == Path("fotos")
