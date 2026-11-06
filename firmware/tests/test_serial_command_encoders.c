#include "../hal/serial_command_encoders.h"
#include <assert.h>
#include <stddef.h>
#include <stdint.h>

int main(void)
{
    uint16_t word=0;
    assert(bh2226_build_dac_word(1,0x80,&word) && word==0x180);
    assert(bh2226_build_dac_word(8,0xFF,&word) && word==0x8FF);
    assert(!bh2226_build_dac_word(0,0,&word));
    assert(!bh2226_build_dac_word(9,0,&word));
    assert(!bh2226_build_dac_word(1,0,NULL));
    uint8_t bits[11];
    assert(u2429_build_volume_bits(true,false,0,bits));
    assert(bits[0]==0 && bits[1]==0);
    /* D2-D6 0dB: H L H L H, D7-D8: H H */
    assert(bits[2]==1 && bits[3]==0 && bits[4]==1 && bits[5]==0 && bits[6]==1);
    assert(bits[7]==1 && bits[8]==1 && bits[9]==1 && bits[10]==1);
    assert(u2429_build_volume_bits(false,true,80,bits));
    /* D2-D6 -80dB: H L L L L, D7-D8 0dB: H H */
    assert(bits[0]==1 && bits[1]==1 && bits[2]==1 && bits[3]==0 && bits[4]==0 && bits[5]==0 && bits[6]==0);
    assert(bits[7]==1 && bits[8]==1);
    assert(u2429_build_volume_bits(false,false,83,bits));
    assert(bits[2]==1 && bits[3]==0 && bits[4]==0 && bits[5]==0 && bits[6]==0);
    assert(bits[7]==0 && bits[8]==0 && bits[9]==1 && bits[10]==1);
    assert(!u2429_build_volume_bits(true,false,84,bits));
    assert(!u2429_build_volume_bits(true,false,0,NULL));
    return 0;
}
