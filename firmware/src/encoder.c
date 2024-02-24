#include <avr/interrupt.h>
#include <avr/io.h>
#include <stdbool.h>

#include "config.h"
#include "encoder.h"
#include "registers.h"

volatile int8_t encoder_delta = 0;

// ENCA = PC0
// ENCB = PB3
// ENCS = PA4

void encoder_init(void) {
    PORT_ENCA.PINCTRL_ENCA = PORT_ISC_BOTHEDGES_gc;
    PORT_ENCB.PINCTRL_ENCB = PORT_ISC_BOTHEDGES_gc;
}

void encoder_poll_button(void) {
    static bool prev_held = 0;

    bool held = PORT_ENCS.IN & BIT_ENCS;

    regs.status = (
        (held ? STATUS_BUTTON_HELD : 0)
        | ((held && !prev_held) ? STATUS_BUTTON_PRESSED : 0)
        | ((!held && prev_held) ? STATUS_BUTTON_RELEASED : 0)
    );
}

ISR(PORTA_PORT_vect) {
    uint8_t same = !(PORT_ENCA.IN & BIT_ENCA) == !(PORT_ENCB.IN & BIT_ENCB);
    uint8_t inc = 1;

    // who knows if this is correct...

    if (PORT_ENCA.INTFLAGS & BIT_ENCA) {
        PORT_ENCA.INTFLAGS |= BIT_ENCA;
        if (same) {
            inc = -inc;
        }
    }

    if (PORT_ENCB.INTFLAGS & BIT_ENCB) {
        PORT_ENCB.INTFLAGS |= BIT_ENCB;
        if (!same) {
            inc = -inc;
        }
    }

    encoder_delta += inc;
}

ISR(PORTB_PORT_vect, ISR_ALIASOF(PORTA_PORT_vect));
ISR(PORTC_PORT_vect, ISR_ALIASOF(PORTA_PORT_vect));
