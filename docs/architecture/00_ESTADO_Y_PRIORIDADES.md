# Estado técnico — SMART UNI 2.0

## Funcionalidad existente

- Escritorio Python/Tkinter; inicio de sesión local, registro, cursos, horarios y secciones académicas.
- Persistencia JSON local y gestión de materiales del prototipo.
- Escritorio: 43 casos descubiertos (39 verifican el prototipo, 4 de FFI se omiten sin biblioteca cargada); Rust: 14 pruebas y Python-FFI: 4 pruebas por SO en la [etapa 3](../phase-3/3_CIERRE_Y_EVIDENCIAS.md). Dos pruebas Tkinter requieren pantalla gráfica.
- Logotipo original, recursos SVG y tokens visuales.
- Compilación de prototipo mediante GitHub Actions.

## Arquitectura prevista, todavía no implementada

- Android Java, C++/JNI y Rust.
- Integración del núcleo Rust ya existente en la lógica operativa de escritorio y Android; el crate/ABI y sus pruebas sí se implementaron en la etapa 3.
- FastAPI, PostgreSQL, Next.js y servicios de almacenamiento privado.
- SQLite cifrado, Argon2id, protección de claves y E2EE.
- Sincronización offline/online y cuentas remotas.
- Integración automatizada con Figma.

## Estado por fases

- **1 Análisis y línea base** — Completada: inventario y modelo de amenazas documentados, pruebas/capturas/respaldos sintéticos verificados en CI. Riesgos residuales sin corregir.
- **2 Contratos y sistema de diseño** — Completada; separación de capas, contratos v1, tokens y proceso Figma documentados y validados en CI, sin conexión Figma remota.
- **3 Núcleo compartido en Rust** — Completada dentro de alcance: dominio/contratos, ABI C y pruebas criptográficas cruzadas. C++ probado en Linux; biblioteca Android ARM64 compilada, sin dispositivo ni JNI real.
- **4 Persistencia local y funcionamiento offline** — Pendiente.
- **5 Backend, identidad y autorización** — Pendiente.
- **6 Cifrado y gestión de claves** — Pendiente.
- **7 Sincronización multiplataforma** — Pendiente.
- **8 Aplicación Android** — Pendiente.
- **9 Seguridad, integración continua y beta** — Pendiente.
- **10 Lanzamiento gradual** — Pendiente.

La numeración definitiva y sus subfases se encuentran en [ROADMAP.md](../ROADMAP.md). No atribuir al prototipo controles de seguridad que todavía son propuestas.
