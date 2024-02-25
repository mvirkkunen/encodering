#include "test.h"

#include "leds.c"

void setup(void) {
    memset(pending_led_schedules, 0, sizeof(pending_led_schedules));
}

TEST(init_should_set_guard_values) {
    leds_init();

    led_schedule_t *s = pending_led_schedules;

    ASSERT_EQ_INT(s[0].items[0].next_cmp, 255);
    ASSERT_EQ_INT(s[0].items[1].next_cmp, 255);
}

TEST(schedule_should_have_correct_high_pins) {
    leds_update();

    led_schedule_t *s = pending_led_schedules;

    ASSERT_EQ_INT(s[0].high_pin[0], 1 << 0);
    ASSERT_EQ_INT(s[0].high_pin[1], 0);
    ASSERT_EQ_INT(s[0].high_pin[2], 0);
    ASSERT_EQ_INT(s[0].items[0].port_dir[0], 1 << 0);
    ASSERT_EQ_INT(s[0].items[0].port_dir[1], 0);
    ASSERT_EQ_INT(s[0].items[0].port_dir[2], 0);

    ASSERT_EQ_INT(s[1].high_pin[0], 0);
    ASSERT_EQ_INT(s[1].high_pin[1], 1 << 1);
    ASSERT_EQ_INT(s[1].high_pin[2], 0);
    ASSERT_EQ_INT(s[1].items[0].port_dir[0], 0);
    ASSERT_EQ_INT(s[1].items[0].port_dir[1], 1 << 1);
    ASSERT_EQ_INT(s[1].items[0].port_dir[2], 0);

    ASSERT_EQ_INT(s[2].high_pin[0], 0);
    ASSERT_EQ_INT(s[2].high_pin[1], 0);
    ASSERT_EQ_INT(s[2].high_pin[2], 1 << 2);
    ASSERT_EQ_INT(s[2].items[0].port_dir[0], 0);
    ASSERT_EQ_INT(s[2].items[0].port_dir[1], 0);
    ASSERT_EQ_INT(s[2].items[0].port_dir[2], 1 << 2);
}

TEST(guard_values_should_be_set_if_led_levels_are_zero) {
    leds_update();

    led_schedule_t *s = pending_led_schedules;

    ASSERT_EQ_INT(s[0].items[1].next_cmp, 255);
    ASSERT_EQ_INT(s[0].items[1].port_dir[0], 0);
    ASSERT_EQ_INT(s[0].items[1].port_dir[1], 0);
    ASSERT_EQ_INT(s[0].items[1].port_dir[2], 0);

    ASSERT_EQ_INT(s[1].items[1].next_cmp, 255);
    ASSERT_EQ_INT(s[1].items[1].port_dir[0], 0);
    ASSERT_EQ_INT(s[1].items[1].port_dir[1], 0);
    ASSERT_EQ_INT(s[1].items[1].port_dir[2], 0);

    ASSERT_EQ_INT(s[2].items[1].next_cmp, 255);
    ASSERT_EQ_INT(s[2].items[1].port_dir[0], 0);
    ASSERT_EQ_INT(s[2].items[1].port_dir[1], 0);
    ASSERT_EQ_INT(s[2].items[1].port_dir[2], 0);
}

TEST(overflow_isr_should_set_up_schedule_registers) {
    regs.led_level[0] = 0;
    regs.led_level[1] = 16;

    leds_update();

    // Run ISR PIN_COUNT + 1 times to wrap back to first schedule
    _isr_TCA0_OVF_vect();
    _isr_TCA0_OVF_vect();
    _isr_TCA0_OVF_vect();
    _isr_TCA0_OVF_vect();

    ASSERT(memcmp(led_schedules, pending_led_schedules, sizeof(led_schedules)) == 0);

    ASSERT_EQ_INT(TCA0.SINGLE.CMP0, led_schedules[0].items[0].next_cmp);

    ASSERT_EQ_INT(VPORTA.OUT, led_schedules[0].high_pin[0]);
    ASSERT_EQ_INT(VPORTB.OUT, led_schedules[0].high_pin[1]);
    ASSERT_EQ_INT(VPORTC.OUT, led_schedules[0].high_pin[2]);

    ASSERT_EQ_INT(VPORTA.DIR, led_schedules[0].items[0].port_dir[0]);
    ASSERT_EQ_INT(VPORTB.DIR, led_schedules[0].items[0].port_dir[1]);
    ASSERT_EQ_INT(VPORTC.DIR, led_schedules[0].items[0].port_dir[2]);
}

TEST(single_step_schedule) {
    uint8_t level16 = GAMMA_LUT[16];

    regs.led_level[0] = 16;
    regs.led_level[1] = 16;
    regs.led_level[2] = 16;
    regs.led_level[3] = 16;
    regs.led_level[4] = 16;
    regs.led_level[5] = 16;

    leds_update();

    led_schedule_t *s = pending_led_schedules;

    // Schedule 0: all pins start low, then turn off
    ASSERT_EQ_INT(s[0].items[0].port_dir[0], 1 << 0); // high pin
    ASSERT_EQ_INT(s[0].items[0].port_dir[1], 1 << 1);
    ASSERT_EQ_INT(s[0].items[0].port_dir[2], 1 << 2);
    ASSERT_EQ_INT(s[0].items[0].next_cmp, level16);

    ASSERT_EQ_INT(s[0].items[1].port_dir[0], 1 << 0);
    ASSERT_EQ_INT(s[0].items[1].port_dir[1], 0);
    ASSERT_EQ_INT(s[0].items[1].port_dir[2], 0);
    ASSERT_EQ_INT(s[0].items[1].next_cmp, 255);

    // Schedule 1: pins 0 and 2 start low, then turn off
    ASSERT_EQ_INT(s[1].items[0].port_dir[0], 1 << 0);
    ASSERT_EQ_INT(s[1].items[0].port_dir[1], 1 << 1); // high pin
    ASSERT_EQ_INT(s[1].items[0].port_dir[2], 1 << 2);
    ASSERT_EQ_INT(s[1].items[0].next_cmp, level16);

    ASSERT_EQ_INT(s[1].items[1].port_dir[0], 0);
    ASSERT_EQ_INT(s[1].items[1].port_dir[1], 1 << 1);
    ASSERT_EQ_INT(s[1].items[1].port_dir[2], 0);
    ASSERT_EQ_INT(s[1].items[1].next_cmp, 255);

    // Schedule 2: pins 0 and 1 start low, then pin 0 turns off, then pin 1 turns off
    ASSERT_EQ_INT(s[2].items[0].port_dir[0], 1 << 0);
    ASSERT_EQ_INT(s[2].items[0].port_dir[1], 1 << 1);
    ASSERT_EQ_INT(s[2].items[0].port_dir[2], 1 << 2); // high pin
    ASSERT_EQ_INT(s[2].items[0].next_cmp, level16);

    ASSERT_EQ_INT(s[2].items[1].port_dir[0], 0);
    ASSERT_EQ_INT(s[2].items[1].port_dir[1], 0);
    ASSERT_EQ_INT(s[2].items[1].port_dir[2], 1 << 2);
    ASSERT_EQ_INT(s[2].items[1].next_cmp, 255);
}

TEST(multi_step_schedule) {
    uint8_t level16 = GAMMA_LUT[16];
    uint8_t level64 = GAMMA_LUT[64];

    regs.led_level[0] = 0;
    regs.led_level[1] = 16;
    regs.led_level[2] = 16;
    regs.led_level[3] = 16;
    regs.led_level[4] = 16;
    regs.led_level[5] = 64;

    leds_update();

    led_schedule_t *s = pending_led_schedules;

    // Schedule 0: pin 2 starts low, then turns off
    ASSERT_EQ_INT(s[0].items[0].port_dir[0], 1 << 0); // high pin
    ASSERT_EQ_INT(s[0].items[0].port_dir[1], 0);
    ASSERT_EQ_INT(s[0].items[0].port_dir[2], 1 << 2);
    ASSERT_EQ_INT(s[0].items[0].next_cmp, level16);

    ASSERT_EQ_INT(s[0].items[1].port_dir[0], 1 << 0);
    ASSERT_EQ_INT(s[0].items[1].port_dir[1], 0);
    ASSERT_EQ_INT(s[0].items[1].port_dir[2], 0);
    ASSERT_EQ_INT(s[0].items[1].next_cmp, 255);

    // Schedule 1: pins 0 and 2 start low, then turn off
    ASSERT_EQ_INT(s[1].items[0].port_dir[0], 1 << 0);
    ASSERT_EQ_INT(s[1].items[0].port_dir[1], 1 << 1); // high pin
    ASSERT_EQ_INT(s[1].items[0].port_dir[2], 1 << 2);
    ASSERT_EQ_INT(s[1].items[0].next_cmp, level16);

    ASSERT_EQ_INT(s[1].items[1].port_dir[0], 0);
    ASSERT_EQ_INT(s[1].items[1].port_dir[1], 1 << 1);
    ASSERT_EQ_INT(s[1].items[1].port_dir[2], 0);
    ASSERT_EQ_INT(s[1].items[1].next_cmp, 255);

    // Schedule 2: pins 0 and 1 start low, then pin 0 turns off, then pin 1 turns off
    ASSERT_EQ_INT(s[2].items[0].port_dir[0], 1 << 0);
    ASSERT_EQ_INT(s[2].items[0].port_dir[1], 1 << 1);
    ASSERT_EQ_INT(s[2].items[0].port_dir[2], 1 << 2); // high pin
    ASSERT_EQ_INT(s[2].items[0].next_cmp, level16);

    ASSERT_EQ_INT(s[2].items[1].port_dir[0], 0);
    ASSERT_EQ_INT(s[2].items[1].port_dir[1], 1 << 1);
    ASSERT_EQ_INT(s[2].items[1].port_dir[2], 1 << 2); // high pin
    ASSERT_EQ_INT(s[2].items[1].next_cmp, level64);

    ASSERT_EQ_INT(s[2].items[2].port_dir[0], 0);
    ASSERT_EQ_INT(s[2].items[2].port_dir[1], 0);
    ASSERT_EQ_INT(s[2].items[2].port_dir[2], 1 << 2); // high pin
    ASSERT_EQ_INT(s[2].items[2].next_cmp, 255);
}
