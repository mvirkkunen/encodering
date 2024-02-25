#define _AVR_IO_H_

extern uint8_t _io_mem[0x10000];

#define _SFR_MEM8(N) (_io_mem[N])

#include </home/matti/avr-gcc-13.2.0-x64-linux/avr/include/avr/iotn1616.h>

#undef VPORTA
#undef VPORTB
#undef VPORTC
#undef RSTCTRL
#undef SLPCTRL
#undef CLKCTRL
#undef BOD
#undef VREF
#undef WDT
#undef CPUINT
#undef CRCSCAN
#undef RTC
#undef EVSYS
#undef CCL
#undef PORTMUX
#undef PORTA
#undef PORTB
#undef PORTC
#undef ADC0
#undef ADC1
#undef AC0
#undef AC1
#undef AC2
#undef DAC0
#undef DAC1
#undef DAC2
#undef USART0
#undef TWI0
#undef SPI0
#undef TCA0
#undef TCB0
#undef TCB1
#undef TCD0
#undef SYSCFG
#undef NVMCTRL
#undef SIGROW
#undef FUSE
#undef LOCKBIT
#undef USERROW

VPORT_t VPORTA;
VPORT_t VPORTB;
VPORT_t VPORTC;
CPUINT_t CPUINT;
PORT_t PORTA;
PORT_t PORTB;
PORT_t PORTC;
TCA_t TCA0;
