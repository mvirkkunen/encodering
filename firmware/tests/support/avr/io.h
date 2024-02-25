#include "include_next/avr/io.h"

#undef _MMIO_BYTE
#undef _MMIO_WORD
#undef _MMIO_DWORD

typedef struct _test_io {
    VPORT_t _VPORTA;
    VPORT_t _VPORTB;
    VPORT_t _VPORTC;
    RSTCTRL_t _RSTCTRL;
    SLPCTRL_t _SLPCTRL;
    CLKCTRL_t _CLKCTRL;
    BOD_t _BOD;
    VREF_t _VREF;
    WDT_t _WDT;
    CPUINT_t _CPUINT;
    CRCSCAN_t _CRCSCAN;
    RTC_t _RTC;
    EVSYS_t _EVSYS;
    CCL_t _CCL;
    PORTMUX_t _PORTMUX;
    PORT_t _PORTA;
    PORT_t _PORTB;
    PORT_t _PORTC;
    ADC_t _ADC0;
    ADC_t _ADC1;
    AC_t _AC0;
    AC_t _AC1;
    AC_t _AC2;
    DAC_t _DAC0;
    DAC_t _DAC1;
    DAC_t _DAC2;
    USART_t _USART0;
    TWI_t _TWI0;
    SPI_t _SPI0;
    TCA_t _TCA0;
    TCB_t _TCB0;
    TCB_t _TCB1;
    TCD_t _TCD0;
    SYSCFG_t _SYSCFG;
    NVMCTRL_t _NVMCTRL;
    SIGROW_t _SIGROW;
    FUSE_t _FUSE;
    LOCKBIT_t _LOCKBIT;
    USERROW_t _USERROW;
} _test_io_t;

extern _test_io_t _test_io;

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

#define VPORTA  (_test_io._VPORTA)
#define VPORTB  (_test_io._VPORTB)
#define VPORTC  (_test_io._VPORTC)
#define RSTCTRL (_test_io._RSTCTRL)
#define SLPCTRL (_test_io._SLPCTRL)
#define CLKCTRL (_test_io._CLKCTRL)
#define BOD     (_test_io._BOD)
#define VREF    (_test_io._VREF)
#define WDT     (_test_io._WDT)
#define CPUINT  (_test_io._CPUINT)
#define CRCSCAN (_test_io._CRCSCAN)
#define RTC     (_test_io._RTC)
#define EVSYS   (_test_io._EVSYS)
#define CCL     (_test_io._CCL)
#define PORTMUX (_test_io._PORTMUX)
#define PORTA   (_test_io._PORTA)
#define PORTB   (_test_io._PORTB)
#define PORTC   (_test_io._PORTC)
#define ADC0    (_test_io._ADC0)
#define ADC1    (_test_io._ADC1)
#define AC0     (_test_io._AC0)
#define AC1     (_test_io._AC1)
#define AC2     (_test_io._AC2)
#define DAC0    (_test_io._DAC0)
#define DAC1    (_test_io._DAC1)
#define DAC2    (_test_io._DAC2)
#define USART0  (_test_io._USART0)
#define TWI0    (_test_io._TWI0)
#define SPI0    (_test_io._SPI0)
#define TCA0    (_test_io._TCA0)
#define TCB0    (_test_io._TCB0)
#define TCB1    (_test_io._TCB1)
#define TCD0    (_test_io._TCD0)
#define SYSCFG  (_test_io._SYSCFG)
#define NVMCTRL (_test_io._NVMCTRL)
#define SIGROW  (_test_io._SIGROW)
#define FUSE    (_test_io._FUSE)
#define LOCKBIT (_test_io._LOCKBIT)
#define USERROW (_test_io._USERROW)
