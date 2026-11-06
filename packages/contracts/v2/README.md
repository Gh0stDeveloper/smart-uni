# Contrato de sincronización SMART UNI v2 (etapa 7)

Este protocolo es **independiente** del contrato local v1 de eventos históricos. No subir directamente los eventos v1 existentes: pueden contener texto claro y su actor_ref no es autenticación.

## Recursos y autenticación

Todas las rutas /api/v1/sync requieren JWT OIDC válido. El servidor obtiene owner_id exclusivamente de (issuer, sub) verificados y PostgreSQL. El usuario **nunca** envía owner_id, role ni contraseñas a la API de sincronización.

Una escritura PUT o DELETE lleva un contenedor AES-256-GCM SUAEAD01. Incluso el tombstone DELETE contiene el literal interno cifrado y autenticado tombstone:v1; no existe DELETE sin ciphertext. El servidor valida el framing, longitud y contexto, pero NO puede verificar tags GCM sin la clave de los clientes. Los clientes verifican el tag y la secuencia antes de avanzar el cursor SQLCipher.

El AAD visible y autenticado coincide exactamente con el contexto ASCII:

    sync/{owner_uuid_hex}/{resource_uuid_hex}/epoch-{epoch}/base-{base_revision}/kind-{kind}

kind es put, delete o blob. UUID hex sin guiones, epoch entero positivo y base_revision revisión previa. El contexto ata propietario, recurso, época, revisión y tipo, pero **NO reemplaza control de acceso**. El secreto E2EE de 32 bytes debe distribuirse a dispositivos autorizados mediante un mecanismo aún no implementado en UI/Android. El servidor no recibe ese secreto.

## Cambios incrementales

- POST /api/v1/sync/push: operación UUID idempotente, resource UUID, base_revision, epoch, tipo y ciphertext_b64. Si la revisión coincide, crea una revisión nueva y cursor secuencial; devuelve ack. Un operation_id repetido con el mismo contenido devuelve duplicate=true sin nuevo evento. Reutilizar el mismo UUID con otros bytes se rechaza.
- GET /api/v1/sync/pull?cursor=N&limit=30: log ordenado por dueño, revisiones y ciphertext (hasta 100 por página) con has_more y high_watermark. El cursor se confirma localmente solo tras descifrar/autenticar TODOS los cambios de la página.
- Una escritura con base antigua responde 409 y crea un conflicto con la versión candidata cifrada, sin pisar la versión aceptada. GET /api/v1/sync/conflicts lista las propuestas pendientes; POST /push con resolve_conflict_id y nuevos bytes cifrados sobre el base_revision actualizado resuelve manualmente. POST /conflicts/{id}/dismiss conserva la versión candidata histórica en servidor y el cliente conserva su copia local.
- Las eliminaciones son revisiones con tombstone, no borrados físicos inmediatos. No hay compactación, retención ni garbage collection porque faltan confirmaciones de todos los dispositivos.

## Materiales cifrados reanudables

- POST /api/v1/sync/blobs/init acepta blob UUID, resource UUID, base_revision, epoch, sha256 y tamaño total del ciphertext.
- PUT /api/v1/sync/blobs/{id}/parts/{i} carga hasta 128 KiB por parte, validando X-Chunk-Sha256. Cargar la misma parte dos veces es idempotente; cambiar bytes previamente recibidos se rechaza.
- Repetir init devuelve received_parts para reanudar tras fallo o reinicio. POST /complete verifica todos los fragmentos, SHA-256 total y SUAEAD01 del contexto del propietario/recurso, sin descifrar.
- GET /api/v1/sync/blobs/{id}/manifest y /parts/{i} permiten descarga cifrada con reanudación y comprobación independiente de SHA-256. GET /blobs/{id} permite un acceso completo a ciphertext con tamaño máximo de 8 MiB y cabecera.

**Límites:** por ahora máximo 8 MiB por contenedor Rust + cabecera, 128 KiB por fragmento, 16 uploads incompletos por usuario; los blobs se mantienen en tablas bytea de PostgreSQL, no en S3/almacenamiento distribuido. No se admiten paquetes de contenido en claro. Los IDs, tamaños, épocas, frecuencias y cursor siguen visibles al servidor.

## Garantías y deuda explícita

No hay todavía login OIDC real del escritorio, alta/posesión de claves HPKE, Android en ejecución, firma de tombstones contra un servidor malicioso, recuperación/rotación automática, monitorización, rate limiting en edge, RLS DB, GC de chunks, sync automático del JSON legacy, resolución de conflictos dentro de la UI ni despliegue remoto HTTPS. La API plaintext de notas v1 está **deshabilitada por defecto**; el operador puede reactivarla SOLO para demos sintéticas mediante SMARTUNI_DEMO_PLAINTEXT_NOTES=1, opción insegura no válida para producción. Aunque el contenido de /sync esté cifrado, esto no convierte toda la aplicación en un producto E2EE certificado.

Ver [etapa 7 y pruebas](../../../docs/phase-7/7_CIERRE_Y_EVIDENCIAS.md) y [pendientes](../../../docs/PENDIENTES_SMART_UNI_2_0.md).
