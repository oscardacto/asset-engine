"""Pruebas de la identificación de formatos: contenido sobre extensión.

En simple: comprueban que una foto renombrada a .txt se reconoce igual, que un
texto con nombre .jpg no cuela, que un HEIC de iPhone se identifica aunque no
podamos abrirlo, y que lo que declaramos soportado el sistema lo abre de verdad.
"""

from pathlib import Path

import cv2
import numpy as np
import pytest

from media_optimizer.core import CorruptMediaError
from media_optimizer.ingest import (
    SUPPORTED_FORMATS,
    ImageFormat,
    detect_image_format,
    is_supported_image,
)
from media_optimizer.testing import encode_jpeg, flat_image, not_an_image

_EXTENSION_POR_FORMATO = {
    ImageFormat.JPEG: ".jpg",
    ImageFormat.PNG: ".png",
    ImageFormat.WEBP: ".webp",
}


def _escribir(carpeta: Path, nombre: str, contenido: bytes) -> Path:
    destino = carpeta / nombre
    destino.write_bytes(contenido)
    return destino


def _codificar(extension: str) -> bytes:
    ok, buffer = cv2.imencode(extension, flat_image(8, 8, 128))
    assert ok
    return bytes(buffer.tobytes())


def _cabecera_isobmff(marca: bytes) -> bytes:
    return b"\x00\x00\x00\x20ftyp" + marca + b"\x00\x00\x00\x00"


class TestContenidoSobreExtension:
    def test_una_foto_renombrada_a_txt_sigue_siendo_jpeg(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path, "foto.txt", encode_jpeg(flat_image(16, 16, 120)))
        assert detect_image_format(ruta) is ImageFormat.JPEG

    def test_un_texto_con_nombre_jpg_no_es_imagen(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path, "documento.jpg", b"esto es texto plano, no una foto")
        assert detect_image_format(ruta) is None


class TestFormatosSoportados:
    @pytest.mark.parametrize(
        ("formato", "extension"),
        list(_EXTENSION_POR_FORMATO.items()),
    )
    def test_se_reconocen_y_son_soportados(
        self, tmp_path: Path, formato: ImageFormat, extension: str
    ) -> None:
        ruta = _escribir(tmp_path, f"imagen{extension}", _codificar(extension))
        assert detect_image_format(ruta) is formato
        assert is_supported_image(ruta)


class TestReconocidosNoSoportados:
    @pytest.mark.parametrize(
        ("marca", "esperado"),
        [(b"heic", ImageFormat.HEIC), (b"mif1", ImageFormat.HEIC), (b"avif", ImageFormat.AVIF)],
    )
    def test_heic_y_avif_se_identifican_pero_no_se_soportan(
        self, tmp_path: Path, marca: bytes, esperado: ImageFormat
    ) -> None:
        ruta = _escribir(tmp_path, "foto_iphone.heic", _cabecera_isobmff(marca))
        assert detect_image_format(ruta) is esperado
        assert not is_supported_image(ruta)


class TestDesconocidos:
    def test_bytes_sin_firma_no_lanzan_excepcion(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path, "basura.bin", not_an_image())
        assert detect_image_format(ruta) is None

    def test_archivo_vacio_es_desconocido(self, tmp_path: Path) -> None:
        assert detect_image_format(_escribir(tmp_path, "vacio.jpg", b"")) is None

    def test_contenedor_isobmff_de_marca_ajena_es_desconocido(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path, "video.mp4", _cabecera_isobmff(b"isom"))
        assert detect_image_format(ruta) is None


class TestArchivoIlegible:
    def test_una_ruta_inexistente_degrada_con_causa(self, tmp_path: Path) -> None:
        with pytest.raises(CorruptMediaError, match="no se pudo leer") as capturado:
            detect_image_format(tmp_path / "fantasma.jpg")
        assert capturado.value.source == tmp_path / "fantasma.jpg"


class TestFirmaNoEsIntegridad:
    def test_una_cabecera_valida_con_basura_detras_sigue_siendo_jpeg(self, tmp_path: Path) -> None:
        completo = encode_jpeg(flat_image(16, 16, 120))
        ruta = _escribir(tmp_path, "rota.jpg", completo[:32] + b"\x00" * 64)
        assert detect_image_format(ruta) is ImageFormat.JPEG


class TestCoherenciaConElStack:
    @pytest.mark.parametrize("formato", sorted(SUPPORTED_FORMATS))
    def test_todo_formato_declarado_soportado_lo_abre_opencv(self, formato: ImageFormat) -> None:
        datos = _codificar(_EXTENSION_POR_FORMATO[formato])
        decodificada = cv2.imdecode(np.frombuffer(datos, dtype=np.uint8), cv2.IMREAD_COLOR)
        assert decodificada is not None


class TestNoDestructivo:
    def test_identificar_no_altera_el_archivo(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path, "foto.jpg", encode_jpeg(flat_image(16, 16, 120)))
        contenido, mtime = ruta.read_bytes(), ruta.stat().st_mtime_ns
        detect_image_format(ruta)
        assert ruta.read_bytes() == contenido
        assert ruta.stat().st_mtime_ns == mtime


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_un_archivo_mas_corto_que_la_firma_no_rompe(self, tmp_path: Path) -> None:
        assert detect_image_format(_escribir(tmp_path, "corto.jpg", b"\xff\xd8")) is None

    def test_riff_que_no_es_webp_es_desconocido(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path, "audio.wav", b"RIFF\x00\x00\x00\x00WAVEfmt ")
        assert detect_image_format(ruta) is None

    def test_los_formatos_serializan_a_string_plano(self) -> None:
        assert str(ImageFormat.JPEG) == "jpeg"

    def test_el_conjunto_soportado_es_inmutable(self) -> None:
        assert isinstance(SUPPORTED_FORMATS, frozenset)
