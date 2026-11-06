# Contratos compartidos versionados de SMART UNI

Los esquemas **v1 / 1.0.0** viven en `packages/contracts/v1/`. Son especificaciones serializables para clientes Windows/Linux/Android futuros, **no** una API ni sincronización en funcionamiento. No se implementan endpoints, autenticación OIDC ni cambios sobre el JSON de usuarios durante 2.2.

| Archivo | Contenido |
|---|---|
| `registry.json` | Versión, IDs, operaciones de dominio y códigos de error estables |
| `envelope.schema.json` | Envoltorio de operación futuro con ID para idempotencia, base revision opcional y fecha UTC |
| `error.schema.json` | Código de error normalizado, mensaje seguro y detalles opcionales |
| `legacy-json.schema.json` | Descripción de compatibilidad del almacenamiento JSON local versión 1 |
| `examples/` | Mensajes sintéticos válidos y ejemplo de versión rechazada |

**Reglas:** IDs locales de entidad = UUID hex minúscula de 32 caracteres; `actor_ref` = correo local normalizado solo como referencia, **nunca identidad autenticada**. Una API deberá obtener la identidad real de su sesión validada y verificar propietario del recurso, ignorando un `actor_ref` controlado por cliente para autorización. El `operation_id` reserva formato para futuras operaciones idempotentes, pero actualmente no existe cola ni protocolo de sincronización. `base_revision` es una propuesta de control de concurrencia, no una revisión del JSON actual.

Versionado semántico: añadir campos opcionales preserva compatibilidad dentro de 1.x; cambiar nombres/códigos o retirar campos exige nueva versión mayor. Los clientes deben rechazar una versión mayor desconocida (no ignorarla silenciosamente). Las operaciones del registro son una **propuesta de mensajes**, no un compromiso de disponibilidad ni implementación de UI.

**Validación real de esquema:** `python -m pip install jsonschema==4.23.0` y `python scripts/check_contracts.py` desde raíz. GitHub Actions ejecuta ese mismo validador con `Draft202012Validator`, incluyendo fixtures positivos, inválidos y consistencia de enums. Las pruebas unitarias usan stdlib para no añadir paquetes a la ejecución de escritorio. Prohibido introducir datos privados, hashes reales, tokens o secretos en ejemplos.

**Evidencia registrada:** [validación de contratos JSON Schema y fixtures](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42162128182) en el commit [0a02c42](https://github.com/Gh0stDeveloper/smart-uni/commit/0a02c42c22d481c34bf20d374ac2bc2dead50000). El contrato continúa sin implementación de backend o cliente Android.
