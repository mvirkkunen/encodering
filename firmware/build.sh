set -e

CC="${CC:-gcc}"
AVR_GCC="${AVR_GCC:-avr-gcc}"
AVR_OBJCOPY="${AVR_OBJCOPY:-avr-objcopy}"

source build.local.sh || true

rm -rf build/

mkdir build/
$AVR_GCC $AVR_CFLAGS \
    -mmcu=attiny1616 \
    -DF_CPU=20000000UL \
    -Os \
    -Wall \
    -Werror \
    src/*.c \
    src/*.S \
    -o build/encodering.elf

mkdir build/tests
fail=0
for test in tests/*.c; do
    $CC -Itests/support/ -Isrc/ -Wall -Werror -DUNITTEST tests/support/test.c $test -o build/${test}_runner
    echo ${test}:
    if ! build/${test}_runner; then
        fail=1
    fi
    echo
done

if [ "$fail" == "1" ]; then
    echo "Unit tests failed"
    exit 1
else
    echo "Unit tests passed"
fi

$AVR_OBJCOPY -O binary build/encodering.elf build/encodering.bin

ls -l build/encodering.bin
