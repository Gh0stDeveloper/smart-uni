#include "smartuni_core.h"
#include <cassert>
#include <cstdint>
#include <cstring>
#include <iostream>

int main() {
    const char *operation =
        R"({"schema_version":"1.0.0","operation":"notes.create",)"
        R"("operation_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",)"
        R"("actor_ref":"student@example.edu","occurred_at":"2026-11-06T04:00:00Z","payload":{}})";
    const auto *bytes = reinterpret_cast<const uint8_t *>(operation);
    assert(smartuni_abi_version() == SMARTUNI_ABI_VERSION);
    assert(smartuni_crypto_self_test_v1() == SMARTUNI_STATUS_OK);
    assert(smartuni_validate_operation_v1(bytes, std::strlen(operation)) == SMARTUNI_STATUS_OK);
    const char *invalid = "{}";
    assert(smartuni_validate_operation_v1(reinterpret_cast<const uint8_t *>(invalid), 2) == SMARTUNI_STATUS_INVALID);
    const char *email = "user@uni.edu";
    assert(smartuni_validate_email_v1(reinterpret_cast<const uint8_t *>(email), std::strlen(email)) == SMARTUNI_STATUS_OK);
    // Clave y contenido exclusivamente sintéticos. ABI C retorna buffers caller-owned.
    uint8_t key[32] = {0};
    const auto *ctx = reinterpret_cast<const uint8_t *>("owner/ci/demo/epoch-1");
    const auto *plain = reinterpret_cast<const uint8_t *>("ficticio");
    uint8_t sealed[512] = {0};
    size_t sealed_length = 0;
    assert(smartuni_seal_record_v1(key, 32, ctx, 21, plain, 8,
        sealed, sizeof(sealed), &sealed_length) == SMARTUNI_STATUS_OK);
    assert(sealed_length > 8);
    uint8_t opened[512] = {0};
    size_t opened_length = 0;
    assert(smartuni_open_record_v1(key, 32, ctx, 21, sealed, sealed_length,
        opened, sizeof(opened), &opened_length) == SMARTUNI_STATUS_OK);
    assert(opened_length == 8);
    assert(std::memcmp(opened, plain, opened_length) == 0);
    std::cout << "C++ -> Rust ABI v1: OK\n";
    return 0;
}
