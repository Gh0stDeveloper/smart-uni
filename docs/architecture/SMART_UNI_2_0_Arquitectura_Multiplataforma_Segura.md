# SMART UNI 2.0 — Arquitectura multiplataforma segura (Windows, Linux y Android)

**Fecha:** 5 de noviembre de 2026  
**Estado:** propuesta de arquitectura / documento de implementación, **sin modificar el código existente**.  
**Base revisada:** `SMART_UNI_Entrega_Final_Completa.zip` y propuesta anterior `SMART_UNI_2_0_Arquitectura_y_Plan_Produccion.md`.

## 1. Qué queremos lograr

La idea es mantener SMART UNI con el mismo diseño aprobado: birrete azul y turquesa, tipografías y colores, navegación unificada sin panel derecho. Vamos a tener dos aplicaciones, una para Windows/Linux y otra para Android, que compartan sus datos con un servidor cuando haya Internet. Si no hay Internet, las tareas, los apuntes y los materiales descargados tienen que seguir funcionando y guardándose localmente.

No vamos a confiar toda la seguridad a un lenguaje. Separaremos la interfaz, la lógica de negocio, el cifrado, la gestión de claves, las comunicaciones y los permisos. **Ningún cliente es una zona de confianza:** ni un EXE ni una APK pueden guardar secretos universales de servidor de forma segura, aunque estén escritos en C++ o Rust.

## 2. Decisiones de tecnología

| Parte | Elección | Motivo |
|---|---|---|
| Núcleo compartido | **Rust** (`smartuni-core`) | Reutilizar modelo, validaciones, operaciones offline, cifrado y protocolo de sincronización; seguridad de memoria |
| Escritorio Windows/Linux | **UI actual Python/Tkinter**, puente PyO3/cffi hacia Rust | Conservar exactamente la interfaz y migrar lógica sensible gradualmente; Python no almacena claves de servidor |
| Android | **Java** para Activity, navegación, accesibilidad y UI, **C++/NDK JNI** para adaptador de red/endpoints, **Rust** compilado como biblioteca nativa para criptografía y datos | Cumplir la distribución de responsabilidades solicitada sin duplicar los algoritmos criptográficos |
| API/backend | **FastAPI (Python)** + servicios de dominio; **Next.js/TypeScript** para panel, documentación y portal web | Responsabilidades claras. El cliente no se conecta directamente a PostgreSQL |
| Base de datos | **SQLCipher/SQLite** local, **PostgreSQL** servidor | Datos utilizables sin Internet y sincronización centralizada |
| Archivos | Carpeta privada cifrada/caché local + almacenamiento remoto privado compatible S3 | Sincronizar materiales sin exponerlos en URL pública |
| Autenticación | OIDC/OAuth 2.0 Authorization Code + PKCE en navegador del sistema | No incrustar client secrets en EXE/APK |
| Criptografía | Argon2id, TLS 1.3, AEAD (AES-256-GCM o XChaCha20-Poly1305) y HPKE cuando el caso de uso lo justifique | Estándares auditables, sin cifrados inventados |
| Diseño | Figma + tokens visuales versionados | Una misma identidad visual adaptada al tamaño de cada pantalla |

**Ruby no es parte de la arquitectura inicial.** Rust cubre mejor el núcleo compartido, así que agregar Ruby solo complicaría la compilación y el mantenimiento. C++ se utilizará donde exista una razón de integración o un requisito expreso de Android; evitaremos duplicar código crítico en C++ y Rust.

## 3. Arquitectura por capas

```text
               DISEÑO COMPARTIDO — FIGMA
             tokens (colores/tipos/espacios)
                       │
       ┌───────────────┴─────────────────┐
       ▼                                 ▼
 WINDOWS / LINUX                       ANDROID
 Python/Tkinter actual                 Java (UI nativa)
       │                                 │
 PyO3/FFI                           JNI C++ (API y endpoints)
       │                                 │
       └───────────────┬─────────────────┘
                       ▼
              RUST: smartuni-core
     reglas del dominio / cifrado / cola / conflictos
                       │
       ┌───────────────┴─────────────────┐
       ▼                                 ▼
 SQLite/SQLCipher                   Transporte HTTPS
 archivos privados                  con tokens de sesión
       │                                 │
       └───────────────┬─────────────────┘
                       ▼
              GATEWAY / API HTTPS
        Next.js (portal y panel, BFF)
        FastAPI (API de sincronización)
                       │
           ┌───────────┴────────────┐
           ▼                        ▼
       PostgreSQL              Object Storage
       metadata/ACL             archivos cifrados
```

### Límites de confianza

1. **La interfaz nunca decide los permisos definitivos.** Cada lectura, escritura y descarga requiere autorización del servidor en base a la identidad autenticada.
2. **Los endpoints pueden ubicarse en C++ en Android**, pero sus direcciones no son secretos. Se pueden recuperar de una APK analizando la app, tráfico o símbolos. No confiaremos en la ocultación como mecanismo de seguridad.
3. **C++/Rust no pueden mantener secretos universales en los clientes.** Las claves maestras del servidor y credenciales de la base de datos no se distribuyen. Las claves de usuario/dispositivo se almacenan con controles del SO cuando sea posible.
4. Todo código remoto y cualquier archivo adjunto se considera no confiable.

## 4. Cifrado: dónde y cómo

**Datos en tránsito.** Todo tráfico externo viaja por HTTPS/TLS 1.3 con validación estricta de certificado y hostname, sin TLS inseguro de respaldo ni tráfico HTTP. No registrar tokens ni cuerpos sensibles. Una política de pinning, si se adopta, tendrá mecanismo de rotación y recuperación para evitar bloquear clientes por certificados renovados.

**Datos locales.** SQLCipher protege la base SQLite; los adjuntos sensibles se cifran individualmente mediante una clave aleatoria por archivo (DEK), con cifrado autenticado y metadatos mínimos. Proteger la clave de cifrado de base/archivos con Android Keystore (preferir respaldo en hardware si está disponible), Windows DPAPI y el almacén seguro del escritorio Linux cuando exista, con un flujo de recuperación seguro si no existe.

**Contraseñas.** No cifrar contraseñas para poder recuperarlas: verificar hashes de **Argon2id** con sal única y parámetros calibrados. Mantener compatibilidad temporal con PBKDF2-SHA256 y migrar al validar correctamente una credencial anterior o mediante restablecimiento. Nunca enviar contraseñas a logs ni conservarlas en memoria más de lo necesario.

**Cifrado adicional del contenido sincronizado (E2EE, recomendado para apuntes y documentos privados).** TLS protege el canal, pero para reducir lo que puede leer el servidor cifrar el contenido privado **antes** de subirlo con una clave de contenido controlada por el usuario/dispositivos autorizados. Un esquema de envoltura de claves por dispositivo (por ejemplo HPKE estándar para distribución de claves, más AEAD para el contenido) permite sincronizar entre Android/Windows/Linux. Se necesita diseñar con precisión: alta de dispositivo, revocación, rotación de claves, claves de recuperación, pérdida de dispositivos, acceso compartido a apuntes, y qué metadatos serán visibles (IDs, tamaños, versiones, estados de sincronización). **E2EE no será un interruptor agregado al final**: se valida con un prototipo antes de implementarlo para datos reales. Un servidor E2EE no puede buscar ni procesar automáticamente el texto privado que no puede descifrar.

**Cifrado del servidor.** Además de E2EE para contenido privado, cifrado de respaldos/volúmenes, permisos limitados, rotación de credenciales y gestión de claves en un KMS o gestor de secretos. La privacidad de correo de login y datos necesarios para facturación/identidad tiene un modelo distinto al de los documentos E2EE.

**No inventar protocolos propios, ni combinar AES, HPKE y TLS sin definir las garantías buscadas.** Toda implementación usará bibliotecas mantenidas, versiones fijas y pruebas cruzadas entre plataformas. TLS no sustituye E2EE y E2EE no sustituye TLS ni autorización.

## 5. Seguridad Android: C++ y Java, con Rust compartido

- **Java:** UI nativa, acceso a APIs de plataforma, permisos, compatibilidad con accesibilidad, comunicación con Keystore mediante puente limitado y mecanismo oficial de login en navegador. Nunca incluir credenciales de base de datos o un secreto fijo de producción en Java.
- **C++ (NDK/JNI):** adaptador de endpoints/API solicitado; serialización/validación de frontera y comunicación de red nativa. Evitar exponer tokens en logs, cadenas constantes sensibles o excepciones. Compilar con endurecimiento y sanitizers durante QA. El servidor es quien impone autorizaciones, incluso si se copia la API.
- **Rust (`smartuni-core`):** cifrado, formatos interoperables, persistencia offline, reconciliación y reglas compartidas. Exponer una interfaz C estable para Android C++ y enlace Python/FFI para escritorio. Reducir conversiones de buffers sensibles y documentar propiedad/liberación de memoria.
- **Keystore/KeyMint:** claves específicas por dispositivo protegidas por Android; aprovechar hardware cuando esté disponible, sin impedir automáticamente el uso legítimo de dispositivos que no lo soportan.
- **Play Integrity:** señales verificadas **en el servidor**, no como único criterio de autenticación. Protección anti-tamper y detección de hooking como defensa complementaria, no como prueba de que el cliente es confiable. Evaluar impacto en accesibilidad y dispositivos legítimos.
- **OWASP MASVS/MASTG:** checklist de almacenamiento, criptografía, autenticación, red, plataforma, código, resiliencia y privacidad.
- **Distribución:** APK/AAB firmados, build de release sin debugging, políticas de respaldo, permisos mínimos y pruebas en teléfonos físicos.

La interfaz Android debe parecerse a SMART UNI, pero adaptada a móviles: mismos colores, birrete, iconografía y jerarquía, con navegación táctil. No copiar literalmente tamaños y disposición del escritorio.

## 6. Seguridad Windows y Linux

- Mantener Tkinter durante la transición para no romper el diseño. **Python se queda en la UI**, no en el núcleo criptográfico.
- Rust implementa operaciones sensibles. Las llamadas se exponen por FFI y se prueban con fuzzing y análisis estático.
- Base cifrada; almacenamiento de claves con DPAPI (Windows) y Secret Service/KWallet cuando proceda (Linux), ofreciendo desbloqueo con contraseña o clave de recuperación si no existe un almacén de secretos confiable.
- Ejecutables firmados cuando sea viable; actualizaciones con firma y verificación antes de instalar. Cuidar rutas locales de usuario, permisos de archivos, no permitir carga de bibliotecas o plugins arbitrarios.
- El núcleo nativo puede ser extraído y depurado en el equipo del usuario: **no depender del secreto del binario**.

## 7. Protección del servidor y ataques SQL

La API FastAPI es el único camino normal de los clientes hacia los datos. Next.js se dedica al portal/panel y, si hace de BFF, se autentica con servicios internos mediante credenciales administradas en servidor. Nunca exponer Postgres/Redis públicamente ni usar credenciales administrativas en el navegador o en Android.

1. **Consultas parametrizadas / prepared statements**, ORM seguro, ninguna concatenación de SQL usando texto recibido. Listas permitidas para identificadores/ordenamientos SQL dinámicos.
2. Validación estricta de entradas (Pydantic/Zod), límites de tamaño, rechazo de claves desconocidas donde corresponda, y controles anti-inyección también en búsquedas, nombres de archivo y comandos.
3. **Autorización por propietario y recurso** en cada endpoint: previene acceso horizontal entre estudiantes; considerar Row Level Security como defensa adicional, no como sustituto.
4. Roles de base de datos con mínimo privilegio, migrador separado, credenciales de corta duración cuando sea viable; secretos fuera de Git.
5. CSRF y cookies seguras en panel web, protección contra XSS, CORS restringido, CSP y headers de seguridad; límites de solicitud y protección de abuso.
6. Operaciones de sincronización idempotentes, revisiones de servidor, validación de esquemas/versiones y protección contra replay donde aplica.
7. Cifrado TLS entre servicios cuando cruza fronteras de confianza; backups cifrados con restauración probada, audit logs sin contenido privado y alertas.
8. Revisión de dependencias, SAST, SCA, secret scanning, DAST, análisis de contenedores, SBOM, despliegues firmados, pruebas de penetración y política de vulnerabilidades.
9. Evaluar OWASP ASVS para backend y MASVS para Android. No prometer seguridad absoluta; generar evidencia medible de cada control.

## 8. Sincronización offline/online compartida

- Todos los clientes usan UUID estables por usuario, dispositivo y objeto; no el correo como identificador primario.
- Una transacción local escribe dato cifrado y operación `outbox` en forma atómica. La UI siempre responde desde SQLite, sin esperar la red.
- `sync/push` envía cambios cifrados con ID de operación, versión base y autorización. El servidor verifica propietario e idempotencia y guarda versiones/metadatos; no necesita descifrar el cuerpo privado E2EE.
- `sync/pull` usa cursor y versiones: el cliente descarga, valida, descifra y confirma localmente. Reintentos exponenciales con jitter; nunca eliminar cambios pendientes por una caída.
- Conflictos en notas y documentos: conservar ambos contenidos cifrados y permitir resolverlos en el cliente. Borrado lógico/tombstones con retención y resincronización segura.
- Archivos grandes: chunks verificables, subida reanudable, cifrado autenticado por objeto/segmento correctamente diseñado, límites y almacenamiento privado.
- Pruebas: cliente Windows crea offline, Android recibe online, Android edita offline, Linux reconcilia; verificar conflictos, revocación, cambio de clave y pérdida de dispositivo.

## 9. Figma e identidad visual

Los recursos SVG y `design/tokens.json` del proyecto permiten comenzar con Figma desde los diseños aprobados. Proponer un **archivo maestro Figma** con componentes y variables: logo original, paleta, tipografías, espaciados, botones, formularios, tarjetas y estados (normal/error/offline/sincronizando). Dos familias de frames: escritorio 1366/1600 y móvil Android con diseño adaptable.

- Exportación unidireccional inicial: Figma → tokens versionados en Git → Tkinter/CSS/Android Resources.
- Vinculación más automatizada: API de Figma (lectura de archivo, componentes, estilos, variables, versiones y webhooks según permisos/plan), con validación en pull request; **no hacer cambios directos en producción por cada edición de Figma**.
- La API de Figma no convierte automáticamente una pantalla en interfaz funcional, ni garantiza sincronización bidireccional del diseño. Requiere conectarlo, otorgar permisos y definir los mapeos por plataforma.

## 10. Estructura propuesta de repositorio

```text
smart-uni/
├── apps/
│   ├── desktop/           # UI Tkinter actual, recursos, launcher
│   ├── android/           # Java UI + C++ NDK/JNI
│   └── web/               # Next.js/TypeScript: portal y panel
├── services/
│   └── api/               # FastAPI, esquemas, permisos y sync
├── crates/
│   ├── smartuni-core/     # Rust: dominio y motor offline
│   ├── smartuni-crypto/   # Rust: wrappers de primitivas auditadas
│   └── smartuni-ffi/      # ABI, puente Python/Android
├── packages/
│   ├── contracts/         # OpenAPI / JSON Schema / vectores interop
│   └── design-tokens/     # Figma + tokens probados
├── infra/                 # Docker, despliegue, secretos de ejemplo
├── security/              # threat-model, ADR, evidencias de pruebas
├── docs/                  # arquitectura, migraciones, tutoriales
└── .github/workflows/     # matriz CI: win/linux/android/server
```

## 11. Plan por fases y criterios de aceptación

La numeración oficial está en [ROADMAP.md](../ROADMAP.md), con 30 subfases y criterios verificables. Este documento conserva decisiones técnicas, pero no establece numeración independiente.

| Fase oficial | Enfoque | Evidencia |
|---|---|---|
| **Fase 1: Análisis y línea base** | Conocer los riesgos y fijar el comportamiento actual antes de migrar. | Pruebas, revisión y entregables documentados |
| **Fase 2: Contratos y sistema de diseño** | Modularizar sin modificar la interfaz aprobada. | Pruebas, revisión y entregables documentados |
| **Fase 3: Núcleo compartido en Rust** | Concentrar las funciones sensibles e interoperables en componentes mantenibles. | Pruebas, revisión y entregables documentados |
| **Fase 4: Persistencia local y funcionamiento offline** | Garantizar datos disponibles sin Internet y migraciones recuperables. | Pruebas, revisión y entregables documentados |
| **Fase 5: Backend, identidad y autorización** | Proporcionar servicios online con separación verificable entre usuarios. | Pruebas, revisión y entregables documentados |
| **Fase 6: Cifrado y gestión de claves** | Proteger contenidos privados sin perder la capacidad de recuperación legítima. | Pruebas, revisión y entregables documentados |
| **Fase 7: Sincronización multiplataforma** | Conciliar datos offline entre Windows, Linux y Android sin pérdidas. | Pruebas, revisión y entregables documentados |
| **Fase 8: Aplicación Android** | Construir un cliente móvil con la identidad SMART UNI y seguridad compartida. | Pruebas, revisión y entregables documentados |
| **Fase 9: Seguridad, integración continua y beta** | Verificar que los controles prometidos existen y resisten fallos. | Pruebas, revisión y entregables documentados |
| **Fase 10: Lanzamiento gradual** | Publicar con controles de privacidad, soporte y operación. | Pruebas, revisión y entregables documentados |

## 12. Matriz mínima de pruebas de seguridad

- **SQL injection:** entradas maliciosas en todos los parámetros del API, filtros y ordenamientos, sin alteración de consultas.
- **Autorización:** usuario A no lee, borra ni sincroniza recursos de usuario B, aunque altere IDs y JSON de petición.
- **Tráfico:** no existe HTTP en producción; MITM falla; credenciales y cuerpos E2EE no aparecen en logs.
- **Credenciales:** Argon2id, migración de PBKDF2, cierre/revocación de sesión, rate limiting, bloqueo por intentos sin permitir denegación masiva.
- **Android:** análisis APK, comprobación de strings/credenciales, instrumentación, configuración de permisos, backup, Keystore y Play Integrity verificada server-side cuando proceda.
- **Desktop:** revisión binaria, permisos de rutas, almacenamiento de claves, dependencias, actualización firmada y archivos maliciosos.
- **Offline:** cortar red durante escritura y subida, apagar máquina, corrupción de BD, dispositivo robado, recuperación de clave, rotación, cuenta desvinculada.
- **Interoperabilidad:** vectores criptográficos reproducibles en Android/Win/Linux, mismo formato de contenedor y migración de versiones.
- **Diseño:** regresión visual, accesibilidad, modo móvil y escritorio, icono original, sin panel derecho.

## 13. Alcances y decisiones pendientes de producto

1. **E2EE:** confirmar si notas, tareas, calendario y materiales personales deben ser ilegibles para el servidor; esto condiciona búsqueda, compartición, soporte y recuperación.
2. **Colaboración:** si se compartirán apuntes con Amigos, se requiere gestión explícita de claves/permisos por destinatario; no incluir en MVP sin su modelo de amenazas.
3. **Recuperación:** diseñar clave de recuperación y flujo cuando se pierden todos los dispositivos; nadie puede prometer E2EE fuerte y al mismo tiempo recuperar secretos sin mecanismo de respaldo.
4. **Compatibilidad Android:** versión mínima de Android, dispositivos sin StrongBox/attestation, y controles ante root (riesgo, no bloqueo general por defecto).
5. **Figma:** conexión con el archivo oficial y acceso autorizado a APIs y variables del plan.
6. **Plataformas:** priorizar Windows/Linux existentes, habilitar API y Android sobre contratos comunes, sin inventar fechas ni garantizar que una auditoría pase sin ejecutarla.

## 14. Referencias verificadas

- OWASP Password Storage Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- OWASP SQL Injection Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
- OWASP MASVS: https://mas.owasp.org/MASVS/
- RFC 8252 OAuth native apps: https://www.rfc-editor.org/rfc/rfc8252.html
- RFC 9180 HPKE: https://www.rfc-editor.org/rfc/rfc9180.html
- Android Play Integrity: https://developer.android.com/google/play/integrity
- Figma API: https://developers.figma.com/docs/rest-api/
- UniFFI: https://mozilla.github.io/uniffi-rs/

---

**Estado final de este documento:** arquitectura acordable, no código aplicado. El diseño actual y los archivos de la entrega final permanecen intactos. El primer trabajo práctico sería completar Fase 1: Análisis y línea base, seguida de Fase 2: Contratos y sistema de diseño; después construir el núcleo Rust con pruebas criptográficas cruzadas.