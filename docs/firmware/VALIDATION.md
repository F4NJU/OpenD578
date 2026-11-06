# Conditions de validation et de publication firmware

La publication de sources et de tests ne constitue jamais une autorisation d'ecrire la Flash du poste.

## Blocages avant installation sur poste

1. Carte cible et empreinte exactes du firmware verifiees; bootloader et restauration qualifies.
2. Cablage GPIO du pilote autonome et niveaux electriques mesures ou revus; aucune sortie inconnue forcee.
3. Moteur LCD, interruptions, timings et arbitre des ressources stables; pas d'utilisation d'adresses de fonctions RAM constructeur comme API.
4. NAND : lecture seule dans le banc, regions de calibration sauvegardees et processus de restauration prouve avant toute ecriture.
5. Frequences RX/TX, PTT, busy, puissance, temperature, protec. antenne et sortie RF verifies sur equipements de mesure.
6. Simulation reproductible, tests de non-regression puis essais controle sur materiel; journaliser la revision carte et l'empreinte SHA-256.

Le depot n'inclut pas les images constructeur, dumps de Flash/NAND, parametres prives ni codeplug. Les notes de reverse engineering peuvent referencer leurs hashes pour garantir la reproductibilite.

Voir [boot et flash](../02_CPU_FLASH_BOOT_USB_SWD.md), [NAND](../03_NAND_LECTURES_ECC_CARTE.md), [calibration](../PROGRAMMING_AND_CALIBRATION.md), [limites](../07_ERREURS_CORRECTIONS_HYPOTHESES_ET_NO_GO.md).
