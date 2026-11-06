# CPS et mises à jour : différences PRO, PLUS et firmwares libres

## 1. Deux branches GD32, pas un seul firmware

| Propriété | D578UV PRO étudié | D578UV PLUS observé |
| --- | --- | --- |
| MCU | GD32F303, confirmé sur le matériel | GD32F303, confirmé par observation de l'utilisateur |
| Application étudiée | GD32 V1.21 | Branche GD32 V2.08, identité et layout à comparer |
| Carte RF airband | Connecteur de la carte fille supplémentaire absent sur PRO observé | Carte fille sur la RF observée, référence de puce `KT0905R/KT09S5R` non tranchée |
| Carte BT | Support `D868BT-SP` et module blindé à investiguer | Carte BT à investiguer par révision |
| USB et CPS | VID/PID 28E9:018A et protocole observés dans l'application V1.21 | Même famille MCU, **pas de validation du même protocole exact dans notre banc** |
| Codeplug NAND | Premiers canaux V1.21 décodés partiellement | À comparer par fichier/capture de lecture V2.08 |

Référence des versions officielles : [AnyTone USA](https://anytoneusa.com/Downloads/) et [fabricant](https://www.anytone.net/download). Le fabricant distingue PRO `1.xx` et PLUS `2.xx`. Les informations sur **le processeur identique** sont des observations du poste, pas une preuve de compatibilité binaire.

## 2. Trois opérations souvent confondues

1. **CPS / codeplug** : `PROGRAM`, `R`, `W`, `END` sur la connexion USB CDC normale ; données utilisateurs et réglages selon les adresses demandées.
2. **MCU Update** : mode firmware spécial, outil fabricant, en général fichier manifeste `.spi` puis `.CDI`/`.CDD`, commande `UPDATE` et transport propre. Le choix de branche GD32/AT et du modèle est déterminant.
3. **Mise à jour baseband** : chaîne de communication avec le SCT3258/DMR (SCT_PORT et firmware spécifique). Ce n'est pas le même bootloader ni le même stockage que le GD32.

Ne pas déduire des captures CPS que le bootloader se programme avec `W` et `END`. Les règles de récupération, de calibration et de redémarrage sont différentes.

## 3. Clients externes utiles

- [qdmr](https://github.com/hmatuschek/qdmr) : éditeur GPL-3 avec interfaces AnyTone spécifiques. Référence de travail pour le protocole et les modèles D578UV/D578UVII.
- [dmr-tools/codeplugs](https://github.com/dmr-tools/codeplugs/tree/master/d578uv) : données de structure pour le codeplug D578, versionnées, utiles pour recouper les offsets et champs.
- [AnyTone_CPS Linux](https://github.com/hardenedpenguin/AnyTone_CPS) : profil de modèle `d578uv_v1.21`, flux USB et import/export `.atcp`. Ne pas intégrer directement son code GPL dans un fichier non compatible sans vérifier les obligations.
- [AesApp WebCPS](https://cps.aes.app/manual/en/about) : documentation du WebCPS ; son propre support distingue les D578 PLUS en 2.xx des branches PRO en 1.xx. Cela concerne **cet outil**, pas une impossibilité fondamentale de décoder le PRO.

## 4. OpenGD77 et l'option d'interopérabilité

Le protocole du CPS OpenGD77 n'est pas le protocole AnyTone OEM. Il utilise lui aussi un transport série et des commandes commençant par certaines lettres ASCII (`R`, `W`, `X`, `C`), mais la trame, les zones et la translation d'adresses sont différentes.

Un firmware autonome OpenD578 peut soit :

- implémenter un sous-ensemble strictement identifié du **protocole AnyTone OEM** pour la compatibilité avec les clients existants ; ou
- implémenter un **shim OpenGD77** avec une image de codeplug adaptée ; ou
- proposer un protocole propre avec un outil de programmation dédié.

Ces choix ne sont pas simultanément interchangeables. La première livraison doit avoir une identité de modèle explicite et des tests indépendants avant de débloquer des écritures. Conserver une commande de diagnostic distincte du flux CPS : un `printf` au milieu d'une réponse binaire corrompt le protocole.

## 5. Politique de versions proposée

Pour chaque matériel documenté, tenir : `board_revision`, `mcu_model`, `application_version`, `usb_vid_pid`, `cps_schema`, `nand_map_version`, `baseband_firmware`, `bluetooth_firmware`, `module_variant`, `evidence`. Une mise à jour d'un champ n'implique **aucun** changement automatique des autres.

Le PLUS ne doit être autorisé à écrire des données OEM que lorsque sa carte NAND, son identity et ses réponses sont caractérisées séparément.
