#ifdef UNITTEST
#include_next "config.h"
#else

#pragma once

#include "config_types.h"

#define I2C_ADDRESS 0x37
#define PIN_COUNT 6
#define LED_COUNT 30

#define PORT_ENCA    PORTC
#define BIT_ENCA     PIN0_bm
#define PINCTRL_ENCA PIN0CTRL

#define PORT_ENCB    PORTB
#define BIT_ENCB     PIN3_bm
#define PINCTRL_ENCB PIN3CTRL

#define PORT_ENCS    PORTA
#define BIT_ENCS     PIN4_bm

#define PORT_INT     PORTA
#define BIT_INT      PIN6_bm

extern const pin_def_t PIN_DEFS[PIN_COUNT];
extern const led_def_t LED_DEFS[LED_COUNT];

#ifdef CONFIG_C

const pin_def_t PIN_DEFS[PIN_COUNT] = {
    { 0, 1 << 3 },
    { 0, 1 << 2 },
    { 0, 1 << 1 },
    { 2, 1 << 3 },
    { 2, 1 << 2 },
    { 2, 1 << 1 },
};

const led_def_t LED_DEFS[LED_COUNT] = {
    { 0, 1, 0 },
    { 0, 2, 2 },
    { 0, 3, 4 },
    { 0, 4, 6 },
    { 0, 5, 8 },
    { 1, 0, 1 },
    { 1, 2, 10 },
    { 1, 3, 12 },
    { 1, 4, 14 },
    { 1, 5, 16 },
    { 2, 0, 3 },
    { 2, 1, 11 },
    { 2, 3, 18 },
    { 2, 4, 20 },
    { 2, 5, 22 },
    { 3, 0, 5 },
    { 3, 1, 13 },
    { 3, 2, 19 },
    { 3, 4, 24 },
    { 3, 5, 26 },
    { 4, 0, 7 },
    { 4, 1, 15 },
    { 4, 2, 21 },
    { 4, 3, 25 },
    { 4, 5, 28 },
    { 5, 0, 9 },
    { 5, 1, 17 },
    { 5, 2, 23 },
    { 5, 3, 27 },
    { 5, 4, 29 },
};

#endif

#endif