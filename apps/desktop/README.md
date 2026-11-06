# SMART UNI — aplicación de escritorio (prototipo)

Esta es la versión de SMART UNI que ya desarrollamos en Python/Tkinter para Windows y Linux. **Conservamos el inicio de sesión, la navegación actual y el icono original del birrete azul/turquesa.** No estamos modificando su diseño para empezar SMART UNI 2.0.

## Cómo ejecutar

Necesitamos Python 3.10+ con Tkinter:

```bash
cd apps/desktop
python main.py
```

**Para la exposición únicamente:** correo `demo@smartuni.edu`, contraseña `Demo1234!`. Esta cuenta se eliminará en producción.

## Funciones existentes

Registro y acceso local, panel, cursos, horarios, anuncios, Inicio, Perfil, Amigos, Calendario, Material, Tareas y Apuntes.

El modo de uso normal guarda JSON **sin cifrar**. La etapa 4 añadió **SQLCipher experimental y opcional**; la etapa 6 añade cifrado de copias de materiales usando Rust obligatorio y paquetes de recuperación. Aún no existe cliente Android, sincronización ni E2EE remoto; el modo JSON normal sigue sin cifrar.

## Pruebas

```bash
cd apps/desktop
python -m unittest discover -s tests -v
```

La suite normal descubre 79 casos: 42 ejecutados correctamente y 37 omitidos sin SQLCipher/Rust y sus bibliotecas independientes. Los tests nativos se ejecutan en workflows específicos: 22 Rust + 5 interoperabilidad + 4 materiales + 2 DB recuperación + 4 FFI por SO. Dos pruebas Tkinter necesitan pantalla gráfica. En CI especial SQLCipher se ejecutan 22/22 sin omisiones. Evidencia: [etapa 1](../../docs/phase-1/1_CIERRE_Y_EVIDENCIAS.md) y [etapa 2](../../docs/phase-2/2_CIERRE_Y_EVIDENCIAS.md).

## Windows

Puedes ejecutar `compilar_exe_windows.bat` en una computadora con Python instalado. Utiliza PyInstaller para crear `dist/Smart_Uni.exe`. El script genera un icono .ico a partir del isotipo original, sin cambiar las pantallas.

También hay un flujo de GitHub Actions para compilar la aplicación.

## Figma

La fuente del diseño está en `design/figma_svg/` y los colores/fuentes en `design/tokens.json`. Los recursos actuales son una base de referencia; algunas maquetas antiguas pueden no representar la navegación final. La interfaz ejecutable es la referencia de comportamiento visual actual.

Las decisiones de SMART UNI 2.0 están en `../../docs/architecture/`.
## Organización de la etapa 2

`smart_uni/domain.py` mantiene validaciones y algoritmos heredados; `repository.py` abstrae el JSON; `session.py` conserva la identidad local sin introducir API online; `core.py` y `student_data.py` implementan los servicios, y las pantallas originales permanecen en `ui.py` y `student_ui.py`. Los roles visuales se leen mediante `design_system.py` de los tokens originales. Ningún control remoto de autorización, SQLite, Rust ni sincronización está implementado todavía.

## Núcleo nativo Rust disponible (etapa 3)

El adaptador opcional `smart_uni/native_bridge.py` puede cargar una biblioteca Rust local construida con Cargo al definir `SMARTUNI_NATIVE_LIB`; no participa en el arranque de Tkinter ni cambia el login o los datos actuales. [Documentación y pruebas](../../docs/phase-3/3_CIERRE_Y_EVIDENCIAS.md). En el workflow normal hay 43 tests descubiertos (39 ejecutados + 4 de puente omitidos); en el workflow Rust se ejecutan los cuatro tests de FFI **contra código nativo real**, tanto en Windows como en Linux.

## Modo cifrado opt-in (4.1–4.3)

Instalar `python -m pip install -r requirements-secure.txt` en Windows/Linux con keyring del SO desbloqueado. Establecer `SMARTUNI_STORAGE=secure` y ejecutar `python main.py`. La base local utiliza SQLCipher y, si existe JSON v1, lo migra **conservando el origen**. Si falta clave o servicio de claves, aborta sin crear una base sin cifrar. El EXE clásico de GitHub Actions no incluye SQLCipher; esta configuración debe probarse desde fuente.

El modo seguro mantiene tareas, apuntes y perfil en SQLCipher, registra operaciones cubiertas en outbox y presenta estados locales. Con `SMARTUNI_NATIVE_LIB` señalando la biblioteca Rust compilada también cifra nuevas copias de materiales (hasta 8 MiB) como `.sun1`; sin Rust, la importación falla cerrado. Materiales descifrados solo mediante `material_bytes` en memoria; el visor externo sigue bloqueado. Los originales seleccionados ya existen en claro fuera de SMART UNI. No se garantiza aún autorización por sesión ni red; nunca mostrar “sincronizado” sin ACK del servidor. [Acta técnica](../../docs/phase-4/4_CIERRE_Y_EVIDENCIAS.md) y [registro de pendientes P01–P43](../../docs/PENDIENTES_SMART_UNI_2_0.md).

## Protección de hash histórico y etapa 5

Se añadieron límites verificables de costo PBKDF2 (100 000 a 1 000 000 rondas, sal de 16 bytes, digest de 32 bytes) conservando las 260 000 rondas de registros existentes. [Regresión CI](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42225588765). La nueva API remota existe en [services/api](../../services/api/README.md), **sin conexión al cliente Tkinter y sin autorización de sesión local todavía**. No introducir datos reales en el JSON o los materiales clásicos.

## Etapa 6: materiales cifrados y recuperación en modo seguro

Para pruebas desde fuente: instalar `requirements-secure.txt`, construir `smartuni-core` con Cargo y establecer `SMARTUNI_NATIVE_LIB` a su ruta real y `SMARTUNI_STORAGE=secure`. El modo seguro importa un archivo de hasta 8 MiB cifrándolo antes de guardarlo, sin generar un segundo archivo de texto claro. La lectura de `material_bytes` devuelve bytes solo en memoria; el visor gráfico externo todavía no se habilita. `secure_files.py` ofrece export/restore cifrado de la clave de materiales y `key_recovery.py` hace lo mismo para la clave SQLCipher, **por separado**; requiere custodiar las bases, materiales, dos copias y frases con seguridad. La experiencia guiada/automática de recovery no existe. [Evidencia técnica](../../docs/phase-6/6_CIERRE_Y_EVIDENCIAS.md) · [Riesgos P01–P43](../../docs/PENDIENTES_SMART_UNI_2_0.md).
