"""Pruebas del rastro estructurado: que cada evento se escriba, y que se escriba bien.

En simple: verifican que cada línea es JSON legible, que los datos que se le
adjuntan a un evento aparecen, y —lo más importante— que un archivo de log en una
ruta difícil **guarda bytes de verdad**. Esa última comprobación existe porque el
handler de la biblioteca estándar, ante un archivo llamado ``NUL.log``, dice que
todo va bien mientras tira cada registro a la basura.
"""

import io
import json
import logging
import sys
from pathlib import Path
from typing import Any

import pytest

from media_optimizer.ingest import filesystem
from media_optimizer.logs import (
    JsonLinesFormatter,
    configure_logging,
    get_logger,
)

_RUTA_LARGA = ("y" * 40,) * 8


def _lineas(salida: io.StringIO) -> list[dict[str, Any]]:
    return [json.loads(linea) for linea in salida.getvalue().splitlines() if linea.strip()]


@pytest.fixture
def salida() -> io.StringIO:
    return io.StringIO()


class TestFormatoDeLinea:
    def test_cada_evento_es_una_linea_de_json_valido(self, salida: io.StringIO) -> None:
        registro = configure_logging(stream=salida)
        registro.info("empieza la ingesta")
        registro.warning("una foto se descartó")

        eventos = _lineas(salida)
        assert len(eventos) == 2
        assert eventos[0]["message"] == "empieza la ingesta"
        assert eventos[1]["level"] == "WARNING"

    def test_las_claves_salen_ordenadas(self, salida: io.StringIO) -> None:
        registro = configure_logging(stream=salida)
        registro.info("evento", extra={"zeta": 1, "alfa": 2})

        crudo = salida.getvalue().strip()
        claves = list(json.loads(crudo))
        assert claves == sorted(claves)

    def test_los_campos_reservados_siempre_estan(self, salida: io.StringIO) -> None:
        registro = configure_logging(stream=salida)
        registro.info("evento")
        assert {"timestamp", "level", "logger", "message"} <= set(_lineas(salida)[0])

    def test_los_acentos_se_escriben_tal_cual(self, salida: io.StringIO) -> None:
        registro = configure_logging(stream=salida)
        registro.info("orientación ilegible en la fotografía")
        assert "orientación" in salida.getvalue()
        assert "\\u00f3" not in salida.getvalue()

    def test_una_excepcion_queda_registrada(self, salida: io.StringIO) -> None:
        registro = configure_logging(stream=salida)
        try:
            raise ValueError("archivo corrupto")
        except ValueError:
            registro.exception("no se pudo leer el asset")
        assert "archivo corrupto" in _lineas(salida)[0]["error"]


class TestCamposDelLlamador:
    def test_los_datos_adjuntos_aparecen_en_la_linea(self, salida: io.StringIO) -> None:
        registro = configure_logging(stream=salida)
        registro.info("asset descartado", extra={"asset": "IMG_0031.jpg", "motivo": "borrosa"})

        evento = _lineas(salida)[0]
        assert evento["asset"] == "IMG_0031.jpg"
        assert evento["motivo"] == "borrosa"

    def test_un_dato_no_serializable_no_rompe_la_linea(self, salida: io.StringIO) -> None:
        """Un asset raro degrada su propio evento; no tumba el rastro entero."""
        registro = configure_logging(stream=salida)
        registro.info("evento", extra={"ruta": Path("C:/fotos/terraza.jpg")})

        evento = _lineas(salida)[0]
        assert "terraza.jpg" in evento["ruta"]

    def test_un_dato_del_llamador_no_puede_falsear_el_nivel(self, salida: io.StringIO) -> None:
        registro = configure_logging(stream=salida)
        registro.info("evento", extra={"level": "CRITICAL"})
        assert _lineas(salida)[0]["level"] == "INFO"


class TestNiveles:
    def test_por_debajo_del_nivel_configurado_no_se_registra(self, salida: io.StringIO) -> None:
        registro = configure_logging(level=logging.WARNING, stream=salida)
        registro.debug("detalle")
        registro.info("informativo")
        registro.warning("advertencia")
        assert [evento["level"] for evento in _lineas(salida)] == ["WARNING"]

    def test_el_logger_de_un_modulo_cuelga_del_raiz(self, salida: io.StringIO) -> None:
        configure_logging(stream=salida)
        get_logger("ingest").info("desde ingesta")
        assert _lineas(salida)[0]["logger"] == "media_optimizer.ingest"


class TestIdempotencia:
    def test_configurar_dos_veces_no_duplica_lineas(self, salida: io.StringIO) -> None:
        configure_logging(stream=salida)
        registro = configure_logging(stream=salida)
        registro.info("una sola vez")
        assert len(_lineas(salida)) == 1


@pytest.mark.skipif(sys.platform != "win32", reason="rutas hostiles de Windows")
class TestRutasQueLaStdlibPierde:
    """Cada prueba comprueba **bytes en disco**, no que no haya excepción.

    Es la distinción que importa: con ``NUL.log`` el handler estándar no lanza nada
    y aun así no queda nada escrito.
    """

    def _escribir_y_leer(self, destino: Path) -> str:
        registro = configure_logging(stream=io.StringIO(), log_file=destino)
        registro.info("evento que tiene que sobrevivir")
        for manejador in tuple(registro.handlers):
            manejador.close()
        return filesystem.read_bytes(destino).decode("utf-8")

    def test_un_log_en_ruta_larga_guarda_bytes_reales(self, tmp_path: Path) -> None:
        destino = tmp_path.joinpath(*_RUTA_LARGA) / "run.log"
        assert len(str(destino)) > 260
        assert "tiene que sobrevivir" in self._escribir_y_leer(destino)

    @pytest.mark.parametrize("nombre", ["CON.log", "NUL.log", "COM1.log"])
    def test_un_log_con_nombre_de_dispositivo_guarda_bytes_reales(
        self, tmp_path: Path, nombre: str
    ) -> None:
        """`NUL.log` es el caso grave: la stdlib no falla, simplemente no escribe."""
        contenido = self._escribir_y_leer(tmp_path / nombre)
        assert json.loads(contenido.splitlines()[0])["message"] == "evento que tiene que sobrevivir"

    def test_el_handler_crea_la_carpeta_que_falte(self, tmp_path: Path) -> None:
        destino = tmp_path / "sin" / "crear" / "todavia" / "run.log"
        assert "tiene que sobrevivir" in self._escribir_y_leer(destino)


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_el_formateador_funciona_suelto(self) -> None:
        registro = logging.LogRecord("m", logging.INFO, "f", 1, "hola", None, None)
        assert json.loads(JsonLinesFormatter().format(registro))["message"] == "hola"

    def test_un_mensaje_con_parametros_se_resuelve(self, salida: io.StringIO) -> None:
        registro = configure_logging(stream=salida)
        registro.info("procesadas %d de %d fotos", 12, 109)
        assert _lineas(salida)[0]["message"] == "procesadas 12 de 109 fotos"

    def test_el_rastro_no_se_propaga_al_logger_global(self, salida: io.StringIO) -> None:
        """Si se propagara, un `basicConfig` ajeno duplicaría cada línea en texto plano."""
        assert configure_logging(stream=salida).propagate is False

    def test_la_marca_de_tiempo_tiene_milisegundos(self, salida: io.StringIO) -> None:
        registro = configure_logging(stream=salida)
        registro.info("evento")
        marca = _lineas(salida)[0]["timestamp"]
        assert marca.endswith("Z")
        assert len(marca.split(".")[1]) == 4  # tres dígitos + la Z
