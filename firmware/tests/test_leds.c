#include "test.h"

#include "leds.c"

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
