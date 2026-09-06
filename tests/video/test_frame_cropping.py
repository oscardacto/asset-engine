"""Pruebas del encuadre vertical aplicado a clips reales.

En simple: comprueban que el comando de recorte lleva las coordenadas exactas que
la aritmética calculó, que las rutas se entregan en la forma que la herramienta
sí abre, que el desplazamiento pedido nunca se sale del cuadro, y que el archivo
original queda byte a byte igual después de encuadrarlo.

El comando se verifica **sin ejecutar nada**: ahí es donde viven los errores de
encuadre, y comprobarlos cuesta milisegundos en vez de un renderizado.
"""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from media_optimizer.core import CorruptMediaError
from media_optimizer.ingest import filesystem
from media_optimizer.video import (
    ALTO_VERTICAL,
    ANCHO_VERTICAL,
    build_crop_command,
    crop_to_vertical,
    frame_to_vertical,
    is_available,
    read_dimensions,
)

_SIN_BINARIO = not is_available()
_RUTA_LARGA = ("w" * 40,) * 8


def _clip(destino: Path, ancho: int, alto: int, segundos: int = 2) -> None:
    """Genera un clip sintético de las medidas pedidas."""
    binario = filesystem.find_executable("ffmpeg")
    assert binario is not None
    filesystem.make_directory(destino.parent)
    subprocess.run(  # noqa: S603 - ruta absoluta, lista de argumentos, sin shell
        [
            binario,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=s={ancho}x{alto}:d={segundos}:r=15",
            "-pix_fmt",
            "yuv420p",
            filesystem.system_path(destino),
        ],
        capture_output=True,
        check=True,
        timeout=120,
    )


class TestComandoDeRecorte:
    """Se verifica sin ejecutar: ahí viven los errores de encuadre."""

    def test_el_filtro_lleva_las_coordenadas_calculadas(self, tmp_path: Path) -> None:
        encuadre = frame_to_vertical(1920, 1080)
        comando = build_crop_command(tmp_path / "e.mp4", encuadre, tmp_path / "s.mp4")

        grafo = comando[comando.index("-filter_complex") + 1]
        assert "crop=1080:1920:1167:0" in grafo
        assert "scale=3414:1920" in grafo

    def test_reinicia_las_marcas_de_tiempo_antes_de_todo(self, tmp_path: Path) -> None:
        comando = build_crop_command(
            tmp_path / "e.mp4", frame_to_vertical(1920, 1080), tmp_path / "s.mp4"
        )
        grafo = comando[comando.index("-filter_complex") + 1]
        assert grafo.index("setpts=PTS-STARTPTS") < grafo.index("scale=")

    def test_las_rutas_se_entregan_adaptadas(self, tmp_path: Path) -> None:
        """La herramienta abre los archivos por su cuenta; no adapta la ruta sola."""
        entrada, salida = tmp_path / "clip.mp4", tmp_path / "vertical.mp4"
        comando = build_crop_command(entrada, frame_to_vertical(1920, 1080), salida)

        assert filesystem.system_path(entrada) in comando
        assert filesystem.system_path(salida) in comando

    def test_lleva_las_banderas_de_reproducibilidad(self, tmp_path: Path) -> None:
        comando = build_crop_command(
            tmp_path / "e.mp4", frame_to_vertical(1920, 1080), tmp_path / "s.mp4"
        )
        assert "-filter_complex_threads" in comando
        assert comando[comando.index("-filter_complex_threads") + 1] == "1"
        assert comando[comando.index("-map_metadata") + 1] == "-1"

    def test_es_determinista(self, tmp_path: Path) -> None:
        encuadre = frame_to_vertical(3840, 2160)
        primero = build_crop_command(tmp_path / "e.mp4", encuadre, tmp_path / "s.mp4")
        segundo = build_crop_command(tmp_path / "e.mp4", encuadre, tmp_path / "s.mp4")
        assert primero == segundo


class TestDesplazamiento:
    def test_por_defecto_el_recorte_sale_del_centro(self) -> None:
        encuadre = frame_to_vertical(1920, 1080)
        sobrante = encuadre.scaled_width - ANCHO_VERTICAL
        assert encuadre.crop.x == sobrante // 2

    def test_un_desplazamiento_mueve_el_encuadre(self, tmp_path: Path) -> None:
        base = frame_to_vertical(1920, 1080)
        movido = build_crop_command(tmp_path / "e.mp4", base, tmp_path / "s.mp4", offset_x=200)
        grafo = movido[movido.index("-filter_complex") + 1]
        assert f"crop=1080:1920:{base.crop.x + 200}:0" in grafo

    def test_un_desplazamiento_negativo_mueve_al_otro_lado(self, tmp_path: Path) -> None:
        base = frame_to_vertical(1920, 1080)
        movido = build_crop_command(tmp_path / "e.mp4", base, tmp_path / "s.mp4", offset_x=-200)
        grafo = movido[movido.index("-filter_complex") + 1]
        assert f"crop=1080:1920:{base.crop.x - 200}:0" in grafo

    def test_un_desplazamiento_excesivo_se_acota_al_margen(self, tmp_path: Path) -> None:
        """Salirse del cuadro rompería el lote a la mitad; se acota en vez de fallar."""
        base = frame_to_vertical(1920, 1080)
        margen = base.scaled_width - ANCHO_VERTICAL

        comando = build_crop_command(tmp_path / "e.mp4", base, tmp_path / "s.mp4", offset_x=99_999)

        grafo = comando[comando.index("-filter_complex") + 1]
        assert f"crop=1080:1920:{margen}:0" in grafo

    def test_un_desplazamiento_negativo_excesivo_se_acota_a_cero(self, tmp_path: Path) -> None:
        comando = build_crop_command(
            tmp_path / "e.mp4",
            frame_to_vertical(1920, 1080),
            tmp_path / "s.mp4",
            offset_x=-99_999,
        )
        grafo = comando[comando.index("-filter_complex") + 1]
        assert "crop=1080:1920:0:0" in grafo

    def test_un_clip_ya_vertical_no_tiene_margen_que_desplazar(self, tmp_path: Path) -> None:
        comando = build_crop_command(
            tmp_path / "e.mp4",
            frame_to_vertical(1080, 1920),
            tmp_path / "s.mp4",
            offset_x=500,
        )
        grafo = comando[comando.index("-filter_complex") + 1]
        assert "crop=1080:1920:0:0" in grafo


@pytest.mark.skipif(_SIN_BINARIO, reason="el binario de video no está instalado")
class TestSobreClipsReales:
    def test_lee_las_dimensiones_del_clip(self, tmp_path: Path) -> None:
        clip = tmp_path / "medido.mp4"
        _clip(clip, 640, 480)
        assert read_dimensions(clip) == (640, 480)

    def test_la_salida_mide_exactamente_el_formato_vertical(self, tmp_path: Path) -> None:
        origen, destino = tmp_path / "apaisado.mp4", tmp_path / "vertical.mp4"
        _clip(origen, 640, 360)

        crop_to_vertical(origen, destino)

        assert read_dimensions(destino) == (ANCHO_VERTICAL, ALTO_VERTICAL)

    def test_el_original_queda_intacto(self, tmp_path: Path) -> None:
        origen, destino = tmp_path / "original.mp4", tmp_path / "vertical.mp4"
        _clip(origen, 640, 360)
        antes = filesystem.read_bytes(origen)

        crop_to_vertical(origen, destino)

        assert filesystem.read_bytes(origen) == antes

    def test_devuelve_el_encuadre_que_aplico(self, tmp_path: Path) -> None:
        """Quien llama necesita saber qué se recortó para poder explicarlo."""
        origen, destino = tmp_path / "o.mp4", tmp_path / "v.mp4"
        _clip(origen, 640, 360)

        encuadre = crop_to_vertical(origen, destino)

        assert encuadre.crop.width == ANCHO_VERTICAL
        assert encuadre.crops_width is True

    def test_un_clip_ya_vertical_se_conserva(self, tmp_path: Path) -> None:
        origen, destino = tmp_path / "vert.mp4", tmp_path / "salida.mp4"
        _clip(origen, 360, 640)

        encuadre = crop_to_vertical(origen, destino)

        assert encuadre.crops_width is False
        assert read_dimensions(destino) == (ANCHO_VERTICAL, ALTO_VERTICAL)

    def test_funciona_con_una_ruta_larga(self, tmp_path: Path) -> None:
        origen = tmp_path.joinpath(*_RUTA_LARGA) / "largo.mp4"
        destino = tmp_path / "salida.mp4"
        _clip(origen, 640, 360)
        assert len(str(origen)) > 260

        crop_to_vertical(origen, destino)

        assert read_dimensions(destino) == (ANCHO_VERTICAL, ALTO_VERTICAL)

    def test_es_determinista_byte_a_byte(self, tmp_path: Path) -> None:
        origen = tmp_path / "o.mp4"
        _clip(origen, 640, 360)
        primero, segundo = tmp_path / "a.mp4", tmp_path / "b.mp4"

        crop_to_vertical(origen, primero)
        crop_to_vertical(origen, segundo)

        assert filesystem.read_bytes(primero) == filesystem.read_bytes(segundo)


@pytest.mark.skipif(_SIN_BINARIO, reason="el binario de video no está instalado")
class TestDegradacion:
    def test_un_clip_ilegible_aparta_ese_clip(self, tmp_path: Path) -> None:
        roto = tmp_path / "roto.mp4"
        filesystem.write_bytes(roto, b"esto no es un video")

        with pytest.raises(CorruptMediaError):
            read_dimensions(roto)

    def test_un_clip_inexistente_aparta_ese_clip(self, tmp_path: Path) -> None:
        with pytest.raises(CorruptMediaError):
            read_dimensions(tmp_path / "no_existe.mp4")

    def test_encuadrar_un_clip_ilegible_aparta_ese_clip(self, tmp_path: Path) -> None:
        roto = tmp_path / "roto.mp4"
        filesystem.write_bytes(roto, b"nada de video")

        with pytest.raises(CorruptMediaError):
            crop_to_vertical(roto, tmp_path / "salida.mp4")


class TestClipQueAbrePeroNoMide:
    def test_un_clip_sin_medidas_validas_aparta_ese_clip(self, tmp_path: Path) -> None:
        """Un contenedor puede abrirse y aun así no declarar dimensiones."""

        class _CapturaMuda:
            def isOpened(self) -> bool:  # noqa: N802 - la firma la fija la librería
                return True

            def get(self, _propiedad: int) -> float:
                return 0.0

            def release(self) -> None:
                return None

        with (
            patch("cv2.VideoCapture", return_value=_CapturaMuda()),
            pytest.raises(CorruptMediaError, match="medidas válidas"),
        ):
            read_dimensions(tmp_path / "mudo.mp4")


@pytest.mark.skipif(_SIN_BINARIO, reason="el binario de video no está instalado")
class TestHerramientaQueRechaza:
    def test_si_la_herramienta_rechaza_el_encuadre_se_aparta_ese_clip(self, tmp_path: Path) -> None:
        """El clip se lee bien, pero el destino pedido no se puede escribir."""
        origen = tmp_path / "valido.mp4"
        _clip(origen, 320, 240)

        with pytest.raises(CorruptMediaError):
            crop_to_vertical(origen, tmp_path / "salida.formato_inexistente")
