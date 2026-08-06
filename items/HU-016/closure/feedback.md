# Feedback — HU-016

## Anti-patrones detectados
- **Rama muerta en el saneado.** La primera versión tenía un `elif not punto: tronco = limpio`
  cuyo resultado no se usaba después. Es el tercer caso de fallback inútil en el proyecto
  (HU-009, HU-011 y ahora este). **El patrón se repite lo suficiente como para vigilarlo:
  cuando una función encadena condiciones sobre partes de un texto, conviene releer si cada
  rama tiene consecuencia.**

## Decisiones rechazadas
- **Copiar los originales al directorio de trabajo** — prohibido por charter §6.3, y además
  duplicaría gigabytes sin aportar nada.
- **Verificar la intocabilidad con `mtime`** — rechazado: el sistema operativo puede
  alterarlo por su cuenta (un antivirus, una indexación). El hash de contenido es más
  estricto y hay test que lo demuestra tocando el `mtime` sin cambiar los bytes.
- **Sufijo de hash para desambiguar** — rechazado: sería inequívoco pero ilegible, y estos
  nombres los va a leer una persona en su carpeta de salidas. Numérico y determinista.
- **Crear ya las carpetas de revelados y reels** — rechazado por YAGNI: inventar layout sin
  consumidor. Nacen con sus HUs.
- **Comparar nombres ocupados de forma sensible a mayúsculas** — rechazado por la evidencia
  medida en HU-010: en NTFS eso permitiría que dos salidas se pisaran en silencio.

## Lecciones aprendidas
- **Un principio del charter se vuelve útil cuando se puede comprobar.** "No destructivo"
  llevaba 19 HUs siendo una promesa repetida en docstrings. Ahora hay una función que toma
  la huella antes y la compara después; HU-017 podrá afirmarlo con evidencia en vez de con
  confianza.
- **Leer y escribir son problemas simétricos pero opuestos, y conviene separarlos en HUs
  distintas.** ADR-004 lo delimitó explícitamente y eso hizo que esta HU llegara con el
  alcance ya recortado: no hubo que decidir nada de arquitectura, solo implementar.
