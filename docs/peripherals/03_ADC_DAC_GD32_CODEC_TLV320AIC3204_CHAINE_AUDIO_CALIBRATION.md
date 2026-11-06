# 03 - ADC/DAC : GD32 ADC0, BH2226FV, TLV320AIC3204 et chemin audio

> **RECONSTITUTION du 05/11/2026.** Aucun des octets du document historique de meme nom n'est pretendu recuperer. On separe ici des circuits bien distincts, leurs bus, les acces OEM releves et les inconnues.

## 1. Ne pas confondre quatre fonctions

| Fonction | Composant | Destination et protocoles | Etat sur D578 |
| --- | --- | --- | --- |
| ADC tension lente | **ADC0 interne au GD32F303VKT6** | Echantillonnage de contacts et potentiometres par GPIO analogiques + DMA | Configuration et voies de lecture etudiees dans OEM/banc |
| DAC 8 sorties controle analogique | **ROHM BH2226FV-E2** (marquage H2226, SSOP-B16 confirme utilisateur) | 8 sorties 8 bits, mots serie 12 bits / interface 3 fils | Composant identifie, destination des 8 sorties inconnue |
| CODEC PCM/analogique | **TLV320AIC3204** TI | ADC + DAC audio, filtres, gains, interface serie I2S et commandes registre | Composant de famille D578 ; codec modele via SCT3258, pinout sur PCB a confirmer |
| Controle du niveau analogique | **UTC U2429G** | Attenuateur 2 canaux et commande 11 bits CLOCK/DATA | Identification du composant, GPIO et trajets exacts inconnus |

Le **SGM8272** est un double amplificateur operationnel analogique et le **MC34119G** un amplificateur de haut-parleur, pas des bus de registres a piloter directement. Les amplis **YD1517P (PRO)** et **PA1517G (PLUS)** restent des elements de puissance audio a commander par voies analogiques / standby.

## 2. ADC0 du GD32 et acquisition DMA

- Base peripherique ADC0 retrouvee : `0x40012400` ; des traces du convertisseur atteignent `0x4001244C`.
- Les entrees de facade de la revision etudiee sont compatibles avec `PB0 ADC8`, `PB1 ADC9` pour des reseaux de touches, `PC2 ADC12`, `PC5 ADC15` pour les deux potentiometres de volume.
- L'attribution physique A/B et le tableau complet `seuil ADC -> touche` doivent suivre les rapports d'acquisition ; une correspondance logicielle n'est pas une mesure de continuite.
- Le banc possede `bench/adc_dma.py`, `bench/emulate_adc_v121.py`, `bench/lab_inputs.py` et des tests de scenarios. Le test ADC **ne represente pas** une conversion audio AIC3204.
- **Respecter** ADC sample time, sequence de canaux, DMA (taille/type/increment), alignement, timeout, filtrage et hysteresis ; les seuils reperes dans l'OEM peuvent dependre du reseau resistif et de la tension de reference.

### Contrat recommande pour un pilote OpenD578

1. Configurer l'horloge du ADC et les entrees analogiques; initialiser VREF et verifier plage admissible avant chaque interpretation de valeur.
2. Capturer un snapshot des quatre voies sans bloquer le scheduler; proteger contre DMA partiellement rafraichi.
3. Debouncer touches sur plusieurs acquisitions et conserver l'etat de repos/erreur de conversion distinct d'un appui.
4. Convertir chaque potentiometre en pourcentage ou dB **apres identification de la courbe et des limites du circuit U2429**; ne pas programmer un autre bus analogique avec un chiffre ADC brut.
5. Au redemarrage, valider la calibration locale et ne pas ecraser les valeurs usine dans NAND/Flash si leur format n'est pas compris.

## 3. BH2226FV, sorties DAC et plages de tension

Le BH2226FV-E2 est un composant 8 bits x 8 canaux, **SSOP-B16**, alimentation specifiee **2,7 a 5,5 V**, interface serie 3 fils. Un mot ordinaire contient une selection de canal et une valeur 8 bits, **12 bits au total** ; la table de commandes initiales doit etre lue dans la notice ROHM (power down, DAC/I/O). Une encodeur logiciel pur existe dans `firmware/hal/serial_command_encoders.c` et ses tests, **sans acces GPIO**.

| Sortie | Alias datasheet | Destination sur le D578 |
| --- | --- | --- |
| 1 | DA1 | **Non tracee** |
| 2 | DA2 | Non tracee |
| 3 | DA3 | Non tracee |
| 4 | DA4 | Non tracee |
| 5 | DA5 | Non tracee |
| 6 | DA6 | Non tracee |
| 7 | DA7 | Non tracee |
| 8 | DA8 | Non tracee |

Par hypothese d'architecture, certaines sorties pourraient piloter les varicaps ou amplificateurs de commande RF. **Cela ne prouve aucun lien** vers le PA ou les frequences. Les mesures doivent documenter DAx -> passifs -> SGM8272 et/ou varicaps et leur variation en reception ordinaire, sans emission.

## 4. TLV320AIC3204 et passage par SCT3258

TI documente un codec audio faible puissance avec conversion ADC/DAC et systeme de registres pagines. Sur les radios AnyTone avec SCT3258, RadioFoundry indique que le **SCT3258 controle le codec** via ses propres messages de configuration et sert de liaison I2S pour les echantillons ; le GD32 ne doit pas etre suppose connecter directement les pins SCL/SDA du codec.

Dans notre banc :

- `bench/sct_hpi.py` reconnait des paquets `type 0x40` de **codec-bypass** sous conditions de protocole, et produit des triplets `(page, registre, valeur)` dans `codec_writes`.
- Le registre de page `0` du model n'accepte que certaines valeurs, restriction du **modele teste** et non une limite generale TI.
- Des dizaines de commandes de gain, mute et equalisation existent dans la pile OEM / SCT ; **le banc ne traite pas les echantillons PCM comme un DSP physiquement fidele**.
- L'interface codec peut etre I2C en theorie, mais **le chemin de commande reel par paquets HPI** change l'architecture des pilotes.

### Pour reconstruire une table de reglages audio

Capturer la sequence complete apres reset en reception, apres changement FM/DMR, changement d'ampli poste/micro, variation de volume, activation Bluetooth et mutation des menus. Conserver ordre, page, reg, valeur, delai et etat du SCT. Faire un diff de transactions entre deux conditions, puis retrouver la signification chez TI. **Ne pas injecter une image de registre prise dans un autre poste** sans qualification des gains et du chemin audio.

## 5. Volume, mute et selection haut-parleur : elements de preuve internes

La notice utilisateur du banc V11.8 fournit une trace plus precise que la seule datasheet :

- `Speaker Mode` stocke son selecteur OEM en RAM a `0x2000431B` (0 = Mic Spk, 1 = Radio Spk, 2 = Both) ; ce n'est **pas** une adresse de registre materiel.
- Routine OEM `0x08090A86` associee a la commande **PA7** : `Mic Spk` PA7 haut, `Radio Spk` PA7 bas, `Both` PA7 bas en reception active.
- Registre RF **banque 1/page 0/adresse 0x25**, bit 4, observe dans les routines `0x08072514`, `0x08072544` / `0x08070A8C` ; distinct de la sortie PA7.
- Ces sorties paraissent gouverner deux mute de haut-parleur, mais leur continuite vers YD1517P, MC34119G ou U2429 **n'a pas ete mesuree**.
- Lors de la comparaison des menus, le nombre de configuration codec est reste constant (24 dans une simulation) ; cela ne prouve pas que le codec n'intervient jamais dans d'autres modes.

Attention aux bornes `SP+` et `SP-` du microphone : liaison differentielle possible, `SP-` ne doit pas etre mis a GND par supposition.

## 6. Parametres usine, offsets et calibration

La cartographie NAND historique situe la calibration active et ses copies vers `0x02F00000..0x02F80679`, et la configuration locale entre `0x02FA0000..0x02FDFFFF`. Des lectures physiques montrent des **copies proches** dans ces zones. Ces adresses sont des espaces logiques NAND, **pas** une structure de registre ADC0 ni des registres I2S. Leur codage reste en partie inconnu.

Une documentation de calibration exploitable doit contenir : variante et numero de carte, valeur brute, unite, graduation, methode de mesure, conditions de temperature/tension, offset et gain, adresse NAND, duplication/CRC/ECC, initiateur d'ecriture et menu OEM associe. Les valeurs de polarisation PA et les references RF ne doivent jamais etre recalibrees sur la base d'une comparaison heuristique de deux fichiers.

## 7. Tests et limites de pilotage

- Ecrire et tester des fonctions **pures** de decode ADC, filtrage touche, encodage BH2226 et U2429; ne brancher le GPIO reel qu'apres mesures et extraction d'un firmware HAL autonome.
- Utiliser les scenarios du banc pour les transitions Speaker Mode ; verifier dans un autre temps les niveaux physiques de PA7/CI audio.
- Decoder les commandes codec via HPI en **lecture seule sur fichier de trace** ; ne pas reprogrammer la page 0 au hasard.
- Toutes les constantes d'adresses SRAM OEM sont propres a la version **PRO GD32 V1.21** et ne doivent pas etre reutilisees comme API du firmware alternatif.

## 8. Sources

- Projet : `../NOTICE_CHANGELOG_MICROPHONE_V11_8.md`, `../FACADE_GPIO_BOUTONS_CODEUR_VOLUMES_ET_ECLAIRAGES.md`, `../04_RAM_ROUTINES_UI_RF_ET_BROCHAGE.md`, `../hardware/BH2226_H2226_DAC_RF.md`, `../hardware/VOLUME_U2429G.md`, `../hardware/AUDIO_MC34119_SGM8272.md`, `bench/sct_hpi.py`, `bench/adc_dma.py`.
- ROHM BH2226FV : <https://www.rohm.com/products/data-converter/d-a-converters/8bit-d-a/bh2226fv-product>.
- TI TLV320AIC3204 : <https://www.ti.com/product/TLV320AIC3204>.
- RadioFoundry, chemin codec via SCT : <https://radiofoundry.org/docs/spec/hardware-anytone>.
- UTC U2429G : <https://www.unisonic.com.tw/uploadfiles/836/part_no_pdf/U2429.pdf>.
