#include "test.h"

#include "encoder.c"
#include "unittest.h"

void setup(void) {
    encoder_delta = 0;
}

static void setab(bool a, bool b) {
    if (!!(PORT_ENCA.IN & BIT_ENCA) != a) {
        TLOG("a change");
        PORT_ENCA.INTFLAGS |= BIT_ENCA;
        if (a) {
            PORT_ENCA.IN |= BIT_ENCA;
        } else {
            PORT_ENCA.IN &= ~BIT_ENCA;
        }
    }

    if (!!(PORT_ENCB.IN & BIT_ENCB) != b) {
        TLOG("b change");
        PORT_ENCB.INTFLAGS |= BIT_ENCB;
        if (b) {
            PORT_ENCB.IN |= BIT_ENCB;
        } else {
            PORT_ENCB.IN &= ~BIT_ENCB;
        }
    }
}

#define STEP(A, B, DELTA) \
    do {                                       \
        setab((A), (B));                       \
        _isr_PORTA_PORT_vect();                \
        ASSERT_EQ_INT(encoder_delta, (DELTA)); \
    } while(0);

TEST(no_movement) {
    STEP(0, 0, 0);
    STEP(0, 0, 0);
    STEP(0, 0, 0);
}

TEST(clockwise_movement) {
    STEP(0, 0, 0);
    STEP(1, 0, 1);
    STEP(1, 1, 2);
    STEP(0, 1, 3);
    STEP(0, 0, 4);
    STEP(1, 0, 5);
    STEP(1, 1, 6);
    STEP(0, 1, 7);
}

TEST(counterclockwise_movement) {
    STEP(0, 0, 0);
    STEP(0, 1, -1);
    STEP(1, 1, -2);
    STEP(1, 0, -3);
    STEP(0, 0, -4);
    STEP(0, 1, -5);
    STEP(1, 1, -6);
    STEP(1, 0, -7);
}

TEST(direction_change) {
    STEP(0, 0, 0);
    STEP(1, 0, 1);
    STEP(1, 1, 2);
    STEP(1, 0, 1);
    STEP(0, 0, 0);
}

TEST(delta_reset) {
    STEP(0, 0, 0);
    STEP(1, 0, 1);
    STEP(1, 1, 2);
    STEP(0, 1, 3);
    STEP(0, 0, 4);

    encoder_delta = 0;

    STEP(0, 0, 0);
    STEP(1, 0, 1);
    STEP(1, 1, 2);
    STEP(0, 1, 3);
}
