"""Prueba de gobernanza: nadie toca el disco fuera de la capa de acceso.

En simple: recorre el código de producción y falla si algún módulo abre
archivos, consulta metadatos o recorre carpetas por su cuenta. No es una prueba
funcional — es la que impide que dentro de seis meses alguien reintroduzca, sin
darse cuenta, el fallo que hizo falta un lote real para descubrir.

Analiza el árbol sintáctico, no el texto: así una palabra dentro de una
docstring no puede disparar un falso positivo.
"""

import ast
from pathlib import Path

RAIZ_PRODUCCION = Path(__file__).resolve().parents[1] / "src" / "media_optimizer"
MODULO_EXENTO = "filesystem.py"
_MODULO_CAPA = "filesystem"

_METODOS_DE_DISCO = frozenset(
    {
        "open",
        "read_bytes",
        "write_bytes",
        "read_text",
        "write_text",
        "stat",
        "lstat",
        "exists",
        "is_file",
        "is_dir",
        "iterdir",
        "walk",
        "glob",
        "rglob",
        "mkdir",
        "rmdir",
        "rename",
        "replace",
        "unlink",
        "touch",
        "imread",
        "imwrite",
    }
)
_MODULOS_DE_DISCO = frozenset({"os", "shutil", "tempfile"})

# Clases de terceros que abren el archivo por dentro: la llamada no menciona `open`
# ni `os`, pero acaba en disco igual. Se midió que `logging.FileHandler` normaliza la
# ruta con `abspath` y, ante un nombre de dispositivo, descarta cada registro sin
# protestar. Heredar de ellas sí está permitido — es como la capa las adapta.
_ABRIDORES_DE_ARCHIVO = frozenset(
    {
        "FileHandler",
        "RotatingFileHandler",
        "TimedRotatingFileHandler",
        "WatchedFileHandler",
    }
)


def _nombre_invocado(nodo: ast.Call) -> str | None:
    """Nombre relevante de una llamada, o ``None`` si pasa por la capa de acceso.

    Distinguir el receptor es lo que separa ``ruta.read_bytes()`` —acceso directo,
    prohibido— de ``filesystem.read_bytes(ruta)`` —a través de la capa, correcto—.
    """
    if isinstance(nodo.func, ast.Attribute):
        receptor = nodo.func.value
        if isinstance(receptor, ast.Name):
            if receptor.id == _MODULO_CAPA:
                return None
            if receptor.id in _MODULOS_DE_DISCO:
                return f"{receptor.id}.{nodo.func.attr}"
        return nodo.func.attr
    if isinstance(nodo.func, ast.Name):
        return nodo.func.id
    return None


def _accesos_en(archivo: Path) -> list[tuple[int, str]]:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
    hallazgos: list[tuple[int, str]] = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        nombre = _nombre_invocado(nodo)
        if nombre is None:
            continue
        if (
            nombre in _METODOS_DE_DISCO
            or nombre in _ABRIDORES_DE_ARCHIVO
            or nombre.split(".")[0] in _MODULOS_DE_DISCO
        ):
            hallazgos.append((nodo.lineno, nombre))
    return hallazgos


def _modulos_de_produccion() -> list[Path]:
    return sorted(p for p in RAIZ_PRODUCCION.rglob("*.py") if p.name != MODULO_EXENTO)


def test_ningun_modulo_de_produccion_toca_el_disco_por_su_cuenta() -> None:
    infracciones: list[str] = []
    for archivo in _modulos_de_produccion():
        relativo = archivo.relative_to(RAIZ_PRODUCCION.parent.parent)
        infracciones += [
            f"{relativo}:{linea} -> {nombre}()" for linea, nombre in _accesos_en(archivo)
        ]

    assert not infracciones, (
        f"{len(infracciones)} accesos directos al filesystem fuera de la capa "
        f"(ADR-004):\n  " + "\n  ".join(infracciones)
    )


def test_la_regla_detecta_un_handler_que_abre_el_archivo_por_dentro(tmp_path: Path) -> None:
    """La regla tiene que ver lo que no dice `open`: se comprueba, no se supone.

    Sin esto no habría forma de saber si la regla pasa por estar bien o por no
    mirar; la versión anterior dejaba entrar `logging.FileHandler` sin protestar.
    """
    culpable = tmp_path / "culpable.py"
    culpable.write_text("import logging\nh = logging.FileHandler('run.log')\n", encoding="utf-8")
    assert _accesos_en(culpable) == [(2, "FileHandler")]


def test_heredar_del_handler_para_adaptarlo_si_esta_permitido(tmp_path: Path) -> None:
    """Es exactamente lo que hace la capa: envolverlo, no usarlo tal cual."""
    correcto = tmp_path / "correcto.py"
    correcto.write_text(
        "import logging\nclass Propio(logging.FileHandler):\n    pass\n", encoding="utf-8"
    )
    assert _accesos_en(correcto) == []


def test_la_capa_de_acceso_existe_y_esta_exenta() -> None:
    """La exención solo tiene sentido si el módulo exento realmente existe."""
    assert (RAIZ_PRODUCCION / "ingest" / MODULO_EXENTO).is_file()


def test_el_dominio_puro_no_importa_nada_de_infraestructura() -> None:
    """`core/` no puede depender de la capa de acceso ni de librerías de IO."""
    prohibidos = {"os", "shutil", "cv2", "numpy", "media_optimizer.ingest"}
    for archivo in sorted((RAIZ_PRODUCCION / "core").rglob("*.py")):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                nombres = {alias.name for alias in nodo.names}
            elif isinstance(nodo, ast.ImportFrom):
                nombres = {nodo.module or ""}
            else:
                continue
            assert not (nombres & prohibidos), f"{archivo.name} importa {nombres & prohibidos}"
