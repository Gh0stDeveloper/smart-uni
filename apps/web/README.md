# SMART UNI 2.0 — Portal Next.js / Auth.js

**Estado:** aplicación Next.js compilada y validada en CI, pero no desplegada ni conectada a un proveedor OIDC real. La API demo de notas en claro responde 410 por defecto y el formulario se oculta. El canal de sync v2 cifrado no cuenta todavía con editor E2EE web. Usar solo datos sintéticos. Ver [cierre técnico](../../docs/phase-5/5_CIERRE_Y_EVIDENCIAS.md).

## Diseño y seguridad

- Next.js 16.4.5, TypeScript, Auth.js next-auth 5.0.0-beta.32 (versión parcheada).
- Keycloak/OIDC Authorization Code con `checks: ["pkce", "state", "nonce"]`. Las credenciales del cliente confidencial se leen solo del servidor.
- JWT de sesión cifrada/cookie HttpOnly gestionados por Auth.js. El token de acceso API queda en callback JWT del servidor y nunca en la sesión pública del navegador.
- El BFF comprueba identidad concreta, caducidad, rutas backend fijas, HTTPS en producción, sin redirects ni cache de datos privados. Operaciones POST exigen Origin exacto para frenar CSRF.
- Backend determina roles/propietario en PostgreSQL. Un supuesto rol admin del cliente no da acceso. Botón de salida intenta revocar bearer de esta API y después borrar cookie local; falta logout global del IdP.
- Se conserva el icono PNG original SMART UNI, paleta azul/turquesa y diseño sin panel derecho adicional.

## Configuración y reproducción

Ver [plantilla .env.example](.env.example). Definir con credenciales reales en el gestor de secretos:

- `AUTH_SECRET`: aleatorio de al menos 32 caracteres.
- `AUTH_URL` y `PORTAL_ORIGIN`: mismo origen HTTPS del portal productivo.
- `AUTH_KEYCLOAK_ISSUER`, `AUTH_KEYCLOAK_ID` y `AUTH_KEYCLOAK_SECRET`.
- `SMARTUNI_API_INTERNAL_URL`: HTTPS del backend, no URL elegida por el navegador.

El IdP debe registrar callback exacto de Auth.js, habilitar PKCE S256 y entregar **access tokens JWT con aud smartuni-api**. Esto necesita configuración del IdP; introducir variables no habilita automáticamente el acceso.

Desde apps/web:

    npm install
    npm run test
    npm run typecheck
    npm run build
    npm run dev

Para desarrollo, se admite Origin HTTP solo en localhost/127.0.0.1; en producción es obligatorio HTTPS. La resolución de dependencias se archiva como artefacto de GitHub CI; el lockfile persistente/SBOM y firma de paquetes siguen abiertos en P09.

## Pruebas y pendientes

El [workflow web](https://github.com/Gh0stDeveloper/smart-uni/actions/workflows/web-portal.yml) prueba TypeScript, build, seguridad de origen, URL fija del API y rutas HTTP sin sesión. No prueba acceso interactivo con IdP de producción ni cookies detrás de reverse proxy. No hay token refresh operativo ni sincronización entre escritorio y Android; revisar [registro maestro P01–P52](../../docs/PENDIENTES_SMART_UNI_2_0.md).

## Estado de sincronización etapa 7

El portal detecta HTTP 410 del antiguo CRUD de notas y no muestra formulario sin habilitación de demo. El backend ciphertext-only existe y se prueba con clientes Rust/SQLCipher, **no** con un editor E2EE en el navegador. Falta provisión de claves, sesión/refresh real de IdP y UI de conflictos. [Acta y limitaciones](../../docs/phase-7/7_CIERRE_Y_EVIDENCIAS.md).
