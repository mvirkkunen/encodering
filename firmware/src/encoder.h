#include <stdint.h>

extern volatile int8_t encoder_delta;

void encoder_init(void);
void encoder_poll_button(void);

