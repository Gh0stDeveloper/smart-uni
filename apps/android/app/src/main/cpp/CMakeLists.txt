cmake_minimum_required(VERSION 3.22.1)
project(smartuni_android LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# No mock ni fallback sin cifrado: la biblioteca Rust se compila antes de Gradle.
if(ANDROID_ABI STREQUAL "arm64-v8a")
    set(RUST_TARGET "aarch64-linux-android")
elseif(ANDROID_ABI STREQUAL "x86_64")
    set(RUST_TARGET "x86_64-linux-android")
else()
    message(FATAL_ERROR "Arquitectura Android no validada: ${ANDROID_ABI}")
endif()

set(RUST_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../../core/rust")
set(RUST_ARCHIVE "${RUST_ROOT}/target/${RUST_TARGET}/release/libsmartuni_core.a")
if(NOT EXISTS "${RUST_ARCHIVE}")
    message(FATAL_ERROR "No existe núcleo Rust ${RUST_TARGET}. Compilar cargo --release --target antes de Gradle; prohibido fallback plaintext")
endif()

add_library(smartuni_core STATIC IMPORTED)
set_target_properties(smartuni_core PROPERTIES IMPORTED_LOCATION "${RUST_ARCHIVE}")
add_library(smartuni_android SHARED bridge.cpp)
target_include_directories(smartuni_android PRIVATE "${RUST_ROOT}/include")
target_compile_options(smartuni_android PRIVATE -Wall -Wextra -Werror -fstack-protector-strong -fvisibility=hidden)
target_link_options(smartuni_android PRIVATE "-Wl,-z,relro" "-Wl,-z,now")
target_link_libraries(smartuni_android PRIVATE smartuni_core log android)
