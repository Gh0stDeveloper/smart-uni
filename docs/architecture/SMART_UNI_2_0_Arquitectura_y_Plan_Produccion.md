# SMART UNI 2.0 — Arquitectura y plan de producción

**Documento de diseño técnico | 5 de noviembre de 2026 | Estado: propuesta, sin cambios todavía en el código**

## 1. Qué queremos lograr

Vamos a conservar SMART UNI como aplicación de escritorio en Python, con su mismo diseño, colores, logotipo y menú. La diferencia es que ya no dependerá solamente de un archivo JSON de demostración.

**SMART UNI 2.0 será offline-first:** primero guardamos las operaciones en la computadora. Si hay conexión y la cuenta está vinculada a la nube, sincronizamos automáticamente. Si falla Internet, la aplicación sigue funcionando y deja los cambios pendientes para más adelante.

**Alcance inicial de producción:** registro/perfil, calendario, tareas, apuntes, materias, documentos y la lista de compañeros; sincronización de la misma cuenta en Windows y Linux. La colaboración entre usuarios, el chat, los datos académicos oficiales y las notificaciones push quedarían para una evolución posterior.

## 2. Diagnóstico del proyecto existente

Revisamos la última entrega disponible en `SMART_UNI_Entrega_Final_Completa.zip`.

| Archivo actual | Qué hace | Evolución prevista |
|---|---|---|
| `main.py` | Inicia servicios y ventanas; crea datos de demostración | Configuración por entorno, inyección de dependencias, migración y arranque de sincronizador |
| `smart_uni/core.py` | Registro, PBKDF2, lectura/escritura del JSON, cursos y avisos | Servicios de dominio, repositorios SQLite y autenticación separada |
| `smart_uni/student_data.py` | Amigos, eventos, tareas, apuntes y archivos por correo | Servicios con identificadores inmutables, transacciones y registro de cambios |
| `smart_uni/ui.py` | Login, registro, menú y pantallas originales | Conservar disposición, estilos, navegación e icono; conectar nuevos servicios |
| `smart_uni/student_ui.py` | Mi espacio y sus pantallas | Conservar el diseño, mostrar estado de sincronización sin panel adicional |
| `tests/` | 17 pruebas académicas | Mantener y ampliar con pruebas de migración, conflictos, red, seguridad y empaquetado |

Hoy el usuario se reconoce por el correo dentro de `student_spaces[email]`; cambiar un correo no debería afectar a sus datos. El material se copia al directorio `materiales/`; el servidor debe recibir los archivos reales, no solo sus rutas. `seed_demo` se ejecuta desde `main.py`; debemos desactivarlo para los usuarios de producción.

## 3. Arquitectura propuesta

```text
SMART UNI Desktop (Windows / Linux)
  ├─ UI Tkinter actual (sin rediseño)
  ├─ Servicios de dominio: tareas, apuntes, calendario, perfil, materiales
  ├─ Repositorios SQLite (base local)
  ├─ Registro de cambios pendientes (outbox)
  ├─ Motor de sincronización (hilo de trabajo, no bloquea Tkinter)
  ├─ Caché de archivos y respaldos
  └─ Sesión local / credenciales seguras del sistema operativo
                │ HTTPS / TLS
                ▼
SMART UNI API (FastAPI, Python)
  ├─ Identidad y autorización
  ├─ /v1/sync/push y /v1/sync/pull
  ├─ Conflictos, versiones e idempotencia
  ├─ Metadatos y autorización de archivos
  └─ Observabilidad, auditoría y límites
                │
        ┌───────┴─────────┐
        ▼                 ▼
 PostgreSQL          Almacenamiento de objetos
 cuentas, datos,     documentos; subida y descarga
 cambios, versiones  por lotes con verificación SHA-256
```

**Tecnologías iniciales:** Python + Tkinter actuales, SQLite local (WAL para acceso en una misma máquina), FastAPI, PostgreSQL, SQLAlchemy/Alembic para migraciones, almacenamiento de objetos compatible S3, HTTPS, CI en Windows y Linux. Redis o servicios adicionales solo si las pruebas demuestran que hacen falta.

**Ubicación de archivos locales:** usar una carpeta por usuario, con `platformdirs`, nunca dentro del ejecutable ni en una ruta compartida por red.

## 4. Base local y modelo de datos

Tablas locales principales: `profiles`, `subjects`, `courses`, `announcements`, `friends`, `events`, `tasks`, `notes`, `materials`, `attachments`, `outbox`, `sync_state` y `schema_migrations`.

Cada registro sincronizable tendrá al menos `id` UUID creado en el cliente, `owner_id` estable, `revision` (asignada o validada por el servidor), `created_at`, `updated_at`, `deleted_at` opcional y `sync_status`. No usaremos el correo como clave de propiedad: el correo puede cambiar.

**Regla para el guardado:** en una sola transacción SQLite guardamos el dato modificado y añadimos su operación a `outbox`. La interfaz responde en ese momento; no espera a Internet.

**Migración JSON → SQLite:** hacer copia de seguridad, leer datos antiguos, crear UUID para perfiles, importar categorías, respetar los IDs ya usados en los registros, copiar metadatos de documentos, verificar recuentos y abrir la nueva BD. El JSON original se conserva hasta que la migración esté verificada y exista un respaldo restaurable. Probar migración interrumpida y repetida para evitar duplicaciones.

## 5. Motor de sincronización

1. El usuario crea o modifica un dato; SQLite confirma el cambio local y una operación pendiente.
2. Un worker comprueba conexión y sesión; si no hay, termina sin bloquear ni mostrar un error invasivo.
3. `POST /v1/sync/push` envía operaciones con identificador de idempotencia, ID del dispositivo y versión base.
4. El servidor valida identidad y propiedad; aplica una operación como máximo una vez. Devuelve aceptación, versión y posibles conflictos.
5. `GET /v1/sync/pull?cursor=...` devuelve cambios confirmados por el servidor para la cuenta. El cursor es opaco y se actualiza localmente en la misma transacción que aplica los cambios.
6. Reintenta con espera exponencial y jitter cuando hay errores temporales. Jamás borra un cambio local por un fallo de red.

**Borrados:** utilizar marcas de eliminación (`deleted_at` / tombstones), no borrar de inmediato del historial de sincronización. Establecer un periodo de retención y un mecanismo seguro de resincronización completa para dispositivos que estuvieron mucho tiempo desconectados.

**Conflictos:**
- Tareas y calendario: comparar `revision` de cada registro y aplicar si corresponde; si otra computadora lo modificó antes, obtener el último estado y ofrecer resolución cuando sea necesario.
- Apuntes: si los dos dispositivos cambiaron el contenido, conservar ambas versiones y dejar que el usuario elija o combine; nunca sobreescribir el texto silenciosamente.
- Amigos: evitar duplicados por par `(owner_id, contact)`.
- Documentos: versiones inmutables y comprobación SHA-256; si se modifican simultáneamente, conservar ambas.
- Perfil/cuenta: el servidor es la fuente autorizada para identidad, correo y control de dispositivos.

## 6. Inicio de sesión offline y online

Debemos distinguir entre dos tipos de usuario:

- **Perfil local nuevo:** puede empezar sin Internet. Sus datos permanecen exclusivamente en ese equipo hasta que el usuario cree o vincule una cuenta online y confirme que le pertenece.
- **Cuenta online previamente vinculada a este dispositivo:** permite acceso offline a los datos locales mediante desbloqueo protegido del dispositivo; no se intenta verificar contraseñas remotas sin servidor. La revocación remota solo se puede conocer al recuperar conectividad.

Un dispositivo nunca utilizado no puede consultar una cuenta online ajena sin conectarse primero para autenticarla. El inicio de sesión de la app debe conservar su estilo actual, aunque podemos agregar estados discretos "Sin conexión", "Pendiente" y "Sincronizado".

Recomendación: proveedor de identidad compatible con OAuth 2.0/OIDC, flujo Authorization Code + PKCE en el navegador del sistema, claves/token en el almacén seguro del SO, sesiones revocables. No incrustar secretos en el EXE. No migrar hashes de contraseñas como si fueran credenciales reutilizables; la vinculación debe requerir autenticación y confirmación del propietario.

## 7. Documentos, seguridad y respaldo

Los documentos se guardan primero localmente. Se transmite su contenido por HTTPS a almacenamiento de objetos con autorización y URL temporal, verificando tamaño, SHA-256 y tipo permitido. Mantener el límite actual de 30 MB por archivo como punto de partida, ajustable según pruebas. Descargar por demanda y conservar caché para apertura offline. Los archivos privados no deben quedar públicos.

La aplicación no debe subir archivos ni datos del estudiante antes de que este acepte vincular la cuenta. También requiere aviso de privacidad, exportación/borrado de datos y permisos claros para compartir.

Seguridad: cifrado local de información sensible cuando corresponda, protección de claves por SO, validación en servidor y por usuario, rate limiting, registros sin contraseñas/tokens/texto de apuntes, TLS, controles de dependencias y respaldos cifrados con restauración probada. Para contraseñas administradas por nosotros, usar un esquema moderno como Argon2id.

SQLite WAL mejora la concurrencia local, pero no permite múltiples computadoras abriendo un mismo archivo SQLite en red. La sincronización siempre pasa por la API.

## 8. Conservación exacta del diseño

No sustituiremos Tkinter ni reharemos el estilo aprobado. Preservaremos colores, fuentes, login, logo/birrete original, menú hamburguesa unificado y todas las pantallas. La interfaz nueva solo añadirá pequeños estados dentro de la cabecera o Ajustes: sincronizado, pendiente, offline, error recuperable, fecha de última sincronización y botón "Sincronizar ahora". Ningún panel auxiliar permanente a la derecha.

Todo acceso a red se hará en un hilo/worker o mecanismo asíncrono que no bloquee Tkinter; las actualizaciones de controles gráficos se comunicarán al hilo principal de manera segura.

## 9. Plan de implementación por fases

| Fase | Trabajo | Entregable y criterio de aceptación |
|---|---|---|
| **0. Línea base** | Congelar última versión, auditar datos de ejemplo, definir contratos e inventariar pantallas | Pruebas actuales en CI, capturas originales y copia íntegra antes de tocar datos |
| **1. Separación de capas** | Extraer interfaces de repositorio, servicios de dominio e identidad de la UI | Mismas pantallas y funciones, pruebas actuales sin regresiones |
| **2. Persistencia local** | SQLite, migraciones, respaldo y traslado JSON; outbox transaccional | Cerrar/reabrir sin pérdida; migración recuperable; sin bloqueo gráfico |
| **3. Identidad y backend** | FastAPI, PostgreSQL, cuentas, permisos, sesiones, API y despliegue de pruebas | Dos cuentas aisladas; ninguna puede consultar datos ajenos |
| **4. Sincronización de registros** | Push/pull incremental, cursor, idempotencia, tombstones y conflictos | Crear offline, reconectar y ver datos en segundo equipo; reintentos sin duplicados |
| **5. Sincronización de materiales** | Carga/descarga, hashes, caché y reanudación | Abrir archivo offline; sincronizar en segundo equipo; falla de carga recuperable |
| **6. Seguridad y resistencia** | Cifrado, controles de sesión, manejo de errores, monitoreo, restauración | Fallos simulados, caducidad, reconexión y respaldos probados |
| **7. Distribución y beta** | Instaladores Windows/Linux firmados cuando corresponda, actualizaciones, CI, pruebas en equipos reales | Instalación limpia, actualización sin perder datos, pilotos y corrección de bloqueantes |
| **8. Lanzamiento** | Políticas, privacidad, soporte, métricas y procedimientos operativos | Go/no-go con validaciones completadas; lanzamiento gradual |

No avanzar de fase si falla la migración de datos, una operación pierde información, se rompe la UI o existe acceso entre cuentas sin autorización.

## 10. Pruebas indispensables

- Migrar el JSON real del prototipo (sin cuenta demo en producción), 2 veces y después de simular un cierre inesperado.
- Crear tarea y apunte offline; cerrar SMART UNI; abrir y verificar que siguen guardados.
- Sincronizar en 2 dispositivos, reconectar tras una semana offline y evitar duplicados.
- Editar el mismo apunte en 2 equipos sin conexión, luego resolver el conflicto sin pérdida.
- Crear, borrar y descargar archivos; verificar SHA-256; interrumpir subidas.
- Probar pérdida de token, cambio de contraseña, cierre de sesión y aislamiento entre cuentas.
- Interrumpir Internet durante una operación, forzar respuestas 429/500 y recuperar el servicio.
- Verificar responsividad del menú, formularios e icono original; comparar capturas antes/después.
- Probar instaladores/actualizadores reales en Windows y Linux y restaurar un respaldo.

## 11. Decisiones técnicas de alcance

- **MVP:** un usuario, varios dispositivos y sincronización privada; no chat en tiempo real ni integración universitaria.
- **Cuenta nueva sin Internet:** datos locales hasta vinculación verificada.
- **Servidor:** autoridad para propiedad, autorización y revisiones; la app es autoridad temporal de cambios locales sin enviar.
- **Red:** la conexión mejora la experiencia pero nunca es requisito para guardar contenidos personales locales.
- **Conservación:** migración reversible, sin modificar ni borrar el JSON anterior antes de confirmar éxito.
- **UI:** el diseño aprobado es un requisito de compatibilidad, no una parte a rediseñar.

**Próximo paso implementable:** Fase 0 y Fase 1. En esas fases la aplicación debe verse y comportarse exactamente como ahora, mientras dejamos lista la arquitectura de datos para añadir SQLite y la sincronización posteriormente.