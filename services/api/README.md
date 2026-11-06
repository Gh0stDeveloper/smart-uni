# SMART UNI — API FastAPI + PostgreSQL

**Estado:** backend probado contra PostgreSQL real, pero sin desplegar y sin IdP externo conectado. El CRUD de notas legacy en claro está DESHABILITADO por defecto (HTTP 410); el nuevo /api/v1/sync guarda únicamente ciphertext SUAEAD01. Sin despliegue ni IdP real, solo datos sintéticos. Consultar [registro de pendientes](../../docs/PENDIENTES_SMART_UNI_2_0.md).

## Componentes técnicos

- FastAPI 0.162.0, SQLAlchemy 2.0.51, psycopg3 y migraciones Alembic. Se rechaza SQLite en lugar de PostgreSQL.
- Tablas base: identities, notes (demo legacy), revoked_tokens; fase 7 añade sync_owner_state, sync_resources, sync_versions, sync_conflicts, sync_blobs y sync_blob_parts (cifrado, CAS e idempotencia).
- JWT RS256 con issuer, audience, sub, iat y exp obligatorios; JWKS HTTPS definido desde entorno. Nunca se acepta jku/x5u elegido por el token, roles del cuerpo de la petición o actor_ref del cliente.
- Cuentas nuevas con rol student, nunca admin; solo operador de DB autorizado promueve manualmente la identidad revisando issuer y subject.
- Lectura y escritura de apuntes con filtro owner_id del servidor. Acceso a recursos ajenos responde 404.
- POST /api/v1/sessions/revoke invalida ese JWT para esta API, sin revocar sesiones del proveedor externo.

## Variables requeridas

Copiar nombres de [plantilla .env.example](.env.example) a un gestor de secretos, nunca versionar valores reales.

- `DATABASE_URL`: URL privada postgresql+psycopg://usuario:clave@host:5432/db.
- `OIDC_ISSUER`: issuer HTTPS exacto del IdP.
- `OIDC_AUDIENCE`: audience del resource server, normalmente smartuni-api.
- `OIDC_JWKS_URL`: endpoint de claves públicas HTTPS configurado por operador.

Ejecutar desde la raíz del repositorio, en un equipo con PostgreSQL 16 disponible:

    python -m pip install -r services/api/requirements.txt
    alembic -c services/api/alembic.ini upgrade head
    python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000
    pytest services/api/tests/test_api.py services/api/tests/test_sync.py -q
    # Los E2E de Rust/SQLCipher se ejecutan en sync-e2e.yml con deps adicionales.

Las migraciones requieren permisos DDL; en producción usar un rol separado de migraciones y otro de operación, con permisos mínimos. No exponer el puerto sin reverse proxy HTTPS, control de tráfico y auditoría.

## Endpoints

- GET /healthz — liveness sin inspección de DB.
- GET /api/v1/me — identidad y rol efectivos de PostgreSQL.
- CRUD /api/v1/notes legacy: **410 por defecto**. Habilitar solo pruebas sintéticas con SMARTUNI_DEMO_PLAINTEXT_NOTES=1; NUNCA en producción.
- GET /api/v1/admin/metrics — solo rol administrativo de BD.
- POST /api/v1/sessions/revoke — revocación del bearer actual.

- /api/v1/sync/push y /pull: operaciones cifradas, ACK idempotente, cursor, revisiones y tombstones.
- /api/v1/sync/conflicts y /dismiss: propuestas cifradas sin sobrescribir.
- /api/v1/sync/blobs/init, /parts/{index}, /complete, /manifest, /blobs/{id}: subida/descarga cifrada reanudable con SHA-256.

No hay API propia de contraseñas, autosubscripción admin ni endpoints de APK. El protocolo sync no genera/entrega claves ni sustituye un enrolamiento HPKE autenticado.

## Evidencia y límites

[Workflow backend](https://github.com/Gh0stDeveloper/smart-uni/actions/workflows/backend-api.yml): PostgreSQL 16 real, alembic upgrade/downgrade/upgrade, firmas RSA de test y aislamiento de cuentas, JWT manipulados y revocación. Fixture JWKS es local para evitar depender de una cuenta real; NO verifica descubrimiento/JWKS ni login de un proveedor OIDC remoto.

Falta despliegue, RLS como defensa adicional, limitación de tráfico, operación/backup y revisión externa de seguridad. Consultar los pendientes P02, P15, P16, P17, P18 y P01–P52 antes de tratarlo como listo para datos reales.

## Etapa 7 — Sincronización ciphertext-only

[Contrato v2](../../packages/contracts/v2/README.md) · [Acta y pruebas E2E](../../docs/phase-7/7_CIERRE_Y_EVIDENCIAS.md). El servidor identifica al propietario solo por JWT OIDC + DB, asigna cursores/revisiones y verifica framing/sha256, pero no puede validar el tag AEAD sin clave privada del cliente. Las claves E2EE nunca se suben. El cliente Rust/SQLCipher autentica contenidos antes de avanzar. Queda pendiente IdP real, rate limiting, RLS, GC blobs, migración de nota legacy y antirollback ante servidor adversarial.
