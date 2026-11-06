# Estado técnico — SMART UNI 2.0

## Funcionalidad existente

- Escritorio Python/Tkinter; inicio de sesión local, registro, cursos, horarios y secciones académicas.
- Persistencia JSON local y gestión de materiales del prototipo.
- Escritorio: 79 descubiertos, 42 ejecutados y 37 omitidos en suite legacy; Rust: 22 tests y pruebas independientes Python (5 interop, 4 archivos, 2 recuperación DB, 4 FFI) por SO en [etapa 6](../phase-6/6_CIERRE_Y_EVIDENCIAS.md); SQLCipher legacy: 22/22 por SO; backend PostgreSQL: 14 y portal: 3 + smoke HTTP en etapa 5.
- Logotipo original, recursos SVG y tokens visuales.
- Compilación de prototipo mediante GitHub Actions.

## Arquitectura prevista, todavía no implementada

- Android Java, C++/JNI y Rust.
- Integración del núcleo Rust ya existente en la lógica operativa de escritorio y Android; el crate/ABI y sus pruebas sí se implementaron en la etapa 3.
- Despliegue operativo de FastAPI/PostgreSQL y portal Next.js ya implementados en laboratorio; servicios de almacenamiento privado y OIDC externo aún faltan.
- Producción: SQLCipher por defecto y KeyStore real, cifrado de archivos grandes, gestión de dispositivos autenticada, recuperación asistida y E2EE hacia API. El modo opt-in ya cifra copias locales de materiales mediante Rust y tiene paquetes de recuperación Argon2id probados; NO protege el modo legacy ni la API.
- Sincronización offline/online y cuentas remotas.
- Integración automatizada con Figma.

## Estado por fases

- **1 Análisis y línea base** — Completada: inventario y modelo de amenazas documentados, pruebas/capturas/respaldos sintéticos verificados en CI. Riesgos residuales sin corregir.
- **2 Contratos y sistema de diseño** — Completada; separación de capas, contratos v1, tokens y proceso Figma documentados y validados en CI, sin conexión Figma remota.
- **3 Núcleo compartido en Rust** — Completada dentro de alcance: dominio/contratos, ABI C y pruebas criptográficas cruzadas. C++ probado en Linux; biblioteca Android ARM64 compilada, sin dispositivo ni JNI real.
- **4 Persistencia local y funcionamiento offline** — Implementación técnica validada en modo opt-in (SQLCipher, migración, backup/restore, outbox), no distribución segura: [acta](../phase-4/4_CIERRE_Y_EVIDENCIAS.md).
- **5 Backend, identidad y autorización** — Base técnica FastAPI/PostgreSQL, JWT RS256 con rol/propietario verificado y portal Next.js/Auth.js con controles HTTP; **sin login IdP externo ni despliegue real**. [Acta](../phase-5/5_CIERRE_Y_EVIDENCIAS.md).
- **6 Cifrado y gestión de claves** — Componentes de laboratorio validados: AEAD Rust/FFI, contenedores locales de materiales y recuperación, HPKE con roster en memoria y C++/Android compilado. **No E2EE productivo**. [Acta](../phase-6/6_CIERRE_Y_EVIDENCIAS.md).
- **7 Sincronización multiplataforma** — Pendiente.
- **8 Aplicación Android** — Pendiente.
- **9 Seguridad, integración continua y beta** — Pendiente.
- **10 Lanzamiento gradual** — Pendiente.

La numeración definitiva y sus subfases se encuentran en [ROADMAP.md](../ROADMAP.md). No atribuir al prototipo controles de seguridad que todavía son propuestas.

## Deuda técnica y seguridad abierta

El [registro maestro de 43 pendientes](../PENDIENTES_SMART_UNI_2_0.md) es obligatorio para las etapas siguientes. Especialmente críticos son JSON/materiales legacy en claro, autorización por cuenta, protección y recuperación de claves, sincronización remota y validación de dependencias antes del lanzamiento.
