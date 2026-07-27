"""Pruebas del triaje: qué se acepta, qué se aparta y con qué motivo.

En simple: comprueban que un archivo roto no tumba el lote, que cada tipo de
problema se distingue del resto, que un JPEG a medio descargar se detecta sin
abrir la imagen, y que nada se pierde ni se duplica en el reparto.
"""

from pathlib import Path

import cv2
import pytest

from media_optimizer.ingest import (
    QuarantineReason,
    triage_media,
)
from media_optimizer.testing import encode_jpeg, flat_image, not_an_image, truncated_jpeg


def _escribir(destino: Path, contenido: bytes) -> Path:
    destino.write_bytes(contenido)
    return destino


def _codificar(extension: str, lado: int = 64) -> bytes:
    ok, buffer = cv2.imencode(extension, flat_image(lado, lado, 128))
    assert ok
    return bytes(buffer.tobytes())


def _foto(brillo: int = 120) -> bytes:
    return encode_jpeg(flat_image(32, 32, brillo))


def _cabecera_heic() -> bytes:
    return b"\x00\x00\x00\x20ftypheic" + b"\x00" * 16


def _motivos(resultado: object) -> dict[str, QuarantineReason]:
    apartados = resultado.quarantined  # type: ignore[attr-defined]
    return {asset.path.name: asset.reason for asset in apartados}


class TestElLoteContinua:
    def test_un_archivo_roto_no_detiene_el_triaje(self, tmp_path: Path) -> None:
        buena = _escribir(tmp_path / "buena.jpg", _foto())
        inexistente = tmp_path / "fantasma.jpg"
        basura = _escribir(tmp_path / "basura.bin", not_an_image())

        resultado = triage_media([buena, inexistente, basura])

        assert resultado.accepted == (buena,)
        assert len(resultado.quarantined) == 2


class TestMotivosDistinguibles:
    def test_cada_problema_tiene_su_propio_motivo(self, tmp_path: Path) -> None:
        rutas = [
            tmp_path / "ilegible.jpg",
            _escribir(tmp_path / "vacio.jpg", b""),
            _escribir(tmp_path / "basura.bin", not_an_image()),
            _escribir(tmp_path / "iphone.heic", _cabecera_heic()),
            _escribir(tmp_path / "media.jpg", truncated_jpeg(flat_image(64, 64, 120))),
        ]

        motivos = _motivos(triage_media(rutas))

        assert motivos == {
            "ilegible.jpg": QuarantineReason.UNREADABLE,
            "vacio.jpg": QuarantineReason.EMPTY,
            "basura.bin": QuarantineReason.UNKNOWN_FORMAT,
            "iphone.heic": QuarantineReason.UNSUPPORTED_FORMAT,
            "media.jpg": QuarantineReason.TRUNCATED,
        }

    def test_el_detalle_nombra_el_formato_concreto(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path / "iphone.heic", _cabecera_heic())
        (apartado,) = triage_media([ruta]).quarantined
        assert "heic" in apartado.detail


class TestTruncamiento:
    def test_un_jpeg_a_medias_se_aparta_y_el_completo_se_acepta(self, tmp_path: Path) -> None:
        imagen = flat_image(64, 64, 120)
        completo = _escribir(tmp_path / "completo.jpg", encode_jpeg(imagen))
        medio = _escribir(tmp_path / "medio.jpg", truncated_jpeg(imagen))

        resultado = triage_media([completo, medio])

        assert resultado.accepted == (completo,)
        assert resultado.quarantined[0].reason is QuarantineReason.TRUNCATED

    def test_relleno_despues_del_cierre_no_es_truncamiento(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path / "con_relleno.jpg", _foto() + b"\x00" * 16)
        assert triage_media([ruta]).accepted == (ruta,)


class TestRepartoCompleto:
    def test_las_dos_listas_suman_la_entrada_y_no_se_solapan(self, tmp_path: Path) -> None:
        rutas = [
            _escribir(tmp_path / "buena1.jpg", _foto(100)),
            _escribir(tmp_path / "buena2.jpg", _foto(200)),
            _escribir(tmp_path / "mala.bin", not_an_image()),
            _escribir(tmp_path / "vacia.jpg", b""),
        ]
        resultado = triage_media(rutas)
        apartadas = {asset.path for asset in resultado.quarantined}

        assert len(resultado.accepted) + len(apartadas) == len(rutas)
        assert not set(resultado.accepted) & apartadas


class TestDeterminismo:
    def test_el_orden_de_entrada_no_altera_el_resultado(self, tmp_path: Path) -> None:
        rutas = [
            _escribir(tmp_path / "z.jpg", _foto(100)),
            _escribir(tmp_path / "a.bin", not_an_image()),
            _escribir(tmp_path / "m.jpg", _foto(200)),
        ]
        assert triage_media(rutas) == triage_media(reversed(rutas))


class TestNoDestructivo:
    def test_el_triaje_no_altera_ningun_archivo(self, tmp_path: Path) -> None:
        rutas = [
            _escribir(tmp_path / "buena.jpg", _foto()),
            _escribir(tmp_path / "rota.jpg", truncated_jpeg(flat_image(64, 64, 120))),
        ]
        antes = {ruta: (ruta.read_bytes(), ruta.stat().st_mtime_ns) for ruta in rutas}

        triage_media(rutas)

        for ruta, (contenido, mtime) in antes.items():
            assert ruta.read_bytes() == contenido
            assert ruta.stat().st_mtime_ns == mtime


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_un_lote_vacio_devuelve_dos_listas_vacias(self) -> None:
        resultado = triage_media([])
        assert resultado.accepted == ()
        assert resultado.quarantined == ()

    @pytest.mark.parametrize("extension", [".png", ".webp"])
    def test_otros_formatos_soportados_completos_se_aceptan(
        self, tmp_path: Path, extension: str
    ) -> None:
        ruta = _escribir(tmp_path / f"captura{extension}", _codificar(extension))
        assert triage_media([ruta]).accepted == (ruta,)

    @pytest.mark.parametrize("extension", [".png", ".webp"])
    def test_otros_formatos_soportados_truncados_se_apartan(
        self, tmp_path: Path, extension: str
    ) -> None:
        completo = _codificar(extension)
        ruta = _escribir(tmp_path / f"media{extension}", completo[: len(completo) // 2])
        (apartado,) = triage_media([ruta]).quarantined
        assert apartado.reason is QuarantineReason.TRUNCATED

    def test_los_motivos_serializan_a_string_plano(self) -> None:
        assert str(QuarantineReason.TRUNCATED) == "truncated"

    def test_el_resultado_es_inmutable(self, tmp_path: Path) -> None:
        ruta = _escribir(tmp_path / "foto.jpg", _foto())
        resultado = triage_media([ruta])
        with pytest.raises(AttributeError):
            resultado.accepted = ()  # type: ignore[misc]
