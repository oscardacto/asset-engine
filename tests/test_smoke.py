"""Comprueba que el paquete instala, importa y declara su versión.

En simple: si esto falla, el proyecto ni siquiera arranca.
"""

import media_optimizer


def test_el_paquete_expone_su_version() -> None:
    assert media_optimizer.__version__ == "0.1.0"
