#include <avr/interrupt.h>
#include <avr/io.h>

#include <stdbool.h>
#include <stdint.h>
#include "i2c.h"
#include "registers.h"

static volatile bool i2c_in_progress = false;

void i2c_init(void) {
    // Smart mode enable, stop interrupt enable, data interrupt enable
    TWI0.SCTRLA = TWI_SMEN_bm;

    TWI0.SADDR = I2C_ADDRESS;

    // Enable I2C
    TWI0.SCTRLA |= TWI_ENABLE_bm;
}

void i2c_enable(void) {
    // Enable stop and data interrupts
    TWI0.SCTRLA |= TWI_PIEN_bm | TWI_APIEN_bm | TWI_DIEN_bm;
}

void i2c_disable(void) {
    // Disable stop and data interupts
    TWI0.SCTRLA &= ~(TWI_PIEN_bm | TWI_APIEN_bm | TWI_DIEN_bm);
}

#define PTR_WITHIN_MEMBER(PTR, MEMBER) (offsetof(registers_t, MEMBER) <= (PTR) && (PTR) < offsetof(registers_t, MEMBER) + sizeof(regs.MEMBER))

ISR(TWI0_TWIS_vect) {
    static uint8_t ptr = 0;
    static bool counter_written = false;
    static bool first = true;

    uint8_t status = TWI0.SSTATUS;

    if (status & TWI_DIF_bm) {
        // Data interrupt - reading data register clears interrupt flag

        i2c_in_progress = true;

        if (status & TWI_DIR_bm) {
            // Read

            TWI0.SDATA = ((uint8_t*)&regs)[ptr];

            if (ptr == offsetof(registers_t, status)) {
                // TODO: this is racey
                regs.status &= ~0x7f;
            }
        } else {
            // Write

            if (first) {
                // Register address
                first = false;
                ptr = TWI0.SDATA - 1;

                // Update buffered counter
                counter_written = false;
                regs.buffered_counter = reg_counter;
            } else {
                // Data

                if (!PTR_WITHIN_MEMBER(ptr, read_only)) {
                    ((uint8_t*)&regs)[ptr] = TWI0.SDATA;
                }

                if (PTR_WITHIN_MEMBER(ptr, buffered_counter)) {
                    counter_written = true;
                }
            }
        }
    }

    if (status & TWI_APIF_bm) {
        // Stop interrupt

        first = true;
        i2c_in_progress = false;

        // Update counter if written
        if (counter_written) {
            reg_counter = regs.buffered_counter;
        }

        // TODO: INT pin

        // Clear interrupt flag
        TWI0.SCTRLB = 0;
    }

    ptr++;
    if (ptr >= sizeof(regs)) {
        ptr = 0;
    }
}
