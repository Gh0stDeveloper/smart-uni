# 8 Aplicación Android — seguimiento de cierre técnico

**Estado actual: etapa abierta, tres subfases parcialmente implementadas.** La existencia de código o APK no autoriza distribución real ni cierre de los checkboxes oficiales.

## Implementación inicial anterior

Android Java con seis pantallas y un apunte local cifrado por Rust/Keystore; integración binaria ABI Rust ARM64/x86_64. El build [#42296402993](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42296402993) generó APK debug, release y AAB release de laboratorio, pero **falló la instrumentación** con ADB offline y Process crashed antes de ejecutar tests. Los intentos posteriores [#42301518374](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42301518374) y [#42302247683](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42302247683) también registraron fallo de la etapa de emulador; ningún resultado permite atribuir el crash exclusivamente a aplicación o infraestructura.

## Segunda iteración en main

[Implementación 8.1–8.3](https://github.com/Gh0stDeveloper/smart-uni/commit/c0203af7ebdc822fac6e25e3d661807540fcce90):

| Subfase | Nueva función implementada | Evidencia aún necesaria |
|---|---|---|
| 8.1 Interfaz Java | CRUD local de notas, tareas, eventos; importación/lectura de materiales cifrados y diseño original | Build, test emulador, UI/accessibility en móviles/tablets físicos, persistencia concurrente |
| 8.2 Comunicación JNI | Endpoints fijos me, sync pull/push/conflicts por C++, adaptador TLS Android con bearer dinámico, limites y respuesta tipada | OIDC/PKCE real, owner/E2EE/ACK, blobs, IdP HTTPS real, control anti-MITM, reintentos/errores |
| 8.3 Rust/Keystore | Bóveda multi-registro y archivos cifrados mediante Rust/Keystore, migración conservadora de un apunte, fail-closed al perder el wrap; pruebas nuevas | CI instrumentado en verde, SQLCipher, recovery, TEE/StrongBox, firma release, dispositivos reales |

La segunda compilación se verificará en [Actions Android](https://github.com/Gh0stDeveloper/smart-uni/actions/workflows/android.yml) para este commit. **No atribuir éxito a la ejecución hasta que termine**.

## Restricciones explícitas

No existe login ni sesión OIDC del cliente Android, ni enrolamiento HPKE autenticado, ni sincronización real entre Windows/Linux/Android, ni almacenamiento SQLCipher para Android. El motor JNI de request no transforma respuestas en cambios locales. No hay recuperación validada tras pérdida del dispositivo; si Keystore se pierde, los archivos pueden quedar inaccesibles. No se incluyen credenciales de firma comercial; APK debug es de laboratorio, AAB sin firma no es apto para Play.

## Próximos trabajos

1. Resolver fallos de CI/emulador y validar seis tests instrumentados.
2. Implementar OIDC/PKCE + enrolamiento de dispositivo, sesión/clave protegida y autorización real; conectar protocolo E2EE incremental.
3. Completar objetos académicos, SQLCipher y material/metadata atómicos, previsualización segura, recuperación y múltiples instalaciones.
4. Validar accesibilidad, integridad, firma y pruebas físicas, y solo entonces revisar checkboxes 8.1–8.3.

Los riesgos P01/P14/P15/P18/P41/P44–P57 continúan abiertos en [registro maestro](../PENDIENTES_SMART_UNI_2_0.md).

## Hallazgo verificable y corrección del runner

En la primera ejecución de la segunda iteración [Android #42307503657](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42307503657), el artifact `smart-uni-android-pruebas-fase8` contiene un XML de JUnit con **6 tests ejecutados, 0 failures, 0 errors, 0 skipped**. Gradle imprimió `BUILD SUCCESSFUL in 55s`, pero el job terminó failure porque el action `reactivecircus/android-emulator-runner` ejecutó cada línea de `script` en un shell distinto. `test_result=$?` no sobrevivió entre llamadas y `exit "$test_result"` falló con `Illegal number`. No fue un crash de la aplicación en ese run. La corrección [01a4ad1](https://github.com/Gh0stDeveloper/smart-uni/commit/01a4ad1a503b1aeb6d4749ab3d704a7d1d19fae8) usa `bash scripts/android_instrumentation.sh` como único comando y recoge diagnóstico acotado.

## Progreso nuevo de OIDC

[Commit 73c74ea](https://github.com/Gh0stDeveloper/smart-uni/commit/73c74eab16e5147fcac2d46808fdf393282cbaa3): AppAuth 0.11.1 para Authorization Code PKCE/state/nonce, callback privado, sesión cifrada Rust/Keystore con expiración y validación JNI de /me. Sin issuer/client_id configurado se mantiene **deshabilitado**. No hay inicio de sesión probado con IdP real, token refresh, sync/ACK ni revocación de proveedor; por ello 8.2 permanece parcial.

Las nuevas pruebas de sesión son sintéticas y su resultado depende de una ejecución CI posterior. No afirmar cierre hasta disponer de CI verde del nuevo commit y validación física.
