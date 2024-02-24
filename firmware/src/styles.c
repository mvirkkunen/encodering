#include "styles.h"
#include "leds.h"
#include "registers.h"

static void fill(uint8_t level) {
    for (uint8_t i = 0; i < LED_COUNT; i++) {
        regs.led_level[i] = level;
    }
}

static void style_single(uint8_t delta) {
    if (delta) {
        fill(regs.config.off_level);
        regs.led_level[reg_counter % LED_COUNT] = regs.config.on_level;
        leds_update();
    }
}

static void style_manual(uint8_t delta) {
    leds_update();
}

const style_func_t STYLES[STYLE_COUNT] = {
    style_single,
    style_manual,
};
