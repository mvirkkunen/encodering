#include <setjmp.h>
#include <stdarg.h>
#include <string.h>

#define CONFIG_C
#include "config.h"

#include "registers.h"
#include "test.h"

volatile uint16_t reg_counter;
volatile registers_t regs;
uint8_t _io_mem[0x10000];

static _test_record_t test_records[1024] = {0};
static unsigned test_record_count = 0;
static jmp_buf test_jmp_buf;

void _test_fail(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    printf("FAIL\n    ");
    vprintf(fmt, args);
    va_end(args);
    longjmp(test_jmp_buf, 1);
}

void _test_register(const char *name, _test_func_t func) {
    test_records[test_record_count++] = (_test_record_t){ name, func };
}

int main() {
    int r = 0;
    for (unsigned i = 0; i < test_record_count; i++) {
        printf("  %s: ", test_records[i].name);

        reg_counter = 0;
        memset((void*)&regs, 0, sizeof(regs));
        memset(_io_mem, 0, sizeof(_io_mem));

        setup();

        int result = setjmp(test_jmp_buf);
        if (result == 0) {
            test_records[i].func();
        }

        r |= result;

        teardown();

        if (result == 0) {
            printf("PASS\n");
        }
    }

    return r;
}
