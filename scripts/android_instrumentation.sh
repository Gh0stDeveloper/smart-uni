#!/usr/bin/env bash
# ReactiveCircus ejecuta cada línea de script en un proceso separado;
# mantener el estado y el código de retorno en este proceso único.
set -uo pipefail
mkdir -p apps/android/app/build/diagnostics
status=0
(
  cd apps/android
  gradle --no-daemon :app:connectedDebugAndroidTest
) || status=$?
# Capturar errores mientras el emulador aún está vivo, sin bloquear teardown.
timeout 15s adb logcat -d -t 1800 -s AndroidRuntime:E   > apps/android/app/build/diagnostics/android-runtime.log || true
exit "$status"
