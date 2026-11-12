# Captures F4EGM — vérification et premier essai réel

Date : 12 novembre 2026. Dépôt amont : Telectroboy/OpenD578, commit
`391490e21ebedd0edf295d4ed4ccd63ab8f16054`.

## Entrées authentifiées

Chemin exact : `browser-bench/samples/F4EGM.zip` (respecter les majuscules).
Taille ZIP : 8 812 776 octets. SHA256 de l'archive :
`cc4f96fb71be8373ca5f5d38c93419db3cd1766098f1f7bd378d83bce44b66c9`.
Son identifiant de blob Git a aussi été recalculé :
`f3f7f31eb68f47d89016a49badb70ca1c2f66fec`.

| Capture | Octets | SHA256 |
| --- | ---: | --- |
| full_flash_pass1.bin | 3145728 | e2f2483baf60e2bfcab656e25e949670713222591ef4d611d6089054819a750e |
| nand_main_256MiB.bin | 268435456 | 329d22165d234bf0df043e62af11397dea96327925b9db18f3c354230ff40945 |
| nand_oob64_8MiB.bin | 8388608 | 9a999b9fd13a02b45ed4d38e68f9e9c7d1095994c751e36e04f4a62b2e4c5106 |
| nand_ecc_status_128KiB.bin | 131072 | b40ebd3ebc3923f01d9d98a52a3b019b65785641ba76687127678b788ea793c6 |

Ces empreintes correspondent aux constantes du banc. `prepare()` extrait aussi
une application V1.21 de 1 020 300 octets, SHA256
`02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a`.

Le vérificateur ajouté ne nécessite aucune dépendance externe et ne modifie ni
n'extrait les entrées :

```sh
python tools/verify_f4egm_archive.py /chemin/F4EGM.zip
```

Deux tests unitaires accompagnent l'outil ; ils ne sont pas des essais firmware.

## Environnement Python préparé

Python portable officiel 3.13.5, isolé du système. Paquets binaires installés et
imports vérifiés : unicorn 2.1.4, capstone 5.0.9 (version de distribution), pillow
13.0.0, numpy 2.3.5, pyserial 3.5. Aucune compilation NumPy nécessaire.
La version interne affichée par le module capstone peut différer de la métadonnée
de sa distribution ; les dépendances épinglées ont été contrôlées par métadonnée.

## Essais et limites distinctes

**Actualisation : fichier SCT retrouvé et validé.** F4EGM l'a fourni séparément
dans `browser-bench/samples/SCT3258TD_UpdateFlash_V2_01_07BF.hex` (amont
`8c7f2b5ff4df83fa9bef7a64fc5a597d61ace57f`). Taille 603 102 octets, SHA256
`d5ada473af891b6c707978f0b9dde81324afcc4af27348d3bcdf70615ab19407`.
`check_inputs()` et `prepare_sct_reference()` passent. Le blocage d'entrée du
paragraphe 1 ci-dessous est historique et résolu ; le ZIP conserve bien quatre
captures et le SCT est un cinquième fichier séparé. Ce contrôle de référence
n'implique pas de développer ou de qualifier le DMR.

Après ajout du SCT, `run_lcd.py` (moteur Python, sans accélération LCD native,
budget 200 000 instructions) s'arrête normalement sur `instruction_budget`,
PC `0x0808ADFA`, avec sept buffers NAND, aucun pixel et sans lecture CPS.
C'est une exécution OEM limitée réussie, pas un démarrage complet qualifié.

1. **Banc Python OEM historique (`run_lcd.py`)** : sa vérification préalable
   demande encore `SCT3258TD_UpdateFlash_V2_01_07BF.hex`. Ce fichier n'est pas
   dans le ZIP. Le dossier de quatre captures ne satisfait donc pas à lui seul
   `check_inputs()` pour ce parcours. Le bootstrap SCT de 2048 octets présent dans
   la Flash ne remplace pas cette référence complète de 603 102 octets.
2. **Modèle matériel Python (`run_hardware.py`)** : premier essai arrêté
   volontairement au budget de 20 000 instructions ; puis budget de 1 000 000
   avec la touche POWER maintenue. Le second exécute réellement 69 119 instructions
   avant `RF SPI has multiple active chip selects` (catégorie `execution_boundary`),
   PC `0x0800870C`, écriture `0x33111144` sur GPIOB `0x40010C00`. Aucun pixel LCD
   n'avait encore été produit. Cette limite est conservée, pas contournée.
3. **WebAssembly existant** : initialisation et chargement effectués, essai ensuite
   interrompu ; aucune lecture USB/CPS complète obtenue. Ce n'est pas une preuve
   de panne du banc navigateur ni une validation réussie.

L'essai matériel charge la Flash à `0x08000000`, utilise le vecteur applicatif
`0x08006000`, les trois captures NAND et le bootstrap SCT extrait de la Flash à
l'offset `0xF56CC` (2048 octets). Le moteur est `python`, sans bibliothèque native
compilée. Les données NAND originales sont ouvertes par l'overlay du banc ; aucun
état NAND persistant ni transfert CPS d'écriture n'a été demandé. Les empreintes
des quatre copies source sont recontrôlées après les essais.

Il reste à clarifier avec F4EGM le parcours recommandé pour ces quatre fichiers
(banc navigateur actuel ou Python historique) et à résoudre les prérequis/limites
de ce parcours avant de qualifier identification, lecture et fermeture END du CPS.
Ce rapport ne contient ni noms de canaux ni données personnelles des captures.
