# 1 Análisis y línea base — cierre técnico y evidencias

## 1 Análisis y línea base

**Resultado: COMPLETADA en alcance de línea base.** El cierre certifica inventario, riesgos identificados y regresión; **no** certifica que el prototipo sea seguro para datos personales reales ni autoriza producir builds para usuarios finales.

### 1.1 Inventario del prototipo

[Inventario](1.1_INVENTARIO_DEL_PROTOTIPO.md) contrastado con el árbol original de `main` `6da9e168787af77570a6882a009e1a82ea90c530`. Python/Tkinter y JSON existentes; Rust, Android, backend y E2EE no implementados. Diseño, icono, fuentes, navegación y servicios funcionales no fueron alterados.

### 1.2 Auditoría y modelo de amenazas

[Auditoría](1.2_AUDITORIA_Y_MODELO_DE_AMENAZAS.md): 11 riesgos R01–R11 clasificados con evidencias por archivo y mitigaciones futuras. Especialmente R01 (datos sin cifrar), R02 (servicios identificados por email sin identidad de sesión verificable) y R04 (escrituras sin bloqueo/backup funcional). La suite no prueba ausencia de vulnerabilidades y los riesgos permanecen abiertos.

### 1.3 Pruebas y regresión

[Informe de pruebas](1.3_PRUEBAS_Y_REGRESION.md), commit de implementación y captura [`212e7b057c17e3f1465e1e6e41560877c8e8a4dd`](https://github.com/Gh0stDeveloper/smart-uni/commit/212e7b057c17e3f1465e1e6e41560877c8e8a4dd).

| Ejecución | Estado GitHub | Evidencia |
|---|---|---|
| [Pruebas de escritorio #42160375952](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42160375952) | Éxito | **Windows 26/26** y **Linux 26/26**, cinco capturas PNG y respaldo sintético por SO. |
| [Compilación EXE Windows #42160375857](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42160375857) | Éxito | [Artefacto EXE #13476432687](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42160375857/artifacts/13476432687). |
| [Convenciones #42160375903](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42160375903) | Éxito | Validador del ROADMAP y nombres, sin infracciones. |

**Artefactos con duración limitada (30 días):** [capturas/respaldo Windows #13476337984](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42160375952/artifacts/13476337984) y [capturas/respaldo Linux #13477155070](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42160375952/artifacts/13477155070). Cada ZIP contiene `01_acceso.png`, `02_panel.png`, `03_tareas.png`, `04_material.png`, `05_apuntes.png`, `respaldo_demo_sintetico.json` y `manifest.json`. Sus hashes se registraron en los logs de las tareas correspondientes; no se subieron datos reales. Los ZIP pueden caducar; el generador y los tests permanecen versionados para reproducirlos.

**Hashes de respaldos generados (SHA-256):** Windows `1c1b58be72a42d74a6a9f36d8aac9cd696c73a2eae9005db1f8d88c50e9040ab`; Linux `2fbb9bda071f9aba210759b694a6fe9957ac6b045ebf1068216f8f54251994b8`.

**Revisión de regresión:** `core.py`, `student_data.py`, `ui.py`, `student_ui.py`, `main.py`, PNG/SVG y tokens no fueron modificados por el commit de pruebas. No hubo comparación automática con capturas de una versión anterior, evaluación de accesibilidad ni prueba en hardware real: quedan como verificaciones futuras, no como pruebas completadas.

**Decisión:** se cierra **1 Análisis y línea base** con riesgos conocidos documentados. **2 Contratos y sistema de diseño sigue pendiente y no se inicia en este trabajo.** Cualquier trabajo posterior debe conservar estos artefactos, tratar R01–R11 y comprobar nuevamente la regresión.
