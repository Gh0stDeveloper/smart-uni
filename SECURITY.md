# Seguridad de SMART UNI

Este repositorio contiene un **prototipo académico**, no una aplicación apta para datos reales en producción.

## Antes de subir información

No subir archivos JSON de usuarios, bases de datos, claves privadas, tokens, certificados, llaves API ni credenciales del servidor. Los ejemplos de demostración no representan cuentas reales.

## Controles implementados parcialmente y pendientes

- Rust incorpora contenedor `SUAEAD01` AES-256-GCM autenticado, recuperación `SURECV01` Argon2id y HPKE X25519 de laboratorio. El modo SQLCipher opt-in cifra copias nuevas de materiales con motor Rust. El nuevo canal /api/v1/sync solo acepta SUAEAD01 y el cliente Rust autentica antes de avanzar cursor. El JSON legacy y portal no disponen de integración E2EE real: **no existe E2EE de producto ni prueba de historial anti-rollback frente a servidor malicioso**. [Etapa 6](docs/phase-6/6_CIERRE_Y_EVIDENCIAS.md).
- Se exige TLS 1.3 en un despliegue futuro; todavía no hay endpoints de producción conectados. TLS no sustituye E2EE ni autorización.
- Base SQLCipher protegida solo **en modo opt-in**; archivos nuevos de hasta 8 MiB se guardan cifrados por Rust, con claves de contenido separadas de la clave DB y paquetes Argon2id recuperables. El origen importado sigue externo, el modo JSON es claro, el visor externo está bloqueado, el EXE común no incorpora Rust/SQLCipher ni se han probado keyrings OS físicos.
- API FastAPI/PostgreSQL valida tokens OIDC RS256 y permisos por propietario; portal Next.js usa Auth.js con PKCE/state/nonce y cookies protegidas. **Falta proveedor OIDC externo, refresh/logout global y despliegue HTTPS real**. Contraseñas legacy PBKDF2 ahora limitan iteraciones; Argon2id y gestión completa de credenciales siguen pendientes.
- Permisos básicos y consultas SQLAlchemy parametrizadas probados en API PostgreSQL de laboratorio; RLS, auditoría operativa, rate limiting y permisos de DB de producción siguen pendientes.
- Firmado de artefactos y verificación de actualizaciones.

**La existencia de biblioteca o pruebas sintéticas no implica protección del producto distribuido.** No introducir datos privados reales: quedan [52 pendientes abiertos o parciales](docs/PENDIENTES_SMART_UNI_2_0.md), incluido control de acceso, cifrado de adjuntos y recuperación de claves. Se exigirán pruebas en equipos reales y revisión de seguridad antes de producción.

## Informes de vulnerabilidades

Evitar publicar detalles explotables en issues públicos. Contactar de forma privada al propietario del repositorio o utilizar el canal privado de reporte de vulnerabilidades de GitHub si está habilitado.

## Etapa 7: protocolo E2EE experimental

FastAPI recibe únicamente ciphertext en /api/v1/sync y deriva propietario de OIDC; el cliente SQLCipher/Rust autentica tags AEAD y tombstones. El CRUD de notas legacy en claro está deshabilitado **por defecto** y devuelve HTTP 410. SMARTUNI_DEMO_PLAINTEXT_NOTES=1 es exclusivamente para pruebas sintéticas, no distribución; la tabla notes previa todavía no se ha migrado ni borrado.

No hay provisión de clave verificada por dispositivo, IdP real, Android activo, anti-rollback firmado, cuotas completas, RLS ni auditoría externa. El EXE clásico sigue en JSON/credenciales demo. [Acta 7](docs/phase-7/7_CIERRE_Y_EVIDENCIAS.md).
