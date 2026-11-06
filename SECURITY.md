# Seguridad de SMART UNI

Este repositorio contiene un **prototipo académico**, no una aplicación apta para datos reales en producción.

## Antes de subir información

No subir archivos JSON de usuarios, bases de datos, claves privadas, tokens, certificados, llaves API ni credenciales del servidor. Los ejemplos de demostración no representan cuentas reales.

## Modelo de seguridad propuesto (no implementado)

- Ya existe un núcleo Rust con dominio, ABI y vectores AES-256-GCM probados; cifrado de datos reales, gestión de claves y sincronización siguen **sin implementar**. Ver [etapa 3](docs/phase-3/3_CIERRE_Y_EVIDENCIAS.md).
- TLS 1.3 para las comunicaciones; cuando corresponda, cifrado de extremo a extremo sobre TLS.
- Cifrado local con claves individuales y almacenes del sistema operativo.
- Argon2id en sistemas que administren contraseñas; OAuth2/OIDC con PKCE para autenticación online.
- Permisos verificados en backend, consultas SQL parametrizadas y auditoría.
- Firmado de artefactos y verificación de actualizaciones.

**Ninguna de estas medidas está implementada por el hecho de aparecer en la documentación.** Se exigirán pruebas y revisión de seguridad antes de producción.

## Informes de vulnerabilidades

Evitar publicar detalles explotables en issues públicos. Contactar de forma privada al propietario del repositorio o utilizar el canal privado de reporte de vulnerabilidades de GitHub si está habilitado.
