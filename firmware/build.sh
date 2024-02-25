set -e

CC="${CC:-gcc}"
AVR_GCC="${AVR_GCC:-avr-gcc}"
AVR_OBJCOPY="${AVR_OBJCOPY:-avr-objcopy}"

source build.local.sh || true

rm -rf build/

# Build actual binary

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

# Grab include path from avr-gcc and create delegating headers

mkdir build/include_next/
AVR_INCLUDE_PATH=""
while read -r dir
do
    if [[ -d "$dir" ]]; then
        AVR_INCLUDE_PATH="$AVR_INCLUDE_PATH -I$dir"
        for file in avr/io.h; do
            if [[ -f "$dir/$file" ]]; then
                mkdir -p build/include_next/$(dirname $file)
                echo "#include \"$dir/$file\"" > build/include_next/$file
                break
            fi
        done
    fi
done < <($AVR_GCC -Wp,-v /.c 2>&1)

# Build and run unit tests

mkdir build/tests
fail=0
for test in tests/*.c; do
    $CC -Itests/support/ -Ibuild/ $AVR_INCLUDE_PATH -Isrc/ -Wall -Werror -DUNITTEST -D__AVR_ATtiny1616__ tests/support/test.c $test -o build/${test}_runner
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

# Extract binary and show size

$AVR_OBJCOPY -O binary build/encodering.elf build/encodering.bin

ls -l build/encodering.bin
