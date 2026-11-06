# Guía de Figma — SMART UNI 2.0

**Estado:** proceso documentado, **no conectado** a Figma API ni a un archivo de diseño remoto. La referencia aprobada es la aplicación Tkinter ejecutable, conservando colores, birrete, tipografía y menú único. No restaurar el panel lateral derecho de maquetas anteriores.

## Recursos oficiales

- Fuente canónica de tokens: `packages/design-system/tokens.json`.
- Identidad del birrete SVG/PNG: `packages/design-system/identity.json`, hashes de blob Git verificados.
- Copia de ejecución: `apps/desktop/design/tokens.json`, idéntica byte a byte a la fuente compartida.
- Referencia visual: capturas y manifest de [1.3](../../../docs/phase-1/1.3_PRUEBAS_Y_REGRESION.md).

## Procedimiento de revisión

1. Crear la propuesta en un archivo Figma de titularidad autorizada, con frames desktop y móviles futuros. Ningún archivo remoto está actualmente vinculado.
2. Contrastar con la UI real aprobada: colores, fuentes, icono, jerarquía, menú y todas las pantallas; documentar diferencias.
3. Obtener aprobación humana antes de editar la fuente canónica. Mantener los cambios de interfaz independientes de cambios de contratos.
4. Sincronizar el espejo con `python scripts/sync_design_tokens.py --write`, ejecutar comprobador `python scripts/check_design_system.py`, y pruebas Windows/Linux.
5. Revisar las capturas reales de CI y registrar evidencia/commit en GitHub. No se permite exportar automáticamente desde Figma a `main`.

La sincronización bidireccional, lectura de variables/componentes o webhooks necesitan conexión autorizada posterior, mapeos por plataforma y revisión de cambios. Esta guía no afirma que estas funciones estén operativas.
