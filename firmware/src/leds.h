
#define LED_CYCLES_PER_SECOND (F_CPU / 256)

extern volatile uint8_t led_cycles;

void leds_init(void);
void leds_update(void);

