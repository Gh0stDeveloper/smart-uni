# Seguridad de SMART UNI

Este repositorio contiene un **prototipo académico**, no una aplicación apta para datos reales en producción.

## Antes de subir información

No subir archivos JSON de usuarios, bases de datos, claves privadas, tokens, certificados, llaves API ni credenciales del servidor. Los ejemplos de demostración no representan cuentas reales.

## Controles implementados parcialmente y pendientes

- Rust incorpora contenedor `SUAEAD01` AES-256-GCM autenticado, recuperación `SURECV01` Argon2id y HPKE X25519 de laboratorio. El modo SQLCipher opt-in cifra copias nuevas de materiales con motor Rust. No se protegen los JSON/archivos legacy ni los apuntes remotos; **no existe E2EE end-to-end efectivo en producción**. [Etapa 6](docs/phase-6/6_CIERRE_Y_EVIDENCIAS.md).
- Se exige TLS 1.3 en un despliegue futuro; todavía no hay endpoints de producción conectados. TLS no sustituye E2EE ni autorización.
- Base SQLCipher protegida solo **en modo opt-in**; archivos nuevos de hasta 8 MiB se guardan cifrados por Rust, con claves de contenido separadas de la clave DB y paquetes Argon2id recuperables. El origen importado sigue externo, el modo JSON es claro, el visor externo está bloqueado, el EXE común no incorpora Rust/SQLCipher ni se han probado keyrings OS físicos.
- API FastAPI/PostgreSQL valida tokens OIDC RS256 y permisos por propietario; portal Next.js usa Auth.js con PKCE/state/nonce y cookies protegidas. **Falta proveedor OIDC externo, refresh/logout global y despliegue HTTPS real**. Contraseñas legacy PBKDF2 ahora limitan iteraciones; Argon2id y gestión completa de credenciales siguen pendientes.
- Permisos básicos y consultas SQLAlchemy parametrizadas probados en API PostgreSQL de laboratorio; RLS, auditoría operativa, rate limiting y permisos de DB de producción siguen pendientes.
- Firmado de artefactos y verificación de actualizaciones.

**La existencia de biblioteca o pruebas sintéticas no implica protección del producto distribuido.** No introducir datos privados reales: quedan [43 pendientes abiertos o parciales](docs/PENDIENTES_SMART_UNI_2_0.md), incluido control de acceso, cifrado de adjuntos y recuperación de claves. Se exigirán pruebas en equipos reales y revisión de seguridad antes de producción.

## Informes de vulnerabilidades

Evitar publicar detalles explotables en issues públicos. Contactar de forma privada al propietario del repositorio o utilizar el canal privado de reporte de vulnerabilidades de GitHub si está habilitado.
