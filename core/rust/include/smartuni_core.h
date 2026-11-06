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
int32_t smartuni_validate_email_v1(const uint8_t *ptr, size_t len);
int32_t smartuni_validate_operation_v1(const uint8_t *ptr, size_t len);

/* Esta ABI NO autentica, NO autoriza y no maneja secretos del servidor. */

#ifdef __cplusplus
}
#endif
#endif /* SMARTUNI_CORE_H */
