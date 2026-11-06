# Hardware abstraction and board drivers

Place standalone MCU drivers here after verifying the target board GPIO and timing.
Avoid OEM RAM offsets and manufacturer function addresses as runtime dependencies.

## Nouveaux périphériques RF et audio

Les contrats de pilotes et leur niveau de vérification figurent dans [PILOTES_RDA_QA_BH_U2429_AUDIO.md](../../docs/firmware/PILOTES_RDA_QA_BH_U2429_AUDIO.md). Aucune constante de calibration RF n'est inscrite comme valeur universelle. Les premières fonctions seront testées hors poste jusqu'à identification physique des GPIO.
