#include <avr/interrupt.h>
#include <avr/io.h>
#include <stdbool.h>

#include "config.h"
#include "encoder.h"
#include "registers.h"
#include "unittest.h"

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
    uint8_t event = (
        0
        | !!(PORT_ENCA.IN & BIT_ENCA) << 3
        | !!(PORT_ENCB.IN & BIT_ENCB) << 2
        | !!(PORT_ENCA.INTFLAGS & BIT_ENCA) << 1
        | !!(PORT_ENCB.INTFLAGS & BIT_ENCB) << 0
    );

    switch (event) {
        case 0b1010:
        case 0b1101:
        case 0b0110:
        case 0b0001:
            encoder_delta++;
            break;
        case 0b0101:
        case 0b1110:
        case 0b1001:
        case 0b0010:
            encoder_delta--;
            break;
    }

    PORT_ENCB.INTFLAGS &= ~BIT_ENCB;
    PORT_ENCA.INTFLAGS &= ~BIT_ENCA;
}

ISR(PORTB_PORT_vect, ISR_ALIASOF(PORTA_PORT_vect));
ISR(PORTC_PORT_vect, ISR_ALIASOF(PORTA_PORT_vect));
