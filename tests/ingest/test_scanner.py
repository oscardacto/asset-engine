"""Pruebas del escaneo de carpeta: orden estable, qué se incluye y qué se rechaza.

En simple: comprueban que escanear la misma carpeta dos veces da exactamente la
misma lista, que no se cuela nada que no deba (ocultos, carpetas) ni se pierde
nada que sí (archivos sin extensión, subcarpetas), y que los originales quedan
intactos.
"""

from pathlib import Path

import pytest

from media_optimizer.core import InvalidInputError
from media_optimizer.ingest import scan_input_folder
from media_optimizer.testing import flat_image, write_jpeg


def _poblar(carpeta: Path, *nombres: str) -> None:
    for nombre in nombres:
        destino = carpeta / nombre
        destino.parent.mkdir(parents=True, exist_ok=True)
        write_jpeg(destino, flat_image(16, 16, 120))


def _nombres(rutas: tuple[Path, ...], raiz: Path) -> list[str]:
    return [ruta.relative_to(raiz).as_posix() for ruta in rutas]


class TestOrdenDeterminista:
    def test_el_orden_no_depende_del_orden_de_creacion(self, tmp_path: Path) -> None:
        _poblar(tmp_path, "c.jpg", "a.jpg", "b.jpg")
        assert _nombres(scan_input_folder(tmp_path), tmp_path) == ["a.jpg", "b.jpg", "c.jpg"]

    def test_dos_escaneos_devuelven_exactamente_lo_mismo(self, tmp_path: Path) -> None:
        _poblar(tmp_path, "z.jpg", "sesion/m.jpg", "a.jpg")
        assert scan_input_folder(tmp_path) == scan_input_folder(tmp_path)


class TestRecursividad:
    def test_por_defecto_recorre_subcarpetas(self, tmp_path: Path) -> None:
        _poblar(tmp_path, "foto1.jpg", "sesion/foto2.jpg")
        assert _nombres(scan_input_folder(tmp_path), tmp_path) == ["foto1.jpg", "sesion/foto2.jpg"]

    def test_sin_recursion_solo_el_nivel_superior(self, tmp_path: Path) -> None:
        _poblar(tmp_path, "foto1.jpg", "sesion/foto2.jpg")
        resultado = scan_input_folder(tmp_path, recursive=False)
        assert _nombres(resultado, tmp_path) == ["foto1.jpg"]


class TestQueSeIncluye:
    def test_no_filtra_por_extension(self, tmp_path: Path) -> None:
        _poblar(tmp_path, "foto.jpg")
        (tmp_path / "documento.txt").write_text("texto", encoding="utf-8")
        (tmp_path / "sin_extension").write_bytes(b"datos")
        assert _nombres(scan_input_folder(tmp_path), tmp_path) == [
            "documento.txt",
            "foto.jpg",
            "sin_extension",
        ]

    def test_omite_directorios_y_entradas_ocultas(self, tmp_path: Path) -> None:
        _poblar(tmp_path, "visible.jpg", ".oculta.jpg", ".cache/interna.jpg")
        (tmp_path / "subcarpeta_vacia").mkdir()
        assert _nombres(scan_input_folder(tmp_path), tmp_path) == ["visible.jpg"]

    def test_carpeta_vacia_es_un_lote_legitimo(self, tmp_path: Path) -> None:
        assert scan_input_folder(tmp_path) == ()


class TestEntradasInvalidas:
    def test_carpeta_inexistente_falla_con_mensaje_accionable(self, tmp_path: Path) -> None:
        with pytest.raises(InvalidInputError, match="no existe"):
            scan_input_folder(tmp_path / "fantasma")

    def test_una_ruta_de_archivo_no_es_carpeta_de_entrada(self, tmp_path: Path) -> None:
        _poblar(tmp_path, "foto.jpg")
        with pytest.raises(InvalidInputError, match="no es una carpeta"):
            scan_input_folder(tmp_path / "foto.jpg")


class TestEstabilidadDeNombres:
    def test_los_acentos_no_alteran_el_orden_entre_ejecuciones(self, tmp_path: Path) -> None:
        _poblar(tmp_path, "camion.jpg", "camión.jpg", "cama.jpg")
        primero = scan_input_folder(tmp_path)
        assert primero == scan_input_folder(tmp_path)
        assert _nombres(primero, tmp_path)[0] == "cama.jpg"

    def test_el_orden_ignora_mayusculas(self, tmp_path: Path) -> None:
        _poblar(tmp_path, "Bravo.jpg", "alfa.jpg")
        assert _nombres(scan_input_folder(tmp_path), tmp_path) == ["alfa.jpg", "Bravo.jpg"]


class TestNoDestructivo:
    def test_escanear_no_altera_los_archivos(self, tmp_path: Path) -> None:
        _poblar(tmp_path, "foto.jpg", "sesion/otra.jpg")
        antes = {
            ruta: (ruta.read_bytes(), ruta.stat().st_mtime_ns)
            for ruta in (tmp_path / "foto.jpg", tmp_path / "sesion" / "otra.jpg")
        }
        scan_input_folder(tmp_path)
        for ruta, (contenido, mtime) in antes.items():
            assert ruta.read_bytes() == contenido
            assert ruta.stat().st_mtime_ns == mtime


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_devuelve_rutas_absolutas_utilizables(self, tmp_path: Path) -> None:
        _poblar(tmp_path, "sesion/foto.jpg")
        (encontrada,) = scan_input_folder(tmp_path)
        assert encontrada.is_file()
        assert encontrada.name == "foto.jpg"

    def test_anidamiento_profundo_se_recorre_completo(self, tmp_path: Path) -> None:
        _poblar(tmp_path, "a/b/c/d/honda.jpg")
        assert _nombres(scan_input_folder(tmp_path), tmp_path) == ["a/b/c/d/honda.jpg"]

    def test_el_resultado_es_inmutable(self, tmp_path: Path) -> None:
        _poblar(tmp_path, "foto.jpg")
        assert isinstance(scan_input_folder(tmp_path), tuple)
