
#define LED_CYCLES_PER_SECOND (F_CPU / 256)

extern volatile uint16_t led_cycles;

void leds_init(void);
