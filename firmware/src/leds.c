#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/pgmspace.h>

#include "config.h"
#include "leds.h"
#include "registers.h"
#include "unittest.h"

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

static volatile bool schedule_update = true;

volatile uint8_t led_cycles = 0;

typedef struct led_schedule_item {
    uint8_t port_dir[3];
    uint8_t next_cmp;
} led_schedule_item_t;

typedef struct led_schedule {
    // 1 item for enabled pins, PIN_COUNT - 1 items for actual schedule items, 1 item for guard values (TODO: do we need an extra item for guard..?)
    led_schedule_item_t items[PIN_COUNT + 2];
    uint8_t high_pin[3];
} led_schedule_t;

static led_schedule_t led_schedules[PIN_COUNT];
static led_schedule_t pending_led_schedules[PIN_COUNT];

void leds_init(void) {
    // Set LED compare interrupt as high priority so it can interrupt other interrupts
    CPUINT.LVL1VEC = TCA0_CMP0_vect_num;

    // Enable compare 0 and overflow interrupts
    TCA0.SINGLE.INTCTRL = TCA_SINGLE_CMP0_bm | TCA_SINGLE_OVF_bm;

    // Initialize LED schedule
    leds_update();

    // Set counter to large value so timer immediately overflows without running compare ISR
    TCA0.SINGLE.CNT = 255;

    // Set clock divisor to 16 and enable timer
    TCA0.SINGLE.CTRLA = TCA_SINGLE_CLKSEL_DIV16_gc | TCA_SINGLE_ENABLE_bm;
}

void leds_update(void) {
    typedef struct group_led {
        uint8_t port;
        uint8_t bit;
        uint8_t cmp;
    } group_led_t;

    // Create LED schedule for each high pin index
    for (uint8_t high_pin_index = 0; high_pin_index < PIN_COUNT; high_pin_index++) {
        led_schedule_t *sched = &pending_led_schedules[high_pin_index];
        led_schedule_item_t *item = &sched->items[0];

        // TLOG("processing high pin %d", high_pin_index);

        // Enable current high pin in schedule
        const pin_def_t *high_pin = &PIN_DEFS[high_pin_index];
        for (uint8_t port = 0; port < 3; port++) {
            item->port_dir[port] = sched->high_pin[port] = (high_pin->port == port) ? high_pin->bit : 0;
        }

        // LEDs in this high pin group
        group_led_t group[PIN_COUNT];
        uint8_t count = 0;
        uint8_t cur_cmp = 255;

        TLOG("high pin=%d", high_pin_index);

        // Find LEDs with correct high_pin and copy their information to the group array
        for (const led_def_t *led_def = &LED_DEFS[0]; led_def < &LED_DEFS[LED_COUNT]; led_def++) {
            if (led_def->high_pin != high_pin_index) {
                TLOG("LED: wrong high pin");
                continue;
            }

            // Look up PWM value from registers and gamma correct it to get compare value
            uint8_t cmp = pgm_read_byte(&GAMMA_LUT[regs.led_level[led_def->led_index]]);
            if (cmp == 0) {
                TLOG("LED: off");
                // LED is off, skip it
                continue;
            }

            TLOG("LED: added");

            // Calculate minimum PWM in group to use as starting value later
            if (cmp < cur_cmp) {
                cur_cmp = cmp;
            }

            // Include LED in group
            const pin_def_t *low_pin = &PIN_DEFS[led_def->low_pin];
            group[count] = (group_led_t){
                .port = low_pin->port,
                .bit = low_pin->bit,
                .cmp = cmp,
            };
            count++;

            // Enable pin in schedule item
            item->port_dir[low_pin->port] = low_pin->bit;
        }

        item->next_cmp = cur_cmp;
        TLOG("next_cmp: %d", item->next_cmp);
        item++;

        // Create LED schedule by inserting LEDs sorted by ascending PWM level. If multiple LEDs have the same PWM value,
        // they are all inserted into the same item.
        for (uint8_t inserted = 0; inserted < count; ) {
            uint8_t next_pwm = 255;

            // Initialize schedule item with enabled LED bits from previous step and current PWM value
            *item = (led_schedule_item_t){{item[-1].port_dir[0], item[-1].port_dir[1], item[-1].port_dir[2]}, cur_cmp};
            for (uint8_t i = 0; i < count; i++) {
                TLOG("i=%d cmp=%d", i, group[i].cmp);
                if (group[i].cmp == cur_cmp) {
                    //  Turn off this LED at this step
                    item->port_dir[group[i].port] &= ~group[i].bit;
                    inserted++;
                } else if (cur_cmp < group[i].cmp && group[i].cmp < next_pwm) {
                    // Potential next PWM level to consider
                    next_pwm = group[i].cmp;
                }
            }

            item->next_cmp = next_pwm;
            cur_cmp = next_pwm;
            TLOG("next_cmp: %d", item->next_cmp);
            item++;
        }

        // Add guard values to end of schedule
        item->next_cmp = 255;

        sched++;
    }

    // Notify ISR we would like to load the pending schedule
    schedule_update = true;
}

ISR(TCA0_OVF_vect) {
    static led_schedule_t *sched = &led_schedules[0];

    // Stop and reset timer while we set up next schedule
    TCA0.SINGLE.CTRLA &= ~TCA_SINGLE_ENABLE_bm;
    TCA0.SINGLE.CNT = 0;

    // Clear interrupt flag
    TCA0.SINGLE.INTFLAGS |= TCA_SINGLE_OVF_bm;

    // Set first compare value
    TCA0.SINGLE.CMP0 = sched->items[0].next_cmp;

    TLOG("set next_cmp %d", sched->items[0].next_cmp);

    // Set pin levels, high pin is high, others are low
    VPORTA.OUT = sched->high_pin[0];
    VPORTB.OUT = sched->high_pin[1];
    VPORTC.OUT = sched->high_pin[2];

    // Enable all pin outputs used by schedule
    VPORTA.DIR = sched->items[0].port_dir[0];
    VPORTB.DIR = sched->items[0].port_dir[1];
    VPORTC.DIR = sched->items[0].port_dir[2];

#ifndef UNITTEST
    // Wrap LED ISR pointer
    led_schedule_t *ptr = (led_schedule_t *)(intptr_t)((GPIOR1 << 8) | GPIOR0);
    if (ptr == &led_schedules[PIN_COUNT]) {
        ptr = &led_schedules[0];
        GPIOR0 = (intptr_t)ptr;
        GPIOR1 = (intptr_t)ptr >> 8;
    }
#endif

    // Enable timer
    TCA0.SINGLE.CTRLA |= TCA_SINGLE_ENABLE_bm;

    // Go to next schedule
    sched++;
    if (sched == &led_schedules[PIN_COUNT]) {
        sched = &led_schedules[0];
    }

    // Copy in pending schedule if requested
    if (schedule_update) {
        schedule_update = false;
        memcpy(led_schedules, pending_led_schedules, sizeof(led_schedules));
    }

    led_cycles++;

    // TODO: maybe sleep CPU if no LEDs active
}
