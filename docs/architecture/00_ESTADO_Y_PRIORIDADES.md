# Estado técnico — SMART UNI 2.0

## Funcionalidad existente

- Escritorio Python/Tkinter; inicio de sesión local, registro, cursos, horarios y secciones académicas.
- Persistencia JSON local y gestión de materiales del prototipo.
- Escritorio: 84 descubiertos, 42 ejecutados y 42 omitidos sin nativas; Rust: 22, 5 interop, 4 materiales, 2 recovery, 5 cliente sync y 4 FFI por SO. SQLCipher legacy: 22/22 por SO. Backend PostgreSQL: 22 pruebas; 6 E2E Linux Rust+SQLCipher+PG. [Etapa 7](../phase-7/7_CIERRE_Y_EVIDENCIAS.md).
- Logotipo original, recursos SVG y tokens visuales.
- Compilación de prototipo mediante GitHub Actions.

## Arquitectura prevista, todavía no implementada

- Android Java, C++/JNI y Rust ya se encuentran compilables en un cliente experimental con almacenamiento cifrado local; falta integrarlo a OIDC y sync E2EE real.
- Integración del núcleo Rust ya existente en la lógica operativa de escritorio y Android; el crate/ABI y sus pruebas sí se implementaron en la etapa 3.
- Despliegue operativo de FastAPI/PostgreSQL y portal Next.js ya implementados en laboratorio; servicios de almacenamiento privado y OIDC externo aún faltan.
- Producción: SQLCipher por defecto y KeyStore real, cifrado de archivos grandes, gestión de dispositivos autenticada, recuperación asistida y E2EE hacia API. El modo opt-in ya cifra copias locales de materiales mediante Rust y tiene paquetes de recuperación Argon2id probados; NO protege el modo legacy ni la API.
- Sincronización automática en la UI y cuentas remotas con IdP real: existe el motor v2 ciphertext-only probado, aún sin integración final.
- Integración automatizada con Figma.

## Estado por fases

- **1 Análisis y línea base** — Completada: inventario y modelo de amenazas documentados, pruebas/capturas/respaldos sintéticos verificados en CI. Riesgos residuales sin corregir.
- **2 Contratos y sistema de diseño** — Completada; separación de capas, contratos v1, tokens y proceso Figma documentados y validados en CI, sin conexión Figma remota.
- **3 Núcleo compartido en Rust** — Completada dentro de alcance: dominio/contratos, ABI C y pruebas criptográficas cruzadas. C++ probado en Linux; biblioteca Android ARM64 compilada, sin dispositivo ni JNI real.
- **4 Persistencia local y funcionamiento offline** — Implementación técnica validada en modo opt-in (SQLCipher, migración, backup/restore, outbox), no distribución segura: [acta](../phase-4/4_CIERRE_Y_EVIDENCIAS.md).
- **5 Backend, identidad y autorización** — Base técnica FastAPI/PostgreSQL, JWT RS256 con rol/propietario verificado y portal Next.js/Auth.js con controles HTTP; **sin login IdP externo ni despliegue real**. [Acta](../phase-5/5_CIERRE_Y_EVIDENCIAS.md).
- **6 Cifrado y gestión de claves** — Componentes de laboratorio validados: AEAD Rust/FFI, contenedores locales de materiales y recuperación, HPKE con roster en memoria y C++/Android compilado. **No E2EE productivo**. [Acta](../phase-6/6_CIERRE_Y_EVIDENCIAS.md).
- **7 Sincronización multiplataforma** — Motor técnico E2EE de laboratorio (PostgreSQL, Rust/SQLCipher, cursor, CAS, conflictos, tombstones y blobs cifrados reanudables), sin IdP real, Android ni sincronización UI automática. [Acta](../phase-7/7_CIERRE_Y_EVIDENCIAS.md).
- **8 Aplicación Android** — Parcial: interfaz con CRUD local cifrado, rutas API vía JNI C++ y Keystore/Rust; falta instrumentación aprobada, IdP y sincronización productiva. [Acta](../phase-8/8_CIERRE_Y_EVIDENCIAS.md).
- **9 Seguridad, integración continua y beta** — Parcial: CodeQL/SCA/gates CI y firma offline experimental; beta externa sin autorizar. [Acta](../phase-9/9_CIERRE_Y_EVIDENCIAS.md).
- **10 Lanzamiento gradual** — Pendiente.

La numeración definitiva y sus subfases se encuentran en [ROADMAP.md](../ROADMAP.md). No atribuir al prototipo controles de seguridad que todavía son propuestas.

## Deuda técnica y seguridad abierta

El [registro maestro de 64 asuntos](../PENDIENTES_SMART_UNI_2_0.md) es obligatorio para las etapas siguientes. Especialmente críticos son JSON/materiales legacy en claro, autorización por cuenta, protección y recuperación de claves, sincronización remota y validación de dependencias antes del lanzamiento.
