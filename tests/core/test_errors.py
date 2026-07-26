"""Pruebas de los errores del dominio: jerarquía, contrato de captura y causas.

En simple: verifican que "archivo dañado" y "entrada inválida" se capturan con
una sola base, que un bug del programa NO queda atrapado por esa base, y que
el error de archivo dañado siempre viaja con su ruta y su causa.
"""

from pathlib import Path

import pytest

from media_optimizer.core import (
    CorruptMediaError,
    InvalidInputError,
    MediaOptimizerError,
)


class TestJerarquia:
    def test_los_errores_del_dominio_heredan_de_la_base(self) -> None:
        assert issubclass(CorruptMediaError, MediaOptimizerError)
        assert issubclass(InvalidInputError, MediaOptimizerError)

    def test_la_base_es_exception_normal_no_baseexception_directa(self) -> None:
        assert issubclass(MediaOptimizerError, Exception)


class TestContratoDeCaptura:
    def test_captura_archivo_danado_y_entrada_invalida_con_una_sola_base(self) -> None:
        for error in (
            CorruptMediaError(Path("x.jpg"), "JPEG truncado"),
            InvalidInputError("formato no soportado"),
        ):
            with pytest.raises(MediaOptimizerError):
                raise error

    def test_un_bug_pasa_de_largo_no_lo_atrapa_la_base_del_dominio(self) -> None:
        def etapa_con_bug() -> None:
            try:
                msg = "bug del programa"
                raise ValueError(msg)
            except MediaOptimizerError:  # pragma: no cover
                pytest.fail("un bug jamás debe quedar atrapado como error del dominio")

        with pytest.raises(ValueError, match="bug del programa"):
            etapa_con_bug()


class TestArchivoDanado:
    def test_lleva_ruta_y_causa_como_campos(self) -> None:
        error = CorruptMediaError(Path("originales/x.jpg"), "JPEG truncado")
        assert error.source == Path("originales/x.jpg")
        assert error.reason == "JPEG truncado"

    def test_el_mensaje_incluye_ruta_y_causa(self) -> None:
        texto = str(CorruptMediaError(Path("originales/x.jpg"), "JPEG truncado"))
        assert "x.jpg" in texto
        assert "JPEG truncado" in texto


class TestEntradaInvalida:
    def test_transporta_el_mensaje_accionable_tal_cual(self) -> None:
        mensaje = "el perfil no declara 'ambientes': añade la clave o usa el perfil de ejemplo"
        assert str(InvalidInputError(mensaje)) == mensaje


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_capturar_el_tipo_especifico_sigue_funcionando(self) -> None:
        with pytest.raises(CorruptMediaError):
            raise CorruptMediaError(Path("x.jpg"), "cabecera ilegible")

    def test_keyboard_interrupt_no_es_error_del_dominio(self) -> None:
        assert not issubclass(KeyboardInterrupt, MediaOptimizerError)
