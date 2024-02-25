#pragma once

#include "config_types.h"

#define I2C_ADDRESS 0x37
#define PIN_COUNT 3
#define LED_COUNT 6

#define PORT_ENCA    PORTA
#define BIT_ENCA     PIN0_bm
#define PINCTRL_ENCA PIN0CTRL

#define PORT_ENCB    PORTB
#define BIT_ENCB     PIN1_bm
#define PINCTRL_ENCB PIN1CTRL

#define PORT_ENCS    PORTC
#define BIT_ENCS     PIN2_bm

#define PORT_INT     PORTA
#define BIT_INT      PIN3_bm

extern const pin_def_t PIN_DEFS[PIN_COUNT];
extern const led_def_t LED_DEFS[LED_COUNT];

#ifdef CONFIG_C

const pin_def_t PIN_DEFS[PIN_COUNT] = {
    { 0, 1 << 0 },
    { 1, 1 << 1 },
    { 2, 1 << 2 },
};

const led_def_t LED_DEFS[LED_COUNT] = {
    { 0, 1, 0 },
    { 0, 2, 1 },
    { 1, 0, 2 },
    { 1, 2, 3 },
    { 2, 0, 4 },
    { 2, 1, 5 },
};

#endif