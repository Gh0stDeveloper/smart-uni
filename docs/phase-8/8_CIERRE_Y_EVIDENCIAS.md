# 8 Aplicación Android — evaluación de avance

## Alcance del commit

Implementación inicial Android Java + C++ JNI + Rust; navegación y un apunte offline cifrado con Android Keystore. La compilación ARM64/x86_64 y los tests instrumentados están definidos en [workflow Android](../../.github/workflows/android.yml). La **ejecución de CI del nuevo commit y su resultado** deben verificarse antes de declarar una subfase cerrada. Esta acta no inventa resultados.

| Subfase | Implementado | Para cierre |
|---|---|---|
| 8.1 Interfaz nativa Java | Activity funcional, identidad visual, navegación, editor de nota local | Build CI verde y accesibilidad en móviles/tablets, más secciones de dominio |
| 8.2 Comunicación C++/JNI | Puente criptográfico y diagnóstico HTTPS `/healthz` sin secretos | OIDC PKCE real y push/pull/blobs nativos + pruebas de TLS/red |
| 8.3 Rust y Android Keystore | Rust staticlib, Keystore envuelve DEK, cifrado en Rust, fail-closed, tests instrumentados y configuración de build APK/AAB | CI APK/AAB verde, ejecución en dispositivo físico, firma release verificable, recuperación |

## Garantías y restricciones

El resultado NO sincroniza con Windows/Linux; no usa sesión OIDC ni autorización de usuario, no soporta transferencias remotas, no migra registros ni dispone de copias restaurables. Si se pierde la Keystore se puede perder el apunte. APK debug firmado de pruebas != artefacto de producción. AAB release **sin firma** no se puede subir a Google Play. Pruebas automatizadas en emulador tampoco certifican hardware Keystore real.

Los controles P01/P15/P18/P37/P38/P41/P44–P52 siguen abiertos, junto con el trabajo Android nuevo. No usar datos reales ni comunicar disponibilidad productiva hasta revisar seguridad en la etapa 9.

## Próxima revisión

1. Consultar [Actions Android](https://github.com/Gh0stDeveloper/smart-uni/actions/workflows/android.yml) del commit.
2. Corregir errores de compilación o pruebas, documentar hash y ejecución específicos.
3. Integrar OIDC/PKCE, E2EE multi-objeto/SQLCipher y sincronización con APIs v2 antes de marcar 8.2/8.3 terminadas.

## Observación posterior — inicio de etapa 9

Al consultar el resultado final del [run Android #42296402993](https://github.com/Gh0stDeveloper/smart-uni/actions/runs/42296402993) se verificó que **no pasó**: construyó paquetes y publicó el artefacto, pero ADB informó offline de forma repetida y la instrumentación se cerró con Process crashed (0/0 tests). La etapa 8 sigue abierta. Fase 9 añade diagnósticos y KVM para intentar reproducir y corregir; no se atribuye el crash a una causa única sin más pruebas.
