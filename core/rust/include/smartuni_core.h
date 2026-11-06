#ifndef SMARTUNI_CORE_H
#define SMARTUNI_CORE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SMARTUNI_ABI_VERSION 1u
#define SMARTUNI_STATUS_OK 0
#define SMARTUNI_STATUS_POINTER_ERROR (-1)
#define SMARTUNI_STATUS_INVALID (-2)
#define SMARTUNI_STATUS_INTERNAL (-3)

/* Punteros válidos por toda la llamada; no se transfieren ni liberan buffers. */
uint32_t smartuni_abi_version(void);
int32_t smartuni_crypto_self_test_v1(void);
int32_t smartuni_validate_email_v1(const uint8_t *ptr, size_t len);
int32_t smartuni_validate_operation_v1(const uint8_t *ptr, size_t len);


/* SMART UNI 6.1/6.2: formatos autenticados; NO equivalen a autorización.
 * Todos los buffers de salida pertenecen al llamador y no solapan entradas.
 * out_len se escribe 0 ante error. Claves/passphrases: borrar por llamador.
 * No llamar con punteros C inválidos; la biblioteca no es sandbox.
 */
int32_t smartuni_seal_record_v1(
    const uint8_t *key, size_t key_len, const uint8_t *context, size_t context_len,
    const uint8_t *plaintext, size_t plain_len,
    uint8_t *out, size_t capacity, size_t *out_len);
int32_t smartuni_open_record_v1(
    const uint8_t *key, size_t key_len, const uint8_t *context, size_t context_len,
    const uint8_t *ciphertext, size_t ciphertext_len,
    uint8_t *out, size_t capacity, size_t *out_len);
int32_t smartuni_export_recovery_v1(
    const uint8_t *key, size_t key_len, const uint8_t *passphrase, size_t phrase_len,
    uint8_t *out, size_t capacity, size_t *out_len);
int32_t smartuni_restore_recovery_v1(
    const uint8_t *package, size_t package_len, const uint8_t *passphrase, size_t phrase_len,
    uint8_t *out, size_t capacity, size_t *out_len);

/* Esta ABI NO autentica, NO autoriza y no maneja secretos del servidor. */

#ifdef __cplusplus
}
#endif
#endif /* SMARTUNI_CORE_H */
