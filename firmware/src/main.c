#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/sleep.h>
#include <stdbool.h>
#include <stdint.h>

#include "config.h"
#include "i2c.h"
#include "leds.h"
#include "registers.h"

volatile registers_t reg = {0};

volatile uint32_t counter = 0;
volatile uint32_t status = 0;
volatile bool i2c_in_progress = false;

int main(void) {
    leds_init();
    i2c_init();

    sei();

    while (true) {
        //sleep_cpu();
    }
}
