#include <stdint.h>

#define STYLE_COUNT 2

typedef void (*style_func_t)(uint8_t);

extern const style_func_t STYLES[STYLE_COUNT];
