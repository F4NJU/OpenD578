#ifndef OPEND578_SERIAL_COMMAND_ENCODERS_H
#define OPEND578_SERIAL_COMMAND_ENCODERS_H
#include <stdbool.h>
#include <stdint.h>

/* Encodage logique de mots constructeur, SANS accès GPIO, radio ni mémoires.
 * Toute connexion aux broches du D578 reste à identifier/valider. */
bool bh2226_build_dac_word(uint8_t channel_1_to_8, uint8_t value, uint16_t *out_word);

/* Produit D0..D10 dans cet ordre. Niveau logique D0=0 : 2 canaux,
 * D0=1 : un seul canal choisi par D1=0/1 ; volume 0..83 = atténuation dB.
 * Encodage datasheet, application sur poste NON vérifiée. Pas de code mute. */
bool u2429_build_volume_bits(bool both_channels, bool channel_2,
                             uint8_t attenuation_db, uint8_t bits_d0_to_d10[11]);
#endif
