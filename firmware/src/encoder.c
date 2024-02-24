#include <avr/interrupt.h>
#include <avr/io.h>

#include "config.h"
#include "encoder.h"

volatile int8_t encoder_delta = 0;

// ENCA = PC0
// ENCB = PB3
// ENCS = PA4

void encoder_init(void) {
    PORT_ENCA.PINCTRL_ENCA = PORT_ISC_BOTHEDGES_gc;
    PORT_ENCB.PINCTRL_ENCB = PORT_ISC_BOTHEDGES_gc;
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

/*ISR(PORTB_vect) {
    // Clear interrupt
    PORTB.INTFLAGS |= PORT_INT3_bm;

}

ISR(PORTC_vect) {
    // Clear interrupt
    PORTC.INTFLAGS |= PORT_INT0_bm;


}*/
