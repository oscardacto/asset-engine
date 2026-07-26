---
description: Estándares de código Python — límites de tamaño, tipado y convenciones de dominio.
paths:
  - "**/*.py"
---

# Estándares Python (media-optimizer)

**Límites duros** (al excederlos se refactoriza; se vuelven config de ruff cuando exista `pyproject.toml`):
- Módulo ≤ 300 líneas · función ≤ 40 líneas · ≤ 5 parámetros · anidamiento ≤ 3 niveles

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
