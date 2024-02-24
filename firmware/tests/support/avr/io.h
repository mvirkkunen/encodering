#define _AVR_IO_H_

#define _VECTOR(N) vector_ ## N

extern uint8_t _io_mem[0x10000];

#define ISR(NAME) void NAME(void)
#define _SFR_MEM8(N) (_io_mem[N])

#include </home/matti/avr-gcc-13.2.0-x64-linux/avr/include/avr/iotn1616.h>
