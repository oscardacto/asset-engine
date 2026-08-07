"""Pruebas de los flags de degradación, calibradas con los números del lote real.

En simple: verifican que una foto con nombre de WhatsApp se marca, que una
renombrada se atrapa igual por su física (sin metadatos y comprimida al extremo),
que una editada de agencia —que también pierde los metadatos pero pesa el doble
por píxel— NO se marca, y que el flag de resolución dice exactamente para qué
formatos del negocio no alcanza una foto.
"""

import pytest

from media_optimizer.core import OutputFormat, OutputIntent
from media_optimizer.ingest.degradation import (
    WHATSAPP_MAX_BYTES_PER_PIXEL,
    below_native,
    whatsapp_compression,
)

_PIXELES_12MP = 4080 * 3060

_FEED = OutputFormat(intent=OutputIntent.FEED, width=1080, height=1350)
_STORY = OutputFormat(intent=OutputIntent.STORY, width=1080, height=1920)
_COVER = OutputFormat(intent=OutputIntent.COVER, width=1920, height=1080)


def _wa(nombre: str = "IMG-20260324-WA0062.jpg", **cambios: object) -> bool:
    base: dict[str, object] = {
        "name": nombre,
        "size_bytes": int(0.05 * _PIXELES_12MP),
        "pixels": _PIXELES_12MP,
        "exif_present": False,
    }
    return whatsapp_compression(**{**base, **cambios})  # type: ignore[arg-type]


class TestNombreDeWhatsApp:
    @pytest.mark.parametrize(
        "nombre",
        ["IMG-20260324-WA0062.jpg", "img-20260324-wa0001.jpg", "copia IMG-20251101-WA1234.jpg"],
    )
    def test_el_nombre_de_whatsapp_basta_por_si_solo(self, nombre: str) -> None:
        """Aunque la foto pese mucho y traiga EXIF: el nombre no aparece por accidente."""
        assert _wa(nombre, size_bytes=_PIXELES_12MP, exif_present=True) is True

    @pytest.mark.parametrize("nombre", ["IMG_20260324_120000.jpg", "sala-WAKEUP.jpg", "WA.jpg"])
    def test_un_nombre_parecido_pero_no_de_whatsapp_no_dispara_solo(self, nombre: str) -> None:
        assert _wa(nombre, size_bytes=_PIXELES_12MP, exif_present=True) is False


class TestFisicaDelArchivo:
    def test_una_renombrada_se_atrapa_por_sus_huellas(self) -> None:
        """Sin nombre WA, pero sin EXIF y comprimida al extremo: los números del lote real."""
        assert _wa("foto_bonita.jpg", size_bytes=int(0.08 * _PIXELES_12MP)) is True

    def test_una_editada_de_agencia_no_es_falso_positivo(self) -> None:
        """El caso FP real del lote: sin EXIF, pero a 0.234+ bytes por píxel."""
        assert _wa("alcoba_001_v2.jpg", size_bytes=int(0.234 * _PIXELES_12MP)) is False

    def test_una_foto_con_exif_no_dispara_por_peso(self) -> None:
        """Las 83 fotos de cámara del lote conservan EXIF; ninguna puede disparar."""
        assert _wa("cell.jpg", size_bytes=int(0.08 * _PIXELES_12MP), exif_present=True) is False

    def test_el_umbral_es_parametro(self) -> None:
        pesada = int(0.2 * _PIXELES_12MP)
        assert _wa("x.jpg", size_bytes=pesada) is False
        assert _wa("x.jpg", size_bytes=pesada, max_bytes_per_pixel=0.3) is True

    def test_cero_pixeles_es_contrato_roto(self) -> None:
        with pytest.raises(ValueError, match="pixels"):
            _wa(pixels=0)


class TestBajoElNativo:
    def test_dice_exactamente_que_formatos_no_alcanza(self) -> None:
        cortas = below_native(1080, 1350, (_FEED, _STORY, _COVER))
        assert cortas == (OutputIntent.STORY, OutputIntent.COVER)

    def test_una_foto_grande_alcanza_para_todo(self) -> None:
        assert below_native(4080, 3060, (_FEED, _STORY, _COVER)) == ()

    def test_una_vertical_alcanza_un_formato_horizontal(self) -> None:
        """El recorte puede girar el encuadre: 3060x4080 llena un 1920x1080."""
        assert below_native(3060, 4080, (_COVER,)) == ()

    def test_un_perfil_sin_formatos_no_tiene_nada_que_incumplir(self) -> None:
        assert below_native(100, 100, ()) == ()

    def test_dimensiones_imposibles_son_contrato_roto(self) -> None:
        with pytest.raises(ValueError, match="dimensiones"):
            below_native(0, 100, (_FEED,))


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_el_umbral_calibrado_es_el_del_lote_real(self) -> None:
        """0.114 (WA máx) < 0.15 < 0.234 (editada mín): el margen medido."""
        assert 0.114 < WHATSAPP_MAX_BYTES_PER_PIXEL < 0.234

    def test_el_resultado_es_determinista(self) -> None:
        assert _wa() is _wa()

    def test_justo_en_el_umbral_no_dispara(self) -> None:
        exacto = int(WHATSAPP_MAX_BYTES_PER_PIXEL * _PIXELES_12MP)
        assert _wa("x.jpg", size_bytes=exacto) is False
