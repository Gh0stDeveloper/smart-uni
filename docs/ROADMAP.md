# Hoja de ruta oficial — SMART UNI 2.0

> **Referencia obligatoria:** [Convención de fases y subfases](CONVENCIONES_FASES.md). Cada etapa se identifica como **Fase 1: Nombre** y sus divisiones como **Subfase 1.1: Nombre**. Se comienza en 1, con numeración correlativa y sin letras.
>
> **Estado del producto:** existe un prototipo de escritorio Python/Tkinter. El núcleo Rust, Android, el backend, la sincronización online y el cifrado E2EE están planificados, no implementados.

## Índice de fases

- **Fase 1: Análisis y línea base** — Conocer los riesgos y fijar el comportamiento actual antes de migrar.
- **Fase 2: Contratos y sistema de diseño** — Modularizar sin modificar la interfaz aprobada.
- **Fase 3: Núcleo compartido en Rust** — Concentrar las funciones sensibles e interoperables en componentes mantenibles.
- **Fase 4: Persistencia local y funcionamiento offline** — Garantizar datos disponibles sin Internet y migraciones recuperables.
- **Fase 5: Backend, identidad y autorización** — Proporcionar servicios online con separación verificable entre usuarios.
- **Fase 6: Cifrado y gestión de claves** — Proteger contenidos privados sin perder la capacidad de recuperación legítima.
- **Fase 7: Sincronización multiplataforma** — Conciliar datos offline entre Windows, Linux y Android sin pérdidas.
- **Fase 8: Aplicación Android** — Construir un cliente móvil con la identidad SMART UNI y seguridad compartida.
- **Fase 9: Seguridad, integración continua y beta** — Verificar que los controles prometidos existen y resisten fallos.
- **Fase 10: Lanzamiento gradual** — Publicar con controles de privacidad, soporte y operación.

## Criterios comunes

- No alterar el diseño aprobado ni incorporar un panel derecho redundante.
- No declarar avances terminados sin archivos de código, resultados de pruebas y evidencia.
- No utilizar datos reales ni claves del servidor en ejemplos o pruebas del prototipo.
- Conservar respaldos y compatibilidad en cada migración; no perder operaciones offline.
- Aplicar autorización por recurso en el servidor, incluso si el cliente usa Rust o C++.
- Mantener los nombres oficiales en commits de hito, documentos, informes e issues.

## Fase 1: Análisis y línea base

**Objetivo:** Conocer los riesgos y fijar el comportamiento actual antes de migrar.

### Subfase 1.1: Inventario del prototipo

- [ ] Inventariar código, dependencias, JSON, archivos, iconografía y pantallas.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 1.2: Auditoría y modelo de amenazas

- [ ] Documentar credenciales, límites de confianza, datos personales y amenazas.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 1.3: Pruebas y regresión

- [ ] Crear evidencia reproducible Windows/Linux, capturas y respaldos de prueba.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre:** evidencia verificable, pruebas satisfactorias y revisión antes de continuar.

## Fase 2: Contratos y sistema de diseño

**Objetivo:** Modularizar sin modificar la interfaz aprobada.

### Subfase 2.1: Separación de capas de escritorio

- [ ] Separar UI, dominio, repositorios y sesión sin romper funciones.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 2.2: Contratos compartidos

- [ ] Versionar esquemas, identificadores, errores y operaciones entre clientes.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 2.3: Sistema visual y Figma

- [ ] Centralizar diseño, tokens, iconos y proceso de revisión entre plataformas.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre:** evidencia verificable, pruebas satisfactorias y revisión antes de continuar.

## Fase 3: Núcleo compartido en Rust

**Objetivo:** Concentrar las funciones sensibles e interoperables en componentes mantenibles.

### Subfase 3.1: Dominio y biblioteca Rust

- [ ] Implementar lógica compartida con pruebas y versiones de datos.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 3.2: Interfaces nativas y FFI

- [ ] Preparar enlaces Python ↔ Rust y C/C++ ↔ Rust para Android.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 3.3: Validación criptográfica cruzada

- [ ] Seleccionar bibliotecas auditadas y probar vectores entre plataformas.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre:** evidencia verificable, pruebas satisfactorias y revisión antes de continuar.

## Fase 4: Persistencia local y funcionamiento offline

**Objetivo:** Garantizar datos disponibles sin Internet y migraciones recuperables.

### Subfase 4.1: Base local protegida

- [ ] Introducir SQLite cifrado y protección de claves por sistema operativo.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 4.2: Migración JSON y respaldos

- [ ] Migrar sin borrar el origen; verificar restauración e interrupciones.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 4.3: Cola de operaciones pendientes

- [ ] Guardar cambios y outbox en una transacción; reflejar estados discretos.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre:** evidencia verificable, pruebas satisfactorias y revisión antes de continuar.

## Fase 5: Backend, identidad y autorización

**Objetivo:** Proporcionar servicios online con separación verificable entre usuarios.

### Subfase 5.1: API y PostgreSQL

- [ ] Desarrollar FastAPI, migraciones, validaciones y SQL parametrizado.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 5.2: Portal Next.js

- [ ] Crear panel TypeScript con roles, cookies seguras y defensas web.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 5.3: Cuentas y permisos

- [ ] OIDC/OAuth con PKCE; pruebas de aislamiento, sesiones y autorización.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre:** evidencia verificable, pruebas satisfactorias y revisión antes de continuar.

## Fase 6: Cifrado y gestión de claves

**Objetivo:** Proteger contenidos privados sin perder la capacidad de recuperación legítima.

### Subfase 6.1: Modelo de cifrado

- [ ] Definir TLS, E2EE, metadatos visibles y formatos autenticados.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 6.2: Administración y recuperación

- [ ] Altas y bajas de dispositivos, rotación y copias de recuperación.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 6.3: Interoperabilidad y revisión

- [ ] Pruebas de cifrado, errores, recuperación y control de claves en clientes.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre:** evidencia verificable, pruebas satisfactorias y revisión antes de continuar.

## Fase 7: Sincronización multiplataforma

**Objetivo:** Conciliar datos offline entre Windows, Linux y Android sin pérdidas.

### Subfase 7.1: Sincronización incremental

- [ ] Push/pull con cursor, revisiones, idempotencia y reintentos.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 7.2: Conflictos y eliminaciones

- [ ] Conservar versiones y permitir resolver conflictos; tombstones.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 7.3: Materiales y archivos

- [ ] Adjuntos privados cifrados, subida reanudable y verificación de integridad.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre:** evidencia verificable, pruebas satisfactorias y revisión antes de continuar.

## Fase 8: Aplicación Android

**Objetivo:** Construir un cliente móvil con la identidad SMART UNI y seguridad compartida.

### Subfase 8.1: Interfaz nativa Java

- [ ] Pantallas accesibles y adaptativas con el diseño e icono originales.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 8.2: Comunicación C++/JNI

- [ ] Red y endpoints en código nativo sin tratar rutas como secretos.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 8.3: Rust y Android Keystore

- [ ] Integrar núcleo, protección de claves, pruebas y firma de APK/AAB.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre:** evidencia verificable, pruebas satisfactorias y revisión antes de continuar.

## Fase 9: Seguridad, integración continua y beta

**Objetivo:** Verificar que los controles prometidos existen y resisten fallos.

### Subfase 9.1: Auditoría de seguridad

- [ ] Pruebas SQLi, control de acceso, SAST, dependencias y fuzzing.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 9.2: Compilación y actualización

- [ ] CI multiplataforma, firma, actualización segura y rollback.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 9.3: Beta controlada

- [ ] Validar dispositivos reales, recuperar datos y cerrar defectos críticos.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre:** evidencia verificable, pruebas satisfactorias y revisión antes de continuar.

## Fase 10: Lanzamiento gradual

**Objetivo:** Publicar con controles de privacidad, soporte y operación.

### Subfase 10.1: Privacidad y cumplimiento

- [ ] Exportación/borrado de datos, avisos y permisos documentados.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 10.2: Operación y soporte

- [ ] Monitoreo, incidentes, copias, recuperación y reporte privado.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

### Subfase 10.3: Aprobación de publicación

- [ ] Checklist go/no-go y despliegue progresivo verificable.
- [ ] Adjuntar pruebas, criterios de aceptación y enlace al commit correspondiente.

**Criterio de cierre:** evidencia verificable, pruebas satisfactorias y revisión antes de continuar.

---

## Control del avance

La primera fase está **en preparación**; ninguna de las diez fases se considera completada. Un cambio de estado exige evidencia verificable.

El detalle técnico se encuentra en [arquitectura multiplataforma](architecture/SMART_UNI_2_0_Arquitectura_Multiplataforma_Segura.md). **Este documento prevalece** cuando otros planes anteriores utilizan números o etapas diferentes.
