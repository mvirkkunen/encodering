#pragma once

#include <stdint.h>

typedef struct pin_def {
    uint8_t port;
    uint8_t bit;
} pin_def_t;

typedef struct led_def {
    uint8_t high_pin;
    uint8_t low_pin;
    uint8_t led_index;
} led_def_t;
