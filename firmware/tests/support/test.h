#pragma once

#include <stdint.h>
#include <stdio.h>

typedef void (*_test_func_t)(void);

typedef struct _test_record {
    const char* name;
    _test_func_t func;
} _test_record_t;

__attribute__ ((format (printf, 1, 2))) void _test_fail(const char *fmt, ...);
__attribute__ ((format (printf, 1, 2))) void _test_log(const char *fmt, ...);
void _test_register(const char *name, _test_func_t func);

void setup(void);
void teardown(void);

#define TEST(NAME) \
    static void NAME(void);                                                                               \
    __attribute__((constructor)) static void _test_register_##NAME(void) { _test_register(#NAME, NAME); } \
    void NAME(void)

#define _ASSERT_FAIL(FMT, ...) \
    _test_fail("assertion " FMT " failed at %s:%d\n", __VA_ARGS__, __FILE__, __LINE__);

#define ASSERT(X) if (!(X)) { _ASSERT_FAIL("%s", #X); }

#define ASSERT_EQ_INT(ACTUAL, EXPECTED) \
    do {                                                                                 \
        int _actual = (ACTUAL), _expected = (EXPECTED);                                  \
        if (_actual != _expected) {                                                      \
            _ASSERT_FAIL("%d == %d (%s == %s)", _actual, _expected, #ACTUAL, #EXPECTED); \
        }                                                                                \
    } while (0);

#define ASSERT_EQ_BYTES(ACTUAL, ...) \
    do {                                                                \
        uint8_t *_actual = ACTUAL;                                      \
        uint8_t _expected[] = __VA_ARGS__;                              \
        for (size_t i = 0; i < sizeof(_expected); i++) {                \
            if (_actual[i] != _expected[i]) {                           \
                _ASSERT_FAIL("at offset %zu: %02x != %02x (%s == %s)",  \
                    i, _actual[i], _expected[i], #ACTUAL, #__VA_ARGS__) \
            }                                                           \
        }                                                               \
    } while (0);
