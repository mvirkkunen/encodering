#pragma once

#include <stdint.h>
#include "config.h"

#define DEVICE_ID 0x1337
#define DEVICE_VERSION 0x0001

/*enum {
    MODE_SINGLE     = (1 << 0),
    MODE_FILL       = (1 << 1),
    MODE_ANTI_ALIAS = (1 << 2),
    MODE_INT_OUT    = (1 << 3),
    MODE_DAC_OUT    = (1 << 4),
    MODE_MANUAL     = (1 << 5),
};*/

enum {
    STYLE_SINGLE = 0,
};

enum {
    COMMAND_RESET    = 0x01,
    COMMAND_RESET_NV = 0x02,
    COMMAND_SAVE_NV  = 0x03,
};

enum {
    STATUS_BUTTON_HELD     = (1 << 0),
    STATUS_BUTTON_PRESSED  = (1 << 1),
    STATUS_BUTTON_RELEASED = (1 << 2),
};

typedef struct __attribute__((__packed__)) config {
    uint8_t style;
    uint16_t counter_min;
    uint16_t counter_max;
    uint8_t led_min;
    uint8_t led_max;
    uint8_t on_level;
    uint8_t off_level;
    uint8_t unused_level;
    uint8_t i2c_addr;
} config_t;

typedef struct __attribute__((__packed__)) registers {
    uint16_t buffered_counter;
    uint8_t status;
    uint8_t command;
    struct {
        uint16_t device_id;
        uint16_t device_version;
    } read_only;
    config_t config;
    uint8_t led_level[LED_COUNT];
} registers_t;

extern volatile uint16_t reg_counter;

extern volatile registers_t regs;

#define DEVICE_ID 0x1337
#define DEVICE_VERSION 0x0001

#define REGS_INIT \
    {                                                                              \
        .config = { .on_level = 255 },                                             \
        .read_only = { .device_id = DEVICE_ID, .device_version = DEVICE_VERSION }, \
    }
