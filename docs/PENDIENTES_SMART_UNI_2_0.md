# SMART UNI 2.0 — Registro maestro de pendientes y riesgos abiertos

**Última revisión:** 6 noviembre 2026. Es obligatorio consultar y actualizar este documento al iniciar/cerrar cada fase, junto con [ROADMAP](ROADMAP.md), [auditoría 1.2](phase-1/1.2_AUDITORIA_Y_MODELO_DE_AMENAZAS.md), [acta 2](phase-2/2_CIERRE_Y_EVIDENCIAS.md) y [acta 3](phase-3/3_CIERRE_Y_EVIDENCIAS.md). Fuente de verdad sobre **lo que NO está listo**, incluyendo trabajos que quedaron a medias en chats anteriores.

**Estados:** Pendiente (no implementado), Parcial (implementado en biblioteca, pruebas o modo experimental, pero no en producción), Resuelto (requiere commit + prueba reproducible + revisión). No eliminar filas antes de evidencia. La aplicación habitual continúa usando JSON sin cifrar; **no usar datos privados reales aún**.

## Pendientes heredados de 1 Análisis y línea base (R01–R11)

| ID | Prioridad | Estado | Pendiente preciso | Etapa y criterio de cierre |
|---|---|---|---|---|
| P01 / R01 | **Crítica** | Parcial | La base SQLCipher solo se activa expresamente, pero el modo normal guarda JSON en claro; los materiales del modo normal también están en claro y el modo seguro bloquea importación de archivos. Tras migrar, permanece el JSON original. | 4/6/9: cifrar y restaurar archivos, quitar texto claro de instalación de producción tras verificar backup, auditar restos en disco |
| P02 / R02 | **Alta** | Pendiente | StudentSpaceService acepta un correo sin demostrar que pertenezca a la sesión activa; actor_ref de los contratos es dato no autenticado. | 5: autorización por identidad/sesión y recurso, pruebas de lectura y escritura cruzadas, autenticación backend real |
| P03 / R03 | Alta | Parcial | Las credenciales demo siguen presentes en la versión JSON y en el flujo de exposición; no se crean automáticamente en el modo seguro, pero tampoco se deshabilitaron en builds de distribución. | 5/9: eliminar cuenta demo de producción y verificar login sin credenciales predeterminadas |
| P04 / R04 | Alta | Parcial | SQLCipher posee BEGIN IMMEDIATE y outbox atómico en acciones cubiertas; read/write legado y eliminaciones sin tipo de evento siguen teniendo riesgos de carrera o no quedar en outbox. | 4/7: todas las mutaciones protegidas bajo la misma transacción + prueba multiproceso |
| P05 / R05 | Media | Parcial | SQLCipher limita permisos POSIX a 0600, pero material JSON heredado usa copy2 y pueden existir directorios/permisos inseguros, incluso Windows ACL no comprobados. | 6/9: aislamiento real de archivos en ambos SO y controles de permisos probados |
| P06 / R06 | Media | Pendiente | La verificación de hashes PBKDF2 heredados lee iteraciones del propio archivo sin límite explícito; posible agotamiento de CPU. | 5/9: cotas de PBKDF2 y migración segura a Argon2id con tests de hashes alterados |
| P07 / R07 | Media | Parcial | En SQLCipher se valida estructura superior y tope 20 MiB; el lector JSON histórico admite tipos incorrectos y no limita contenido total; faltan schemas por sección. | 4/9: validación y fuzzing de contenido, evitar DoS por JSON |
| P08 / R08 | Alta | Parcial | En modo seguro se bloquean archivos hasta tener cifrado; legacy acepta extensiones sin comprobar contenido y abre visores del SO. | 6/9: protección de adjuntos, validación de contenido y apertura controlada |
| P09 / R09 | Alta | Parcial | SQLCipher y keyring fijados en requisitos CI; faltan SBOM, firma de instalador, hashes de Actions, pinning de PyInstaller/Pillow y revisión de ruedas binarias. | 9: lockfiles, firmas, cadena de suministro y auditoría de dependencias |
| P10 / R10 | Alta | Parcial | Ya hay backup/restore cifrado comprobado con interrupción simulada; sin bitácora de auditoría de acciones, retención definida, restauración de adjuntos o prueba de corte de alimentación real. | 4/9: historial mínimo, RPO/RTO y restauraciones integrales reales |
| P11 / R11 | Baja | Pendiente | Las fuentes pueden variar por sistema; faltan regresión pixel a pixel, prueba de accesibilidad y revisión en monitores distintos. | 9: evidencias visuales aprobadas Windows/Linux |

## Pendientes de 2 Contratos y sistema de diseño y 3 Núcleo Rust

| ID | Prioridad | Estado | Pendiente preciso | Etapa/aceptación |
|---|---|---|---|---|
| P12 | Media | Pendiente | No está vinculada una cuenta ni archivo maestro de Figma; hay tokens y proceso manual, no sincronización API, webhooks ni exportación controlada. | 8/9: autorización, mapping y revisión de cambios |
| P13 | Alta | Parcial | Rust 0.1.0 + C ABI y Python ctypes fueron probados, pero las funciones sensibles del escritorio aún están en Python y no delegan almacenamiento, gestión de claves ni sincronización a Rust. | 6/8: puente Rust integrado de forma explícita y prueba de equivalencia |
| P14 | Alta | Pendiente | Android ARM64 compila libsmartuni_core.so, pero sin Java Activity, JNI C++ real, APK/AAB ni ejecución en teléfono. | 8/9: integración Java↔C++↔Rust probada en dispositivo |
| P15 | **Crítica** | Pendiente | AES-GCM funciona con vectores conocidos, no existe contenedor interoperable real, claves por usuario/dispositivo, recuperación, rotación, revocación, E2EE ni sincronización cifrada. | 6/7/8: protocolo documentado y probado entre plataformas |
| P16 | Alta | Pendiente | Cuentas remotas y OIDC/OAuth2 PKCE, revocación de sesión, almacén de tokens y Argon2id por implementar. | 5: sesiones con pruebas de expiración y autorización |
| P17 | Alta | Pendiente | No existen API FastAPI, PostgreSQL, portal Next.js de producción ni controles SQL contra escalamiento entre cuentas. | 5/9: tests DB, ACL, API, migraciones y logging |
| P18 | Alta | Parcial | Outbox local no tiene HTTPS, push/pull, ACK, cursor remoto, conflictos, idempotencia servidor o recuperación en dispositivos múltiples. UI no presenta un estado falso de sincronización. | 7: simulación de cortes, ACK verificado y recuperación idempotente |
| P19 | Alta | Pendiente | Contrato v1 tiene diez operaciones; faltan eventos para borrar amigos/eventos/tareas y otras operaciones que aún se guardan sin outbox. | 7: enum versionado y matriz completa de acciones→eventos |
| P20 | Alta | Pendiente | ABI C recibe punteros confiados al invocador nativo; falta fuzzing, sanitizers, tests de punteros y auditoría del límite FFI. | 8/9: fuzzing/sanitizer Windows/Linux/Android |
| P21 | Alta | Pendiente | No se ha hecho pentest, revisión independiente del producto ni auditoría del código de manejo de claves y sus dependencias. | 9: informe técnico y correcciones verificadas |

## Deuda nueva y decisiones de 4 Persistencia local y funcionamiento offline

| ID | Prioridad | Estado | Qué falta y por qué | Etapa/aceptación |
|---|---|---|---|---|
| P22 | Alta | Parcial | Almacenamiento seguro solo opt-in mediante SMARTUNI_STORAGE=secure, dependencias SQLCipher/keyring opcionales. El EXE distribuido todavía no incluye SQLCipher ni ha sido probado con WinVault/SecretService/KWallet en una sesión real. El modo sin keyring debe fallar cerrado, sin usar sqlite3 en claro. | 6/9: prueba real de keyring y paquete firmado, modo protegido habilitado como predeterminado |
| P23 | Alta | Parcial | Migrar JSON sin borrar origen evita pérdidas, pero deja una copia en texto claro. No existe wizard de aprobación ni limpieza posterior recuperable. | 4/6/9: respaldo íntegro verificado, consentimiento y eliminación programada de restos |
| P24 | **Alta** | Pendiente | Adjuntos cifrados, visualización sin temporales peligrosos, exportación controlada, tamaño, streaming y respaldo/restauración de materiales. Importación bloqueada en modo secure. | 6: probar importación, apertura, borrado y restauración con datos sintéticos |
| P25 | Alta | Parcial | Keyring OS solo abstraído; CI inyecta almacén temporal en memoria porque runners sin sesión de escritorio no sirven para evaluar desbloqueo del SO. La misma cuenta local podría acceder a la clave. | 6/9: Windows Credential Manager, Linux Secret Service/KWallet reales; pérdida de perfil, bloqueo, rotación |
| P26 | Media | Parcial | SQLCipher mantiene snapshot JSON íntegro pero no un modelo normalizado por entidad, índices, cargas incrementales ni benchmarks de grandes libretas. | 4/7: esquema versionado y pruebas de rendimiento/datos extensos sin recortes |
| P27 | Media | Pendiente | Restauración entre SO necesita formato recuperable de claves y prueba de recuperación tras apagado real, no solo excepciones simuladas. | 6/9: proceso de recovery y backups exportables cifrados |
| P28 | Media | Parcial | Estados UI local “Sin conexión”, “Pendiente” y “Error” ya pueden aparecer en modo secure, pero no existe estado “Sincronizado” legítimo sin servidor ni se probó red real. | 7/9: validación de estados reales y confirmación segura del servidor |
| P29 | Media | Parcial | Distintas escrituras del servicio pueden omitir el outbox si se hace write() directo o son operaciones aún no modeladas; métricas/alertas de cambios sin registrar siguen pendientes. | 7: outbox obligatoria para mutaciones sincronizables, tests de inspección de rutas |
| P30 | Media | Pendiente | No existe recuperación de claves al desinstalar/restablecer sistema, ni mecanismo seguro para compartir base cifrada entre dispositivos: copiar solamente SQLCipher no permite abrirlo sin la clave. | 6: backup de claves seguro y revocación/rotación probados |

## Política obligatoria de continuidad

1. **Antes de cada etapa:** releer esta lista, el ROADMAP y el acta anterior. Si se corrige algo, marcar Parcial o Resuelto con enlace a código, pruebas CI y aceptación, sin borrar la fila.
2. **Nunca equiparar código con protección efectiva:** distinguir biblioteca nativa, módulo opcional, función utilizada por la interfaz, funcionalidad empaquetada y protección comprobada en instalaciones reales.
3. **El modo legacy no es seguro para datos privados:** debe mantenerse temporalmente para compatibilidad y recuperación, no como opción aceptable de producción.
4. **Respaldos/migraciones:** no eliminar origen antes de verificación, recuperación completa y decisión del usuario; revisar materiales y claves además de base.
5. **No declarar “sincronizado” sin ACK:** el cliente no se ha conectado al backend; outbox es solo cola local y actor_ref no es autorización.
6. **Siguiente etapa del ROADMAP:** 5 Backend, identidad y autorización; las filas P01/P19/P22/P24/P25 requieren coordinación con 6/7/9 antes de uso productivo.
