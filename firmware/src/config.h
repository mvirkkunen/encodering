#pragma once

#include <stddef.h>
#include <stdint.h>
#include "avr/io.h"
#include "avr/pgmspace.h"

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

typedef struct pin_def {
    uint8_t port;
    uint8_t bit;
} pin_def_t;

typedef struct led_def {
    uint8_t high_pin;
    uint8_t low_pin;
    uint8_t led_index;
} led_def_t;

extern const pin_def_t PIN_DEFS[PIN_COUNT];
extern const led_def_t LED_DEFS[LED_COUNT];

#ifdef CONFIG_C

const pin_def_t PIN_DEFS[PIN_COUNT] = {
    { 0, PIN3_bm },
    { 0, PIN2_bm },
    { 0, PIN1_bm },
    { 2, PIN3_bm },
    { 2, PIN2_bm },
    { 2, PIN1_bm },
};

const led_def_t LED_DEFS[LED_COUNT] = {
    { 0, 1, 0 },
    { 1, 0, 1 },
};

#endif