# Convención obligatoria de fases y subfases

Esta regla se aplica a la hoja de ruta, documentos Markdown, planificación técnica, tickets, informes, presentaciones y mensajes de avance del proyecto SMART UNI.

## Formato único

```text
1 Nombre de la fase
1.1 Nombre de la subfase
```

**Nivel principal:** un número entero consecutivo, comenzando en 1, seguido de un espacio y un nombre descriptivo. No se escribe ninguna palabra antes del número ni se añaden dos puntos.

**Nivel secundario:** dos números positivos separados por un punto, seguidos de un espacio y el nombre. El primero corresponde a la etapa principal y el segundo comienza en 1 dentro de ella.

## Reglas estrictas

1. No utilizar letras, códigos alfanuméricos, prefijos arbitrarios, fase cero ni números negativos.
2. No omitir fases o subfases y no repetir sus identificadores.
3. Cada apartado tiene un nombre explícito; no se aceptan títulos solo con un número.
4. Cada subfase debe pertenecer a su fase principal y seguir el orden ascendente.
5. Los encabezados principales son de nivel `##` y los secundarios de nivel `###`. Solo se muestra el número y el nombre.
6. Cada trabajo debe documentar alcance, cambios, pruebas y evidencia.
7. Los documentos de arquitectura antiguos son contexto técnico; la [hoja de ruta oficial](ROADMAP.md) determina el orden y el estado real.
8. No anunciar una fase como completada sin validación verificable.
9. Una modificación de numeración necesita un cambio coordinado en roadmap, documentación y validadores.

## Ejemplo Markdown

```markdown
## 2 Contratos y sistema de diseño

### 2.1 Separación de capas de escritorio

### 2.2 Contratos compartidos
```

## Cumplimiento automático

Ejecuta desde la raíz:

```bash
python scripts/check_phase_naming.py
```

No se debe añadir `Fase`, `Subfase` ni `:` delante o después del identificador. El flujo [phase-naming.yml](../.github/workflows/phase-naming.yml) ejecuta el mismo comprobador en GitHub Actions. Rechaza encabezados mal formados, saltos de numeración y subfases fuera de su fase.

Las reglas de nomenclatura no alteran la funcionalidad de la aplicación.
