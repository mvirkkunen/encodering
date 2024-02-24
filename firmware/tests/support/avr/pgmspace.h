#define PROGMEM

static inline unsigned char pgm_read_byte(const void* ptr) {
    return *(unsigned char*)ptr;
}
