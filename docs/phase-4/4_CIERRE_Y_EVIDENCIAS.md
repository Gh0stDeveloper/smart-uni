# 4 Persistencia local y funcionamiento offline — acta de alcance y evidencias

## 4 Persistencia local y funcionamiento offline

**Estado técnico:** subfases 4.1, 4.2 y 4.3 implementadas y probadas **solo dentro del alcance de modo cifrado opt-in**. El modo tradicional del prototipo NO ha migrado automáticamente a SQLCipher. **El producto no está listo para almacenar datos personales reales**; los pendientes están en [registro maestro de 30 puntos](../PENDIENTES_SMART_UNI_2_0.md).

### 4.1 Base local protegida

[Documento](4.1_BASE_LOCAL_PROTEGIDA.md). Repositorio SQLCipher 0.6.5, archivo cifrado, keyring OS con denegación de backends no autorizados, transacciones y verificación de integridad. Selección explícita mediante SMARTUNI_STORAGE=secure; JSON clásico sigue intacto en el arranque habitual. Modo de pruebas usa MemoryKeys; se requieren pruebas de Windows Credential Locker/SecretService/KWallet con equipo real. Cifrado de materiales **no implementado**, importación bloqueada en modo seguro. Commits relevantes [16beb1f](https://github.com/Gh0stDeveloper/smart-uni/commit/16beb1ff4c13d27a56555d78aa38aa7fc67f5fa4), [ce8612f](https://github.com/Gh0stDeveloper/smart-uni/commit/ce8612f6633a70a540aaa8fa0f336356e649cab4), [c430282](https://github.com/Gh0stDeveloper/smart-uni/commit/c430282e082fea6987e7481940279fddd509f33a).

### 4.2 Migración JSON y respaldos

[Documento](4.2_MIGRACION_JSON_Y_RESPALDOS.md). Migración v1 con staging temporal cifrado, SHA-256 origen antes/después, validación de contenido, promoción atómica y conservación de JSON original. Backup SQLCipher cifrado y restauración verificada con copia pre-restore; tests de corte, corrupción y reintento. **El JSON de origen sigue en claro**, deliberadamente, hasta implementar procedimiento de eliminación segura reversible. Los archivos de material no se trasladan. Commit [1cabbb](https://github.com/Gh0stDeveloper/smart-uni/commit/1cabbbafbd6a321e98e893d3b4500d7879732820).

### 4.3 Cola de operaciones pendientes

[Documento](4.3_COLA_DE_OPERACIONES_PENDIENTES.md). Snapshot + outbox en transacción SQLCipher con operación UUID idempotente y rollback de ambos registros ante fallo. Integración en acciones de apuntes, tareas, amigos/eventos de alta y perfil en modo seguro. Estados discretos locales “Sin conexión”/“Pendiente”/“Error” visibles en barra sin nuevo panel. No hay push/pull, servidor, ACK, E2EE ni cobertura de todos los borrados. Commit [0160bac](https://github.com/Gh0stDeveloper/smart-uni/commit/0160bac49858d9b8d8eed63c0b3f1c84d6d1f8c6).

### Ejecuciones verificadas

| Workflow | Resultados revisados | Evidencia |
|---|---|---|
| SQLCipher seguro Windows | **22/22 pruebas** ejecutadas satisfactoriamente, **cero omitidas**; cifrado real, migración, interrupción, backup/restore, outbox y modo seguro | [Actions #42221412867](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42221412867) |
| SQLCipher seguro Linux | **22/22 pruebas** ejecutadas satisfactoriamente, **cero omitidas** | [Actions #42221412867](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42221412867) |
| Regresión Tkinter Windows | **65 casos descubiertos: 39 ejecutados correctamente y 26 omitidos** porque son 22 tests SQLCipher y 4 FFI opcionales, ejecutados en workflows especializados | [Actions #42221412820](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42221412820) |
| Regresión Tkinter Linux | **65 casos descubiertos: 39 ejecutados correctamente y 26 omitidos** en flujo de escritorio clásico; no se afirma que 65 pasaron | [Actions #42221412820](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42221412820) |
| EXE clásico Windows | Compilación PyInstaller y tests existentes aprobados. **NO** contiene dependencias SQLCipher en el EXE clásico. | [Actions #42221412736](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42221412736) |

Los paquetes de capturas del escritorio se generan con Tkinter real en Windows y Linux, con respaldo sintético y manifest SHA-256; no verifican el keyring OS real. Toda evidencia es técnica y con datos ficticios.

### Riesgos no mitigados y decisión de producto

El registro [P01–P30](../PENDIENTES_SMART_UNI_2_0.md) incluye los pendientes completos de las etapas 1–4 y de las futuras 5–10. Impedimentos importantes: JSON y materiales por defecto sin cifrar (P01), autorización de cuentas (P02), falta de cifrado de adjuntos (P24), ausencia de keyring real verificado (P25), contratos de eliminaciones incompletos (P19), ausencia de sincronización remota (P18) y falta de recuperación de claves entre dispositivos (P30).

**Cierre del hito 4:** se acepta la implementación técnica reproducible como base para etapas posteriores, **no** se acepta seguridad de producción ni una migración por defecto. No eliminar archivos legacy; no habilitar modo secure como predeterminado antes de resolver bloqueo de materiales, integridad de backups y clave del usuario. Etapa 5 permanece pendiente.
