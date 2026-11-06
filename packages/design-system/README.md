# Sistema visual de SMART UNI — fuente canónica

`packages/design-system/tokens.json` es la **fuente única de los tokens**. La copia `apps/desktop/design/tokens.json` se sincroniza byte a byte para ejecución independiente de Tkinter y PyInstaller. El adaptador `apps/desktop/smart_uni/design_system.py` enlaza los roles existentes con el archivo, sin alterar la paleta o las fuentes.

El icono original del birrete azul/turquesa no se reemplaza: `identity.json` contiene SHA de blob Git del PNG y SVG originales, verificados en CI. La navegación de escritorio es única, arriba a la izquierda, sin panel lateral derecho adicional.

**Para actualizar tokens aprobados:** modificar el JSON canónico, ejecutar `python scripts/sync_design_tokens.py --write` desde la raíz y verificar con `python scripts/check_design_system.py`. El CI compara copias, colores y hashes de recursos. Los binarios Windows/Linux incluyen los tokens embebidos además del icono.

**Figma:** se dispone de un proceso de revisión de frames y tokens, no de una integración técnica activa ni de un enlace a documento maestro. La aplicación Tkinter vigente prevalece sobre maquetas antiguas. Toda alteración visual requerirá aprobación y regresión manual/automática de capturas antes de publicarse.
