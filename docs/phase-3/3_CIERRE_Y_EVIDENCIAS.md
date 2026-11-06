# 3 Núcleo compartido en Rust — cierre verificable

## 3 Núcleo compartido en Rust

**Estado: completada y validada para el alcance del ROADMAP.** El resultado es una biblioteca y puentes probados, no un sistema terminado de cifrado, no una aplicación Android y no la integración de Rust en la persistencia Tkinter.

### 3.1 Dominio y biblioteca Rust

Crate Rust `smartuni-core` versión 0.1.0 (contrato de mensajes 1.0.0, almacenamiento legado v1). Los módulos `domain.rs` y `contracts.rs` implementan validaciones y reglas estrictas, separados de UI y del almacenamiento. [Documento técnico](3.1_DOMINIO_Y_BIBLIOTECA_RUST.md). Cambios principales [d96a387](https://github.com/Gh0stDeveloper/smart-uni/commit/d96a38758c6913e463ed20d02d65d867242829e7), formato [69beecc](https://github.com/Gh0stDeveloper/smart-uni/commit/69beecc446860ef404d469d736e0a4a942431231).

### 3.2 Interfaces nativas y FFI

C ABI v1, cabecera C++, consumidor C++ y adaptador Python ctypes con biblioteca cargada explícitamente. En Linux se compila y **ejecuta** el consumidor C++; en Windows/Linux Python prueba los símbolos contra el binario real. Android ARM64 se **compila** mediante NDK, pero no se ejecuta en Android ni incluye JNI Java. [Documento técnico](3.2_INTERFACES_NATIVAS_Y_FFI.md). Commits [ed2a2d4](https://github.com/Gh0stDeveloper/smart-uni/commit/ed2a2d439923e6ea5b9f9297ea3d62886e623db1), [16947f4](https://github.com/Gh0stDeveloper/smart-uni/commit/16947f420b3ff83b5ff85264d67a1c711f901664), [23613cd](https://github.com/Gh0stDeveloper/smart-uni/commit/23613cd3ff8d0f7c4030cd8482dbdcc453388804).

### 3.3 Validación criptográfica cruzada

AES-256-GCM (`aes-gcm =0.10.3`) prueba dos vectores públicos NIST/BoringSSL, roundtrip y rechazo de AAD/tag alterados. `cryptography==44.0.2` reproduce los dos vectores por OpenSSL en Windows y Linux, de forma independiente a Rust. [Documento técnico](3.3_VALIDACION_CRIPTOGRAFICA_CRUZADA.md). Commits [0b70144](https://github.com/Gh0stDeveloper/smart-uni/commit/0b701447653e421afbdcf0115f559acecda5d3d3), [6ea8a8b](https://github.com/Gh0stDeveloper/smart-uni/commit/6ea8a8b34acf47e3aed5f09c693e5e8e315c7d1a) y [1633c8d](https://github.com/Gh0stDeveloper/smart-uni/commit/1633c8dc36523f428b20df246b1d7b7814cf3212).

## Evidencias CI verificadas

| Evidencia | Resultado | Ejecución |
|---|---|---|
| Rust Linux y Windows | 14 pruebas aprobadas / 0 fallos por SO, rustfmt y Clippy en verde | [Núcleo Rust #42216145594](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42216145594) |
| Python ctypes ↔ Rust | 4 pruebas ejecutadas satisfactoriamente por SO con librería real | [Núcleo Rust #42216145594](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42216145594) |
| Vectores AES-GCM OpenSSL | 2 vectores exactos y alteración de etiqueta rechazada por SO | [Núcleo Rust #42216145594](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42216145594) |
| ABI C++ Linux | Consumidor enlazado y ejecutado satisfactoriamente | [Núcleo Rust #42216145594](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42216145594) |
| Android NDK ARM64 | Biblioteca `.so` enlazada; ejemplo C++ compilado como objeto, sin ejecución | [Núcleo Rust #42216145594](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42216145594) |
| Revisión nombres | Validación documental satisfactoria en commit documental anterior | [Convenciones #42216145608](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42216145608) |
| GUI existente | 43 casos detectados: 39 ejecutados, cuatro de FFI omitidos sin biblioteca; CI Ubuntu/Windows en verde | [Desktop #42215305288](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42215305288) |
| Compilación Windows | Build de prototipo Tkinter original en verde tras los cambios iniciales de etapa 3 | [EXE #42215305144](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42215305144) |

**Artefacto real:** [Biblioteca ARM64 Android y cabecera C #13500574641](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42216145594/artifacts/13500574641). Puede expirar por política de GitHub Actions. Es una biblioteca de prueba, no APK/AAB.

**Límites no ocultados:** a día de cierre no existe integración Rust en `main.py` ni cifrado de JSON/materiales, persistencia SQLite, protección de claves, E2EE, autenticación remota, backend, JNI Java ni prueba en Android real. Rust y Python tienen algoritmos probados con las mismas referencias, pero **no se ha demostrado interoperabilidad de contenedores cifrados entre dispositivos**, porque todavía no hay un formato de producción. La semilla demo y PBKDF2 heredado siguen activos. La seguridad de suministro requiere mejorar versionado/lockfile y revisión de dependencias en etapas posteriores.

**Decisión:** se cierra la etapa 3 dentro del alcance de dominio, FFI y validación criptográfica. Las etapas 4–10 siguen pendientes. No atribuir seguridad de producción a este hito.
