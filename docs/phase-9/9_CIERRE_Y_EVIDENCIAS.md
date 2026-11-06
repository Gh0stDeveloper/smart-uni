# 9 Seguridad, integración continua y beta — acta de progreso

**Estado:** etapa 9 iniciada sobre main; **NO GO para beta externa ni producción**.

## Línea base y hallazgo previo

El workflow Android [#42296402993](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42296402993) pasó compilación Rust para ARM64/x86_64, APK Debug, APK Release y AAB Release y publicó artefactos; aun así **el job terminó failure**. ADB indicó device offline, luego Process crashed y 0 pruebas instrumentadas completas. No se puede distinguir con certeza crash de app vs runner sin logs adicionales. No se declara cerrada la fase 8.

## Avances implantados

| Subfase | Cambios | Evidencia insuficiente y bloqueos |
|---|---|---|
| 9.1 Auditoría | Pruebas HTTP negativas SQLi/IDOR, mutaciones de ABI, gate estático, CodeQL y escaneo de dependencias | Confirmar CI, revisar informes, ASAN/libFuzzer, RLS, rate-limit y pentest |
| 9.2 Compilación y actualización | R8 Android/JNI, KVM y logs de emulador, comprobador offline de firma Ed25519/digest y downgrade | CI Android instrumentación verde, firma comercial y actualizador/rollback reales |
| 9.3 Beta | Checklist de 12 controles inicialmente bloqueados, puerta de validación manual | Telefonía/PC físico, OIDC real, claves, recuperación y revisiones |

Los tests de firma usan claves efímeras sintéticas. NO hay actualización segura instalada ni control criptográfico de versiones persistente en clientes. Los escaneos SCA no bloqueantes deben triagarse antes de beta y son parte de los pendientes.

## Evidencias a inspeccionar tras el commit

- [Regresión obligatoria fase 9](https://github.com/Gh0stDeveloper/smart-uni/actions/workflows/security-phase9.yml)
- [CodeQL fase 9](https://github.com/Gh0stDeveloper/smart-uni/actions/workflows/codeql-phase9.yml)
- [Backend con negativas](https://github.com/Gh0stDeveloper/smart-uni/actions/workflows/backend-api.yml)
- [Rust con mutaciones ABI](https://github.com/Gh0stDeveloper/smart-uni/actions/workflows/rust-core.yml)
- [Android con emulador](https://github.com/Gh0stDeveloper/smart-uni/actions/workflows/android.yml)

Solo completar casillas en el ROADMAP con commits, logs y pruebas demostradas. Mantener P01/P15/P18/P44–P57 y los nuevos controles etapa 9 abiertos hasta cumplimiento objetivo.

## Resultados CI confirmados

| Ejecución | Resultado observado |
|---|---|
| [Seguridad #42301518396](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42301518396) | Policies/test de firmas y beta gate **success**, sin firma comercial |
| [SCA #42301958248](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42301958248) | Pip-audit 0 findings con PyJWT 2.15.1 y pytest 9.2.0, npm-audit 0; Bandit 6 LOW, 0 MEDIUM/HIGH |
| [Backend #42302081048](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42302081048) | **Success** con límite BIGINT y pruebas SQLi/IDOR adicionales |
| [Sync #42301684576](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42301684576) | **Success** protocolo E2EE experimental etapa 7 |
| [CodeQL #42301576397](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42301576397) | Cinco análisis terminaron **success**, revisión de alertas pendiente |
| [Nomenclatura #42301626938](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42301626938) | **Success**, tras corregir un encabezado no permitido |
| [Android #42301518374](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42301518374) | Compilaciones correctas; instrumentación de emulador vuelve a mostrar fallo durante etapa 9, raíz pendiente. Se captura diagnóstico adicional en flujo posterior |

**Hallazgo activo:** la configuración de notas demo en claro era habilitable con una sola variable; la guardia posterior exige issuer .invalid y PostgreSQL loopback. Es una mitigación de laboratorio, no sustituye eliminar código demo de producción ni migrar los registros legacy.

Mantener estado NO-GO beta/producción por bloqueos P01, P15, P38, P44, P45, P53, P56, P60–P64 y pruebas físicas.
