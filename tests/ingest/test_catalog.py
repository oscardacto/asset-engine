"""Pruebas del catálogo: ida y vuelta, escritura sin dejarlo a medias y validación.

En simple: comprueban que lo guardado se recupera igual, que un corte a mitad de
escritura no destruye el catálogo anterior, que el archivo es idéntico ante el
mismo contenido, y que un catálogo manipulado a mano se rechaza con un mensaje
que dice qué está mal.
"""

import json
from pathlib import Path

import pytest

from media_optimizer.core import InvalidInputError, MediaType, Orientation
from media_optimizer.ingest import (
    CATALOG_FILENAME,
    CATALOG_VERSION,
    Catalog,
    CatalogEntry,
    QuarantineReason,
    QuarantineRecord,
    load_catalog,
    save_catalog,
)

_RAIZ = Path("originales/lote-abril")


def _catalogo(**cambios: object) -> Catalog:
    base = {
        "root": _RAIZ,
        "entries": (
            CatalogEntry("a1b2", "sesion/foto2.jpg", MediaType.PHOTO, 1080, 1920),
            CatalogEntry("c3d4", "foto1.jpg", MediaType.PHOTO, 1920, 1080),
        ),
        "quarantined": (
            QuarantineRecord(
                "rota.jpg", QuarantineReason.TRUNCATED, "no llega a su marca de cierre"
            ),
        ),
    }
    base.update(cambios)
    return Catalog(**base)  # type: ignore[arg-type]


class TestIdaYVuelta:
    def test_lo_guardado_se_recupera_igual(self, tmp_path: Path) -> None:
        original = _catalogo()
        save_catalog(original, tmp_path)
        assert load_catalog(tmp_path) == original

    def test_un_lote_vacio_es_valido(self, tmp_path: Path) -> None:
        vacio = Catalog(root=_RAIZ)
        save_catalog(vacio, tmp_path)
        recuperado = load_catalog(tmp_path)
        assert recuperado.entries == ()
        assert recuperado.quarantined == ()

    def test_el_archivo_se_llama_como_la_constante(self, tmp_path: Path) -> None:
        destino = save_catalog(_catalogo(), tmp_path)
        assert destino.name == CATALOG_FILENAME
        assert destino.parent == tmp_path


class TestEscrituraAtomica:
    def test_no_deja_archivos_temporales(self, tmp_path: Path) -> None:
        save_catalog(_catalogo(), tmp_path)
        assert [p.name for p in tmp_path.iterdir()] == [CATALOG_FILENAME]

    def test_el_catalogo_anterior_sobrevive_a_un_fallo(self, tmp_path: Path, monkeypatch) -> None:
        save_catalog(_catalogo(), tmp_path)
        contenido_previo = (tmp_path / CATALOG_FILENAME).read_bytes()

        def falla_al_sustituir(*_: object) -> None:
            msg = "fallo simulado justo antes de sustituir"
            raise OSError(msg)

        monkeypatch.setattr(
            "media_optimizer.ingest.catalog.filesystem.replace_atomic", falla_al_sustituir
        )
        with pytest.raises(OSError, match="fallo simulado"):
            save_catalog(_catalogo(entries=()), tmp_path)

        assert (tmp_path / CATALOG_FILENAME).read_bytes() == contenido_previo
        assert load_catalog(tmp_path).entries != ()


class TestDeterminismo:
    def test_el_mismo_contenido_produce_los_mismos_bytes(self, tmp_path: Path) -> None:
        entradas = _catalogo().entries
        primero = tmp_path / "a"
        segundo = tmp_path / "b"
        primero.mkdir()
        segundo.mkdir()

        save_catalog(_catalogo(entries=entradas), primero)
        save_catalog(_catalogo(entries=tuple(reversed(entradas))), segundo)

        assert (primero / CATALOG_FILENAME).read_bytes() == (
            segundo / CATALOG_FILENAME
        ).read_bytes()

    def test_las_entradas_se_guardan_ordenadas_por_ruta(self, tmp_path: Path) -> None:
        save_catalog(_catalogo(), tmp_path)
        datos = json.loads((tmp_path / CATALOG_FILENAME).read_text(encoding="utf-8"))
        rutas = [entrada["source"] for entrada in datos["entries"]]
        assert rutas == sorted(rutas)


class TestRutasRelativas:
    def test_el_archivo_no_lleva_rutas_absolutas_de_la_maquina(self, tmp_path: Path) -> None:
        save_catalog(_catalogo(), tmp_path)
        texto = (tmp_path / CATALOG_FILENAME).read_text(encoding="utf-8")
        assert "C:" not in texto
        assert str(tmp_path) not in texto

    def test_el_catalogo_sigue_siendo_legible_si_se_mueve_la_carpeta(self, tmp_path: Path) -> None:
        origen = tmp_path / "antes"
        origen.mkdir()
        save_catalog(_catalogo(), origen)
        destino = tmp_path / "despues"
        origen.rename(destino)
        assert load_catalog(destino) == _catalogo()


class TestCatalogoCorrupto:
    def test_si_no_existe_lo_dice(self, tmp_path: Path) -> None:
        with pytest.raises(InvalidInputError, match="no hay catálogo"):
            load_catalog(tmp_path)

    def test_un_json_invalido_se_rechaza(self, tmp_path: Path) -> None:
        (tmp_path / CATALOG_FILENAME).write_text("{esto no es json", encoding="utf-8")
        with pytest.raises(InvalidInputError, match="no es un JSON válido"):
            load_catalog(tmp_path)

    def test_una_version_desconocida_nombra_ambas(self, tmp_path: Path) -> None:
        (tmp_path / CATALOG_FILENAME).write_text(
            json.dumps({"version": 99, "root": ".", "entries": [], "quarantined": []}),
            encoding="utf-8",
        )
        with pytest.raises(InvalidInputError, match=r"99.*soportada 1"):
            load_catalog(tmp_path)

    def test_un_campo_obligatorio_ausente_se_nombra(self, tmp_path: Path) -> None:
        (tmp_path / CATALOG_FILENAME).write_text(
            json.dumps(
                {
                    "version": CATALOG_VERSION,
                    "root": ".",
                    "entries": [
                        {"source": "a.jpg", "media_type": "photo", "width": 1, "height": 1}
                    ],
                    "quarantined": [],
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(InvalidInputError, match="content_hash"):
            load_catalog(tmp_path)

    def test_un_tipo_incorrecto_se_rechaza(self, tmp_path: Path) -> None:
        (tmp_path / CATALOG_FILENAME).write_text(
            json.dumps(
                {
                    "version": CATALOG_VERSION,
                    "root": ".",
                    "entries": [
                        {
                            "content_hash": "a1",
                            "source": "a.jpg",
                            "media_type": "photo",
                            "width": "mil",
                            "height": 1,
                        }
                    ],
                    "quarantined": [],
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(InvalidInputError, match="width"):
            load_catalog(tmp_path)


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_la_orientacion_se_deriva_de_las_medidas(self) -> None:
        assert (
            CatalogEntry("h", "v.jpg", MediaType.PHOTO, 1080, 1920).orientation
            is Orientation.VERTICAL
        )
        assert (
            CatalogEntry("h", "h.jpg", MediaType.PHOTO, 1920, 1080).orientation
            is Orientation.HORIZONTAL
        )
        assert (
            CatalogEntry("h", "c.jpg", MediaType.PHOTO, 500, 500).orientation is Orientation.SQUARE
        )

    def test_las_causas_de_cuarentena_se_recuperan_tipadas(self, tmp_path: Path) -> None:
        save_catalog(_catalogo(), tmp_path)
        (apartado,) = load_catalog(tmp_path).quarantined
        assert apartado.reason is QuarantineReason.TRUNCATED

    def test_un_catalogo_que_no_es_objeto_se_rechaza(self, tmp_path: Path) -> None:
        (tmp_path / CATALOG_FILENAME).write_text("[1, 2, 3]", encoding="utf-8")
        with pytest.raises(InvalidInputError, match="objeto JSON"):
            load_catalog(tmp_path)

    def test_entries_que_no_es_lista_se_rechaza(self, tmp_path: Path) -> None:
        (tmp_path / CATALOG_FILENAME).write_text(
            json.dumps({"version": CATALOG_VERSION, "root": ".", "entries": {}}), encoding="utf-8"
        )
        with pytest.raises(InvalidInputError, match="entries"):
            load_catalog(tmp_path)

    def test_el_catalogo_es_inmutable(self) -> None:
        with pytest.raises(AttributeError):
            _catalogo().entries = ()  # type: ignore[misc]
