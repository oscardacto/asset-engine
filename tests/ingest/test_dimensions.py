"""Pruebas de la lectura de dimensiones y del rechazo de imágenes desproporcionadas.

En simple: comprueban que las medidas leídas de la cabecera son las reales en los
tres formatos, que un archivo diminuto que dice medir 60.000 x 60.000 se aparta
sin abrirse, y que una foto legítima de altísima resolución sí pasa.
"""

from pathlib import Path

import cv2
import pytest

from media_optimizer.ingest import (
    MAX_DECODED_BYTES,
    MAX_SIDE,
    ImageFormat,
    ImageSize,
    QuarantineReason,
    read_image_size,
    read_image_size_from_path,
    triage_media,
)
from media_optimizer.testing import encode_jpeg, flat_image

_ANCHO, _ALTO = 96, 48


def _codificar(extension: str) -> bytes:
    ok, buffer = cv2.imencode(extension, flat_image(_ANCHO, _ALTO, 128))
    assert ok
    return bytes(buffer.tobytes())


def _escribir(destino: Path, contenido: bytes) -> Path:
    destino.write_bytes(contenido)
    return destino


def _cabecera_png(width: int, height: int) -> bytes:
    """PNG mínimo válido en firma e IHDR, que declara las medidas pedidas."""
    return (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\r"
        + b"IHDR"
        + width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + b"\x08\x02\x00\x00\x00"
        + b"IEND\xaeB`\x82"
    )


def _cabecera_webp(variante: bytes, cuerpo: bytes) -> bytes:
    return b"RIFF" + (len(cuerpo) + 12).to_bytes(4, "little") + b"WEBP" + variante + cuerpo


def _cabecera_vp8x(width: int, height: int) -> bytes:
    """Contenedor WebP extendido: las medidas van como valor-1 en 24 bits."""
    cuerpo = (
        b"\x0a\x00\x00\x00"
        + b"\x00\x00\x00\x00"
        + (width - 1).to_bytes(3, "little")
        + (height - 1).to_bytes(3, "little")
    )
    return _cabecera_webp(b"VP8X", cuerpo)


def _cabecera_vp8_con_perdida(width: int, height: int) -> bytes:
    """WebP con pérdida: tras el código de arranque van ancho y alto en 14 bits."""
    cuerpo = (
        b"\x10\x00\x00\x00"
        + b"\x00\x00\x00"
        + b"\x9d\x01\x2a"
        + width.to_bytes(2, "little")
        + height.to_bytes(2, "little")
    )
    return _cabecera_webp(b"VP8 ", cuerpo)


class TestDimensionesPorFormato:
    @pytest.mark.parametrize(
        ("extension", "formato"),
        [(".jpg", ImageFormat.JPEG), (".png", ImageFormat.PNG), (".webp", ImageFormat.WEBP)],
    )
    def test_las_medidas_leidas_son_las_reales(self, extension: str, formato: ImageFormat) -> None:
        medida = read_image_size(_codificar(extension), formato)
        assert medida == ImageSize(width=_ANCHO, height=_ALTO)

    @pytest.mark.parametrize(
        "constructor",
        [_cabecera_vp8x, _cabecera_vp8_con_perdida],
        ids=["vp8x", "vp8_con_perdida"],
    )
    def test_las_otras_variantes_de_webp_tambien_se_leen(self, constructor: object) -> None:
        cabecera = constructor(_ANCHO, _ALTO)  # type: ignore[operator]
        assert read_image_size(cabecera, ImageFormat.WEBP) == ImageSize(_ANCHO, _ALTO)

    def test_desde_una_ruta_tambien_funciona(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path / "foto.jpg", _codificar(".jpg"))
        medida = read_image_size_from_path(ruta, ImageFormat.JPEG)
        assert medida is not None
        assert (medida.width, medida.height) == (_ANCHO, _ALTO)


class TestMemoriaEstimada:
    def test_estima_tres_bytes_por_pixel(self) -> None:
        medida = ImageSize(width=1000, height=1000)
        assert medida.pixels == 1_000_000
        assert medida.estimated_decoded_bytes == 3_000_000
        assert medida.longest_side == 1000


class TestRechazoDeImagenesBomba:
    def test_una_cabecera_enorme_en_un_archivo_diminuto_se_aparta(self, tmp_path: Path) -> None:
        bomba = _escribir(tmp_path / "bomba.png", _cabecera_png(60_000, 60_000))
        assert bomba.stat().st_size < 100

        (apartado,) = triage_media([bomba]).quarantined

        assert apartado.reason is QuarantineReason.TOO_LARGE
        assert "60000x60000" in apartado.detail
        assert "GiB" in apartado.detail

    def test_la_bomba_se_aparta_y_la_foto_normal_se_acepta(self, tmp_path: Path) -> None:
        buena = _escribir(tmp_path / "buena.jpg", encode_jpeg(flat_image(64, 64, 120)))
        bomba = _escribir(tmp_path / "bomba.png", _cabecera_png(60_000, 60_000))

        resultado = triage_media([buena, bomba])

        assert resultado.accepted == (buena,)
        assert resultado.quarantined[0].reason is QuarantineReason.TOO_LARGE

    def test_un_lado_desmesurado_se_aparta_aunque_pese_poco_en_total(self, tmp_path: Path) -> None:
        larga = _escribir(tmp_path / "tira.png", _cabecera_png(70_000, 2))
        (apartado,) = triage_media([larga]).quarantined
        assert apartado.reason is QuarantineReason.TOO_LARGE
        assert str(MAX_SIDE) in apartado.detail


class TestFotosLegitimasDeAltaResolucion:
    def test_una_foto_de_200_megapixeles_se_acepta(self, tmp_path: Path) -> None:
        """El celular de referencia del cliente 0 tiene sensor de 200 MP."""
        ruta = _escribir(tmp_path / "200mp.png", _cabecera_png(16_320, 12_240))
        medida = read_image_size(ruta.read_bytes(), ImageFormat.PNG)

        assert medida is not None
        assert medida.pixels > 199_000_000
        assert medida.estimated_decoded_bytes < MAX_DECODED_BYTES
        assert triage_media([ruta]).accepted == (ruta,)


class TestDimensionesIlegibles:
    def test_un_formato_sin_lector_devuelve_none(self) -> None:
        assert read_image_size(b"cualquier cosa", ImageFormat.HEIC) is None

    @pytest.mark.parametrize(
        ("cabecera", "formato"),
        [
            (b"\x89PNG\r\n\x1a\n" + b"\x00" * 4, ImageFormat.PNG),
            (b"\xff\xd8\xff", ImageFormat.JPEG),
            (b"\xff\xd8\xff\xc0\x00", ImageFormat.JPEG),
            (b"\xff\xd8\xff\xe0\x00\x00", ImageFormat.JPEG),
            (b"\xff\xd8\xff\xe0\x00\x04ABCD", ImageFormat.JPEG),
            (b"RIFF\x00\x00\x00\x00WEBP", ImageFormat.WEBP),
            (_cabecera_webp(b"VP8?", b"\x00" * 20), ImageFormat.WEBP),
        ],
    )
    def test_una_cabecera_incompleta_devuelve_none(
        self, cabecera: bytes, formato: ImageFormat
    ) -> None:
        assert read_image_size(cabecera, formato) is None

    def test_lo_que_no_se_puede_medir_no_se_descarta(self, tmp_path: Path) -> None:
        """JPEG válido en firma y cierre, pero sin un marcador que declare las medidas."""
        sin_medidas = b"\xff\xd8\xff\xe0\x00\x02" + b"\xff\xd9"
        ruta = _escribir(tmp_path / "rara.jpg", sin_medidas)

        assert read_image_size(sin_medidas, ImageFormat.JPEG) is None
        assert triage_media([ruta]).accepted == (ruta,)


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_dimensiones_cero_se_consideran_ilegibles(self) -> None:
        assert read_image_size(_cabecera_png(0, 10), ImageFormat.PNG) is None

    def test_un_lado_justo_en_el_limite_se_acepta(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path / "limite.png", _cabecera_png(MAX_SIDE, 2))
        assert triage_media([ruta]).accepted == (ruta,)

    def test_un_jpeg_con_relleno_ff_antes_del_marcador_se_lee_igual(self) -> None:
        completo = _codificar(".jpg")
        con_relleno = completo[:2] + b"\xff" + completo[2:]
        assert read_image_size(con_relleno, ImageFormat.JPEG) == ImageSize(_ANCHO, _ALTO)

    def test_las_medidas_son_inmutables(self) -> None:
        with pytest.raises(AttributeError):
            ImageSize(width=10, height=10).width = 20  # type: ignore[misc]
