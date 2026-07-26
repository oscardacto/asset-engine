"""Smoke test del esqueleto (HU-150): el paquete importa y declara su versión."""

import media_optimizer


def test_el_paquete_expone_su_version() -> None:
    assert media_optimizer.__version__ == "0.1.0"
