"""Pruebas del hash de contenido y del agrupamiento de copias idénticas.

En simple: comprueban que la firma depende solo del contenido (no del nombre ni
de la carpeta), que es SHA-256 de verdad, que las copias se agrupan y que el
resultado no cambia según el orden en que lleguen los archivos.
"""

import hashlib
from pathlib import Path

import pytest

from media_optimizer.core import CorruptMediaError
from media_optimizer.ingest import (
    HASH_ALGORITHM,
    DuplicateGroup,
    compute_content_hash,
    find_duplicate_groups,
)
from media_optimizer.testing import encode_jpeg, flat_image

_SHA256_DEL_VACIO = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def _escribir(destino: Path, contenido: bytes) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(contenido)
    return destino


def _foto(brillo: int = 120) -> bytes:
    return encode_jpeg(flat_image(32, 32, brillo))


class TestHashDeContenido:
    def test_el_mismo_contenido_da_el_mismo_hash_aunque_cambie_nombre_y_carpeta(
        self, tmp_path: Path
    ) -> None:
        datos = _foto()
        uno = _escribir(tmp_path / "a.jpg", datos)
        otro = _escribir(tmp_path / "sesion" / "copia_de_a.jpg", datos)
        assert compute_content_hash(uno) == compute_content_hash(otro)

    def test_contenido_distinto_da_hash_distinto(self, tmp_path: Path) -> None:
        uno = _escribir(tmp_path / "clara.jpg", _foto(brillo=200))
        otro = _escribir(tmp_path / "oscura.jpg", _foto(brillo=30))
        assert compute_content_hash(uno) != compute_content_hash(otro)

    def test_es_sha256_estandar_segun_vector_conocido(self, tmp_path: Path) -> None:
        assert compute_content_hash(_escribir(tmp_path / "vacio.bin", b"")) == _SHA256_DEL_VACIO

    def test_el_algoritmo_publicado_coincide_con_el_usado(self) -> None:
        assert HASH_ALGORITHM == "sha256"


class TestAgrupamiento:
    def test_agrupa_por_contenido_no_por_nombre(self, tmp_path: Path) -> None:
        datos = _foto()
        original = _escribir(tmp_path / "original.jpg", datos)
        copia = _escribir(tmp_path / "IMG (1).jpg", datos)
        distinta = _escribir(tmp_path / "otra.jpg", _foto(brillo=60))

        (grupo,) = find_duplicate_groups([original, copia, distinta])
        assert set(grupo.paths) == {original, copia}
        assert grupo.content_hash == compute_content_hash(original)

    def test_un_lote_sin_copias_no_produce_grupos(self, tmp_path: Path) -> None:
        rutas = [
            _escribir(tmp_path / f"f{indice}.jpg", _foto(brillo=indice * 40))
            for indice in range(1, 4)
        ]
        assert find_duplicate_groups(rutas) == ()

    def test_el_orden_de_entrada_no_altera_el_resultado(self, tmp_path: Path) -> None:
        primera, segunda = _foto(brillo=100), _foto(brillo=200)
        rutas = [
            _escribir(tmp_path / "a1.jpg", primera),
            _escribir(tmp_path / "b1.jpg", segunda),
            _escribir(tmp_path / "a2.jpg", primera),
            _escribir(tmp_path / "b2.jpg", segunda),
        ]
        assert find_duplicate_groups(rutas) == find_duplicate_groups(reversed(rutas))

    def test_las_rutas_de_cada_grupo_salen_ordenadas(self, tmp_path: Path) -> None:
        datos = _foto()
        zeta = _escribir(tmp_path / "z.jpg", datos)
        alfa = _escribir(tmp_path / "a.jpg", datos)
        (grupo,) = find_duplicate_groups([zeta, alfa])
        assert grupo.paths == (alfa, zeta)


class TestLecturaPorBloques:
    def test_un_archivo_mayor_que_el_bloque_da_el_mismo_hash_que_hashlib(
        self, tmp_path: Path
    ) -> None:
        contenido = b"media-optimizer" * 200_000
        ruta = _escribir(tmp_path / "grande.bin", contenido)
        assert compute_content_hash(ruta) == hashlib.sha256(contenido).hexdigest()


class TestArchivoIlegible:
    def test_una_ruta_inexistente_degrada_con_causa(self, tmp_path: Path) -> None:
        with pytest.raises(CorruptMediaError, match="no se pudo leer") as capturado:
            compute_content_hash(tmp_path / "fantasma.jpg")
        assert capturado.value.source == tmp_path / "fantasma.jpg"


class TestNoDestructivo:
    def test_hashear_no_altera_el_archivo(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path / "foto.jpg", _foto())
        contenido, mtime = ruta.read_bytes(), ruta.stat().st_mtime_ns
        compute_content_hash(ruta)
        assert ruta.read_bytes() == contenido
        assert ruta.stat().st_mtime_ns == mtime


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_dos_archivos_vacios_son_duplicados_entre_si(self, tmp_path: Path) -> None:
        uno = _escribir(tmp_path / "v1.bin", b"")
        otro = _escribir(tmp_path / "v2.bin", b"")
        (grupo,) = find_duplicate_groups([uno, otro])
        assert grupo.content_hash == _SHA256_DEL_VACIO

    def test_tres_copias_caen_en_un_solo_grupo(self, tmp_path: Path) -> None:
        datos = _foto()
        rutas = [_escribir(tmp_path / f"c{i}.jpg", datos) for i in range(3)]
        (grupo,) = find_duplicate_groups(rutas)
        assert len(grupo.paths) == 3

    def test_un_lote_vacio_no_produce_grupos(self) -> None:
        assert find_duplicate_groups([]) == ()

    def test_el_grupo_es_inmutable(self, tmp_path: Path) -> None:
        datos = _foto()
        rutas = [_escribir(tmp_path / f"d{i}.jpg", datos) for i in range(2)]
        (grupo,) = find_duplicate_groups(rutas)
        assert isinstance(grupo, DuplicateGroup)
        with pytest.raises(AttributeError):
            grupo.content_hash = "otro"  # type: ignore[misc]
