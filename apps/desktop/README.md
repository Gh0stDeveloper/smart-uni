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

Los registros se guardan en JSON. Todavía **no existe sincronización real, cifrado de base de datos, servidor ni aplicación Android**.

## Pruebas

```bash
cd apps/desktop
python -m unittest discover -s tests -v
```

Son 26 pruebas automatizadas (17 originales + 9 de línea base); las dos de navegación usan una pantalla gráfica. Evidencia: [acta de cierre](../../docs/phase-1/1_CIERRE_Y_EVIDENCIAS.md).

## Windows

Puedes ejecutar `compilar_exe_windows.bat` en una computadora con Python instalado. Utiliza PyInstaller para crear `dist/Smart_Uni.exe`. El script genera un icono .ico a partir del isotipo original, sin cambiar las pantallas.

También hay un flujo de GitHub Actions para compilar la aplicación.

## Figma

La fuente del diseño está en `design/figma_svg/` y los colores/fuentes en `design/tokens.json`. Los recursos actuales son una base de referencia; algunas maquetas antiguas pueden no representar la navegación final. La interfaz ejecutable es la referencia de comportamiento visual actual.

Las decisiones de SMART UNI 2.0 están en `../../docs/architecture/`.