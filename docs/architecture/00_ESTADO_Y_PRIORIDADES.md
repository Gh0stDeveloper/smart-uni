# Estado técnico — SMART UNI 2.0

## Funcionalidad existente

- Escritorio Python/Tkinter; inicio de sesión local, registro, cursos, horarios y secciones académicas.
- Persistencia JSON local y gestión de materiales del prototipo.
- Conjunto de 26 pruebas (17 iniciales + 9 regresión), con dos pruebas gráficas dependientes de pantalla; resultados en ambos SO [documentados](../phase-1/1_CIERRE_Y_EVIDENCIAS.md).
- Logotipo original, recursos SVG y tokens visuales.
- Compilación de prototipo mediante GitHub Actions.

## Arquitectura prevista, todavía no implementada

- Android Java, C++/JNI y Rust.
- Núcleo Rust común a las plataformas.
- FastAPI, PostgreSQL, Next.js y servicios de almacenamiento privado.
- SQLite cifrado, Argon2id, protección de claves y E2EE.
- Sincronización offline/online y cuentas remotas.
- Integración automatizada con Figma.

## Estado por fases

- **1 Análisis y línea base** — Completada: inventario y modelo de amenazas documentados, pruebas/capturas/respaldos sintéticos verificados en CI. Riesgos residuales sin corregir.
- **2 Contratos y sistema de diseño** — Pendiente.
- **3 Núcleo compartido en Rust** — Pendiente.
- **4 Persistencia local y funcionamiento offline** — Pendiente.
- **5 Backend, identidad y autorización** — Pendiente.
- **6 Cifrado y gestión de claves** — Pendiente.
- **7 Sincronización multiplataforma** — Pendiente.
- **8 Aplicación Android** — Pendiente.
- **9 Seguridad, integración continua y beta** — Pendiente.
- **10 Lanzamiento gradual** — Pendiente.

La numeración definitiva y sus subfases se encuentran en [ROADMAP.md](../ROADMAP.md). No atribuir al prototipo controles de seguridad que todavía son propuestas.
