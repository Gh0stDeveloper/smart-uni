# 6 Cifrado y gestión de claves — acta técnica y evidencias

## 6 Cifrado y gestión de claves

**Estado:** base criptográfica real de 6.1–6.3 implementada y probada, junto con almacenamiento experimental de materiales en SQLCipher. **NO** hay E2EE completo cliente-servidor-cliente; la API todavía almacena notas en texto claro y el modo Tkinter normal escribe JSON claro. Ver [43 pendientes](../PENDIENTES_SMART_UNI_2_0.md). El hito es técnico, **no** autorización para producción.

### 6.1 Modelo de cifrado

[Documento](6.1_MODELO_DE_CIFRADO.md). El núcleo Rust crea contenedores autenticados `SUAEAD01` AES-256-GCM, contexto del propietario, objeto y época en AAD, nonce aleatorio de 96 bits, máximo 8 MiB. Rust expone ABI C con buffers del llamador; el puente `secure_crypto.py` exige librería nativa real y no tiene fallback plaintext. La integración `secure_files.py` cifra una copia del archivo ANTES de escribirla al disco del modo SQLCipher y registra metadata+outbox en una transacción. Lectura de bytes solo en memoria y bloqueo de apertura con lector externo sin protección; el origen seleccionado permanece donde el usuario lo guardó.

Commits: [dd59fae](https://github.com/Gh0stDeveloper/smart-uni/commit/dd59faece079ba719a7a93e4ca0b7eb4f4719d7d), [9b77f6b](https://github.com/Gh0stDeveloper/smart-uni/commit/9b77f6b70cf67a5efb9ca7e258358a175bc7b412), [a384705](https://github.com/Gh0stDeveloper/smart-uni/commit/a384705bdcad64c9ddada6c96950dd67ec482f36).

### 6.2 Administración y recuperación

[Documento](6.2_ADMINISTRACION_Y_RECUPERACION.md). Paquete binario `SURECV01`, 84 bytes con Argon2id m=64MiB t=3 p=1, sal de 16 bytes, AES-256-GCM con nonce aleatorio y tag. SQLCipher y materiales usan dos secretos **diferentes** y requieren paquetes/contraseñas de recuperación independientes; `key_recovery.py` verifica PRAGMA integrity_check y snapshot antes de reinstalar clave DB, `secure_files.py` verifica un material antes de reinstalar clave de contenido. Los archivos cifrados y base DB deben respaldarse aparte.

El núcleo Rust incluye HPKE RFC9180 X25519/HKDF-SHA256/AES256-GCM modo Base, claves a dos destinatarios, `DeviceRoster` en memoria y revocación que genera clave/epoch NUEVOS. No hay alta de dispositivo autenticada, roster persistido, UI de recuperación, revocación retroactiva de lo ya descifrado ni KeyStore físico verificado. La modalidad Base no autentica al remitente y la implementación HPKE requiere auditoría.

Commits: [2e88dea](https://github.com/Gh0stDeveloper/smart-uni/commit/2e88dea7068e63a947d396b932091e46321f5c77), [32e7937](https://github.com/Gh0stDeveloper/smart-uni/commit/32e7937a5f90941ac84af7d271895956c900516d), [1e1fd79](https://github.com/Gh0stDeveloper/smart-uni/commit/1e1fd7937625f4776711989a38aa2c0bd960b733).

### 6.3 Interoperabilidad y revisión

[Documento](6.3_INTEROPERABILIDAD_Y_REVISION.md). Rust ↔ Python/OpenSSL descifran los mismos formatos AES-256-GCM, y Rust Argon2id ↔ argon2-cffi verifican recovery en ambas direcciones. Tests negativos para contextos, claves, tags, contraseñas y archivos corruptos. Los tests de materiales cruzan Rust con SQLCipher real en Windows/Linux.

## Evidencias CI verificadas

| Validación | Resultado | Ejecutado |
|---|---|---|
| Rust y Clippy/Rustfmt Windows y Linux | **22/22 tests por SO**, sin fallos | [Rust #42249602552](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42249602552) |
| Cifrado / Argon2id cruzados Rust ↔ Python/OpenSSL | **5/5 tests por SO** | [Rust #42249602552](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42249602552) |
| Materiales protegidos Rust + SQLCipher | **4/4 tests por SO**, datos sintéticos | [Rust #42249602552](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42249602552) |
| Recuperación de clave SQLCipher | **2/2 tests por SO** | [Rust #42249602552](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42249602552) |
| Pruebas ABI Python + consumidor C++ Linux | **4/4 Python** por SO, C++ ejecutado en Linux | [Rust #42249602552](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42249602552) |
| Android ARM64 NDK | Biblioteca `.so` compilada y ejemplo C++ como objeto; **sin prueba Android en dispositivo** | [Rust #42249602552](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42249602552) |
| SQLCipher Windows/Linux | **22/22 tests por SO** | [SQLCipher #42248920602](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42248920602) |
| Regresión Tkinter | **79 descubiertos: 42 correctos, 37 omitidos** por dependencias opcionales; las suites nativas sí los ejecutan | [Desktop #42248920884](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42248920884) |
| EXE Windows | Compilación del prototipo clásico correcta, **no empaqueta** el Rust/SQLCipher experimental | [EXE #42248920767](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42248920767) |

Los secretos son efímeros/sintéticos. No hay proveedor OIDC real, servidor HTTPS real, Android con JNI ejecutado ni prueba de E2EE productivo.

## Decisión de continuidad y riesgos residuales

La lista maestra [P01–P43](../PENDIENTES_SMART_UNI_2_0.md) exige resolver P01 (JSON en claro), P02 (autorización del servicio desktop), P15/P34/P40 (API notas en claro), P37/P38 (enrolamiento, revocación y re-cifrado), P39 (visor, grandes archivos, orphan ciphertext), P41 (KeyStore real/Android), P42 (entropía y UX de recuperación), P43 (metadatos, nonce y auditoría) antes de lanzamiento.

**Cierre técnico:** subfases 6.1–6.3 desarrolladas y validadas como laboratorio criptográfico e integración opt-in. Etapas 7–10 siguen pendientes. No activar modo seguro por defecto ni usar datos de estudiantes reales mientras la seguridad del producto completo no esté demostrada.
