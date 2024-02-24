#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/sleep.h>
#include <util/atomic.h>
#include <stdbool.h>
#include <stdint.h>

#include "config.h"
#include "registers.h"
#include "leds.h"
#include "encoder.h"
#include "i2c.h"

volatile uint16_t reg_counter;

volatile registers_t regs;

int main(void) {
    leds_init();
    encoder_init();
    i2c_init();
    i2c_enable();

    sei();

    while (true) {
        int8_t delta;
        ATOMIC_BLOCK(ATOMIC_FORCEON) {
            delta = encoder_delta;
        }

        i2c_disable();
        reg_counter += delta;
        i2c_enable();
    }
}
