#include <avr/io.h>

; typedef struct led_schedule_t {
;     uint8_t port_dir[3];
;     uint8_t next_compare;
; } led_schedule_item_t;
;
; [GPIOR1:GPIOR0] is pointer to current item

.global TCA0_CMP0_vect
TCA0_CMP0_vect:
    ; save registers
    in r15, SREG
    push r15
    push r16
    push r17
    push Xl
    push Xh

    ; get schedule pointer
    in Xl, GPIOR0
    in Xh, GPIOR1

next:
    ; update pins
    ld r16, X+                    ; 1
    out VPORTA_DIR, r16           ; 2
    ld r16, X+                    ; 1
    out VPORTB_DIR, r16           ; 2
    ld r16, X+                    ; 1
    out VPORTC_DIR, r16           ; 2

    ; get next timer compare value
    ld r16, X+                    ; 2

    ; check timer counter, if already past next compare value, process immediately
    lds r17, TCA0_SINGLE_CNT      ; 2
    cp r17, r16                   ; 1
    brge next                     ; 2 if taken, 1 if not
    ; total cycles from next to here is 16 cycles so should not fall behind

    ; clear timer compare flag
    ldi r16, TCA_SINGLE_CMP0_bm   ; 1
    sts TCA0_SINGLE_INTFLAGS, r16 ; 2

    ; update timer compare value - this may pend the interrupt again before the ISR returns which is OK
    ; cycles from CNT load to here is less than 16 so ticks should not be missed
    sts TCA0_SINGLE_CMP0, r16     ; 2

    ; save schedule pointer
    out GPIOR0, Xl
    out GPIOR1, Xh

    ; restore registers
    pop Xh
    pop Xl
    pop r17
    pop r16
    pop r15
    out SREG, r15

    reti
