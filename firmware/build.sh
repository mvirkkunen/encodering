set -e

AVR_GCC="${AVR_GCC:-avr-gcc}"
AVR_OBJCOPY="${AVR_OBJCOPY:-avr-objcopy}"

source build.local.sh || true

$AVR_GCC $AVR_CFLAGS \
    -mmcu=attiny1616 \
    -DF_CPU=20000000UL \
    -Os \
    -Wall \
    -Werror \
    src/*.c \
    src/*.S \
    -o encodering.elf

$AVR_OBJCOPY -O binary encodering.elf encodering.bin

ls -l encodering.bin
