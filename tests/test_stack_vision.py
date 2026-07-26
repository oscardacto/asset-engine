"""Humo del stack de visión (HU-152/ADR-002): wheels CPU importables y deterministas.

Se re-ejecuta en cada corrida de pytest, de modo que cualquier actualización futura
del lock re-verifica los wheels automáticamente.
"""

import cv2
import numpy as np


def test_build_de_opencv_es_cpu_only() -> None:
    assert "NVIDIA CUDA: YES" not in cv2.getBuildInformation()


def test_operacion_de_vision_es_determinista() -> None:
    rng = np.random.default_rng(seed=42)
    img = rng.integers(0, 256, size=(64, 64, 3), dtype=np.uint8)
    primera = cv2.GaussianBlur(img, (5, 5), 1.5)
    segunda = cv2.GaussianBlur(img, (5, 5), 1.5)
    assert np.array_equal(primera, segunda)
