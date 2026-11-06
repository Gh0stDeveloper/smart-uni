# Contratos versionados de SMART UNI 2.0

Los protocolos **v1 y v2 son distintos**: no subir automáticamente el outbox v1 histórico porque puede contener texto claro y el actor_ref no es identidad.

- [Contratos v1](v1/): dominio y almacenamiento local, actor_ref de correo no autenticado y operaciones antiguas. Mantener compatibilidad del prototipo.
- [Contratos v2 de sincronización](v2/): cambios ciphertext-only SUAEAD01, UUID de operación/recurso, base_revision, epoch, tombstones y blobs cifrados reanudables con SHA-256. La API extrae propietario exclusivamente de JWT OIDC verificado y PostgreSQL, nunca de parámetros del cliente. Esquemas: [sync-change.schema.json](v2/sync-change.schema.json) y [sync-blob-init.schema.json](v2/sync-blob-init.schema.json).

**Estado:** servidor PostgreSQL y cliente SQLCipher/Rust validados con pruebas E2E de laboratorio. No existen login OIDC desktop ni Android ejecutable; las claves fueron compartidas manualmente en tests. Nunca usar claves ni datos privados reales en fixtures.

Validación actual: python scripts/check_contracts.py (JSON Schema v1 y fixtures) en GitHub Actions, y pruebas API/E2E v2. Quedan pendientes validaciones de fixtures v2 adicionales y pruebas con dispositivos reales. [Acta 7](../../docs/phase-7/7_CIERRE_Y_EVIDENCIAS.md) · [52 pendientes](../../docs/PENDIENTES_SMART_UNI_2_0.md).
