# 7 Sincronización multiplataforma — acta de cierre técnico

## 7 Sincronización multiplataforma

**Estado al 6 de noviembre de 2026:** se implementaron 7.1, 7.2 y 7.3 como **motor de laboratorio cifrado** con API FastAPI/PostgreSQL y cliente Python/SQLCipher/Rust. Se verificó el intercambio entre dos instancias con la misma clave sintética. **No se desplegó un servidor real, no hay proveedor OIDC real ni aprovisionamiento de claves por dispositivo y la app Android todavía no existe; el producto ordinario NO se sincroniza automáticamente**. No se autoriza almacenar datos de estudiantes reales. [Registro maestro: 52 pendientes](../PENDIENTES_SMART_UNI_2_0.md).

### 7.1 Sincronización incremental

[Documento](7.1_SINCRONIZACION_INCREMENTAL.md). Nuevo contrato v2 ciphertext-only en [packages/contracts/v2](../../packages/contracts/v2/README.md): identificadores UUID, revisión CAS, cursor por propietario, ACK idempotente y reintentos durables del cliente. El cliente SQLCipher no envía la cola v1 (que puede contener información sin cifrar). Los paquetes AEAD SUAEAD01 llevan propietario/recurso/revisión/tipo en AAD; el cliente Rust autentica TODO un lote antes de confirmarlo localmente. El servidor deriva propietario del JWT OIDC, no acepta owner enviado por cliente.

Evidencias: [PostgreSQL API 22 pruebas](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42270287641); [6 pruebas end-to-end con SQLCipher, Rust y PostgreSQL](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42270199022), incluyendo corte tras COMMIT y respuesta de ACK perdida sin doble escritura.

### 7.2 Conflictos y eliminaciones

[Documento](7.2_CONFLICTOS_Y_ELIMINACIONES.md). Historial inmutable de versiones aceptadas, conflictos preservados como ciphertext, revisión optimista protegida con bloqueo por propietario. Se verificó caso concurrente con un ACK y un 409, resolución manual elegida por cliente y cifrada de nuevo contra revisión más reciente, y tombstones cifrados autenticados como revisiones. La opción de descartar conflicto conserva la propuesta candidata local sin sobrescribir. **Sin CRDT, UI de resolución ni anti-rollback criptográfico del log frente a un servidor malicioso**.

Evidencia: [tests API PostgreSQL](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42270287641) y [E2E cliente real](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42270199022).

### 7.3 Materiales y archivos

[Documento](7.3_MATERIALES_Y_ARCHIVOS.md). Subida en fragmentos cifrados de 128 KiB, reanudación tras cortes, duplicados seguros, verificación SHA-256 por parte y total, referencia a blobs solo si corresponden a propietario/recurso/epoch/revisión. Descarga con manifiesto cifrado, partes SQLCipher recuperables y descifrado en memoria Rust. **Máximo 8 MiB de plaintext por contenedor**; el servidor no recibe clave de contenido, pero puede ver IDs/tamaño/frecuencia/epoch y validar framing SHA-256, no el tag AEAD sin clave.

Evidencia: [PostgreSQL: fuera de orden, corrupción, reanudación, aislamiento](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42270287641); [E2E: upload parcial, reanudación y descarga entre dos clientes](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42270199022).

## Resultados y criterio de pruebas

| Área | Resultado registrado | Evidencia |
|---|---|---|
| Backend FastAPI/PostgreSQL 16 | **22 pruebas** incluidas aislamiento OIDC, CAS/409, historia/tombstone, blobs corruptos y gate de plaintext. Downgrade/re-upgrade Alembic validado. | [Backend #42270287641](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42270287641) |
| Integración Rust + SQLCipher + PostgreSQL | **6/6 E2E** con dos bases SQLCipher sintéticas, token OIDC firmado de laboratorio, pérdida de ACK, versión remota, conflicto y reanudación. | [Sync E2E #42270199022](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42270199022) |
| Núcleo Rust y cliente Windows/Linux | 22 Rust por sistema, interoperabilidad y 5 pruebas nuevas de cliente con simulador offline por SO, SQLCipher y Rust reales; cliente Android no ejecutado. | [Rust #42270714973](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42270714973) |
| SQLCipher legado Windows/Linux | 22 tests por sistema con driver real; no incluye los E2E adicionales. | [SQLCipher — workflow](https://github.com/Gh0stDeveloper/smart-uni/actions/workflows/secure-storage.yml) |
| Portal Next.js | Build, TypeScript, 3 tests de seguridad y smoke HTTP: ahora se oculta creación de notas en claro cuando API devuelve 410. | [Portal #42270881633](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42270881633) |
| Desktop Windows/Linux | Suite heredada pasa; las suites con dependencia Rust/SQLCipher se ejecutan por separado, no confundir tests omitidos con aprobados. | [Desktop #42270714694](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42270714694) |
| EXE Windows | Prototipo clásico compila; **no empaqueta motor sync E2EE/SQLCipher/Rust**. | [Windows #42270714818](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42270714818) |

Las pruebas JWT usan claves RSA firmadas reales pero un JWKS fixture; las claves de cifrado son sintéticas y se comparten manualmente entre los dos clientes de ensayo. **No se ensayó OIDC de un proveedor real, red HTTPS externa, Android físico/emulado ni UX de sincronización de producto.** Hay históricos de pruebas en CI cuyo fallo se corrigió después; usar las ejecuciones correctas enlazadas, no asumir que cualquier commit intermedio era verde.

## Seguridad de la API antigua

El CRUD previo /api/v1/notes contenía plaintext. Se configuró deshabilitado **por defecto** con respuesta HTTP 410, y el portal de demo deja de mostrar formulario al recibir 410. Solamente puede reactivarse de forma explícita para datos sintéticos mediante SMARTUNI_DEMO_PLAINTEXT_NOTES=1; **no debe utilizarse nunca en producción**. La tabla de notas previa permanece disponible para migración y no fue eliminada. El canal /api/v1/sync usa solo ciphertext SUAEAD01, pero no se puede afirmar que todos los flujos antiguos ya estén cifrados.

## Decisiones y pendientes heredados

El [registro maestro P01–P52](../PENDIENTES_SMART_UNI_2_0.md) mantiene abiertos: P15/P37/P38/P45 (provisión HPKE autorizada, rotación), P18/P44/P46/P47 (login escritorio y adaptación de acciones al outbox v2), P48 (resolución UI), P49/P52 (cuotas, retención y compactación), P34/P40/P50 (eliminación de rutas de texto claro), P51 (pruebas con SO y dispositivos reales). Los materiales >8 MiB, visor externo seguro, backups y secretos de hardware continúan pendientes.

**Cierre técnico de la etapa 7:** backend cifrado y cliente de sincronización experimental integrados y probados, con límites explícitos. La siguiente etapa oficial es [8 Aplicación Android](../ROADMAP.md). No anunciar disponibilidad multi-dispositivo para usuarios reales antes de completar los pendientes.
