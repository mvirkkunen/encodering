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
#include "styles.h"

volatile uint16_t reg_counter;

volatile registers_t regs;

int main(void) {
    leds_init();
    encoder_init();
    i2c_init();
    i2c_enable();

    regs.config.on_level = 255;
    regs.config.off_level = 0;
    regs.config.unused_level = 0;
    regs.read_only.device_id = DEVICE_ID;
    regs.read_only.device_version = DEVICE_VERSION;

    sei();

    while (true) {
        // Run main loop around 200 times a second

        while (led_cycles < LED_CYCLES_PER_SECOND / 200) { }
        led_cycles = 0;

        encoder_poll_button();

        int8_t delta;
        ATOMIC_BLOCK(ATOMIC_FORCEON) {
            delta = encoder_delta;
        }

        i2c_disable();
        reg_counter += delta;
        i2c_enable();

        uint8_t style = regs.config.style;
        if (style < STYLE_COUNT) {
            STYLES[style](delta);
        }
    }
}
