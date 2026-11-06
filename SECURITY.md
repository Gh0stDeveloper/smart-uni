# Seguridad de SMART UNI

Este repositorio contiene un **prototipo académico**, no una aplicación apta para datos reales en producción.

## Antes de subir información

No subir archivos JSON de usuarios, bases de datos, claves privadas, tokens, certificados, llaves API ni credenciales del servidor. Los ejemplos de demostración no representan cuentas reales.

## Controles implementados parcialmente y pendientes

- Ya existe un núcleo Rust con dominio, ABI y vectores AES-256-GCM probados; cifrado de datos reales, gestión de claves y sincronización siguen **sin implementar**. Ver [etapa 3](docs/phase-3/3_CIERRE_Y_EVIDENCIAS.md).
- TLS 1.3 para las comunicaciones; cuando corresponda, cifrado de extremo a extremo sobre TLS.
- Base SQLCipher protegida solo **en modo opt-in**, con integración de keyring OS y tests sintéticos. No hay cifrado activo del JSON o materiales clásicos, no se han ensayado keyrings reales en equipos físicos y el EXE común no incorpora SQLCipher.
- API FastAPI/PostgreSQL valida tokens OIDC RS256 y permisos por propietario; portal Next.js usa Auth.js con PKCE/state/nonce y cookies protegidas. **Falta proveedor OIDC externo, refresh/logout global y despliegue HTTPS real**. Contraseñas legacy PBKDF2 ahora limitan iteraciones; Argon2id y gestión completa de credenciales siguen pendientes.
- Permisos básicos y consultas SQLAlchemy parametrizadas probados en API PostgreSQL de laboratorio; RLS, auditoría operativa, rate limiting y permisos de DB de producción siguen pendientes.
- Firmado de artefactos y verificación de actualizaciones.

**La existencia de biblioteca o pruebas sintéticas no implica protección del producto distribuido.** No introducir datos privados reales: quedan [36 pendientes abiertos o parciales](docs/PENDIENTES_SMART_UNI_2_0.md), incluido control de acceso, cifrado de adjuntos y recuperación de claves. Se exigirán pruebas en equipos reales y revisión de seguridad antes de producción.

## Informes de vulnerabilidades

Evitar publicar detalles explotables en issues públicos. Contactar de forma privada al propietario del repositorio o utilizar el canal privado de reporte de vulnerabilidades de GitHub si está habilitado.
