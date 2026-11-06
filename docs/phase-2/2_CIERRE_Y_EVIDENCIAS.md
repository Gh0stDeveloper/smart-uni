# 2 Contratos y sistema de diseño — cierre y evidencias reales

## 2 Contratos y sistema de diseño

**Estado: completada y validada en alcance.** No se ha iniciado 3 Núcleo compartido en Rust. Se mantiene el diseño y las funciones del prototipo, con esquema JSON local existente; no se declara seguridad de producción.

### 2.1 Separación de capas de escritorio

[Documento de 2.1](2.1_SEPARACION_DE_CAPAS.md). Servicios Tkinter separados de validación/dominio (`domain.py`), persistencia (`repository.py`, `RecordRepository`), estado local (`session.py`) y servicios de aplicación (`core.py` / `student_data.py`). Se preservan `SmartUniService._read/_write`, las firmas públicas y navegación. Commits [b09c9b1](https://github.com/Gh0stDeveloper/smart-uni/commit/b09c9b1f99314013d8a2917f4fe119024583c90b) y corrección verificada [3176e1e](https://github.com/Gh0stDeveloper/smart-uni/commit/3176e1ed5100a3bde7a63bdce68c3e82fc9b0e5e).

### 2.2 Contratos compartidos

[Documento de 2.2](2.2_CONTRATOS_COMPARTIDOS.md). Registro `1.0.0` + JSON Schema Draft 2020-12 de envelope, errores y almacenamiento legacy, fixtures reales sintéticos y rechazo de versiones/IDs/códigos inválidos. Validados con `jsonschema==4.23.0` en GitHub. Commit [14b2cbd](https://github.com/Gh0stDeveloper/smart-uni/commit/14b2cbd2babf7166d7752b1d7278c0b8f5914c26). Ningún endpoint, backend o servicio remoto implementado.

### 2.3 Sistema visual y Figma

[Documento de 2.3](2.3_SISTEMA_VISUAL_Y_FIGMA.md). Fuente canónica `packages/design-system/tokens.json`, copia de escritorio verificada, `design_system.py` en UI, iconos SVG/PNG protegidos por hash SHA de blob Git. PyInstaller Windows/Linux incluye `design/tokens.json`. Procedimiento Figma documentado; **conexión Figma no configurada**. Commits [ee867c5](https://github.com/Gh0stDeveloper/smart-uni/commit/ee867c5bd46da6814af6aca25c18024b63d5512c) y [0a02c42](https://github.com/Gh0stDeveloper/smart-uni/commit/0a02c42c22d481c34bf20d374ac2bc2dead50000).

#### Evidencias de integración y regresión

Comprobado sobre `0a02c42c22d481c34bf20d374ac2bc2dead50000`, el 5 de noviembre de 2026 hora local / 6 de noviembre UTC en GitHub Actions:

| Trabajo | Resultado verificado | URL |
|---|---|---|
| Pruebas Ubuntu | **39 de 39** OK, 4.514 s; capturas y respaldo sintético publicados | [Actions #42162128163](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42162128163) |
| Pruebas Windows | **39 de 39** OK, 9.095 s; capturas y respaldo sintético publicados | [Actions #42162128163](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42162128163) |
| Compilación Windows EXE | **success**; 39 tests OK también dentro del workflow | [Actions #42162128160](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42162128160) |
| JSON Schemas y diseño | **success**, incluyendo validación de contratos, tokens e iconos | [Actions #42162128182](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42162128182) |
| Convención de numeración | **success** | [Actions #42162128175](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42162128175) |

**Artefactos GitHub Actions (retención limitada):** [capturas + respaldo Windows #13477616146](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42162128163/artifacts/13477616146), [capturas + respaldo Linux #13477237721](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42162128163/artifacts/13477237721), [EXE independiente Windows #13477605972](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42162128160/artifacts/13477605972).

Las capturas contienen cinco pantallas de Tk real; los respaldos son solo datos de demo. `manifest.json` de cada archivo registra SHA-256 y el commit. Respaldo Windows SHA-256 `47a934d50619cc292f91135d7a742c893eaf0afa8531f8bfdb2c4845779d1562`; Linux `fb62f2aa4f6a126c1449c7f4e2dcf41d4048a006d14ae97b5fd7fd634b1804f2`. Los hashes reflejan respaldos independientes, no el mismo archivo bit a bit.

**Límites explícitos:** no se comparó automáticamente pixel a pixel contra una captura maestra ni se evaluó accesibilidad en hardware real; los hashes de iconos y paleta sí fueron comprobados. La autorización por recurso R02, cifrado local R01, backup de producción y recuperación siguen pendientes de las etapas correspondientes. No existe enlace real de Figma, app Android, núcleo Rust, backend ni sincronización. El cierre no equivale a aprobación para producción.

**Decisión:** etapa 2 completada dentro de los criterios del ROADMAP; etapa 3 permanece pendiente. Para continuar será necesario mantener esta regresión y no afirmar garantías todavía no implementadas.
