# Android — pendiente

Aquí desarrollaremos la aplicación Android de SMART UNI. Propuesta: Java para pantallas y accesibilidad, C++/JNI para integración nativa de red y endpoints, Rust para núcleo de seguridad compartido.

Todavía **no hay aplicación Android implementada**. Mantendremos la misma identidad visual mediante los tokens del sistema de diseño. Los endpoints visibles en el binario no son secretos; el servidor valida permisos y tokens.

## Avance de la etapa 3 (núcleo compartido)

La biblioteca `core/rust` ya compila para `aarch64-linux-android` mediante Android NDK; la cabecera estable es `core/rust/include/smartuni_core.h` y el consumidor de prueba C++ se compila para ese destino. [Evidencia y límites](../../docs/phase-3/3_CIERRE_Y_EVIDENCIAS.md).

**Importante:** no se ha construido APK/AAB, no hay Activity Java ni adaptación JNI, no se ejecutaron pruebas en un dispositivo Android y el motor de cifrado no protege todavía los datos de usuario. El enlazado real de Java ↔ C++ ↔ Rust se desarrollará en la etapa 8.
