# Feedback — HU-064+061+065
- **HU-056 no se cierra aunque el motor exista**: "declarados en el perfil" exige E6.
  Cerrarla ahora inflaría el avance — el plan aún es dato embebido con TODO(HU-135).
- **2m27s / 16 fotos** de celular queda anotado para HU-063: el revelado es O(n) sobre
  megapíxeles y las fotos de 200 MP dominarán el lote completo. Sin presupuesto no se
  optimiza a ciegas.
- imencode sin EXIF resolvió HU-061 por construcción: no hay metadatos que limpiar si
  nunca se escriben.
