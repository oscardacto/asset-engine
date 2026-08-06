"""Pruebas de la capa de acceso al disco y de los casos que antes rompían el pipeline.

En simple: la primera mitad comprueba que la capa traduce las rutas bien y no
deja escapar su forma interna. La segunda convierte en regresión permanente los
casos reales que descubrimos rompiendo el sistema: un archivo llamado como un
dispositivo antiguo, nombres con punto o espacio final, y rutas larguísimas.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from media_optimizer.core import InvalidInputError
from media_optimizer.ingest import filesystem, scan_input_folder, triage_media
from media_optimizer.testing import encode_jpeg, flat_image

_SOLO_WINDOWS = pytest.mark.skipif(sys.platform != "win32", reason="comportamiento de Windows")
_FOTO = encode_jpeg(flat_image(32, 32, 120))


def _crear_crudo(destino: Path, contenido: bytes = _FOTO) -> Path:
    """Crea el archivo saltando la normalización de Windows, para sembrar casos hostiles.

    Los tests pueden usar IO directo (ADR-004): crear un caso hostil exige
    precisamente saltarse la normalización que la capa aplica.
    """
    if sys.platform == "win32":
        crudo = f"\\\\?\\{destino}"
        os.makedirs(f"\\\\?\\{destino.parent}", exist_ok=True)  # noqa: PTH103
    else:
        crudo = str(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
    with open(crudo, "wb") as archivo:  # noqa: PTH123
        archivo.write(contenido)
    return destino


class TestTraduccionDeRutas:
    def test_aplicarla_dos_veces_da_lo_mismo(self, tmp_path: Path) -> None:
        una_vez = filesystem.system_path(tmp_path / "foto.jpg")
        assert filesystem.system_path(Path(una_vez)) == una_vez

    @_SOLO_WINDOWS
    def test_en_windows_la_ruta_queda_en_forma_extendida(self, tmp_path: Path) -> None:
        assert filesystem.system_path(tmp_path / "foto.jpg").startswith("\\\\?\\")

    @pytest.mark.skipif(sys.platform == "win32", reason="comportamiento POSIX")
    def test_fuera_de_windows_la_capa_no_toca_la_ruta(self, tmp_path: Path) -> None:
        ruta = tmp_path / "foto.jpg"
        assert filesystem.system_path(ruta) == str(ruta)

    def test_resuelve_rutas_relativas_y_saltos_de_carpeta(self, tmp_path: Path) -> None:
        enrevesada = tmp_path / "sub" / ".." / "foto.jpg"
        assert ".." not in filesystem.system_path(enrevesada)

    def test_las_rutas_que_devuelve_no_llevan_la_forma_interna(self, tmp_path: Path) -> None:
        _crear_crudo(tmp_path / "a.jpg")
        _crear_crudo(tmp_path / "sub" / "b.jpg")
        for encontrada in filesystem.iter_files(tmp_path):
            assert "\\\\?\\" not in str(encontrada)
            assert "?" not in str(encontrada)


class TestOperacionesBasicas:
    def test_lee_completo_y_por_tramos(self, tmp_path: Path) -> None:
        ruta = _crear_crudo(tmp_path / "foto.jpg")
        assert filesystem.read_bytes(ruta) == _FOTO
        assert filesystem.read_bytes(ruta, 0, 3) == _FOTO[:3]
        assert filesystem.read_bytes(ruta, 3) == _FOTO[3:]

    def test_escribe_y_relee(self, tmp_path: Path) -> None:
        ruta = tmp_path / "nueva.bin"
        filesystem.write_bytes(ruta, b"contenido")
        assert filesystem.read_bytes(ruta) == b"contenido"

    def test_informa_tamano_existencia_y_tipo(self, tmp_path: Path) -> None:
        ruta = _crear_crudo(tmp_path / "foto.jpg")
        assert filesystem.file_size(ruta) == len(_FOTO)
        assert filesystem.exists(ruta)
        assert filesystem.is_file(ruta)
        assert filesystem.is_directory(tmp_path)
        assert not filesystem.exists(tmp_path / "fantasma.jpg")

    def test_el_reemplazo_atomico_deja_el_destino_completo(self, tmp_path: Path) -> None:
        origen = _crear_crudo(tmp_path / "nuevo.bin", b"nuevo")
        destino = _crear_crudo(tmp_path / "viejo.bin", b"viejo")
        filesystem.replace_atomic(origen, destino)
        assert filesystem.read_bytes(destino) == b"nuevo"
        assert not filesystem.exists(origen)

    def test_no_lista_ocultos_ni_entra_en_carpetas_ocultas(self, tmp_path: Path) -> None:
        _crear_crudo(tmp_path / "visible.jpg")
        _crear_crudo(tmp_path / ".oculta.jpg")
        _crear_crudo(tmp_path / ".cache" / "dentro.jpg")
        assert [p.name for p in filesystem.iter_files(tmp_path)] == ["visible.jpg"]

    def test_sin_recursion_solo_el_primer_nivel(self, tmp_path: Path) -> None:
        _crear_crudo(tmp_path / "arriba.jpg")
        _crear_crudo(tmp_path / "sub" / "abajo.jpg")
        encontrados = list(filesystem.iter_files(tmp_path, recursive=False))
        assert [p.name for p in encontrados] == ["arriba.jpg"]


@_SOLO_WINDOWS
class TestRegresionDeLaEvidencia:
    """Los casos reales que rompían el pipeline, convertidos en regresión permanente."""

    def test_un_nombre_de_dispositivo_no_bloquea_el_proceso(self, tmp_path: Path) -> None:
        """`CON.jpg` dejaba el proceso sin retorno. Se prueba aislado y con límite de tiempo:
        si alguien revierte la capa, este test se agota en vez de fallar — esa es la señal."""
        _crear_crudo(tmp_path / "CON.jpg")
        sonda = tmp_path / "sonda.py"
        sonda.write_text(
            "import sys\n"
            "sys.path.insert(0, sys.argv[2])\n"
            "from media_optimizer.ingest import filesystem\n"
            "from pathlib import Path\n"
            "print(len(filesystem.read_bytes(Path(sys.argv[1]))))\n",
            encoding="utf-8",
        )
        raiz_src = str(Path(__file__).resolve().parents[2] / "src")

        proceso = subprocess.run(  # noqa: S603
            [sys.executable, str(sonda), str(tmp_path / "CON.jpg"), raiz_src],
            capture_output=True,
            timeout=15,
            text=True,
            check=False,
        )

        assert proceso.returncode == 0, proceso.stderr
        assert proceso.stdout.strip() == str(len(_FOTO))

    @pytest.mark.parametrize("nombre", ["punto.jpg.", "espacio.jpg ", "COM1.jpg", "NUL.jpg"])
    def test_los_nombres_antes_inaccesibles_se_leen(self, tmp_path: Path, nombre: str) -> None:
        ruta = _crear_crudo(tmp_path / nombre)
        assert filesystem.read_bytes(ruta) == _FOTO

    def test_una_ruta_larguisima_ya_no_desaparece_del_escaneo(self, tmp_path: Path) -> None:
        honda = tmp_path
        for _ in range(12):
            honda = honda / ("x" * 24)
        _crear_crudo(honda / "honda.jpg")

        encontrados = scan_input_folder(tmp_path)

        assert len(str(honda / "honda.jpg")) > 260
        assert any(p.name == "honda.jpg" for p in encontrados)

    def test_un_lote_con_nombres_hostiles_se_procesa_entero(self, tmp_path: Path) -> None:
        for nombre in ("normal.jpg", "CON.jpg", "punto.jpg.", "espacio.jpg "):
            _crear_crudo(tmp_path / nombre)

        resultado = triage_media(scan_input_folder(tmp_path))

        assert len(resultado.accepted) == 4
        assert resultado.quarantined == ()

    def test_el_orden_sigue_siendo_estable_con_nombres_hostiles(self, tmp_path: Path) -> None:
        for nombre in ("CON.jpg", "punto.jpg.", "normal.jpg", "espacio.jpg ", "camión.jpg"):
            _crear_crudo(tmp_path / nombre)
        assert scan_input_folder(tmp_path) == scan_input_folder(tmp_path)


class TestEntradasInvalidas:
    def test_una_carpeta_inexistente_sigue_dando_error_accionable(self, tmp_path: Path) -> None:
        with pytest.raises(InvalidInputError, match="no existe"):
            scan_input_folder(tmp_path / "fantasma")

    def test_una_ruta_de_archivo_sigue_sin_ser_carpeta(self, tmp_path: Path) -> None:
        ruta = _crear_crudo(tmp_path / "foto.jpg")
        with pytest.raises(InvalidInputError, match="no es una carpeta"):
            scan_input_folder(ruta)
