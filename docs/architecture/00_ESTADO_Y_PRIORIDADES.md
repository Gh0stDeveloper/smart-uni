# Estado técnico — SMART UNI 2.0

## Funcionalidad existente

- Escritorio Python/Tkinter; inicio de sesión local, registro, cursos, horarios y secciones académicas.
- Persistencia JSON local y gestión de materiales del prototipo.
- Conjunto de 17 pruebas, con dos pruebas gráficas dependientes de pantalla.
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

- **Fase 1: Análisis y línea base** — En preparación; auditoría pendiente.
- **Fase 2: Contratos y sistema de diseño** — Pendiente.
- **Fase 3: Núcleo compartido en Rust** — Pendiente.
- **Fase 4: Persistencia local y funcionamiento offline** — Pendiente.
- **Fase 5: Backend, identidad y autorización** — Pendiente.
- **Fase 6: Cifrado y gestión de claves** — Pendiente.
- **Fase 7: Sincronización multiplataforma** — Pendiente.
- **Fase 8: Aplicación Android** — Pendiente.
- **Fase 9: Seguridad, integración continua y beta** — Pendiente.
- **Fase 10: Lanzamiento gradual** — Pendiente.

La numeración definitiva y sus subfases se encuentran en [ROADMAP.md](../ROADMAP.md). No atribuir al prototipo controles de seguridad que todavía son propuestas.
