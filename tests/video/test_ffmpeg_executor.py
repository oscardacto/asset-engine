"""Pruebas del ejecutor de video: qué se le pide a la herramienta y qué se hace con su respuesta.

En simple: comprueban que las banderas que hacen reproducible el resultado están
siempre puestas —aunque quien llame se olvide—, que las rutas se traducen a la
forma que el sistema necesita, y que si la herramienta falla el lote continúa en
vez de caerse. Las pruebas de comando no ejecutan nada: comparan lo que se iba a
pedir. Solo la prueba de integración invoca el binario, y únicamente si existe.
"""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from media_optimizer.core import CorruptMediaError
from media_optimizer.ingest import filesystem
from media_optimizer.video import (
    NORMALIZAR_TIEMPOS_AUDIO,
    NORMALIZAR_TIEMPOS_VIDEO,
    FfmpegResult,
    build_command,
    build_probe_command,
    degrade,
    is_available,
    normalized_segment,
    probe_filtergraph,
    run,
)

_GRAFO = "[0:v]setpts=PTS-STARTPTS,scale=1080:1920[outv]"
_SIN_FFMPEG = not is_available()


def _completado(codigo: int, error: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["ffmpeg"], returncode=codigo, stdout="", stderr=error)


class TestBanderasDeReproducibilidad:
    """No son opcionales: van aunque quien llame no las escriba."""

    def test_el_grafo_nunca_se_reparte_entre_hilos(self, tmp_path: Path) -> None:
        comando = build_command([tmp_path / "a.mp4"], _GRAFO, tmp_path / "out.mp4")
        assert "-filter_complex_threads" in comando
        assert comando[comando.index("-filter_complex_threads") + 1] == "1"

    def test_no_se_queda_esperando_el_teclado(self, tmp_path: Path) -> None:
        assert "-nostdin" in build_command([tmp_path / "a.mp4"], _GRAFO, tmp_path / "o.mp4")

    def test_la_salida_nace_sin_metadatos_del_original(self, tmp_path: Path) -> None:
        comando = build_command([tmp_path / "a.mp4"], _GRAFO, tmp_path / "o.mp4")
        assert comando[comando.index("-map_metadata") + 1] == "-1"

    def test_la_prueba_silenciosa_tambien_lleva_las_banderas(self) -> None:
        comando = build_probe_command(_GRAFO)
        assert "-filter_complex_threads" in comando
        assert "-nostdin" in comando


class TestNormalizacionDeTiempos:
    def test_el_reinicio_va_primero_y_siempre(self) -> None:
        cadena = normalized_segment(["scale=1080:1920", "crop=1080:1920"])
        assert cadena.startswith(NORMALIZAR_TIEMPOS_VIDEO)
        assert cadena == f"{NORMALIZAR_TIEMPOS_VIDEO},scale=1080:1920,crop=1080:1920"

    def test_con_audio_reinicia_las_dos_pistas(self) -> None:
        cadena = normalized_segment(["scale=1080:1920"], con_audio=True)
        assert NORMALIZAR_TIEMPOS_VIDEO in cadena
        assert NORMALIZAR_TIEMPOS_AUDIO in cadena

    def test_un_segmento_sin_filtros_sigue_reiniciando(self) -> None:
        assert normalized_segment([]) == NORMALIZAR_TIEMPOS_VIDEO


class TestRutas:
    def test_las_rutas_se_traducen_antes_de_entregarlas(self, tmp_path: Path) -> None:
        """La herramienta abre los archivos por su cuenta; no aplicaría la traducción sola."""
        entrada, salida = tmp_path / "clip.mp4", tmp_path / "reel.mp4"
        comando = build_command([entrada], _GRAFO, salida)

        assert filesystem.system_path(entrada) in comando
        assert filesystem.system_path(salida) in comando
        assert str(entrada) not in comando or filesystem.system_path(entrada) == str(entrada)

    def test_varias_entradas_conservan_su_orden(self, tmp_path: Path) -> None:
        entradas = [tmp_path / "a.mp4", tmp_path / "b.mp4", tmp_path / "c.mp4"]
        comando = build_command(entradas, _GRAFO, tmp_path / "o.mp4")
        posiciones = [i for i, arg in enumerate(comando) if arg == "-i"]
        assert len(posiciones) == 3
        assert posiciones == sorted(posiciones)

    def test_la_prueba_silenciosa_no_escribe_ningun_archivo(self, tmp_path: Path) -> None:
        comando = build_probe_command(_GRAFO)
        assert comando[-3:] == ("-f", "null", "-")
        assert not list(tmp_path.iterdir())


class TestManejoDeFallos:
    def test_un_fallo_no_lanza_excepcion(self) -> None:
        """El lote continúa: quien llama decide si aparta ese clip."""
        with patch("subprocess.run", return_value=_completado(1, "Invalid argument\n")):
            resultado = run(["ffmpeg", "-i", "x.mp4"])
        assert resultado.ok is False
        assert "Invalid argument" in resultado.stderr

    def test_la_causa_es_la_ultima_linea_del_error(self) -> None:
        with patch("subprocess.run", return_value=_completado(1, "linea 1\nlinea 2\nla causa\n")):
            assert run(["ffmpeg"]).failure_reason == "la causa"

    def test_un_error_vacio_igual_da_una_explicacion(self) -> None:
        with patch("subprocess.run", return_value=_completado(1, "")):
            assert run(["ffmpeg"]).failure_reason

    def test_si_la_herramienta_no_esta_instalada_lo_dice(self) -> None:
        with patch("subprocess.run", side_effect=FileNotFoundError):
            resultado = run(["ffmpeg"])
        assert resultado.ok is False
        assert "no está instalada" in resultado.stderr

    def test_un_proceso_colgado_se_corta(self) -> None:
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ffmpeg", 900)):
            resultado = run(["ffmpeg"])
        assert resultado.ok is False
        assert "límite" in resultado.stderr

    def test_el_exito_se_reporta_como_tal(self) -> None:
        with patch("subprocess.run", return_value=_completado(0)):
            assert run(["ffmpeg"]).ok is True

    def test_degradar_produce_el_error_que_aparta_ese_clip(self) -> None:
        fallo = FfmpegResult(ok=False, stderr="codec no soportado", command=("ffmpeg",))
        error = degrade(Path("clip.mp4"), fallo)
        assert isinstance(error, CorruptMediaError)
        assert "codec no soportado" in str(error)


class TestValidacionSilenciosa:
    def test_valida_el_grafo_sin_renderizar(self) -> None:
        with patch("subprocess.run", return_value=_completado(0)) as invocacion:
            assert probe_filtergraph(_GRAFO).ok is True
        pedido = invocacion.call_args[0][0]
        assert "null" in pedido
        assert "lavfi" in pedido


@pytest.mark.skipif(_SIN_FFMPEG, reason="el binario de video no está instalado")
class TestIntegracionConElBinarioReal:
    """Solo corre si la herramienta existe. Es lo que valida el ADR de verdad."""

    def test_un_grafo_valido_pasa_la_prueba_silenciosa(self) -> None:
        assert probe_filtergraph("[0:v]scale=1080:1920[outv]").ok is True

    def test_un_grafo_invalido_se_rechaza_con_su_causa(self) -> None:
        resultado = probe_filtergraph("[0:v]filtro_que_no_existe=1[outv]")
        assert resultado.ok is False
        assert resultado.failure_reason

    def test_la_herramienta_acepta_la_forma_extendida_de_ruta(self, tmp_path: Path) -> None:
        """La condición que el backlog exige validar antes de adoptar la cadena."""
        destino = tmp_path / "prueba.mp4"
        comando = (
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "nullsrc=s=320x240:r=10",
            "-t",
            "1",
            "-map_metadata",
            "-1",
            filesystem.system_path(destino),
        )
        resultado = run(comando)
        assert resultado.ok, resultado.failure_reason
        assert filesystem.exists(destino)
