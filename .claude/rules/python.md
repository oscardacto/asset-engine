---
description: Estándares de código Python — límites de tamaño, tipado y convenciones de dominio.
paths:
  - "**/*.py"
---

# Estándares Python (media-optimizer)

**Límites duros** (al excederlos se refactoriza; se vuelven config de ruff cuando exista `pyproject.toml`):
- Módulo ≤ 300 líneas · clase ≤ 200 líneas · función ≤ 40 líneas · ≤ 5 parámetros · anidamiento ≤ 3 niveles
- Complejidad ciclomática ≤ 10 (ruff: `mccabe` C901)

**Obligatorio:**
- Tipado completo (mypy estricto) y docstrings en la API pública del módulo.
- Cero números mágicos — umbrales, pesos y rutas van a `config/` o al perfil de negocio.
- `core/` y `ranking/`: funciones puras, sin IO, sin importar OpenCV/ffmpeg.
- Entradas hostiles se validan antes de procesar (paths, formatos, tamaños, EXIF, unicode,
  duplicados); un archivo corrupto degrada ese asset, nunca tumba el pipeline.
- Determinismo: semillas fijas, sin dependencia del orden del filesystem.
- Toda etapa del pipeline registra tiempo, memoria pico, transformaciones aplicadas y score.
- Composición sobre herencia; fail fast en violaciones de contrato, fail safe en datos del usuario.
- `pathlib.Path`, nunca `os.path`; contratos de dominio como dataclasses (frozen cuando aplique).
- Sin estado global; video siempre en streaming (nunca cargar el video completo a RAM);
  evitar copias innecesarias de arrays NumPy — pero nunca a costa del determinismo.
- Logging estructurado del proyecto — cero `print()` en código de librería.
- Seguridad: prohibidos `eval`/`exec`, `pickle.loads` sobre datos no confiables, `yaml.load` sin
  `SafeLoader` y `subprocess(..., shell=True)` — este último admite excepción solo con
  justificación documentada en un ADR. Verificable con las reglas `S` (flake8-bandit) de
  ruff cuando exista `pyproject.toml` (HU-163).
- Ningún `TODO` huérfano: todo `TODO` referencia una HU del backlog o un ADR
  (`# TODO(HU-XXX): …` / `# TODO(ADR-NNN): …`) o no entra al repo.
- Docstrings y comentarios explican **qué hace** el código, en lenguaje simple (si ayuda,
  una línea breve extra tipo "en simple: …" para entenderlo rápido). Nunca referencian
  HUs, specs ni artefactos del proceso — la trazabilidad vive en git y en `items/`
  (excepción: el `TODO(HU-XXX)` del punto anterior).
