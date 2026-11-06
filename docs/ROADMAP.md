# Hoja de ruta oficial — SMART UNI 2.0

> **Referencia obligatoria:** [Convención de fases y subfases](CONVENCIONES_FASES.md). Los títulos se escriben únicamente como **1 Nombre** y **1.1 Nombre**, sin prefijos ni dos puntos. Se comienza en 1, con numeración correlativa y sin letras.
>
> **Estado del producto:** existe un prototipo de escritorio Python/Tkinter. El núcleo Rust, Android, el backend, la sincronización online y el cifrado E2EE están planificados, no implementados.

## Índice de fases

- **1 Análisis y línea base** — Conocer los riesgos y fijar el comportamiento actual antes de migrar.
- **2 Contratos y sistema de diseño** — Modularizar sin modificar la interfaz aprobada.
- **3 Núcleo compartido en Rust** — Concentrar las funciones sensibles e interoperables en componentes mantenibles.
- **4 Persistencia local y funcionamiento offline** — Garantizar datos disponibles sin Internet y migraciones recuperables.
- **5 Backend, identidad y autorización** — Proporcionar servicios online con separación verificable entre usuarios.
- **6 Cifrado y gestión de claves** — Proteger contenidos privados sin perder la capacidad de recuperación legítima.
- **7 Sincronización multiplataforma** — Conciliar datos offline entre Windows, Linux y Android sin pérdidas.
- **8 Aplicación Android** — Construir un cliente móvil con la identidad SMART UNI y seguridad compartida.
- **9 Seguridad, integración continua y beta** — Verificar que los controles prometidos existen y resisten fallos.
- **10 Lanzamiento gradual** — Publicar con controles de privacidad, soporte y operación.

## Criterios comunes

- No alterar el diseño aprobado ni incorporar un panel derecho redundante.
- No declarar avances terminados sin archivos de código, resultados de pruebas y evidencia.
- No utilizar datos reales ni claves del servidor en ejemplos o pruebas del prototipo.
- Conservar respaldos y compatibilidad en cada migración; no perder operaciones offline.
- Aplicar autorización por recurso en el servidor, incluso si el cliente usa Rust o C++.
- Mantener los nombres oficiales en commits de hito, documentos, informes e issues.

## 1 Análisis y línea base

**Objetivo:** Conocer los riesgos y fijar el comportamiento actual antes de migrar.

### 1.1 Inventario del prototipo

- [x] Inventariar código, dependencias, JSON, archivos, iconografía y pantallas.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 1.2 Auditoría y modelo de amenazas

- [x] Documentar credenciales, límites de confianza, datos personales y amenazas.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 1.3 Pruebas y regresión

- [x] Crear evidencia reproducible Windows/Linux, capturas y respaldos de prueba.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.


**Evidencia de cierre:** [1.1 Inventario](phase-1/1.1_INVENTARIO_DEL_PROTOTIPO.md) · [1.2 Auditoría](phase-1/1.2_AUDITORIA_Y_MODELO_DE_AMENAZAS.md) · [1.3 Pruebas](phase-1/1.3_PRUEBAS_Y_REGRESION.md) · [Acta de cierre](phase-1/1_CIERRE_Y_EVIDENCIAS.md). Commit de pruebas `212e7b057c17e3f1465e1e6e41560877c8e8a4dd`: 26/26 Windows y 26/26 Linux, capturas y respaldos sintéticos publicados ([Actions #42160375952](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42160375952)). Compilación Windows [#42160375857](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42160375857) y nomenclatura [#42160375903](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42160375903) exitosas. Los riesgos R01–R11 son pendientes de mitigación en etapas posteriores; esta etapa fija la línea base, no certifica seguridad de producción.

**Criterio de cierre:** completado para el alcance de inventario, auditoría y regresión. Revisar riesgos residuales antes de diseñar cambios en 2.

## 2 Contratos y sistema de diseño

**Objetivo:** Modularizar sin modificar la interfaz aprobada.

### 2.1 Separación de capas de escritorio

- [x] Separar UI, dominio, repositorios y sesión sin romper funciones.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 2.2 Contratos compartidos

- [x] Versionar esquemas, identificadores, errores y operaciones entre clientes.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 2.3 Sistema visual y Figma

- [x] Centralizar diseño, tokens, iconos y proceso de revisión entre plataformas.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Evidencias verificadas:** [2.1 Separación](phase-2/2.1_SEPARACION_DE_CAPAS.md) · [2.2 Contratos](phase-2/2.2_CONTRATOS_COMPARTIDOS.md) · [2.3 Diseño](phase-2/2.3_SISTEMA_VISUAL_Y_FIGMA.md) · [Acta de cierre](phase-2/2_CIERRE_Y_EVIDENCIAS.md). Implementación validada en [commit 0a02c42](https://github.com/Gh0stDeveloper/smart-uni/commit/0a02c42c22d481c34bf20d374ac2bc2dead50000): 39 pruebas OK en Windows y Linux ([Actions #42162128163](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42162128163)), comprobación de contratos/diseño [#42162128182](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42162128182), compilación EXE Windows [#42162128160](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42162128160) y convención [#42162128175](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42162128175) en verde. Capturas y respaldo sintético por sistema publicados. No se ha iniciado 3 ni mitigado R01/R02.

**Criterio de cierre:** cumplido dentro de este alcance de modularización, contratos y conservación del diseño, con revisión de evidencia.

## 3 Núcleo compartido en Rust

**Objetivo:** Concentrar las funciones sensibles e interoperables en componentes mantenibles.

### 3.1 Dominio y biblioteca Rust

- [x] Implementar lógica compartida con pruebas y versiones de datos.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 3.2 Interfaces nativas y FFI

- [x] Preparar enlaces Python ↔ Rust y C/C++ ↔ Rust para Android.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 3.3 Validación criptográfica cruzada

- [x] Seleccionar bibliotecas auditadas y probar vectores entre plataformas.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Evidencia de cierre:** [3.1 Dominio Rust](phase-3/3.1_DOMINIO_Y_BIBLIOTECA_RUST.md) · [3.2 FFI](phase-3/3.2_INTERFACES_NATIVAS_Y_FFI.md) · [3.3 Vectores criptográficos](phase-3/3.3_VALIDACION_CRIPTOGRAFICA_CRUZADA.md) · [Acta de cierre](phase-3/3_CIERRE_Y_EVIDENCIAS.md). [GitHub Actions #42216145594](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42216145594): Rust 14/14 pruebas en Windows y Linux, puente Python 4/4 por sistema, AES-GCM contrastado mediante OpenSSL, consumidor C++ ejecutado en Linux y compilación Android ARM64 con NDK. No se ha ejecutado el binario en Android ni se han migrado datos a Rust.

**Criterio de cierre:** completado para el alcance de dominio, ABI nativa y validación cruzada de primitivas. El cifrado del usuario, gestión de claves y cliente Android permanecen pendientes de las etapas correspondientes.

## 4 Persistencia local y funcionamiento offline

**Objetivo:** Garantizar datos disponibles sin Internet y migraciones recuperables.

### 4.1 Base local protegida

- [x] Introducir SQLite cifrado y protección de claves por sistema operativo.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 4.2 Migración JSON y respaldos

- [x] Migrar sin borrar el origen; verificar restauración e interrupciones.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 4.3 Cola de operaciones pendientes

- [x] Guardar cambios y outbox en una transacción; reflejar estados discretos.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre del hito técnico:** pruebas y evidencia verificadas **en modo SQLCipher opt-in**, sin declarar protección de producción. [4.1 SQLCipher](phase-4/4.1_BASE_LOCAL_PROTEGIDA.md) · [4.2 Migración y respaldos](phase-4/4.2_MIGRACION_JSON_Y_RESPALDOS.md) · [4.3 Outbox](phase-4/4.3_COLA_DE_OPERACIONES_PENDIENTES.md) · [Acta con pruebas reales](phase-4/4_CIERRE_Y_EVIDENCIAS.md). Las dependencias y criterios de cierre productivo que no se cubrieron siguen **abiertos** en el [registro maestro P01–P30](PENDIENTES_SMART_UNI_2_0.md).

**No confundir:** el EXE clásico sigue en JSON, el modo seguro bloquea materiales y no hay sync/red. El cierre técnico de la etapa 4 no autoriza datos reales.

## 5 Backend, identidad y autorización

**Objetivo:** Proporcionar servicios online con separación verificable entre usuarios.

### 5.1 API y PostgreSQL

- [x] Desarrollar FastAPI, migraciones, validaciones y SQL parametrizado.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 5.2 Portal Next.js

- [x] Crear panel TypeScript con roles, cookies seguras y defensas web.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 5.3 Cuentas y permisos

- [x] OIDC/OAuth con PKCE; pruebas de aislamiento, sesiones y autorización.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre del hito técnico:** implementado y validado con Postgres de laboratorio y pruebas de JWT RSA, TypeScript y HTTP. [5.1 API y PostgreSQL](phase-5/5.1_API_Y_POSTGRESQL.md) · [5.2 Portal Next.js](phase-5/5.2_PORTAL_NEXT_JS.md) · [5.3 Cuentas y permisos](phase-5/5.3_CUENTAS_Y_PERMISOS.md) · [Acta de cierre](phase-5/5_CIERRE_Y_EVIDENCIAS.md). **No equivale a identidad productiva ni a login OIDC externo probado**. Prueba de IdP real, refresh y despliegue siguen abiertos en [registro P01–P36](PENDIENTES_SMART_UNI_2_0.md).

## 6 Cifrado y gestión de claves

**Objetivo:** Proteger contenidos privados sin perder la capacidad de recuperación legítima.

### 6.1 Modelo de cifrado

- [x] Definir TLS, E2EE, metadatos visibles y formatos autenticados.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 6.2 Administración y recuperación

- [x] Altas y bajas de dispositivos, rotación y copias de recuperación.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 6.3 Interoperabilidad y revisión

- [x] Pruebas de cifrado, errores, recuperación y control de claves en clientes.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre técnico:** Rust AEAD + HPKE/Argon2id, prototipos de gestión de dispositivos y recuperación probados con claves sintéticas; integración opt-in de materiales en SQLCipher. [6.1 Modelo de cifrado](phase-6/6.1_MODELO_DE_CIFRADO.md) · [6.2 Administración y recuperación](phase-6/6.2_ADMINISTRACION_Y_RECUPERACION.md) · [6.3 Interoperabilidad](phase-6/6.3_INTEROPERABILIDAD_Y_REVISION.md) · [Acta CI](phase-6/6_CIERRE_Y_EVIDENCIAS.md). **La protección E2EE real entre dispositivos, el servidor ciphertext-only, el alta autorizada de dispositivos y el hardware KeyStore siguen abiertos** en [P01–P43](PENDIENTES_SMART_UNI_2_0.md). Las casillas marcan únicamente el desarrollo/test de los componentes iniciales de esta etapa, no la integración productiva.

## 7 Sincronización multiplataforma

**Objetivo:** Conciliar datos offline entre Windows, Linux y Android sin pérdidas.

### 7.1 Sincronización incremental

- [x] Push/pull con cursor, revisiones, idempotencia y reintentos.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 7.2 Conflictos y eliminaciones

- [x] Conservar versiones y permitir resolver conflictos; tombstones.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 7.3 Materiales y archivos

- [x] Adjuntos privados cifrados, subida reanudable y verificación de integridad.
- [x] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre técnico:** API PostgreSQL v2 + cliente SQLCipher/Rust opt-in. [7.1 Sincronización incremental](phase-7/7.1_SINCRONIZACION_INCREMENTAL.md) · [7.2 Conflictos y eliminaciones](phase-7/7.2_CONFLICTOS_Y_ELIMINACIONES.md) · [7.3 Materiales y archivos](phase-7/7.3_MATERIALES_Y_ARCHIVOS.md) · [Acta con pruebas E2E](phase-7/7_CIERRE_Y_EVIDENCIAS.md). **Las casillas representan componentes verificados en laboratorio, no sincronización de la UI ni Android.** IdP, enrolamiento de claves, integración UI, red real, anti-rollback y migración del outbox legacy siguen abiertos en [P01–P52](PENDIENTES_SMART_UNI_2_0.md).

## 8 Aplicación Android

**Objetivo:** Construir un cliente móvil con la identidad SMART UNI y seguridad compartida.

**Implementación inicial en curso:** proyecto Gradle Java con las seis secciones adaptativas y birrete original; nota local cifrada con Rust/Android Keystore; adaptador C++/JNI para diagnóstico HTTPS; workflows APK/AAB y pruebas instrumentadas. **Todavía no equivale a 8 completada:** OIDC/PKCE, sincronización entre dispositivos, almacenamiento multi-entidad, firma comercial y pruebas físicas quedan pendientes. [Acta provisional y evidencias](phase-8/8_CIERRE_Y_EVIDENCIAS.md).

### 8.1 Interfaz nativa Java

- [ ] Pantallas accesibles y adaptativas con el diseño e icono originales.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 8.2 Comunicación C++/JNI

- [ ] Red y endpoints en código nativo sin tratar rutas como secretos.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 8.3 Rust y Android Keystore

- [ ] Integrar núcleo, protección de claves, pruebas y firma de APK/AAB.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre:** evidencia verificable, pruebas satisfactorias y revisión antes de continuar.

## 9 Seguridad, integración continua y beta

**Objetivo:** Verificar que los controles prometidos existen y resisten fallos.

**Desarrollo inicial en curso:** tests negativos SQLi/aislamiento, 640 mutaciones de ABI Rust, SAST CodeQL, informes SCA, puerta estática de seguridad, R8 Android, verificador offline de firma Ed25519 y downgrade, y checklist beta que rechaza por defecto. Los requisitos de auditoría real, firma comercial, actualización de clientes y dispositivos físicos NO se han completado. [Acta y limitaciones](phase-9/9_CIERRE_Y_EVIDENCIAS.md). **Las casillas se mantienen sin marcar** hasta cumplir cada criterio íntegramente.

### 9.1 Auditoría de seguridad

- [ ] Pruebas SQLi, control de acceso, SAST, dependencias y fuzzing.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 9.2 Compilación y actualización

- [ ] CI multiplataforma, firma, actualización segura y rollback.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 9.3 Beta controlada

- [ ] Validar dispositivos reales, recuperar datos y cerrar defectos críticos.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre:** evidencia verificable, pruebas satisfactorias y revisión antes de continuar.

## 10 Lanzamiento gradual

**Objetivo:** Publicar con controles de privacidad, soporte y operación.

### 10.1 Privacidad y cumplimiento

- [ ] Exportación/borrado de datos, avisos y permisos documentados.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 10.2 Operación y soporte

- [ ] Monitoreo, incidentes, copias, recuperación y reporte privado.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### 10.3 Aprobación de publicación

- [ ] Checklist go/no-go y despliegue progresivo verificable.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre:** evidencia verificable, pruebas satisfactorias y revisión antes de continuar.

---

## Control del avance

Las etapas **1–7 están implementadas y validadas dentro de su alcance técnico experimental**. Etapa 7: sync ciphertext-only y conflictos en FastAPI/PostgreSQL, cliente Rust/SQLCipher, cursor CAS y adjuntos reanudables con 22 pruebas API, 6 E2E Linux y 5 pruebas nativas del cliente por SO. **Sin sincronización automática de producto, Android, IdP real ni distribución de claves segura; API plaintext legacy bloqueada por defecto**. Etapas **8 y 9 en curso, sin cierre técnico**; etapa **10 pendiente**. La etapa 8 tiene compilaciones Android reproducibles, pero instrumentación [#42296402993](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42296402993) fallida (ADB offline/crash; cero tests), por lo que no se autoriza beta. [Registro maestro actualizado](PENDIENTES_SMART_UNI_2_0.md).

El detalle técnico se encuentra en [arquitectura multiplataforma](architecture/SMART_UNI_2_0_Arquitectura_Multiplataforma_Segura.md). **Este documento prevalece** cuando otros planes anteriores utilizan números o etapas diferentes.
