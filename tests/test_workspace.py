"""Pruebas del directorio de trabajo: layout, nombres seguros y originales intactos.

En simple: verifican que el programa crea su carpeta de salidas, que convierte
cualquier nombre de entrada en uno que Windows sí puede abrir después, que dos
fotos cuyos nombres solo difieren en mayúsculas no se pisan, y que después de
todo eso las fotos originales siguen byte a byte iguales.
"""

import sys
from pathlib import Path

import pytest

from media_optimizer.ingest import compute_content_hash, filesystem
from media_optimizer.testing import encode_jpeg, flat_image
from media_optimizer.workspace import (
    REPORTS_DIRNAME,
    Workspace,
    find_modified_sources,
    fingerprint_sources,
    safe_output_name,
)

_FOTO = encode_jpeg(flat_image(32, 32, 120))


class TestLayout:
    def test_crea_la_carpeta_de_trabajo_y_la_de_reportes(self, tmp_path: Path) -> None:
        espacio = Workspace(root=tmp_path / "trabajo")
        espacio.ensure()
        assert filesystem.is_directory(espacio.root)
        assert filesystem.is_directory(espacio.reports_dir)
        assert espacio.reports_dir.name == REPORTS_DIRNAME

    def test_ejecutarlo_dos_veces_no_cambia_nada(self, tmp_path: Path) -> None:
        espacio = Workspace(root=tmp_path / "trabajo")
        espacio.ensure()
        espacio.ensure()
        assert filesystem.is_directory(espacio.reports_dir)


class TestNombresEscribibles:
    @pytest.mark.parametrize(
        "entrada",
        ["foto.jpg.", "foto.jpg ", "fo<to>.jpg", 'fo"to".jpg', "fo|to?.jpg", "foto\x00.jpg"],
    )
    def test_un_nombre_problematico_queda_escribible_y_releible(
        self, tmp_path: Path, entrada: str
    ) -> None:
        seguro = safe_output_name(entrada)
        destino = tmp_path / seguro
        filesystem.write_bytes(destino, _FOTO)
        assert destino.read_bytes() == _FOTO

    @pytest.mark.parametrize("entrada", ["CON.jpg", "NUL.jpg", "COM1.jpg", "PRN", "con.JPG"])
    @pytest.mark.skipif(sys.platform != "win32", reason="dispositivos de Windows")
    def test_los_nombres_de_dispositivo_se_sanean(self, tmp_path: Path, entrada: str) -> None:
        seguro = safe_output_name(entrada)
        assert seguro != entrada
        destino = tmp_path / seguro
        filesystem.write_bytes(destino, _FOTO)
        assert destino.read_bytes() == _FOTO

    def test_un_nombre_que_queda_vacio_recibe_un_marcador(self) -> None:
        assert safe_output_name("...") == "sin_nombre"
        assert safe_output_name("   ") == "sin_nombre"

    def test_un_nombre_corriente_no_se_toca(self) -> None:
        assert safe_output_name("IMG_20260716.jpg") == "IMG_20260716.jpg"


class TestColisiones:
    def test_dos_nombres_que_solo_difieren_en_mayusculas_no_se_pisan(self) -> None:
        """En NTFS el segundo sobrescribiría al primero en silencio."""
        primero = safe_output_name("Foto.jpg")
        segundo = safe_output_name("foto.jpg", taken=frozenset({primero}))
        assert primero.casefold() != segundo.casefold()

    def test_varias_colisiones_seguidas_se_numeran(self) -> None:
        usados: set[str] = set()
        for _ in range(3):
            usados.add(safe_output_name("foto.jpg", taken=frozenset(usados)))
        assert usados == {"foto.jpg", "foto_2.jpg", "foto_3.jpg"}

    def test_un_nombre_sin_extension_tambien_se_desambigua(self) -> None:
        assert safe_output_name("informe", taken=frozenset({"informe"})) == "informe_2"

    def test_la_desambiguacion_se_aplica_despues_de_sanear(self) -> None:
        """Dos nombres distintos que se sanean igual no pueden colapsar en uno."""
        primero = safe_output_name("fo<to.jpg")
        segundo = safe_output_name("fo>to.jpg", taken=frozenset({primero}))
        assert primero != segundo


class TestDeterminismo:
    def test_el_mismo_nombre_produce_siempre_el_mismo_resultado(self) -> None:
        assert safe_output_name("fo<to>.jpg.") == safe_output_name("fo<to>.jpg.")

    def test_con_los_mismos_ocupados_el_resultado_es_estable(self) -> None:
        ocupados = frozenset({"foto.jpg", "foto_2.jpg"})
        assert safe_output_name("foto.jpg", ocupados) == safe_output_name("foto.jpg", ocupados)


class TestOriginalesIntactos:
    def test_tras_crear_el_espacio_y_escribir_salidas_los_origenes_no_cambian(
        self, tmp_path: Path
    ) -> None:
        origen = tmp_path / "originales"
        filesystem.make_directory(origen)
        fotos = tuple(origen / f"foto{i}.jpg" for i in range(3))
        for foto in fotos:
            filesystem.write_bytes(foto, _FOTO)

        huella = fingerprint_sources(fotos)
        espacio = Workspace(root=tmp_path / "trabajo")
        espacio.ensure()
        filesystem.write_bytes(espacio.reports_dir / "inventario.md", b"# reporte")

        assert find_modified_sources(huella) == ()

    def test_si_un_origen_cambia_se_detecta_y_se_nombra(self, tmp_path: Path) -> None:
        foto = tmp_path / "foto.jpg"
        filesystem.write_bytes(foto, _FOTO)
        huella = fingerprint_sources((foto,))

        filesystem.write_bytes(foto, _FOTO + b"alterado")

        assert find_modified_sources(huella) == (str(foto),)

    def test_la_huella_usa_el_contenido_no_la_fecha(self, tmp_path: Path) -> None:
        foto = tmp_path / "foto.jpg"
        filesystem.write_bytes(foto, _FOTO)
        huella = fingerprint_sources((foto,))
        foto.touch()  # cambia mtime, no el contenido
        assert find_modified_sources(huella) == ()


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_un_nombre_larguisimo_se_recorta(self) -> None:
        seguro = safe_output_name("x" * 400 + ".jpg")
        assert len(seguro) <= 200

    def test_la_huella_esta_ordenada_para_ser_determinista(self, tmp_path: Path) -> None:
        rutas = tuple(tmp_path / f"{letra}.jpg" for letra in "zab")
        for ruta in rutas:
            filesystem.write_bytes(ruta, _FOTO)
        huella = fingerprint_sources(rutas)
        assert [r for r, _ in huella.hashes] == sorted(r for r, _ in huella.hashes)

    def test_la_huella_guarda_el_hash_de_contenido(self, tmp_path: Path) -> None:
        foto = tmp_path / "foto.jpg"
        filesystem.write_bytes(foto, _FOTO)
        ((_, guardado),) = fingerprint_sources((foto,)).hashes
        assert guardado == compute_content_hash(foto)

    def test_el_espacio_de_trabajo_es_inmutable(self, tmp_path: Path) -> None:
        with pytest.raises(AttributeError):
            Workspace(root=tmp_path).root = tmp_path  # type: ignore[misc]
