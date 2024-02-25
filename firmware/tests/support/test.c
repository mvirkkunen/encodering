#include <setjmp.h>
#include <stdarg.h>
#include <string.h>

#include "avr/io.h"

#define CONFIG_C
#include "config.h"

#include "registers.h"
#include "test.h"

#define RED "\e[1;31m"
#define GREEN "\e[1;32m"
#define RESET "\e[0m"

_test_io_t _test_io;

volatile uint16_t reg_counter;
volatile registers_t regs;

static _test_record_t records[1024] = {0};
static unsigned record_count = 0;
static jmp_buf fail_jmp;

void _test_fail(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    printf(RED "FAIL" RESET "\n    ");
    vprintf(fmt, args);
    va_end(args);
    longjmp(fail_jmp, 1);
}

char log_buf[10 * 1024];
char *log_buf_p;

void _test_log(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    log_buf_p += vsnprintf(log_buf_p, &log_buf[sizeof(log_buf)] - log_buf_p, fmt, args);
    va_end(args);
}

void _test_register(const char *name, _test_func_t func) {
    records[record_count++] = (_test_record_t){ name, func };
}

__attribute__((weak)) void setup(void) { }
__attribute__((weak)) void teardown(void) { }

int main() {
    int r = 0;
    for (unsigned i = 0; i < record_count; i++) {
        printf("  %s: ", records[i].name);

        reg_counter = 0;
        memset((void*)&regs, 0, sizeof(regs));
        memset(&_test_io, 0, sizeof(_test_io));

        log_buf_p = log_buf;

        int result = setjmp(fail_jmp);
        if (result == 0) {
            setup();
            records[i].func();
            teardown();
        }

        r |= result;

        if (result == 0) {
            printf(GREEN "PASS" RESET "\n");
        } else {
            printf("%s", log_buf);
        }
    }

    return r;
}
