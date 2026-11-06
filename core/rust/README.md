# Núcleo Rust de SMART UNI 2.0

Este directorio contiene una biblioteca **real**: crate `smartuni-core`, Rust 2021, versión 0.1.0, contrato compartido 1.0.0, ABI C 1. Su objetivo es preparar dominio y criptografía interoperables entre escritorio Windows/Linux y Android, **sin** reemplazar todavía el código funcional de Tkinter y sin migrar los datos JSON.

| Módulo o recurso | Responsabilidad |
|---|---|
| `src/domain.rs` | Validación de email y registro |
| `src/contracts.rs` | Mensajes JSON v1 y validaciones |
| `src/crypto.rs` | AES-256-GCM, vectores públicos y roundtrip |\n| `src/envelope.rs` | SUAEAD01, AAD autenticado, límite de 8 MiB |\n| `src/recovery.rs` | SURECV01, Argon2id + AES-256-GCM |\n| `src/devices.rs` | HPKE RFC9180 y roster de dispositivos de laboratorio |
| `src/ffi.rs` | Interfaz C estable para Python y C++ |
| `include/smartuni_core.h` | Cabecera C/C++ de interoperabilidad |
| `examples/cpp/smoke.cpp` | Consumidor C++ real |
| `test-vectors/aes256gcm.json` | Vectores públicos NIST/BoringSSL, no secretos |

## Reproducir

Instalar Rust con Cargo y después ejecutar desde la raíz:

- `cargo fmt --manifest-path core/rust/Cargo.toml --all -- --check`
- `cargo test --manifest-path core/rust/Cargo.toml --all-targets`
- `cargo clippy --manifest-path core/rust/Cargo.toml --all-targets -- -D warnings`
- `cargo build --manifest-path core/rust/Cargo.toml --release`

La biblioteca se genera como `libsmartuni_core.so` en Linux o `smartuni_core.dll` en Windows. Para las pruebas de puente Python, definir `SMARTUNI_NATIVE_LIB` con la ruta absoluta y ejecutar `python -m unittest discover -s tests -p test_phase3_native.py -v` desde `apps/desktop`. La suite de la aplicación normal no requiere Rust.

El workflow `.github/workflows/rust-core.yml` cubre Linux, Windows y compilación cruzada Android ARM64 con NDK, con test de consumidor C++ en Linux y compilación C++ de Android sin emulador. Las pruebas de vectores independientes requieren cryptography para Python.

**Limitaciones importantes:** no hay biblioteca JNI ni app Android funcional, ni cifrado activo del JSON legacy, ni E2EE contra el backend (el backend sí existe, pero su CRUD de notas aún escribe texto claro), ni sincronización remota. El campo actor_ref es un dato no confiable; no usarlo para autorización. Los endpoints en C++ no serán secretos. Las claves de pruebas nunca deben copiarse a producción. Para detalle y evidencias consultar [documentación de 3.1](../../docs/phase-3/3.1_DOMINIO_Y_BIBLIOTECA_RUST.md), [3.2](../../docs/phase-3/3.2_INTERFACES_NATIVAS_Y_FFI.md) y [3.3](../../docs/phase-3/3.3_VALIDACION_CRIPTOGRAFICA_CRUZADA.md).

**Evidencia confirmada:** [GitHub Actions #42216145594](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42216145594) terminó en verde en Ubuntu, Windows y compilación cruzada Android ARM64; ver [acta de cierre](../../docs/phase-3/3_CIERRE_Y_EVIDENCIAS.md). Ninguno de los builds del núcleo implica todavía integración del cifrado en los datos de SMART UNI.

## Cifrado y dispositivos (etapa 6)

El núcleo genera contenedores `SUAEAD01` AES-256-GCM, recovery `SURECV01` Argon2id de 84 bytes y envolturas HPKE RFC9180 por dispositivo de laboratorio. Se añade ABI v1 de cifrado y recuperación, consumido por Python ctypes y C++. En CI: 22 pruebas Rust por sistema, 5 de interop criptográfica independiente, 4 de materiales, 2 de recuperación DB y 4 pruebas FFI, además de biblioteca Android ARM64 compilada (sin dispositivo real). **No** está desplegado un servidor ciphertext-only ni una autoridad de enrolamiento. [Acta 6](../../docs/phase-6/6_CIERRE_Y_EVIDENCIAS.md) · [Pendientes](../../docs/PENDIENTES_SMART_UNI_2_0.md).
