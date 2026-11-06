// SMART UNI 8.2: JNI C++ orquesta transporte HTTPS del sistema Android.
// La criptografía reside exclusivamente en smartuni-core (Rust ABI v1).
// Ni hostnames ni rutas de API constituyen secretos; nunca añadir tokens fijos.
#include <jni.h>
#include <algorithm>
#include <cstdint>
#include <string>
#include <vector>
#include "smartuni_core.h"

namespace {

void wipe(std::vector<uint8_t>& bytes) {
    volatile uint8_t* p = bytes.data();
    for (size_t i = 0; i < bytes.size(); ++i) p[i] = 0;
}

bool read_array(JNIEnv* env, jbyteArray array, size_t limit, std::vector<uint8_t>& dest) {
    if (array == nullptr) return false;
    const jsize n = env->GetArrayLength(array);
    if (n < 0 || static_cast<size_t>(n) > limit) return false;
    dest.resize(static_cast<size_t>(n));
    if (n > 0) {
        env->GetByteArrayRegion(array, 0, n, reinterpret_cast<jbyte*>(dest.data()));
        if (env->ExceptionCheck()) {
            env->ExceptionClear();
            wipe(dest);
            return false;
        }
    }
    return true;
}

jbyteArray crypto(JNIEnv* env, jbyteArray key_array, jbyteArray context_array,
                  jbyteArray data_array, bool decrypt) {
    std::vector<uint8_t> key, context, data, result;
    auto cleanup = [&]() {
        wipe(key);
        wipe(data);
        wipe(result);
    };
    if (!read_array(env, key_array, 32, key) || key.size() != 32 ||
        !read_array(env, context_array, 256, context) || context.empty() ||
        !read_array(env, data_array, 8 * 1024 * 1024 + 512, data)) {
        cleanup();
        return nullptr;
    }
    if (!decrypt && data.size() > 8 * 1024 * 1024) {
        cleanup();
        return nullptr;
    }

    const size_t capacity = decrypt ? data.size() : data.size() + context.size() + 128;
    result.resize(std::max<size_t>(capacity, 1));
    size_t written = 0;
    const int32_t status = decrypt
        ? smartuni_open_record_v1(key.data(), key.size(), context.data(), context.size(),
              data.data(), data.size(), result.data(), result.size(), &written)
        : smartuni_seal_record_v1(key.data(), key.size(), context.data(), context.size(),
              data.data(), data.size(), result.data(), result.size(), &written);
    if (status != SMARTUNI_STATUS_OK || written > result.size() || written > 8 * 1024 * 1024 + 512) {
        cleanup();
        return nullptr;
    }
    jbyteArray output = env->NewByteArray(static_cast<jsize>(written));
    if (output != nullptr && written > 0) {
        env->SetByteArrayRegion(output, 0, static_cast<jsize>(written),
                                reinterpret_cast<const jbyte*>(result.data()));
    }
    if (env->ExceptionCheck()) {
        env->ExceptionClear();
        output = nullptr;
    }
    cleanup();
    return output;
}

bool valid_origin(const std::string& origin) {
    constexpr char prefix[] = "https://";
    if (origin.compare(0, sizeof(prefix) - 1, prefix) != 0 ||
        origin.size() <= sizeof(prefix) - 1 || origin.size() > 255) return false;
    const std::string host = origin.substr(sizeof(prefix) - 1);
    if (host.front() == '.' || host.back() == '.' || host.front() == ':' ||
        host.back() == ':' || host.find("..") != std::string::npos) return false;
    for (const unsigned char c : host) {
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || c == '.' || c == '-' ||
              c == ':' || c == '[' || c == ']')) return false;
    }
    return true;
}

bool safe(JNIEnv* env) {
    if (env->ExceptionCheck()) {
        env->ExceptionClear();
        return false;
    }
    return true;
}

// El transporte se controla desde C++ utilizando el stack HTTPS del SO
// a través de JNI. Android valida host/cert; NO deshabilitar TrustManager.
jint https_health(JNIEnv* env, const std::string& origin) {
    if (!valid_origin(origin)) return -1;
    jclass url_class = env->FindClass("java/net/URL");
    if (!url_class || !safe(env)) return -1;
    jmethodID constructor = env->GetMethodID(url_class, "<init>", "(Ljava/lang/String;)V");
    jmethodID open = env->GetMethodID(url_class, "openConnection", "()Ljava/net/URLConnection;");
    if (!constructor || !open || !safe(env)) return -1;
    jstring target = env->NewStringUTF((origin + "/healthz").c_str());
    if (!target || !safe(env)) return -1;
    jobject url = env->NewObject(url_class, constructor, target);
    if (!url || !safe(env)) return -1;
    jobject connection = env->CallObjectMethod(url, open);
    if (!connection || !safe(env)) return -1;
    jclass https = env->FindClass("javax/net/ssl/HttpsURLConnection");
    if (!https || !safe(env) || !env->IsInstanceOf(connection, https)) return -1;

    jmethodID set_connect = env->GetMethodID(https, "setConnectTimeout", "(I)V");
    jmethodID set_read = env->GetMethodID(https, "setReadTimeout", "(I)V");
    jmethodID follow = env->GetMethodID(https, "setInstanceFollowRedirects", "(Z)V");
    jmethodID method = env->GetMethodID(https, "setRequestMethod", "(Ljava/lang/String;)V");
    jmethodID response = env->GetMethodID(https, "getResponseCode", "()I");
    jmethodID disconnect = env->GetMethodID(https, "disconnect", "()V");
    if (!set_connect || !set_read || !follow || !method || !response || !disconnect || !safe(env))
        return -1;
    env->CallVoidMethod(connection, set_connect, 5000);
    env->CallVoidMethod(connection, set_read, 5000);
    env->CallVoidMethod(connection, follow, JNI_FALSE);
    jstring get = env->NewStringUTF("GET");
    if (!get || !safe(env)) return -1;
    env->CallVoidMethod(connection, method, get);
    if (!safe(env)) return -1;
    const jint status = env->CallIntMethod(connection, response);
    const bool success = safe(env);
    env->CallVoidMethod(connection, disconnect);
    safe(env);
    return success ? status : -1;
}

// Operaciones HTTP fijas en C++. La autorización y el framing pertenecen al
// servidor; este puente solo devuelve estado/respuesta sin afirmar sincronización.
jobject exchange_api(JNIEnv* env, jstring raw_origin, jbyteArray token,
                     jint operation, jlong cursor, jbyteArray payload) {
    if (raw_origin == nullptr || token == nullptr || operation < 0 || operation > 3 ||
        cursor < 0 || (operation != 2 && payload != nullptr) ||
        (operation == 2 && payload == nullptr) ||
        env->GetArrayLength(token) < 10 || env->GetArrayLength(token) > 16384 ||
        (payload && env->GetArrayLength(payload) > 180 * 1024)) return nullptr;
    const char* chars = env->GetStringUTFChars(raw_origin, nullptr);
    if (!chars || !safe(env)) return nullptr;
    std::string origin(chars);
    env->ReleaseStringUTFChars(raw_origin, chars);
    if (!valid_origin(origin)) return nullptr;

    const char* method = operation == 2 ? "POST" : "GET";
    std::string route;
    switch (operation) {
        case 0: route = "/api/v1/me"; break;
        case 1: route = "/api/v1/sync/pull?cursor=" +
                        std::to_string(static_cast<int64_t>(cursor)) + "&limit=10"; break;
        case 2: route = "/api/v1/sync/push"; break;
        case 3: route = "/api/v1/sync/conflicts"; break;
        default: return nullptr;
    }
    jclass transport = env->FindClass("xyz/smartuni/app/NativeHttpTls");
    if (!transport || !safe(env)) return nullptr;
    jmethodID send = env->GetStaticMethodID(transport, "execute",
            "(Ljava/lang/String;[B[BLjava/lang/String;)Lxyz/smartuni/app/HttpReply;");
    if (!send || !safe(env)) return nullptr;
    jstring url = env->NewStringUTF((origin + route).c_str());
    jstring request_method = env->NewStringUTF(method);
    if (!url || !request_method || !safe(env)) return nullptr;
    jobject reply = env->CallStaticObjectMethod(
        transport, send, url, token, payload, request_method);
    if (!safe(env)) return nullptr;
    env->DeleteLocalRef(url);
    env->DeleteLocalRef(request_method);
    env->DeleteLocalRef(transport);
    return reply;
}

}  // namespace

extern "C" JNIEXPORT jint JNICALL
Java_xyz_smartuni_app_NativeBridge_abiVersion(JNIEnv*, jclass) {
    return static_cast<jint>(smartuni_abi_version());
}

extern "C" JNIEXPORT jboolean JNICALL
Java_xyz_smartuni_app_NativeBridge_selfTest(JNIEnv*, jclass) {
    return smartuni_abi_version() == SMARTUNI_ABI_VERSION &&
           smartuni_crypto_self_test_v1() == SMARTUNI_STATUS_OK ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jbyteArray JNICALL
Java_xyz_smartuni_app_NativeBridge_seal(JNIEnv* env, jclass, jbyteArray key,
                                       jbyteArray context, jbyteArray plain) {
    return crypto(env, key, context, plain, false);
}

extern "C" JNIEXPORT jbyteArray JNICALL
Java_xyz_smartuni_app_NativeBridge_open(JNIEnv* env, jclass, jbyteArray key,
                                       jbyteArray context, jbyteArray blob) {
    return crypto(env, key, context, blob, true);
}

extern "C" JNIEXPORT jint JNICALL
Java_xyz_smartuni_app_NativeBridge_checkHealth(JNIEnv* env, jclass, jstring base) {
    if (base == nullptr) return -1;
    const char* chars = env->GetStringUTFChars(base, nullptr);
    if (chars == nullptr) {
        safe(env);
        return -1;
    }
    const std::string origin(chars);
    env->ReleaseStringUTFChars(base, chars);
    return https_health(env, origin);
}

extern "C" JNIEXPORT jobject JNICALL
Java_xyz_smartuni_app_NativeBridge_apiRequest(JNIEnv* env, jclass,
                                               jstring origin, jbyteArray bearer,
                                               jint operation, jlong cursor,
                                               jbyteArray payload) {
    return exchange_api(env, origin, bearer, operation, cursor, payload);
}
