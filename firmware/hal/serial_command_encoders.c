#include "serial_command_encoders.h"

bool bh2226_build_dac_word(uint8_t channel_1_to_8, uint8_t value, uint16_t *out_word)
{
    if (!out_word || channel_1_to_8 < 1 || channel_1_to_8 > 8)
        return false;
    /* D8..D11 = selection de canal 1..8, D0..D7 = code 8 bits.
     * Le décalage série réel est MSB-first suivant la fiche ROHM. */
    *out_word = (uint16_t)(((uint16_t)channel_1_to_8 << 8) | value);
    return true;
}

bool u2429_build_volume_bits(bool both_channels, bool channel_2,
                             uint8_t attenuation_db, uint8_t bits_d0_to_d10[11])
{
    if (!bits_d0_to_d10 || attenuation_db > 83)
        return false;
    /* Table UTC U2429 : ATT1 code 21 pour 0 dB, décrément par pas de 4 dB.
     * ATT2 code 3 pour 0 dB, décrément par pas de 1 dB.
     * Ceci n'inclut pas le code de coupure -infinity. */
    const uint8_t coarse = (uint8_t)(21 - attenuation_db / 4);
    const uint8_t fine = (uint8_t)(3 - attenuation_db % 4);
    bits_d0_to_d10[0] = both_channels ? 0 : 1;
    bits_d0_to_d10[1] = channel_2 ? 1 : 0;
    for (unsigned i = 0; i < 5; ++i)
        bits_d0_to_d10[i+2] = (uint8_t)((coarse >> i) & 1u);
    for (unsigned i = 0; i < 2; ++i)
        bits_d0_to_d10[i+7] = (uint8_t)((fine >> i) & 1u);
    bits_d0_to_d10[9] = 1;
    bits_d0_to_d10[10] = 1;
    return true;
}
