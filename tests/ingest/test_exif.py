"""Pruebas de la lectura de EXIF: tolerancia a metadatos rotos y orientación.

En simple: comprueban que una foto sin metadatos o con metadatos corruptos no
rompe nada, que la orientación y la fecha se leen bien cuando están, y que las
medidas se traducen cuando la cámara estaba girada.
"""

from datetime import datetime
from pathlib import Path

import pytest

from media_optimizer.ingest import (
    ExifData,
    ExifOrientation,
    ImageSize,
    oriented_size,
    read_exif,
    read_exif_from_header,
)
from media_optimizer.testing import encode_jpeg, exif_block, flat_image, jpeg_with_exif

_IMAGEN = flat_image(96, 48, 128)


def _escribir(destino: Path, contenido: bytes) -> Path:
    destino.write_bytes(contenido)
    return destino


class TestExifAusente:
    def test_una_foto_sin_metadatos_no_rompe_nada(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path / "sin_exif.jpg", encode_jpeg(_IMAGEN))
        datos = read_exif(ruta)
        assert datos == ExifData()
        assert not datos.is_present
        assert not datos.is_malformed


class TestOrientacion:
    @pytest.mark.parametrize(
        ("valor", "esperada"),
        [
            (1, ExifOrientation.NORMAL),
            (6, ExifOrientation.ROTATE_90),
            (8, ExifOrientation.ROTATE_270),
        ],
    )
    def test_se_lee_el_valor_declarado(
        self, tmp_path: Path, valor: int, esperada: ExifOrientation
    ) -> None:
        ruta = _escribir(
            tmp_path / f"o{valor}.jpg", jpeg_with_exif(_IMAGEN, exif_block(orientation=valor))
        )
        datos = read_exif(ruta)
        assert datos.orientation is esperada
        assert datos.is_present
        assert not datos.is_malformed

    def test_un_valor_fuera_de_rango_se_ignora_y_marca_incompleto(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path / "rara.jpg", jpeg_with_exif(_IMAGEN, exif_block(orientation=99)))
        datos = read_exif(ruta)
        assert datos.orientation is None
        assert datos.is_malformed


class TestExifMalformado:
    def test_un_bloque_truncado_degrada_sin_lanzar(self, tmp_path: Path) -> None:
        completo = exif_block(orientation=6)
        ruta = _escribir(
            tmp_path / "truncado.jpg", jpeg_with_exif(_IMAGEN, completo[: len(completo) // 2])
        )
        datos = read_exif(ruta)
        assert datos.is_present
        assert datos.is_malformed

    def test_una_cabecera_tiff_invalida_degrada_sin_lanzar(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path / "basura.jpg", jpeg_with_exif(_IMAGEN, b"XX\x00\x00basura"))
        datos = read_exif(ruta)
        assert datos.is_present
        assert datos.is_malformed
        assert datos.orientation is None


class TestFechaDeCaptura:
    def test_se_lee_la_fecha_original(self, tmp_path: Path) -> None:
        ruta = _escribir(
            tmp_path / "fechada.jpg",
            jpeg_with_exif(_IMAGEN, exif_block(captured_at="2026:04:04 15:30:00")),
        )
        datos = read_exif(ruta)
        assert datos.captured_at == datetime(2026, 4, 4, 15, 30, 0)
        assert not datos.is_malformed

    def test_una_fecha_con_formato_invalido_degrada(self, tmp_path: Path) -> None:
        ruta = _escribir(
            tmp_path / "mala_fecha.jpg",
            jpeg_with_exif(_IMAGEN, exif_block(captured_at="no-es-una-fecha!")),
        )
        datos = read_exif(ruta)
        assert datos.captured_at is None
        assert datos.is_malformed


class TestMedidasSegunOrientacion:
    def test_una_camara_girada_intercambia_ancho_y_alto(self) -> None:
        crudas = ImageSize(width=48, height=96)
        assert oriented_size(crudas, ExifOrientation.ROTATE_90) == ImageSize(width=96, height=48)

    @pytest.mark.parametrize(
        "orientacion", [None, ExifOrientation.NORMAL, ExifOrientation.ROTATE_180]
    )
    def test_sin_giro_las_medidas_no_cambian(self, orientacion: ExifOrientation | None) -> None:
        crudas = ImageSize(width=48, height=96)
        assert oriented_size(crudas, orientacion) == crudas


class TestExifHostil:
    def test_un_puntero_fuera_del_bloque_no_lee_fuera_de_rango(self, tmp_path: Path) -> None:
        hostil = b"II\x2a\x00" + (8).to_bytes(4, "little") + (1).to_bytes(2, "little")
        hostil += (0x8769).to_bytes(2, "little") + b"\x04\x00" + (1).to_bytes(4, "little")
        hostil += (999_999).to_bytes(4, "little") + b"\x00\x00\x00\x00"
        ruta = _escribir(tmp_path / "hostil.jpg", jpeg_with_exif(_IMAGEN, hostil))
        datos = read_exif(ruta)
        assert datos.is_malformed

    def test_un_contador_de_entradas_absurdo_se_rechaza(self, tmp_path: Path) -> None:
        hostil = b"II\x2a\x00" + (8).to_bytes(4, "little") + (60_000).to_bytes(2, "little")
        ruta = _escribir(tmp_path / "muchas.jpg", jpeg_with_exif(_IMAGEN, hostil))
        datos = read_exif(ruta)
        assert datos.is_malformed
        assert datos.orientation is None

    def test_un_bloque_recortado_a_mitad_de_entrada_marca_incompleto(self, tmp_path: Path) -> None:
        cabecera = b"II\x2a\x00" + (8).to_bytes(4, "little")
        parcial = cabecera + (3).to_bytes(2, "little") + b"\x12\x01"
        ruta = _escribir(tmp_path / "parcial.jpg", jpeg_with_exif(_IMAGEN, parcial))
        assert read_exif(ruta).is_malformed


class TestNoDestructivo:
    def test_leer_exif_no_altera_el_archivo(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path / "foto.jpg", jpeg_with_exif(_IMAGEN, exif_block(orientation=6)))
        contenido, mtime = ruta.read_bytes(), ruta.stat().st_mtime_ns
        read_exif(ruta)
        assert ruta.read_bytes() == contenido
        assert ruta.stat().st_mtime_ns == mtime


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_orientaciones_que_intercambian_ejes(self) -> None:
        intercambian = {o for o in ExifOrientation if o.swaps_axes}
        assert intercambian == {
            ExifOrientation.MIRROR_HORIZONTAL_ROTATE_270,
            ExifOrientation.ROTATE_90,
            ExifOrientation.MIRROR_HORIZONTAL_ROTATE_90,
            ExifOrientation.ROTATE_270,
        }

    def test_orientacion_y_fecha_juntas(self, tmp_path: Path) -> None:
        bloque = exif_block(orientation=6, captured_at="2026:04:04 15:30:00")
        ruta = _escribir(tmp_path / "completa.jpg", jpeg_with_exif(_IMAGEN, bloque))
        datos = read_exif(ruta)
        assert datos.orientation is ExifOrientation.ROTATE_90
        assert datos.captured_at is not None

    def test_un_archivo_que_no_es_jpeg_no_tiene_exif(self) -> None:
        assert read_exif_from_header(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32) == ExifData()

    @pytest.mark.parametrize(
        ("cabecera", "descripcion"),
        [
            (b"\xff\xd8" + b"\xff\xff\xff\xe0\x00\x02", "relleno FF antes del marcador"),
            (b"\xff\xd8" + b"\xff\xd9" + b"\x00" * 8, "marcador sin longitud (standalone)"),
            (b"\xff\xd8" + b"\xff\xe0\x00\x00" + b"\x00" * 8, "longitud de segmento invalida"),
            (b"\xff\xd8" + b"\x00\x00\x00\x00" + b"\x00" * 8, "byte que no inicia marcador"),
            (b"\xff\xd8" + b"\xff\xe1\x00\x08" + b"otro\x00\x00", "APP1 que no es EXIF"),
        ],
    )
    def test_cabeceras_jpeg_sin_exif_utilizable(self, cabecera: bytes, descripcion: str) -> None:
        assert read_exif_from_header(cabecera) == ExifData(), descripcion

    def test_los_datos_son_inmutables(self) -> None:
        with pytest.raises(AttributeError):
            ExifData().orientation = ExifOrientation.NORMAL  # type: ignore[misc]
