# Estado de los componentes

## Funciona actualmente
- Aplicación Tkinter en Windows/Linux, persistencia local JSON, registro, login, secciones académicas.
- 17 pruebas de funcionalidad/UI, sujetas a entorno gráfico.
- Icono y tokens originales disponibles para futuras interfaces.

## Todavía no funciona (plan SMART UNI 2.0)
- Android Java/C++/Rust
- Núcleo Rust compartido
- API FastAPI + PostgreSQL y panel Next.js
- SQLite cifrado, Argon2id migrado y sincronización online/offline
- Autenticación remota y cifrado extremo a extremo

## Orden de implementación
Primero auditoría y migraciones compatibles; después Rust y SQLite; a continuación API/identidades/sincronización; finalmente Android, seguridad final y distribución. No comprometemos datos reales de estudiantes antes de realizar pruebas de seguridad.
