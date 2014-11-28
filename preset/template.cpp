//${src_file_name}

#define F_CPU 4000000UL
#include <avr/io.h>
#include <util/delay.h>


int main(void){
    // put your main code here:
    DDRC=0xFF;

    while(1){
        PORTC^=_BV(PC0);
        _delay_ms(120);
    }
}
