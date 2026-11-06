# Guía de colaboración — SMART UNI

El trabajo de SMART UNI debe mantener la interfaz aprobada, proteger los datos y registrar avances verificables.

## Identificación obligatoria del trabajo

Toda tarea por etapas debe denominarse **Fase 1: Nombre** y **Subfase 1.1: Nombre**, utilizando la numeración oficial de [docs/ROADMAP.md](docs/ROADMAP.md).

Reglas completas: [docs/CONVENCIONES_FASES.md](docs/CONVENCIONES_FASES.md).

## Requisitos de una entrega

1. Indicar fase y subfase exactas.
2. Describir el alcance, archivos modificados, resultados y riesgos.
3. Ejecutar pruebas relevantes y enlazar resultados reproducibles.
4. Conservar el diseño y el icono originales de SMART UNI.
5. No publicar secretos ni información real de estudiantes.
6. Distinguir siempre entre características existentes y propuestas.
7. Añadir migraciones y respaldo cuando se modifiquen formatos de datos.
8. Actualizar README, roadmap y arquitectura cuando proceda.

## Comprobaciones

```bash
python scripts/check_phase_naming.py
cd apps/desktop
python -m unittest discover -s tests -v
```

Las pruebas gráficas omitidas por falta de pantalla deben reportarse como omitidas y nunca como ejecutadas satisfactoriamente. No llamar «producción» al prototipo.
