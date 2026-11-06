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
> **Estado real:** la aplicación de escritorio en Python/Tkinter es un prototipo funcional. Android, sincronización y E2EE **completo entre clientes y servidor** siguen sin implementar; la etapa 6 añadió cifrado local de materiales, recuperación de claves y HPKE de laboratorio. **La API FastAPI/PostgreSQL y el portal Next.js existen y pasan CI, pero todavía no están desplegados ni conectados a un proveedor OIDC real**. **SQLCipher cifrado ya existe en modo experimental opt-in, no por defecto**. El núcleo Rust 0.1.0 ya cifra materiales del modo seguro mediante ABI y se probó contra OpenSSL, pero la aplicación tradicional y la API no usan todavía E2EE. No se deben introducir datos privados reales en esta versión.

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

Por defecto los datos se almacenan en **JSON local sin cifrar**. Como alternativa experimental, la etapa 4 permite SQLCipher con migración conservadora, cola offline y keyring del SO, pero **no cifra adjuntos ni constituye un sistema de producción**. La lista Amigos no ofrece comunicación online.

## Tecnologías y plataformas

### Lenguajes

| Icono | Tecnología | Responsabilidad | Estado |
|---|---|---|---|
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/python/python-original.svg" width="26" alt="Python" /> | **Python** | Escritorio Tkinter y backend FastAPI | Escritorio + API de laboratorio funcional |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/rust/rust-original.svg" width="26" alt="Rust" /> | **Rust** | Dominio, AES-256-GCM, HPKE, Argon2id recovery y ABI C | Implementado en biblioteca y archivos del modo SQLCipher, no E2EE productivo |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/cplusplus/cplusplus-original.svg" width="26" alt="C++" /> | **C++** | Red/JNI nativo para Android | Planificado |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/java/java-original.svg" width="26" alt="Java" /> | **Java** | Interfaz Android | Planificado |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/typescript/typescript-original.svg" width="26" alt="TypeScript" /> | **TypeScript** | Next.js, portal y administración | Portal implementado y probado, sin desplegar |
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

**En uso:** Tkinter/JSON legacy, SQLCipher opt-in con adjuntos cifrados por Rust y outbox, núcleo Rust con AEAD/Argon2id/HPKE, FastAPI/PostgreSQL y Next.js probados, contratos y tokens. **Pendientes:** empaquetado Rust/SQLCipher en EXE, IdP real, permisos de sesión desktop, keyring hardware real, Android/JNI, E2EE en API, sincronización, visor seguro de archivos y Figma.

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
│   └── web/                # Portal Next.js implementado (no desplegado)
├── core/rust/              # Documentación del núcleo futuro
├── services/api/           # FastAPI, PostgreSQL y migraciones Alembic
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

Android aún no tiene cliente ejecutable. Web y API ahora contienen código funcional y probado en CI, **pero sin despliegue ni login externo comprobado**. Rust contiene la biblioteca compartida con pruebas para Windows/Linux y compilación arm64 Android.

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

La suite de escritorio detecta **79 casos**: 42 ejecutados correctamente y 37 omitidos en el modo legacy sin dependencias opcionales; las pruebas Rust/SQLCipher y recuperación se ejecutan en los workflows especializados Windows/Linux. Los 22 casos SQLCipher se ejecutan **sin omisiones** en su workflow Windows/Linux, igual que los cuatro FFI en el workflow Rust. El workflow Rust ejecuta esas cuatro pruebas contra la biblioteca real en Windows/Linux, además de las 14 pruebas Rust en cada sistema. Para generar el ejecutable Windows usa `compilar_exe_windows.bat`; en Linux, `compilar_linux.sh`. Los instaladores firmados todavía no están listos.

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
| **3 Núcleo compartido en Rust** | Completada: [evidencias de cierre](docs/phase-3/3_CIERRE_Y_EVIDENCIAS.md) |
| **4 Persistencia local y funcionamiento offline** | Implementación técnica validada, **opt-in**, no apta para producción: [acta de cierre](docs/phase-4/4_CIERRE_Y_EVIDENCIAS.md) |
| **5 Backend, identidad y autorización** | Base técnica implementada y validada, sin despliegue ni IdP externo: [acta 5](docs/phase-5/5_CIERRE_Y_EVIDENCIAS.md) |
| **6 Cifrado y gestión de claves** | Base criptográfica y archivos seguros opt-in validados: [acta de cierre](docs/phase-6/6_CIERRE_Y_EVIDENCIAS.md); NO E2EE productivo |
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
- **[Registro maestro de pendientes y riesgos abiertos (P01–P43)](docs/PENDIENTES_SMART_UNI_2_0.md)**

**Desarrollo:** [Ghost Developer](https://github.com/Gh0stDeveloper)

---

<div align="center">SMART UNI · Organización académica con diseño consistente y evolución segura</div>

## Persistencia cifrada opcional (etapa 4)

Para probar desde código fuente, instalar `pip install -r apps/desktop/requirements-secure.txt` y configurar `SMARTUNI_STORAGE=secure` con keyring del SO desbloqueado antes de iniciar. La aplicación usa `data.sqlcipher` y preserva `data.json` si migra; si falta la clave no se degrada a SQLite sin cifrar. El EXE normal **no empaqueta SQLCipher**. La importación de materiales se bloquea en modo seguro hasta tener contenedores de archivos cifrados. [Pruebas y límites](docs/phase-4/4_CIERRE_Y_EVIDENCIAS.md) · [Todos los pendientes](docs/PENDIENTES_SMART_UNI_2_0.md).

## Backend y portal de laboratorio — etapa 5

La API [FastAPI + PostgreSQL](services/api/README.md) dispone de migraciones Alembic, consultas parametrizadas, JWT OIDC RS256, propietario por identidad DB, rol admin validado por PostgreSQL y revocación de tokens propia. El [portal Next.js](apps/web/README.md) utiliza Auth.js con PKCE, state y nonce, cookies de sesión protegidas y BFF que no expone tokens al navegador. **No hay todavía IdP externo conectado ni despliegue productivo.** Los apuntes de prueba del backend se almacenan sin E2EE. [Acta técnica](docs/phase-5/5_CIERRE_Y_EVIDENCIAS.md) y [43 pendientes de seguridad y funcionalidad](docs/PENDIENTES_SMART_UNI_2_0.md).

## Cifrado y recuperación de la etapa 6

El núcleo [Rust](core/rust/README.md) implementa contenedor autenticado `SUAEAD01` AES-256-GCM, paquetes de recuperación `SURECV01` mediante Argon2id, y distribución HPKE X25519 a dispositivos de laboratorio. En modo SQLCipher opt-in, [archivos cifrados](apps/desktop/README.md) se guardan en formato `.sun1` únicamente con biblioteca Rust real; las claves de base y materiales pueden exportarse/restaurarse con **paquetes separados** y frases de recuperación no almacenadas. La lectura de materiales es por bytes en memoria, no abre visores externos de forma automática. **No hay cifrado E2EE de la API, rotación real multi-dispositivo ni Android en ejecución**. [Acta 6](docs/phase-6/6_CIERRE_Y_EVIDENCIAS.md) · [Pendientes P01–P43](docs/PENDIENTES_SMART_UNI_2_0.md).
