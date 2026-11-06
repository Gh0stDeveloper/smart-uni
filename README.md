<div align="center">

<img src="apps/desktop/design/previews/00_isotipo_smart_uni.png" width="120" alt="Logotipo original SMART UNI: birrete azul y turquesa" />

# SMART UNI

### Plataforma académica multiplataforma · Offline-first · Seguridad por diseño

**Organiza tareas, apuntes, calendario, materiales y actividades académicas en un solo lugar.**

SMART UNI 2.0 evolucionará desde el prototipo de escritorio existente hacia un ecosistema para **Windows, Linux y Android**, capaz de trabajar sin Internet y sincronizar al recuperar conexión.

[![Pruebas de escritorio](https://github.com/Gh0stDeveloper/smart-uni/actions/workflows/desktop-tests.yml/badge.svg)](https://github.com/Gh0stDeveloper/smart-uni/actions/workflows/desktop-tests.yml)
[![Convención de fases](https://github.com/Gh0stDeveloper/smart-uni/actions/workflows/phase-naming.yml/badge.svg)](https://github.com/Gh0stDeveloper/smart-uni/actions/workflows/phase-naming.yml)
![Estado](https://img.shields.io/badge/Estado-Prototipo%20y%20desarrollo-2B80EC)

[**Hoja de ruta**](docs/ROADMAP.md) · [**Arquitectura**](docs/architecture/SMART_UNI_2_0_Arquitectura_Multiplataforma_Segura.md) · [**Seguridad**](SECURITY.md) · [**Convenciones**](docs/CONVENCIONES_FASES.md)

</div>

> [!IMPORTANT]
> **Estado real:** la aplicación de escritorio en Python/Tkinter es un prototipo funcional. Las versiones Android y web, el núcleo Rust, la API online, la sincronización, la base cifrada y el E2EE están **planificados, no implementados**. No se deben introducir datos privados reales en esta versión.

---

## Índice

1. [Introducción](#introducción)
2. [Funciones del prototipo](#funciones-del-prototipo)
3. [Tecnologías y plataformas](#tecnologías-y-plataformas)
4. [Arquitectura prevista](#arquitectura-prevista)
5. [Estructura del repositorio](#estructura-del-repositorio)
6. [Instalación y uso](#instalación-y-uso)
7. [Pruebas y compilación](#pruebas-y-compilación)
8. [Hoja de ruta oficial](#hoja-de-ruta-oficial)
9. [Diseño y Figma](#diseño-y-figma)
10. [Seguridad y contribuciones](#seguridad-y-contribuciones)

## Introducción

**SMART UNI** es un proyecto de organización académica desarrollado por **Ghost Developer**. Su propósito es reunir en una aplicación clara las herramientas que un estudiante necesita para planificar sus actividades y consultar materiales.

La versión actual mantiene el diseño aprobado: birrete azul/turquesa, navegación unificada, espacios organizados y ninguna columna auxiliar innecesaria a la derecha.

La arquitectura futura prioriza el uso sin conexión, la preservación de datos, la protección criptográfica y la interoperabilidad. No consideramos un componente seguro únicamente porque esté desarrollado en C++ o Rust: cada garantía debe probarse.

## Funciones del prototipo

| Sección | Funcionalidad actual |
|---|---|
| Acceso | Registro e inicio de sesión local |
| Panel académico | Resumen general del estudiante |
| Cursos y horarios | Consulta de organización académica |
| Anuncios | Avisos de la aplicación |
| Perfil | Información básica del estudiante |
| Amigos | Agenda local de compañeros |
| Calendario | Eventos y recordatorios |
| Material | Documentos organizados por materias |
| Tareas | Actividades pendientes y completadas |
| Apuntes | Notas organizadas por materias |

Los datos se almacenan actualmente en **JSON local**. La lista Amigos todavía no ofrece comunicación online real.

## Tecnologías y plataformas

### Lenguajes

| Icono | Tecnología | Responsabilidad | Estado |
|---|---|---|---|
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/python/python-original.svg" width="26" alt="Python" /> | **Python** | Escritorio Tkinter y futura API | Escritorio funcional |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/rust/rust-original.svg" width="26" alt="Rust" /> | **Rust** | Núcleo nativo compartido y seguridad | Planificado |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/cplusplus/cplusplus-original.svg" width="26" alt="C++" /> | **C++** | Red/JNI nativo para Android | Planificado |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/java/java-original.svg" width="26" alt="Java" /> | **Java** | Interfaz Android | Planificado |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/typescript/typescript-original.svg" width="26" alt="TypeScript" /> | **TypeScript** | Next.js, portal y administración | Planificado |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/javascript/javascript-original.svg" width="26" alt="JavaScript" /> | **JavaScript** | Herramientas web | Planificado |

### Herramientas y programas

<div align="center">

<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/windows11/windows11-original.svg" width="37" title="Windows" alt="Windows" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/linux/linux-original.svg" width="37" title="Linux" alt="Linux" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/android/android-original.svg" width="37" title="Android" alt="Android" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/nextjs/nextjs-original.svg" width="37" title="Next.js" alt="Next.js" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/fastapi/fastapi-original.svg" width="37" title="FastAPI" alt="FastAPI" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/postgresql/postgresql-original.svg" width="37" title="PostgreSQL" alt="PostgreSQL" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/sqlite/sqlite-original.svg" width="37" title="SQLite" alt="SQLite" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/figma/figma-original.svg" width="37" title="Figma" alt="Figma" />

</div>

**En uso:** Python/Tkinter modularizado, repositorio JSON v1, sesión local, contratos JSON Schema versionados, compilación y pruebas de escritorio, iconos SVG y tokens canónicos. **Previstos:** Rust, Android, Next.js, FastAPI, PostgreSQL, SQLite protegido e integración de Figma.

## Arquitectura prevista

```text
            SMART UNI (clientes)
       ┌──────────────┬──────────────┐
       │ Windows/Linux│ Android      │
       │ Python UI    │ Java + C++   │
       └───────┬──────┴──────┬───────┘
               └─────┬───────┘
                     ▼
          Núcleo compartido Rust
     Dominio · cifrado · sincronización
                     │
           ┌─────────┴──────────┐
           ▼                    ▼
       SQLite local          HTTPS/TLS
       + archivos               │
                             API FastAPI
                             Portal Next.js
                                │
                        PostgreSQL + Storage
```

La sincronización **offline-first** y el cifrado E2EE son objetivos de diseño. El backend será responsable de autorizar cada recurso; ocultar endpoints en binarios no sustituye la autorización.

[Arquitectura multiplataforma](docs/architecture/SMART_UNI_2_0_Arquitectura_Multiplataforma_Segura.md) · [Plan técnico](docs/architecture/SMART_UNI_2_0_Arquitectura_y_Plan_Produccion.md)

## Estructura del repositorio

```text
smart-uni/
├── .github/workflows/      # CI y convenciones
├── apps/
│   ├── desktop/            # Prototipo Python ejecutable
│   ├── android/            # Arquitectura futura Java/C++/Rust
│   └── web/                # Portal Next.js futuro
├── core/rust/              # Documentación del núcleo futuro
├── services/api/           # Documentación del backend futuro
├── packages/design-system/ # Tokens canónicos e identidad visual
├── packages/contracts/     # Esquemas v1 de datos y operaciones
├── docs/
│   ├── ROADMAP.md          # Fases y subfases oficiales
│   ├── CONVENCIONES_FASES.md
│   └── architecture/       # Propuestas técnicas
├── scripts/                # Validaciones del proyecto
├── CONTRIBUTING.md
├── SECURITY.md
└── README.md
```

Los directorios de Android, web, API y Rust **no contienen todavía productos ejecutables**.

## Instalación y uso

**Requisitos:** Python 3.10 o superior, Tkinter y un entorno gráfico en Windows/Linux.

```bash
git clone https://github.com/Gh0stDeveloper/smart-uni.git
cd smart-uni/apps/desktop
python main.py
```

En Linux podría ser necesario instalar Tkinter mediante el gestor de paquetes y usar `python3`.

La cuenta de demostración se utiliza únicamente para pruebas y debe eliminarse antes de la producción; no uses información académica privada.

## Pruebas y compilación

```bash
cd apps/desktop
python -m unittest discover -s tests -v
```

La suite incluye **39 casos** (17 originales, 9 de línea base, 6 de separación de capas, 4 de contratos y 3 del diseño); dos requieren sesión gráfica. Para generar el ejecutable Windows usa `compilar_exe_windows.bat`; en Linux, `compilar_linux.sh`. Los instaladores firmados todavía no están listos.

Para comprobar la nomenclatura documental, desde la raíz:

```bash
python scripts/check_phase_naming.py
```

[GitHub Actions](https://github.com/Gh0stDeveloper/smart-uni/actions) contiene los flujos de pruebas, compilación y validación.

## Hoja de ruta oficial

Los apartados se identifican únicamente como **1 Nombre** y **1.1 Nombre**, sin palabras o signos adicionales. Sus identificadores son numéricos, consecutivos y comienzan en 1.

| Etapa | Estado |
|---|---|
| **1 Análisis y línea base** | Completada: [evidencias de cierre](docs/phase-1/1_CIERRE_Y_EVIDENCIAS.md) |
| **2 Contratos y sistema de diseño** | Completada: [evidencias de cierre](docs/phase-2/2_CIERRE_Y_EVIDENCIAS.md) |
| **3 Núcleo compartido en Rust** | Pendiente |
| **4 Persistencia local y funcionamiento offline** | Pendiente |
| **5 Backend, identidad y autorización** | Pendiente |
| **6 Cifrado y gestión de claves** | Pendiente |
| **7 Sincronización multiplataforma** | Pendiente |
| **8 Aplicación Android** | Pendiente |
| **9 Seguridad, integración continua y beta** | Pendiente |
| **10 Lanzamiento gradual** | Pendiente |

La [hoja de ruta](docs/ROADMAP.md) incluye las **30 subfases**, entregables, pruebas y orden de trabajo. Consulta también la [convención obligatoria](docs/CONVENCIONES_FASES.md).

## Diseño y Figma

Se conservarán el icono original, la paleta azul/turquesa, Poppins, Roboto, el menú único y la interfaz limpia sin panel lateral derecho innecesario.

- [Isotipo SVG](apps/desktop/design/figma_svg/00_isotipo_smart_uni.svg)
- [Tokens de diseño](packages/design-system/tokens.json)
- [Guía para Figma](apps/desktop/docs/GUIA_FIGMA.md)

La integración automatizada con Figma está prevista, pero **no se encuentra conectada al código**.

## Seguridad y contribuciones

El repositorio es **público**. No subir datos reales, tokens, claves privadas, credenciales ni documentos personales. El prototipo no cuenta aún con las garantías de seguridad de SMART UNI 2.0.

Se planean Argon2id cuando corresponda, TLS, cifrado en reposo, gestión de claves, autorización por recurso, SQL parametrizado, auditoría y pruebas especializadas. La inclusión en este README no implica implementación.

- [Política de seguridad](SECURITY.md)
- [Guía de contribución](CONTRIBUTING.md)
- [Estado real de componentes](docs/architecture/00_ESTADO_Y_PRIORIDADES.md)

**Desarrollo:** [Ghost Developer](https://github.com/Gh0stDeveloper)

---

<div align="center">SMART UNI · Organización académica con diseño consistente y evolución segura</div>
