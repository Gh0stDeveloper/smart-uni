# SMART UNI

Plataforma académica para estudiantes. Estamos trabajando para que funcione **sin conexión** y sincronice datos entre **Windows, Linux y Android** cuando vuelva Internet.

> **Estado actual:** prototipo académico de escritorio (Python + Tkinter). **SMART UNI 2.0 todavía NO es una versión de producción.** El backend, la app Android, el cifrado de base de datos y el núcleo Rust están planificados, no implementados.

## Qué tenemos ahora

El prototipo incluye inicio de sesión local, registro, panel de cursos y horarios, anuncios, inicio académico, perfil, amigos, calendario, material, tareas y apuntes. La información se guarda en JSON local. La interfaz aprobada mantiene el icono original del birrete, el menú único y **ningún panel adicional a la derecha**.

## Dónde estamos trabajando

- `apps/desktop/` — Código del prototipo para Windows/Linux y pruebas.
- `apps/android/` — Futura app Java + C++/JNI + núcleo Rust.
- `apps/web/` — Futuro portal/panel Next.js.
- `core/rust/` — Futuro núcleo común para cifrado, operaciones locales y sincronización.
- `services/api/` — Futuro servidor FastAPI con PostgreSQL.
- `packages/design-system/` — Guía visual y tokens compatibles con Figma.
- `docs/architecture/` — Arquitectura, decisiones de seguridad y fases de producción.

## Cómo ejecutar el prototipo de escritorio

Necesitamos Python 3.10+ y Tkinter. Desde la raíz del repositorio:

```bash
cd apps/desktop
python main.py
```

Para ejecutar las pruebas:

```bash
cd apps/desktop
python -m unittest discover -s tests -v
```

La cuenta `demo@smartuni.edu` es **solo para pruebas**, no para producción. La aplicación aún utiliza PBKDF2-SHA256 y archivos JSON; su migración está documentada. No debemos subir datos reales de estudiantes ni credenciales.

## Cómo construiremos SMART UNI 2.0

1. Auditar la versión de escritorio y preparar pruebas de regresión.
2. Separar la interfaz y los servicios e introducir el núcleo compartido en Rust.
3. Migrar los datos locales a SQLite cifrado y conservar la compatibilidad con JSON.
4. Desarrollar FastAPI, PostgreSQL, Next.js y autenticación segura.
5. Implementar sincronización offline-first, conflictos y archivos.
6. Integrar Android (Java, C++/JNI y Rust), sin incrustar secretos universales.
7. Verificar seguridad, compatibilidad y compilaciones para distribuir una beta.

**Puntos de seguridad:** Argon2id donde se administren contraseñas; TLS 1.3; cifrado autenticado de datos sensibles; consultas SQL parametrizadas; autorización por recurso; autenticación del dispositivo; rotación de claves; respaldos y pruebas de seguridad. Rust/C++ por sí solos no reemplazan esos controles.

## Criterios para cambios

- Conservar la interfaz original SMART UNI.
- Mantener el código organizado y explicaciones claras.
- No marcar características como terminadas hasta que existan pruebas.
- No enviar contraseñas, tokens, claves privadas ni datos reales al repositorio.
- Documentar pruebas y decisiones de seguridad en cada fase.

El repositorio actualmente es **público**. Antes de publicar una producción real hay que completar una auditoría y definir una política de privacidad.

Consulta el plan en `docs/architecture/`.