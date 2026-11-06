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
    assert(smartuni_validate_operation_v1(bytes, std::strlen(operation)) == SMARTUNI_STATUS_OK);
    const char *invalid = "{}";
    assert(smartuni_validate_operation_v1(reinterpret_cast<const uint8_t *>(invalid), 2) == SMARTUNI_STATUS_INVALID);
    const char *email = "user@uni.edu";
    assert(smartuni_validate_email_v1(reinterpret_cast<const uint8_t *>(email), std::strlen(email)) == SMARTUNI_STATUS_OK);
    std::cout << "C++ -> Rust ABI v1: OK\n";
    return 0;
}
