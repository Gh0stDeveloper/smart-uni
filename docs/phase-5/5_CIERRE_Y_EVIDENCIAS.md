# 5 Backend, identidad y autorización — acta técnica

## 5 Backend, identidad y autorización

**Estado:** las tres subfases tienen código implementado y pruebas de laboratorio; NO está finalizada la conexión de un proveedor OIDC externo, el despliegue productivo, la integración desktop/Android ni E2EE. **No considerar listo para datos personales reales.** La [lista maestra de pendientes](../PENDIENTES_SMART_UNI_2_0.md) sigue vigente y se amplía para la etapa 5.

### 5.1 API y PostgreSQL

API FastAPI con SQLAlchemy parametrizado, modelos PostgreSQL, migraciones Alembic, CRUD protegido por propietario, rol admin en BD y hashes de revocación. [Documento 5.1](5.1_API_Y_POSTGRESQL.md). Commits de implementación [cf02897](https://github.com/Gh0stDeveloper/smart-uni/commit/cf0289744f6ad68ec987809a1a7efbc23d943225) y [ead958b](https://github.com/Gh0stDeveloper/smart-uni/commit/ead958b1e2af83bee044a89a9f6ff9cde9f59643).

### 5.2 Portal Next.js

Portal TypeScript Next.js 16 con identidad OIDC (PKCE/state/nonce) y Auth.js patched beta.32, controles CSRF/sesión, BFF con access token sólo servidor y validación de roles por API. Reutiliza icono original. [Documento 5.2](5.2_PORTAL_NEXT_JS.md). [Commit principal 879f156](https://github.com/Gh0stDeveloper/smart-uni/commit/879f15660bb0b0753bbbae575c21286285fe094e).

### 5.3 Cuentas y permisos

JWT RS256 y JWKS configurado, propietariado por Identity.id DB, rechazo de rol en JWT, sesiones revocables para esta API, logout BFF con revocación tentativa, protección de orígenes y topes PBKDF2 heredado. [Documento 5.3](5.3_CUENTAS_Y_PERMISOS.md). No existe IdP conectado ni login/OIDC interactivo probado en producción.

## Pruebas verificadas

| Área | Resultado | CI |
|---|---|---|
| FastAPI + Postgres real | 14/14 tests, RSA sintético real, migración y rollback, denegación cross-owner y revocación selectiva | [Backend #42226125117](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42226125117) |
| Next.js / BFF | 3/3 tests, TypeScript y build; GET anónimo /api/notes y /api/admin/metrics → 401; POST sin Origin → 403 | [Web #42225751848](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42225751848) |
| Windows y Linux desktop | 68 tests descubiertos: 42 ejecutados correctos y 26 omitidos (22 SQLCipher y 4 Rust FFI se prueban en otras suites). Mantiene diseño original. | [Desktop #42225588765](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42225588765) |
| Compilación EXE | Build de prototipo Windows correcto tras corrección PBKDF2 | [EXE #42225588563](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42225588563) |

**Límite de evidencia:** los JWT de pruebas tienen firma real pero el JWKS se proporciona mediante fixture local, sin conexión a IdP real. El portal compila y rechaza peticiones HTTP anónimas, pero no se comprobó login real con Keycloak/otro proveedor. No se ha ejecutado sincronización entre plataformas ni cifrado E2EE de notas/archivos. La API usa contenidos de ensayo en claro hasta definir E2EE. Las credenciales y cookies reales tras proxy/TLS aún se deben probar.

## Decisión de continuidad

Se acepta esta etapa como **base técnica implementada y probada**, no un sistema de identidad productivo. Las comprobaciones de autorización backend se han demostrado, pero no remedian la autorización del servicio local desktop ni todas las obligaciones del registro P01–P36. Las etapas **6–10 permanecen pendientes**, especialmente E2EE, almacenamiento y sincronización real. No se publicará portal/servicio a usuarios reales sin revisar las condiciones pendientes.
