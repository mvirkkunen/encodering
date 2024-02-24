#pragma once

#include <stdint.h>
#include "config.h"

enum {
    MODE_SINGLE     = (1 << 0),
    MODE_FILL       = (1 << 1),
    MODE_ANTI_ALIAS = (1 << 2),
    MODE_INT_OUT    = (1 << 3),
    MODE_DAC_OUT    = (1 << 4),
    MODE_MANUAL     = (1 << 5),
};

enum {
    COMMAND_RESET    = 0x01,
    COMMAND_RESET_NV = 0x02,
    COMMAND_SAVE_NV  = 0x03,
};

enum {
    STATUS_BUTTON_PRESSED  = (1 << 0),
    STATUS_BUTTON_RELEASED = (1 << 1),
};

typedef struct __attribute__((__packed__)) config {
    uint16_t mode;
    uint16_t counter_min;
    uint16_t counter_max;
    uint8_t led_min;
    uint8_t led_max;
    uint8_t i2c_addr;
} config_t;

typedef struct __attribute__((__packed__)) reg {
    uint16_t counter;
    uint8_t status;
    uint8_t command;
    uint16_t device_id;
    uint16_t device_version;
    config_t config;
    uint8_t led_level[LED_COUNT];
} registers_t;

extern volatile registers_t reg;
