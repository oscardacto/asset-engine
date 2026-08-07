"""Flags de material degradado: fotos que llegaron dañadas por el camino.

En simple: hay fotos que técnicamente se abren bien pero ya perdieron calidad
antes de llegar — las que alguien mandó por WhatsApp (que las recomprime
brutalmente y les borra los metadatos) y las que no alcanzan la resolución que
piden los formatos de salida del negocio. Estos flags las marcan para que el
ranking las castigue y el reporte las muestre; no las descartan.

La detección de WhatsApp usa dos señales, calibradas contra el lote real del
cliente: el **nombre** que WhatsApp pone (`IMG-20260324-WA0062.jpg`), y la
**física del archivo** — metadatos borrados y una compresión mucho más agresiva
de la que usa cualquier cámara o editor. La segunda atrapa a las renombradas.
El techo de dimensiones que se usaba antaño ya no sirve: WhatsApp hoy reenvía en
alta resolución, y en el lote real las 16 fotos WA miden lo mismo que las
originales.
"""

import re

from media_optimizer.core import OutputFormat, OutputIntent

# Umbral calibrado sobre el lote real: las fotos WA pesan hasta 0.114 bytes por
# píxel; lo más comprimido que produce una cámara o un editor en el mismo lote
# pesa 0.234. El perfil de negocio puede sobreescribirlo.
WHATSAPP_MAX_BYTES_PER_PIXEL = 0.15

# El nombre con que WhatsApp guarda lo recibido: IMG-fecha-WAseguidilla.
_PATRON_NOMBRE_WA = re.compile(r"\bIMG-\d{8}-WA\d+", re.IGNORECASE)


def whatsapp_compression(
    name: str,
    size_bytes: int,
    pixels: int,
    exif_present: bool,
    *,
    max_bytes_per_pixel: float = WHATSAPP_MAX_BYTES_PER_PIXEL,
) -> bool:
    """Indica si la foto muestra las huellas de la compresión de WhatsApp.

    El nombre de WhatsApp basta por sí solo. Sin él, hacen falta las dos huellas
    físicas juntas: metadatos borrados **y** compresión más agresiva que la de
    cualquier cámara — una editada de agencia también pierde los metadatos, pero
    pesa el doble por píxel que una foto de WhatsApp.
    """
    if pixels <= 0:
        msg = f"pixels debe ser > 0, se recibió {pixels}"
        raise ValueError(msg)
    if _PATRON_NOMBRE_WA.search(name):
        return True
    return not exif_present and (size_bytes / pixels) < max_bytes_per_pixel


def below_native(
    width: int, height: int, formats: tuple[OutputFormat, ...]
) -> tuple[OutputIntent, ...]:
    """Las intenciones de salida del perfil para las que esta foto no alcanza.

    Vacío significa que la foto llena todos los formatos que el negocio produce.
    La comparación admite la foto girada: una vertical de 3060x4080 sí alcanza
    para un formato horizontal de 1920x1080, porque el recorte puede rotar el
    encuadre.
    """
    if width < 1 or height < 1:
        msg = f"las dimensiones deben ser >= 1, se recibió {width}x{height}"
        raise ValueError(msg)
    lado_mayor, lado_menor = max(width, height), min(width, height)
    return tuple(
        formato.intent
        for formato in formats
        if not (
            lado_mayor >= max(formato.width, formato.height)
            and lado_menor >= min(formato.width, formato.height)
        )
    )
