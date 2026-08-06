"""Pruebas de la re-ingesta: qué cambió entre dos pasadas sobre la misma carpeta.

En simple: verifican que volver a ingerir lo mismo no reporta nada nuevo, que
renombrar una foto NO la convierte en otra —lo que evita perder lo que hayas
anotado sobre ella— y que cambiar el contenido de un archivo sí produce un asset
distinto, aunque conserve el nombre.
"""

from pathlib import Path

import pytest

from media_optimizer.core import MediaType
from media_optimizer.ingest import Catalog, CatalogEntry, plan_reingest

_RAIZ = Path("lote")


def _entrada(huella: str, ruta: str) -> CatalogEntry:
    return CatalogEntry(huella, ruta, MediaType.PHOTO, 1920, 1080)


def _catalogo(*entradas: CatalogEntry) -> Catalog:
    return Catalog(root=_RAIZ, entries=entradas)


_FOTO_A = _entrada("aaa", "foto_a.jpg")
_FOTO_B = _entrada("bbb", "foto_b.jpg")


class TestSinCambios:
    def test_comparar_un_catalogo_consigo_mismo_no_reporta_nada(self) -> None:
        catalogo = _catalogo(_FOTO_A, _FOTO_B)
        plan = plan_reingest(catalogo, catalogo)

        assert plan.unchanged == (_FOTO_A, _FOTO_B)
        assert plan.new == ()
        assert plan.moved == ()
        assert plan.removed == ()
        assert not plan.has_changes


class TestAltasYBajas:
    def test_un_archivo_nuevo_se_detecta(self) -> None:
        plan = plan_reingest(_catalogo(_FOTO_A), _catalogo(_FOTO_A, _FOTO_B))
        assert plan.new == (_FOTO_B,)
        assert plan.unchanged == (_FOTO_A,)
        assert plan.has_changes

    def test_un_archivo_que_ya_no_esta_se_detecta(self) -> None:
        plan = plan_reingest(_catalogo(_FOTO_A, _FOTO_B), _catalogo(_FOTO_A))
        assert plan.removed == (_FOTO_B,)
        assert plan.has_changes

    def test_la_primera_ingesta_es_todo_nuevo(self) -> None:
        plan = plan_reingest(Catalog(root=_RAIZ), _catalogo(_FOTO_A, _FOTO_B))
        assert plan.new == (_FOTO_A, _FOTO_B)
        assert plan.unchanged == ()


class TestRenombradosYMovidos:
    def test_renombrar_no_convierte_la_foto_en_otra(self) -> None:
        """El caso que, mal resuelto, haría perder las etiquetas manuales."""
        antes = _catalogo(_entrada("aaa", "IMG_001.jpg"))
        ahora = _catalogo(_entrada("aaa", "terraza/atardecer.jpg"))

        plan = plan_reingest(antes, ahora)

        assert plan.new == ()
        assert plan.removed == ()
        (movido,) = plan.moved
        assert movido.content_hash == "aaa"
        assert movido.previous_source == "IMG_001.jpg"
        assert movido.current_source == "terraza/atardecer.jpg"

    def test_mover_de_carpeta_tambien_es_movido(self) -> None:
        antes = _catalogo(_entrada("aaa", "foto.jpg"))
        ahora = _catalogo(_entrada("aaa", "sesion/foto.jpg"))
        assert len(plan_reingest(antes, ahora).moved) == 1


class TestContenidoCambiado:
    def test_mismo_nombre_con_otro_contenido_es_otro_asset(self) -> None:
        antes = _catalogo(_entrada("aaa", "foto.jpg"))
        ahora = _catalogo(_entrada("zzz", "foto.jpg"))

        plan = plan_reingest(antes, ahora)

        assert plan.new == (_entrada("zzz", "foto.jpg"),)
        assert plan.removed == (_entrada("aaa", "foto.jpg"),)
        assert plan.moved == ()


class TestParticiones:
    def test_las_colecciones_son_disjuntas_y_cubren_todo(self) -> None:
        antes = _catalogo(_FOTO_A, _FOTO_B, _entrada("ccc", "vieja.jpg"))
        ahora = _catalogo(_FOTO_A, _entrada("bbb", "renombrada.jpg"), _entrada("ddd", "nueva.jpg"))

        plan = plan_reingest(antes, ahora)

        assert len(plan.unchanged) + len(plan.moved) + len(plan.new) == len(ahora.entries)
        assert len(plan.removed) == 1
        rutas_actuales = {e.source for e in plan.unchanged} | {m.current_source for m in plan.moved}
        rutas_actuales |= {e.source for e in plan.new}
        assert rutas_actuales == {e.source for e in ahora.entries}


class TestDeterminismo:
    def test_el_mismo_par_de_catalogos_da_el_mismo_plan(self) -> None:
        antes = _catalogo(_FOTO_A, _FOTO_B)
        ahora = _catalogo(_FOTO_B, _entrada("ccc", "nueva.jpg"))
        assert plan_reingest(antes, ahora) == plan_reingest(antes, ahora)

    def test_el_orden_de_las_entradas_no_altera_el_plan(self) -> None:
        antes = _catalogo(_FOTO_A, _FOTO_B)
        ahora_directo = _catalogo(_FOTO_A, _entrada("ccc", "nueva.jpg"))
        ahora_inverso = _catalogo(_entrada("ccc", "nueva.jpg"), _FOTO_A)
        assert plan_reingest(antes, ahora_directo) == plan_reingest(antes, ahora_inverso)


class TestCapaSecundaria:
    """Casos límite adicionales a las pruebas principales."""

    def test_dos_lotes_vacios_no_producen_cambios(self) -> None:
        plan = plan_reingest(Catalog(root=_RAIZ), Catalog(root=_RAIZ))
        assert not plan.has_changes

    def test_copias_del_mismo_contenido_en_varias_rutas(self) -> None:
        """El lote real trae 15 grupos así: mismo contenido, nombres distintos."""
        antes = _catalogo(_entrada("aaa", "original.jpg"))
        ahora = _catalogo(_entrada("aaa", "original.jpg"), _entrada("aaa", "copia.jpg"))

        plan = plan_reingest(antes, ahora)

        assert plan.unchanged == (_entrada("aaa", "original.jpg"),)
        assert len(plan.moved) == 1
        assert plan.new == ()

    def test_el_plan_es_inmutable(self) -> None:
        plan = plan_reingest(Catalog(root=_RAIZ), _catalogo(_FOTO_A))
        with pytest.raises(AttributeError):
            plan.new = ()  # type: ignore[misc]

    def test_vaciar_el_lote_reporta_todo_como_desaparecido(self) -> None:
        plan = plan_reingest(_catalogo(_FOTO_A, _FOTO_B), Catalog(root=_RAIZ))
        assert plan.removed == (_FOTO_A, _FOTO_B)
        assert plan.has_changes
