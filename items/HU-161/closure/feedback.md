# Feedback — HU-161

## Anti-patrones detectados
- (Ninguno nuevo en ejecución. El riesgo R-1 de la spec queda **pendiente de blindar**:
  un `except Exception` descuidado en código futuro se tragaría bugs — anotado para
  HU-163 activar la regla ruff `BLE001` (blind-except) cuando se configuren los gates.)

## Decisiones rechazadas
- **Envolver bugs en la jerarquía del dominio** ("para que el lote nunca se caiga") —
  rechazado y documentado en el propio módulo: degradar un bug a "asset fallido" lo
  esconde en el resumen del lote; los bugs revientan visibles.
- **Validar `reason` no vacío en el constructor de `CorruptMediaError`** — rechazado
  (A-1): una excepción debe ser barata y segura de construir dentro de un `except`;
  fallar al reportar un fallo enmascara el original. La calidad del reason la testea
  quien lo lanza.
- **Subclases finas desde ya** (`UnsupportedFormatError`, `ProfileError`) — rechazado:
  extensión aditiva cuando HU-002/136 las justifiquen.
- **Códigos de error / i18n** — rechazado: sin consumidor en el backlog.

## Lecciones aprendidas
- **La categoría más importante de una taxonomía puede ser la que se deja fuera:** el
  valor de la jerarquía no está en sus 3 clases sino en el test que garantiza que
  `ValueError` NO es capturado por la base. Definir contratos también por lo que
  excluyen, y testear la exclusión.
- **Los contratos previos alimentan al siguiente:** el precedente "violación de contrato
  = ValueError" sembrado en HU-157/158 hizo trivial la decisión de dejar los bugs fuera —
  la consistencia entre HUs de `core/` se está pagando sola.
- **Ciclo S-size en ~30 min de pared** con el patrón establecido (insumo con inventario de
  lanzadores/capturadores → spec compacta → DEV): el overhead ASDD es marginal cuando el
  patrón de la épica ya está calibrado.
