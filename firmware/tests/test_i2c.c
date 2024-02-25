#include "test.h"

#include "i2c.c"
#include "unittest.h"

static void i2c_write_byte(uint8_t byte) {
    TWI0.SDATA = byte;
    TWI0.SSTATUS = TWI_DIF_bm;
    _isr_TWI0_TWIS_vect();
}

static void i2c_stop(void) {
    TWI0.SSTATUS = TWI_APIF_bm;
    _isr_TWI0_TWIS_vect();
}

static void i2c_write(uint8_t reg, const void* data, size_t len) {
    i2c_write_byte(reg);

    for (size_t i = 0; i < len; i++) {
        i2c_write_byte(((uint8_t*)data)[i]);
    }

    i2c_stop();
}

static void i2c_read(uint8_t reg, void* data, size_t len) {
    i2c_write_byte(reg);

    for (size_t i = 0; i < len; i++) {
        TWI0.SSTATUS = TWI_DIF_bm | TWI_DIR_bm;
        _isr_TWI0_TWIS_vect();
        ((uint8_t*)data)[i] = TWI0.SDATA;
    }

    i2c_stop();
}

TEST(read_device_id) {
    uint16_t response[2];
    i2c_read(offsetof(registers_t, read_only), response, sizeof(response));

    ASSERT_EQ_INT(response[0], DEVICE_ID);
    ASSERT_EQ_INT(response[1], DEVICE_VERSION);
}

TEST(prevent_writing_readonly_fields) {
    uint8_t value[4] = {0};
    i2c_write(offsetof(registers_t, read_only), value, sizeof(value));

    ASSERT_EQ_INT(regs.read_only.device_id, DEVICE_ID);
    ASSERT_EQ_INT(regs.read_only.device_version, DEVICE_VERSION);
}

TEST(read_counter) {
    reg_counter = 1234;

    uint16_t result = 0;
    i2c_read(offsetof(registers_t, buffered_counter), &result, sizeof(result));

    ASSERT_EQ_INT(result, 1234);
}

TEST(write_counter) {
    uint16_t value = 4321;
    i2c_write(offsetof(registers_t, buffered_counter), &value, sizeof(value));

    ASSERT_EQ_INT(reg_counter, 4321);
}

