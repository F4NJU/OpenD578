# Calibration, NAND et variantes : éviter la transposition D868 vers D578

Sources : [RadioFoundry §4.4 et §5](https://radiofoundry.org/docs/spec/hardware-anytone), [notre NAND du D578](../../peripherals/01_NAND_SPI_CABLAGE_PILOTE_FORMATS_MEMOIRE.md), [carte mémoire V1.21](../../03_NAND_LECTURES_ECC_CARTE.md), [paramètres TEST](../../TEST_MODE_OPTIONS.md).

## 1. Ce que décrit effectivement RadioFoundry

La section 4 est intitulée **carte des broches du D868UV**. Dans son sous-chapitre NAND, RadioFoundry cite deux copies d'un ensemble de calibration à `0x02F60000` et `0x02F80000`, des tables UHF de 81 éléments et VHF de 39 éléments associées aux niveaux de puissance, ainsi qu'un petit enregistrement de 34 octets dupliqué vers `0x02501000` et `0x02521000`. Il s'agit de conclusions issues des images **D868** examinées par le projet.

Sur nos D578, la NAND physique est une `TC58CVG1S3HRAIG` de 2 Gbit. Les données que nous avons établies portent sur le format `main/OOB`, les commandes SPI et les zones occupées ; le guide historique VK7ZJA situe les calibrations radio dans une plage plus large vers `0x02F00000...0x02F80679` et les données de configuration vers `0x02FA0000...0x02FDFFFF`. **Ne pas effacer ces plages avec une reconstitution 868.**

| Domaine | Référence RadioFoundry D868 | OpenD578 D578 | Décision |
|---|---|---|---|
| Flash externe | GigaDevice/Toshiba selon lot, typiquement 1 Gbit | Toshiba 2 Gbit, main 256 MiB | Utiliser le pilote NAND propre à la puce |
| Calibration PA | Tables par MHz et par puissance vers 0x02F60000 avec backup vers 0x02F80000 | Zones autour de 0x02F00000 à étudier sur capture D578 | Comparer par signatures, ne pas recopier offset |
| Puissance RF | DAC MCU PA4 sur D868 | D578 avec BH2226FV et contrôles RF identifiés dans le banc | Reconstituer courbe à partir des écritures OEM D578 |
| Paramètres locaux | Record 34 octets à 0x02501000 et 0x02521000 | Zones propres D578 et validation CPS du codeplug | Ne pas attribuer ces offsets au D578 |
| Bad blocks / ECC | Driver SPI NAND avec repli | Capture brute + statut ECC disponible | Gérer ECC et sauvegarder OOB |

## 2. Plan concret de corrélation sans écriture

1. Identifier le marqueur du firmware, l'empreinte du dump NAND et la variante précise avant chaque comparaison.
2. Lire **sur une copie** les secteurs connus d'alignement ; calculer SHA-256 et rechercher les répétitions A/B.
3. Cartographier les tables par longueur, checksum et éventuels marqueurs, sans fixer les valeurs nominales d'un autre poste.
4. Dans le banc OEM, modifier seulement des **stimuli de test**, comme fréquence de réception, bande et réglage UI existant, puis relever les lectures NAND et les écritures vers QA4818N/BH2226FV/SCT3258.
5. Associer `FQCA`, `PA*`, `BPF*`, `AGC*`, `SQTH*`, `RSSI*` et tests BER à une donnée **lue** puis à une routine constructeur, plutôt qu'à une adresse présumée.
6. Exiger un export original et une restauration vérifiée avant toute opération d'écriture sur le poste réel. Aucun chemin d'écriture des calibrations n'est activé par ces documents.

## 3. Fichiers de preuve à conserver

Un paquet de mesure devrait contenir `unit.json` (modèle, GD/AT, version, NAND ID), `capture_manifest.json`, `nand_hashes.json`, `nandslices.json` (positions uniquement), `oem_trace.json` et la matrice `calibration_to_gpio.csv`. Les dumps bruts et secrets restent dans le stockage privé. Cela préserve les résultats antérieurs sans exposer de données constructeur ni valeurs d'étalonnage personnelles sur GitHub.
