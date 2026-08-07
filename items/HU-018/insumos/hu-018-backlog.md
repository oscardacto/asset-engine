# Insumo — HU-018 en el backlog

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-018 | Reporte `inventory` (`report inventory`): tabla por asset (dims, orientación, flags — formato Maestro §8.2) | HU-017 | P0 | S |

Primer reporte real del registro. El formato de referencia es la tabla de auditoría
manual del Maestro §8.2 del cliente 0: una fila por asset con sus datos técnicos.
Los flags de calidad (WhatsApp, bajo el nativo) llegan con sus HUs (007, 008) y se
incorporan al reporte de forma aditiva; hoy el catálogo aporta dims, orientación y
cuarentena.
