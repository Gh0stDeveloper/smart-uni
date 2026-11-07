# SMART UNI 8 Aplicación Android

Cliente nativo experimental desarrollado en **Java** (interfaz/accesibilidad), **C++/JNI** (adaptador HTTPS, sin rutas o secretos en Java) y **smartuni-core Rust** (AEAD interoperable). Misma paleta e isotipo original del escritorio.

**Estado:** código de laboratorio de 8.1 y parte de 8.2/8.3. No contiene login OIDC/PKCE, sincronización multiusuario, base SQLCipher Android, recuperación de dispositivos ni enrolamiento HPKE. No cargar información personal real. La sección Apuntes, Tareas y Calendario almacena varios registros locales cifrados; Materiales permite importar contenidos cifrados y vista previa exclusivamente de texto. Son funciones experimentales sin sync. Aún no equivale al conjunto completo de funciones del escritorio. Nunca muestra "sincronizado" sin ACK.

## Compilación desde fuente

Requiere Java 17, Gradle 8.9, Android SDK 35, NDK 27.2.12479018, CMake 3.22.1 y Rust estable. Instalar targets:

```bash
rustup target add aarch64-linux-android x86_64-linux-android
export NDK="$ANDROID_HOME/ndk/27.2.12479018"
export CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER="$NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android26-clang"
export CARGO_TARGET_X86_64_LINUX_ANDROID_LINKER="$NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/x86_64-linux-android26-clang"
cargo build --manifest-path core/rust/Cargo.toml --release --target aarch64-linux-android
cargo build --manifest-path core/rust/Cargo.toml --release --target x86_64-linux-android
cd apps/android
gradle :app:assembleDebug :app:assembleRelease :app:bundleRelease
```

La ruta `core/rust/target/<triple>/release/libsmartuni_core.a` es **obligatoria**; CMake cancela si falta Rust, sin fallback en claro. Debug APK se firma con certificado de depuración, **no distribuir como producción**. Los outputs de release son *sin firma* por defecto; el AAB no se puede subir a Play hasta firmarlo. El build solo cambia a firma release si se inyectan las cuatro variables `SMARTUNI_SIGNING_STORE_FILE`, `SMARTUNI_SIGNING_STORE_PASSWORD`, `SMARTUNI_SIGNING_KEY_ALIAS`, `SMARTUNI_SIGNING_KEY_PASSWORD` desde un entorno protegido. Nunca versionar llaves o contraseñas. No existe aún una firma comercial ni publicación.

## Pruebas

```bash
cd apps/android
gradle :app:connectedDebugAndroidTest
```

Test real en emulador x86_64 API 35: JNI ↔ Rust autoprueba, cifrado/descifrado AES-GCM, rechazo de corrupción y AAD incorrecto, clave envuelta en Android Keystore tras reabrir apunte, URL no HTTPS rechazada. Véase [workflow Android](../../.github/workflows/android.yml) y [acta etapa 8](../../docs/phase-8/8_CIERRE_Y_EVIDENCIAS.md) para estado de ejecución de CI.

## Límites de seguridad

- Solo almacenamiento privado de la app + Android Keystore para **envolver** la clave aleatoria local; la nota se cifra con la ABI Rust SUAEAD01 y AAD específico del archivo. Clave manejada temporalmente en Java/C++ y limpiada best-effort; strings en widgets UI pueden permanecer en memoria. No equiparar a caja fuerte contra un móvil comprometido.
- `allowBackup=false` para evitar copia desincronizada sin la llave Keystore. Desinstalar, reinstalar o perder la clave puede causar **pérdida irrecuperable** del apunte local: no hay recuperación de claves todavía.
- JNI C++ ejecuta el diagnóstico `GET /healthz` sobre `HttpsURLConnection` de Android para validar TLS/hostname con el almacén confiable del SO, sin ignorar certificados ni usar HTTP. No incorpora login, token, push/pull ni política de retry.
- No existe data store multi-registro SQLCipher ni materialización del motor de escritorio. La seguridad del servidor no depende de ocultar endpoints: la autorización es responsabilidad del backend.
- MinSdk 26, target 35, ABIs arm64-v8a y x86_64. Pruebas de dispositivos físicos, accesibilidad automatizada, persistencia tras upgrade y firma release pendientes.

## Documentación

[ROADMAP](../../docs/ROADMAP.md) · [8.1 Interfaz](../../docs/phase-8/8.1_INTERFAZ_NATIVA_JAVA.md) · [8.2 JNI](../../docs/phase-8/8.2_COMUNICACION_CPP_JNI.md) · [8.3 Rust/Keystore](../../docs/phase-8/8.3_RUST_Y_ANDROID_KEYSTORE.md) · [Pendientes](../../docs/PENDIENTES_SMART_UNI_2_0.md).

## Endurecimiento en etapa 9 (experimental)

Release usa R8 + shrinkResources, con reglas para mantener los símbolos Java necesarios para JNI. Se añadió política de verificación offline de releases en scripts/phase9_release_policy.py y SAST/beta gate; **no** implementa in-app updates, release firmado ni recuperación del vault. El workflow Android anterior #42296402993 construyó paquetes pero **falló la prueba instrumentada**; consultar docs/phase-9 y no distribuirlo a estudiantes reales.

## Segunda integración — 8.1 a 8.3

- `LocalVault.java`: bóveda JSON completamente cifrada con Rust/KeyVault y reemplazo atómico, notas múltiples editables, tareas y eventos locales. No equivale a SQLCipher ni a sincronización E2EE.
- `MaterialVault.java`: importación por selector del SO, sin almacenar temporalmente archivos en claro, cifrado local hasta 8 MiB y lectura interna de texto, sin visores externos para PDF/Office/imagen.
- `NativeBridge.apiRequest`: rutas GET /me, pull, conflicts y POST push fijadas en C++; `NativeHttpTls` utiliza certificado/hostname TLS del SO, sin redirecciones. Requiere bearer OIDC externo; aún no existe login Android, ni aplicación de eventos remotos ni ACK.
- Nuevas pruebas instrumentadas para bóveda, corrupción, Keystore y validación de URLs. Continúa pendiente su ejecución verde en el emulador y teléfonos reales.

[Segundo commit de implementación](https://github.com/Gh0stDeveloper/smart-uni/commit/c0203af7ebdc822fac6e25e3d661807540fcce90) · [Acta fase 8](../../docs/phase-8/8_CIERRE_Y_EVIDENCIAS.md).

## Login OIDC de laboratorio (opt-in, sin secretos embebidos)

`net.openid:appauth:0.11.1` gestiona el navegador externo y Authorization Code + PKCE S256/state/nonce. Proveer al compilador únicamente identificadores **públicos**:

```bash
export SMARTUNI_OIDC_ISSUER='https://idp.example.org/realms/smartuni'
export SMARTUNI_OIDC_CLIENT_ID='smartuni-android'
export SMARTUNI_API_ORIGIN='https://api.example.org'
```

Los valores son ilustrativos y no corresponden a servicios reales. El proveedor debe registrar `xyz.smartuni.app:/oauth2redirect` como redirect de cliente público y configurar audience JWT `smartuni-api` para el backend. Sin esos valores el login permanece deshabilitado; no hay credenciales fijas. El access token, cuando existe, se persiste cifrado Rust/Keystore, se caduca localmente y puede comprobarse con GET /me mediante JNI C++.

**Límites:** no hay token refresh, logout global, enlace de dispositivos, App Links verificados ni validación real con proveedor; un callback de esquema personalizado requiere análisis de su superficie de intercepción. Este login no supone sincronización ni E2EE compartido. La cuenta y su servidor deben configurarse fuera del repositorio por el responsable autorizado.

## Verificación Android después del endurecimiento Rust 9.1

El núcleo Rust compilado para Android ahora usa HPKE X25519 únicamente (`default-features = false`), eliminando P-256 y `crypto-bigint` del grafo de dependencias. La actualización está corroborada mediante RustSec y pruebas Linux; **la instrumentación Android de la revisión actual debe ejecutarse por CI**, no inferirse a partir de los builds anteriores. Los artefactos siguen siendo de laboratorio y sin firma comercial. Ver [acta de la etapa 9](../../docs/phase-9/9_CIERRE_Y_EVIDENCIAS.md).
