#include <avr/interrupt.h>
#include <avr/io.h>

#include <stdbool.h>
#include <stdint.h>
#include "i2c.h"
#include "registers.h"

static volatile bool i2c_in_progress = false;

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

            TWI0.SDATA = ((uint8_t*)&reg)[ptr];
        } else {
            // Write

            if (first) {
                // Register address
                first = false;
                ptr = TWI0.SDATA - 1;
            } else {
                // Data
                ((uint8_t*)&reg)[ptr] = TWI0.SDATA;
            }
        }
    }

    if (status & TWI_APIF_bm) {
        // Stop interrupt

        first = true;
        i2c_in_progress = false;

        // Update buffered registers
        //reg.counter = counter;
        //reg.status = status;
        status = 0;

        // TODO: INT pin

        // Clear interrupt flag
        TWI0.SCTRLB = 0;
    }

    ptr++;
    if (ptr >= sizeof(reg)) {
        ptr = 0;
    }
}
