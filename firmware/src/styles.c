#include "styles.h"
#include "registers.h"

static void fill(uint8_t level) {
    for (uint8_t i = 0; i < LED_COUNT; i++) {
        regs.led_level[i] = level;
    }
}

static void style_single(void) {
    fill(regs.config.off_level);

    regs.led_level[reg_counter % LED_COUNT] = regs.config.on_level;
}

static void style_manual(void) {
    // no-op
}

const style_func_t STYLES[STYLE_COUNT] = {
    style_single,
    style_manual,
};
