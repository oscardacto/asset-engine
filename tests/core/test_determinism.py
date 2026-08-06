"""Pruebas de determinismo: que dos ejecuciones iguales den exactamente lo mismo.

En simple: comprueban que el mismo nombre escrito de dos maneras se trate como uno
solo, y que las etiquetas de un reporte salgan siempre en el mismo orden — incluso
comparando **dos ejecuciones distintas del programa**, que es donde el fallo se
manifestaba y donde una prueba dentro de un solo proceso no lo vería.
"""

import subprocess
import sys
import unicodedata
from dataclasses import fields

import pytest

from media_optimizer import core
from media_optimizer.core import (
    QualityReport,
    Verdict,
    stable_order,
    stable_order_by,
    stable_text,
    stable_unique,
)

_ACENTUADO_NFC = unicodedata.normalize("NFC", "café.jpg")
_ACENTUADO_NFD = unicodedata.normalize("NFD", "café.jpg")
_VECINO = "cafz.jpg"

_GUION_REPORTE = """
from media_optimizer.core import QualityReport, Verdict
reporte = QualityReport(
    metrics={"nitidez": 1.0},
    flags=("borrosa", "subexpuesta", "ruidosa", "bajo_nativo", "comprimida"),
    verdict=Verdict.DISCARD,
)
print("|".join(reporte.flags))
"""


def _salida_con_semilla(semilla: str) -> str:
    """Corre el mismo guion en un proceso nuevo con otra semilla de hash."""
    resultado = subprocess.run(  # noqa: S603 - guion fijo, sin entrada externa
        [sys.executable, "-c", _GUION_REPORTE],
        capture_output=True,
        text=True,
        check=True,
        env={"PYTHONHASHSEED": semilla, "PATH": "", "SYSTEMROOT": "C:\\Windows"},
    )
    return resultado.stdout.strip()


class TestFormaUnicaDelTexto:
    def test_dos_escrituras_del_mismo_nombre_son_el_mismo_texto(self) -> None:
        """`café.jpg` con la é entera y con la tilde suelta son el mismo archivo."""
        assert _ACENTUADO_NFC != _ACENTUADO_NFD
        assert stable_text(_ACENTUADO_NFC) == stable_text(_ACENTUADO_NFD)

    def test_un_texto_sin_acentos_no_se_toca(self) -> None:
        assert stable_text("IMG_0031.jpg") == "IMG_0031.jpg"


class TestOrdenEstable:
    def test_la_misma_carpeta_ordena_igual_venga_de_donde_venga(self) -> None:
        """macOS entrega los nombres en NFD y Windows en NFC; el orden no puede depender de eso."""
        desde_windows = stable_order([_ACENTUADO_NFC, _VECINO])
        desde_mac = stable_order([_ACENTUADO_NFD, _VECINO])
        assert desde_windows == desde_mac

    def test_sin_normalizar_el_orden_si_cambiaria(self) -> None:
        """Demuestra el defecto que la función evita: no es una precaución teórica."""
        assert sorted([_ACENTUADO_NFC, _VECINO]) != sorted([_ACENTUADO_NFD, _VECINO])

    def test_ordena_objetos_por_una_clave_de_texto(self) -> None:
        assets = [("z", 1), ("a", 2), ("m", 3)]
        assert stable_order_by(assets, key=lambda par: par[0]) == (("a", 2), ("m", 3), ("z", 1))

    def test_una_coleccion_vacia_no_es_un_error(self) -> None:
        assert stable_order([]) == ()
        assert stable_unique([]) == ()


class TestTextosDistintos:
    def test_descarta_repetidos_y_ordena(self) -> None:
        assert stable_unique(["ruidosa", "borrosa", "ruidosa"]) == ("borrosa", "ruidosa")

    def test_dos_escrituras_del_mismo_texto_cuentan_como_una(self) -> None:
        assert stable_unique([_ACENTUADO_NFC, _ACENTUADO_NFD]) == (_ACENTUADO_NFC,)

    def test_mayusculas_y_minusculas_siguen_siendo_distintas(self) -> None:
        """Aquí no se aplica `casefold`: son textos distintos, no rutas del sistema."""
        assert stable_unique(["Borrosa", "borrosa"]) == ("Borrosa", "borrosa")


class TestFlagsDelReporte:
    def test_los_flags_iteran_siempre_en_el_mismo_orden(self) -> None:
        reporte = QualityReport(
            metrics={}, flags=("ruidosa", "borrosa", "comprimida"), verdict=Verdict.SUPPORT
        )
        assert reporte.flags == ("borrosa", "comprimida", "ruidosa")

    def test_los_flags_repetidos_se_descartan(self) -> None:
        reporte = QualityReport(metrics={}, flags=("borrosa", "borrosa"), verdict=Verdict.DISCARD)
        assert reporte.flags == ("borrosa",)

    def test_preguntar_si_un_flag_esta_sigue_funcionando(self) -> None:
        reporte = QualityReport(metrics={}, flags=("borrosa",), verdict=Verdict.DISCARD)
        assert "borrosa" in reporte.flags
        assert "ruidosa" not in reporte.flags


class TestReproducibilidadEntreProcesos:
    """El fallo vivía **entre** ejecuciones; dentro de una sola no se ve."""

    def test_dos_procesos_con_semillas_distintas_dan_los_mismos_bytes(self) -> None:
        salidas = {_salida_con_semilla(semilla) for semilla in ("0", "1", "42", "7777")}
        assert len(salidas) == 1, f"el orden cambió entre procesos: {salidas}"

    def test_el_orden_es_el_alfabetico_esperado(self) -> None:
        esperado = "bajo_nativo|borrosa|comprimida|ruidosa|subexpuesta"
        assert _salida_con_semilla("0") == esperado


class TestGuardianDeContratos:
    def test_ningun_contrato_de_core_expone_un_conjunto(self) -> None:
        """Un `set` en un contrato es un orden distinto en cada ejecución, esperando salir.

        Vigila los contratos futuros: el defecto que motivó esta HU estaba en uno
        que llevaba cerrado varias HUs sin que nada lo delatara.
        """
        infractores = [
            f"{nombre}.{campo.name}: {campo.type}"
            for nombre in core.__all__
            for tipo in [getattr(core, nombre)]
            if hasattr(tipo, "__dataclass_fields__")
            for campo in fields(tipo)
            if "set[" in str(campo.type).replace("frozenset[", "set[")
        ]
        assert not infractores, f"contratos con colecciones sin orden: {infractores}"


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    @pytest.mark.parametrize("entrada", ["", " ", "ñ", "日本語"])
    def test_textos_raros_no_rompen_la_normalizacion(self, entrada: str) -> None:
        assert stable_text(entrada) == unicodedata.normalize("NFC", entrada)

    def test_aplicar_la_forma_unica_dos_veces_no_cambia_nada(self) -> None:
        assert stable_text(stable_text(_ACENTUADO_NFD)) == stable_text(_ACENTUADO_NFD)

    def test_el_orden_estable_tambien_normaliza_lo_que_devuelve(self) -> None:
        (unico,) = stable_order([_ACENTUADO_NFD])
        assert unico == _ACENTUADO_NFC
