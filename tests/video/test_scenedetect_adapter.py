"""Pruebas del detector de escenas — escritas antes que la implementación.

En simple: describen qué debe hacer el detector antes de que exista. Están
marcadas como fallo esperado, así que la batería sigue en verde y el día que
alguien lo implemente estas pruebas avisan de que ya se pueden desmarcar.

Los videos de prueba se generan en el momento con la herramienta externa, así que
no entra ni un medio real al repositorio.
"""

import subprocess
from itertools import pairwise
from pathlib import Path

import pytest

import media_optimizer.core as dominio
from media_optimizer.core import CorruptMediaError, Scene, SceneDetectorPort
from media_optimizer.ingest import filesystem
from media_optimizer.video import is_available
from media_optimizer.video.scenedetect_adapter import UMBRAL_POR_DEFECTO, PySceneDetectAdapter

_SIN_BINARIO = not is_available()
_RUTA_LARGA = ("y" * 40,) * 8

pendiente = pytest.mark.xfail(strict=True, reason="el detector todavía no está implementado")


def _generar_clip(destino: Path, *, con_corte: bool = True) -> None:
    """Crea un clip sintético; con corte, pasa de negro a blanco en mitad."""
    filesystem.make_directory(destino.parent)
    fuentes = ["color=c=black:s=320x240:d=2:r=15"]
    if con_corte:
        fuentes.append("color=c=white:s=320x240:d=2:r=15")
    entradas: list[str] = []
    for fuente in fuentes:
        entradas += ["-f", "lavfi", "-i", fuente]
    grafo = "[0:v][1:v]concat=n=2:v=1[outv]" if con_corte else "[0:v]setpts=PTS-STARTPTS[outv]"
    binario = filesystem.find_executable("ffmpeg")
    assert binario is not None
    subprocess.run(  # noqa: S603 - lista de argumentos, ruta absoluta, sin shell
        [
            binario,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            *entradas,
            "-filter_complex",
            grafo,
            "-map",
            "[outv]",
            "-pix_fmt",
            "yuv420p",
            filesystem.system_path(destino),
        ],
        capture_output=True,
        check=True,
        timeout=120,
    )


class TestContratoDelPuerto:
    """Lo que el dominio espera; se puede comprobar sin implementar nada."""

    def test_el_adaptador_cumple_el_puerto(self) -> None:
        detector: SceneDetectorPort = PySceneDetectAdapter()
        assert callable(detector.detect)

    def test_el_umbral_por_defecto_esta_declarado(self) -> None:
        assert PySceneDetectAdapter().threshold == UMBRAL_POR_DEFECTO

    def test_el_adaptador_es_inmutable(self) -> None:
        with pytest.raises(AttributeError):
            PySceneDetectAdapter().threshold = 1.0  # type: ignore[misc]

    def test_ninguna_estructura_de_la_libreria_sale_del_adaptador(self) -> None:
        """La restricción dura: el dominio no conoce la librería externa."""
        assert "scenedetect" not in str(dominio.__dict__)
        assert not hasattr(Scene, "get_scene_list")


@pytest.mark.skipif(_SIN_BINARIO, reason="el binario de video no está instalado")
class TestDeteccionSobreClipsReales:
    """Rojo a propósito: describen el comportamiento antes de implementarlo."""

    @pendiente
    def test_un_clip_con_un_corte_produce_dos_escenas(self, tmp_path: Path) -> None:
        clip = tmp_path / "con_corte.mp4"
        _generar_clip(clip)

        escenas = PySceneDetectAdapter().detect(clip, threshold=UMBRAL_POR_DEFECTO)

        assert len(escenas) == 2
        assert escenas[0].index == 0
        assert escenas[1].start_seconds == pytest.approx(escenas[0].end_seconds, abs=0.1)

    @pendiente
    def test_un_clip_sin_cortes_produce_una_sola_escena(self, tmp_path: Path) -> None:
        clip = tmp_path / "sin_corte.mp4"
        _generar_clip(clip, con_corte=False)

        assert len(PySceneDetectAdapter().detect(clip, threshold=UMBRAL_POR_DEFECTO)) == 1

    @pendiente
    def test_las_escenas_salen_en_orden_y_sin_solaparse(self, tmp_path: Path) -> None:
        clip = tmp_path / "orden.mp4"
        _generar_clip(clip)

        escenas = PySceneDetectAdapter().detect(clip, threshold=UMBRAL_POR_DEFECTO)

        assert [e.index for e in escenas] == sorted(e.index for e in escenas)
        for anterior, siguiente in pairwise(escenas):
            assert anterior.end_seconds <= siguiente.start_seconds

    @pendiente
    def test_el_mismo_clip_da_siempre_las_mismas_escenas(self, tmp_path: Path) -> None:
        """El pipeline promete la misma salida ante la misma entrada."""
        clip = tmp_path / "determinista.mp4"
        _generar_clip(clip)
        detector = PySceneDetectAdapter()

        assert detector.detect(clip, threshold=UMBRAL_POR_DEFECTO) == detector.detect(
            clip, threshold=UMBRAL_POR_DEFECTO
        )

    @pendiente
    def test_un_umbral_mas_bajo_no_encuentra_menos_cortes(self, tmp_path: Path) -> None:
        clip = tmp_path / "umbral.mp4"
        _generar_clip(clip)
        detector = PySceneDetectAdapter()

        sensible = detector.detect(clip, threshold=5.0)
        conservador = detector.detect(clip, threshold=90.0)
        assert len(sensible) >= len(conservador)

    @pendiente
    def test_funciona_con_una_ruta_larga(self, tmp_path: Path) -> None:
        """Medido: la librería no encuentra el video si la ruta no se adapta."""
        clip = tmp_path.joinpath(*_RUTA_LARGA) / "largo.mp4"
        _generar_clip(clip)
        assert len(str(clip)) > 260

        assert PySceneDetectAdapter().detect(clip, threshold=UMBRAL_POR_DEFECTO)

    @pendiente
    def test_un_clip_ilegible_degrada_ese_asset(self, tmp_path: Path) -> None:
        roto = tmp_path / "roto.mp4"
        filesystem.write_bytes(roto, b"esto no es un video")

        with pytest.raises(CorruptMediaError):
            PySceneDetectAdapter().detect(roto, threshold=UMBRAL_POR_DEFECTO)

    @pendiente
    def test_un_clip_inexistente_degrada_ese_asset(self, tmp_path: Path) -> None:
        with pytest.raises(CorruptMediaError):
            PySceneDetectAdapter().detect(tmp_path / "no_existe.mp4", threshold=UMBRAL_POR_DEFECTO)
