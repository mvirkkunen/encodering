set -e

AVR_GCC="${AVR_GCC:-avr-gcc}"

source build.local.sh || true

$AVR_GCC $AVR_CFLAGS -mmcu=attiny1616 -DF_CPU=16000000UL -Os src/*.c -o encodering.elf
