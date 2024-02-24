#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/pgmspace.h>

#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include "config.h"
#include "leds.h"
#include "registers.h"

const PROGMEM uint8_t GAMMA_LUT[256] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   1,   1,   1,   1,
      1,   1,   1,   1,   2,   2,   2,   2,   2,   2,   3,   3,   3,   3,   4,   4,
      4,   4,   5,   5,   5,   5,   6,   6,   6,   7,   7,   7,   8,   8,   8,   9,
      9,   9,  10,  10,  11,  11,  11,  12,  12,  13,  13,  14,  14,  15,  15,  16,
     16,  17,  17,  18,  18,  19,  19,  20,  20,  21,  21,  22,  23,  23,  24,  24,
     25,  26,  26,  27,  28,  28,  29,  30,  30,  31,  32,  32,  33,  34,  35,  35,
     36,  37,  38,  38,  39,  40,  41,  42,  42,  43,  44,  45,  46,  47,  47,  48,
     49,  50,  51,  52,  53,  54,  55,  56,  56,  57,  58,  59,  60,  61,  62,  63,
     64,  65,  66,  67,  68,  69,  70,  71,  73,  74,  75,  76,  77,  78,  79,  80,
     81,  82,  84,  85,  86,  87,  88,  89,  91,  92,  93,  94,  95,  97,  98,  99,
    100, 102, 103, 104, 105, 107, 108, 109, 111, 112, 113, 115, 116, 117, 119, 120,
    121, 123, 124, 126, 127, 128, 130, 131, 133, 134, 136, 137, 139, 140, 142, 143,
    145, 146, 148, 149, 151, 152, 154, 155, 157, 158, 160, 162, 163, 165, 166, 168,
    170, 171, 173, 175, 176, 178, 180, 181, 183, 185, 186, 188, 190, 192, 193, 195,
    197, 199, 200, 202, 204, 206, 207, 209, 211, 213, 215, 217, 218, 220, 222, 224,
    226, 228, 230, 232, 233, 235, 237, 239, 241, 243, 245, 247, 249, 251, 253, 255,
};

typedef struct led_schedule_item {
    uint8_t port_dir[3];
    uint8_t next_cmp;
} led_schedule_item_t;

typedef struct led_schedule {
    led_schedule_item_t items[PIN_COUNT + 1];
    uint8_t enabled_pins[3];
    uint8_t high_pin[3];
} led_schedule_t;

static led_schedule_t led_schedule;
static led_schedule_t next_schedule;
static const led_def_t *led_def_p = &LED_DEFS[0];

typedef struct group_led {
    uint8_t port;
    uint8_t bit;
    uint8_t pwm;
} group_led_t;

static void update_led_schedule(void) {
    // High pin number for this group
    uint8_t high_pin_index = led_def_p->high_pin;

    // LEDs for this group
    uint8_t count = 0;
    group_led_t group[PIN_COUNT] = {0};

    // Find next group of consecutive LEDs with identical high_pin and copy their information to group array
    // Copying is performed to ensure that values don't change while we're sorting them
    // LED PWM values are also gamma corrected here
    while (led_def_p->high_pin == high_pin_index) {
        // Look up PWM value from registers and gamma correct it
        uint8_t pwm = pgm_read_byte(&GAMMA_LUT[reg.led_level[led_def_p->led_index]]);

        if (pwm == 0) {
            // LED is off, skip it
            continue;
        }

        // Insert LED to schedule
        const pin_def_t *low_pin = &PIN_DEFS[led_def_p->low_pin];
        group[count] = (group_led_t){
            .port = low_pin->port,
            .bit = low_pin->bit,
            .pwm = pwm,
        };

        count++;

        // Go to next LED definition, wrapping if needed
        led_def_p++;
        if (led_def_p == &LED_DEFS[LED_COUNT]) {
            led_def_p = &LED_DEFS[0];
        }
    }

    // Enable high pin in schedule
    const pin_def_t *high_pin = &PIN_DEFS[high_pin_index];
    for (uint8_t port = 0; port < 2; port++) {
        next_schedule.enabled_pins[port] = next_schedule.high_pin[port] = (high_pin->port == port) ? high_pin->bit : 0;
    }

    // Create LED schedule by inserting LEDs sorted by ascending PWM level. If multiple LEDs have the same PWM value,
    // they are all inserted into the same item.
    led_schedule_item_t *si = &next_schedule.items[0];
    uint8_t cur_pwm = 0;
    for (uint8_t inserted = 0; inserted < count; ) {
        uint8_t next_pwm = 255;

        // Zero port bits and store PWM value
        *si = (led_schedule_item_t){0, 0, 0, cur_pwm};
        for (uint8_t i = 0; i < count; i++) {
            if (group[i].pwm == cur_pwm) {
                // Add this LED's low pin in the current schedule item
                si->port_dir[group[i].port] |= group[i].bit;
                // Enable this LED's low pin in the schedule
                next_schedule.enabled_pins[group[i].port] |= group[i].bit;
                inserted++;
            } else if (cur_pwm < group[i].pwm && group[i].pwm < next_pwm) {
                // Potential next PWM level to consider
                next_pwm = group[i].pwm;
            }
        }

        cur_pwm = next_pwm;
        si++;
    }

    // Add guard values to end of schedule
    si->next_cmp = 255;
    si++;
    si->next_cmp = 255;
}

void leds_init(void) {
    // Set LED compare interrupt as high priority so it can interrupt other interrupts
    CPUINT.LVL1VEC = TCA0_CMP0_vect_num;

    // Enable compare 0 and overflow interrupts
    TCA0.SINGLE.INTCTRL = TCA_SINGLE_CMP0_bm | TCA_SINGLE_OVF_bm;

    // Initialize LED schedule to guard values so first iterations don't do something weird
    next_schedule.items[0].next_cmp = 255;
    next_schedule.items[1].next_cmp = 255;
    memcpy(&led_schedule, &next_schedule, sizeof(led_schedule));

    // Set clock divisor to 16 and enable timer
    TCA0.SINGLE.CTRLA = TCA_SINGLE_CLKSEL_DIV16_gc | TCA_SINGLE_ENABLE_bm;
}

ISR(TCA0_OVF_vect) {
    static VPORT_t * const ports[3] = { &VPORTA, &VPORTB, &VPORTC };

    // Stop and reset timer
    TCA0.SINGLE.CTRLA &= ~TCA_SINGLE_ENABLE_bm;
    TCA0.SINGLE.CNT = 0;

    // Clear interrupt flag
    TCA0.SINGLE.INTFLAGS |= TCA_SINGLE_OVF_bm;

    // Set up next LED schedule
    memcpy(&led_schedule, &next_schedule, sizeof(led_schedule));

    // Set LED ISR pointer
    GPIOR0 = (uint8_t)(uint16_t)&led_schedule.items[0];
    GPIOR1 = (uint8_t)((uint16_t)&led_schedule.items[0] + 1);

    // Set pin levels, high pin is high, others are low
    VPORTA.OUT = led_schedule.high_pin[0];
    VPORTB.OUT = led_schedule.high_pin[1];
    VPORTC.OUT = led_schedule.high_pin[2];

    // Enable all pin outputs
    VPORTA.DIR = led_schedule.enabled_pins[0];
    VPORTB.DIR = led_schedule.enabled_pins[1];
    VPORTC.DIR = led_schedule.enabled_pins[2];

    // Set first compare value
    TCA0.SINGLE.CMP0 = led_schedule.items[0].next_cmp;

    // Enable timer
    TCA0.SINGLE.CTRLA |= TCA_SINGLE_ENABLE_bm;

    // Calculate next schedule
    update_led_schedule();

    // TODO: maybe sleep CPU if no LEDs active
}
