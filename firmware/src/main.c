#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/sleep.h>
#include <stdbool.h>
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
    STATUS_BUTTON_CHANGE  = (1 << 0),
    STATUS_BUTTON_PRESSED = (1 << 1),
};

typedef struct __attribute__((__packed__)) config {
    uint16_t mode;
    uint16_t counter_min;
    uint16_t counter_max;
    uint8_t led_min;
    uint8_t led_max;
    uint8_t i2c_addr;
} config_t;

typedef struct __attribute__((__packed__)) registers {
    uint16_t counter;
    uint8_t status;
    uint8_t command;
    uint16_t device_id;
    uint16_t device_version;
    config_t config;
    uint8_t led_level[LEDS];
} registers_t;

registers_t registers;

volatile uint32_t counter = 0;
volatile uint32_t status = 0;
volatile bool i2c_in_progress = false;

void i2c_init(void) {
    // Smart mode enable, stop interrupt enable, data interrupt enable
    TWI0.SCTRLA = TWI_SMEN_bm | TWI_PIEN_bm | TWI_DIEN_bm;

    TWI0.SADDR = I2C_ADDRESS;

    // Enable I2C
    TWI0.SCTRLA |= TWI_ENABLE_bm;
}

ISR(TWI0_TWIS_vect) {
    static uint8_t ptr = 0;
    static bool first = true;

    uint8_t status = TWI0.SSTATUS;

    if (status & TWI_DIF_bm) {
        // Data interrupt - reading data register clears interrupt flag

        i2c_in_progress = true;

        if (status & TWI_DIR_bm) {
            // Read

            TWI0.SDATA = ((uint8_t*)&registers)[ptr];
        } else {
            // Write

            if (first) {
                // Register address
                first = false;
                ptr = TWI0.SDATA - 1;
            } else {
                // Data
                ((uint8_t*)&registers)[ptr] = TWI0.SDATA;
            }
        }
    }

    if (status & TWI_APIF_bm) {
        // Stop interrupt

        first = true;
        i2c_in_progress = false;

        // Update buffered registers
        registers.counter = counter;
        registers.status = status;
        status = 0;

        // TODO: INT pin

        // Clear interrupt flag
        TWI0.SCTRLB = 0;
    }

    ptr = (ptr + 1) % sizeof(registers);
}

int main(void) {
    i2c_init();

    sei();

    while (true) {
        sleep_cpu();
    }
}
