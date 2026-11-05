# Hoja de ruta — SMART UNI 2.0

## Fase 0 — Base y auditoría

- [x] Recuperar el prototipo de escritorio y ejecutar las 17 pruebas (15 pasan sin UI gráfica; 2 se omiten sin pantalla).
- [x] Definir la arquitectura Windows/Linux/Android y sincronización offline-first.
- [ ] Auditar dependencias, almacenamiento, autenticación y archivos con modelo de amenazas.
- [ ] Definir contratos de datos, versiones de esquema y migraciones seguras.

## Fase 1 — Modularizar

- [ ] Separar la UI de los servicios y repositorios manteniendo el diseño.
- [ ] Definir identificadores estables por estudiante y datos.
- [ ] Escribir pruebas de regresión y escenarios sin red.

## Fase 2 — Rust + almacenamiento

- [ ] Núcleo Rust y FFI Python.
- [ ] SQLite cifrado y migración de JSON.
- [ ] Cola durable de operaciones pendientes.

## Fase 3 — Servidor

- [ ] FastAPI, PostgreSQL y autenticación.
- [ ] Next.js para panel, documentación y administración.
- [ ] Controles de acceso, consultas parametrizadas y registros de auditoría.

## Fase 4 — Sincronización y archivos

- [ ] Sincronizar por cambios con reintentos e idempotencia.
- [ ] Detectar conflictos y conservar versiones recuperables.
- [ ] Sincronizar archivos privados con verificación de integridad.

## Fase 5 — Android y Figma

- [ ] Aplicación Android Java con C++/JNI y núcleo Rust.
- [ ] Compartir tokens visuales y mantener el diseño SMART UNI.
- [ ] Añadir flujos de prototipo y revisión con Figma.

## Fase 6 — Seguridad y distribución

- [ ] Pruebas de penetración y de recuperación; estrategia de claves.
- [ ] CI multiplataforma, firma y distribución beta.
- [ ] Revisión de privacidad, respaldo, monitoreo y actualizaciones.

**Regla:** no marcar una fase como completada sin pruebas y evidencia verificables.
