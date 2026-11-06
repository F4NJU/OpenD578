# Complements techniques tires de l'audit DB1IG / VK7ZJA

Ce document conserve uniquement les **nouveaux details techniques pertinents** et notre analyse de leur integration au D578. Ce n'est ni une copie de la page VK7ZJA ni une preuve que les menus de 2022 ont le meme nom dans les firmwares PRO GD32 V1.21 et PLUS actuels. Les elements valides par l'OEM dans `docs/hardware/VALIDATION_FONCTIONS_OEM.md` conservent leur statut.

Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Autres sources et renvois : [audit par source](AUDIT_CROISE_SOURCES.md).

## 1. Deux mecanismes distincts pour le microphone filaire

### 1.1. Mode de telecommande numerique connu

L'analyse executee du firmware OEM documente la liaison serie USART0 (GPIO PA9/PA10 dans le profil), les trames du microphone vers le poste sur 8 octets commencant par `0x41`, et les reponses/status de 16 octets commencant par `0x53`. Voir `docs/NOTICE_CHANGELOG_MICROPHONE_V11_8.md`. Ces donnees sont **validees par l'analyse OEM** et ne changent pas dans cet audit.

### 1.2. Mode `Level Detection` de la prise micro, ajoute par la source historique

Le guide historique mentionne une entree PTT par **resistance inseree entre les broches 1 et 8**, avec une valeur indiquee entre **1 et 2,2 kohms** et l'option CPS **`HandOpMode = Level Detection`**. Dans son schema de microphone de bureau, l'auteur insiste sur la separation de la masse microphone et de la masse logique et sur le conditionnement d'un electret.

**Consequences pour le firmware :**

- La pile de communication micro devra gerer explicitement deux profils : telecommande numerique du combiné et entree par niveau/impedance. Le GPIO du detection de niveau ne doit **pas** etre deduit du seul chemin USART0.
- Le profil choisi influence la logique du PTT et l'interpretation des touches du micro. Il faut relever, dans le code constructeur, la lecture de `HandOpMode` et le branchement vers le detecteur de niveau.
- Le guide signale un risque de passage accidentel en emission si l'ancien microphone numerique est laisse branche sous le mauvais profil. Pour OpenD578, **PTT doit etre inactif par defaut** si le type de micro ou le profil est inconnu.
- Ne pas bricoler de pontage direct entre les pins : la resistance et la configuration logicielle sont une condition de cet usage historique.

**Nouveau test sans RF :** relever en banc la valeur de la configuration OEM et le chemin d'entree PTT correspondant, sans alimenter le PA. La capture de la transition physique doit etre executee ulterieurement sur charge adaptee si necessaire.

## 2. Modes de demarrage, firmware de sous-modules et support de maintenance

La documentation historique donne plusieurs combinaisons qu'il ne faut pas fusionner sous une seule entree `UPDATE` :

| Demarrage historique | Sous-ensemble cible | Etat de documentation OpenD578 |
|---|---|---|
| `P2 + appui dial` | Ecran de reset | A rattacher au gestionnaire facade et a la machine d'etat OEM |
| `P3 + appui dial` | Diagnostic du module GPS | Nouveau chemin a comparer au driver NMEA et au modele GNSS |
| `P4 + appui dial` | MODE / TEST selon droits AT Options | **Deja analyse dans le firmware** : permissions NAND, routines OEM et comportement reel sur deux appareils |
| `P5 + appui dial` | Test avec Bluetooth (BHT) | Nouveau cas de test pour les interfaces D868BT-SP/ET12 |
| `P6 + appui dial` | Mise a jour LinkBoard Bluetooth | Distinguer transfert de donnees module et firmware MCU GD32 |
| `MENU + appui dial` | Mise a jour baseband SCT3258 | Nouvelle entree a relier au chargeur HPI existant |
| `EXIT + appui dial` | Diagnostic RSSI GPS | Verification possible de la gestion antenne/GNSS et UI |
| `PTT micro + appui dial` | Mise a jour firmware interne du microphone (Hand-Soft) | Ajouter une cible firmware separee du BT01 et du GD32 |
| `P1 + appui dial` | Mise a jour des ressources/icones (selon version) | A comparer au mode MCU UPDATE et au conteneur `.spi` |

Ces combinaisons sont **attribuees a la generation D578 decrite par VK7ZJA**. Dans notre branche, l'entree TEST P4+DIAL dispose deja de traces et d'une validation utilisateur ; les autres scenarios doivent etre recherches dans la table de dispatch de boot, sans declarer les fonctions OEM non fonctionnelles.

Voir `docs/TEST_MODE_OPTIONS.md`, `docs/02_CPU_FLASH_BOOT_USB_SWD.md`, `docs/peripherals/04_DMR_SCT3258_BOOTSTRAP_HPI_PAQUETS_CODEC_PARAMETRES.md`.

## 3. Cartographie de l'alignement et de la calibration RF

Le grand tableau historique permet d'organiser le contenu du menu de service **par type physique** plutot que de traiter tous les octets comme de simples `0..255` :

| Groupe | Identifiants historiquement documentes | Signification pour le futur firmware |
|---|---|---|
| Correction frequence | `FQCA` | Une correction fine de reference, distincte de la frequence de canal et du Doppler |
| Puissance UHF | `PAHU`, `PAMU`, `PALU`, `PASU` | Fourchettes par niveau Turbo/High/Medium/Low, a rapprocher du PA et de ses DAC |
| Puissance VHF | `PAHV`, `PAMV`, `PALV`, `PASV` | Calibration independante des quatre niveaux VHF |
| Deviation | `MODU`, `MODV`, `MODV2`, `CTCW`, `DCSW` | Modulation et tonalites a verifier sur analyseur, pas sur la seule courbe audio |
| Audio TX | `MIC`, `TONEU`, `TONEV2` | Gain micro et references de tons de test distincts des signaux de sortie HP |
| Filtrage de suivi A/B | `BPFLUA`, `BPFMUA`, `BPFHUA`, `BPFLUB`, `BPFMUB`, `BPFHUB` ; equivalents `V` | Points bas/moyen/haut par bande et par voie, probablement lies aux filtres accordables |
| Controle reception | `AGCUA`, `AGCUB`, `AGCVA`, `AGCVB`, `SQTHUA`, `SQTHUB`, `SQTHVA`, `SQTHVB`, `RSSIUA`, `RSSIUB`, `RSSIVA`, `RSSIVB` | Gains, seuils squelch et table RSSI propres aux voies |
| Tests numeriques | `D FSKL/M/H*`, `D 600Hz*`, `D 300Hz*`, `D 1031*`, `D BER*`, `D DIGI` | Voies de validation de modulation DMR, mesures BER et conditions de signal d'essai |
| Alimentation / divers | `VBAT`, `A OBH/OBL`, `D OBH/OBL`, `F1 A0` | Ne pas interpretter ni ecrire ces champs sans avoir reconstruit le chemin OEM correspondant |
| Receveur AM PLUS | `AM BPFL/BPFM/BPFH`, `AM AGC`, `AM RSIV` | Calibrations de la chaine AIRBAND supplementaire, distinctes du RDA5802N FM broadcast |

**Ce qui est deja valide dans OpenD578 :** le mode TEST existe sur le poste de l'utilisateur, les droits de menu ont ete decodes a `0x02FA0002/0x02FA0006`, la logique OEM d'entree a ete reconnue et les circuits RF fonctionnent en exploitation. Ceci ne signifie pas que les **correspondances octet NAND <-> groupe de calibration** sont deja connues pour toutes les versions.

**Prudence importante :** les nombres de la colonne `Typical value` publies par VK7ZJA illustrent le comportement de son unite, **pas celui des deux postes etudies**. Le champ `VBAT` est explicitement critique. Aucune fonction de reecriture de calibration ne sera produite a partir de cette table seule. Notre futur schema doit permettre d'importer les valeurs mesurees et d'enregistrer des hashes avant/apres sans les copier sur un second appareil.

La suite utile est : (1) lire en RAM, dans le modele OEM, le parametre de menu selectionne ; (2) identifier les fonctions qui chargent les zones d'alignement NAND ; (3) comparer aux changements de registres QA4818N et sorties BH2226FV ; (4) tester sans emission les gains et les filtres, puis seulement ensuite sur banc de mesure RF controle.

## 4. La chaine RF historique explique mieux les etages sur le PCB

Les deux voies analogiques du D578 sont **simultanees** ; elles ne reposent pas sur une simple alternance de deux frequences comme certains portables. Le site signale neanmoins qu'une seule chaine de reception DMR est disponible simultanement. Le firmware alternatif doit donc differencier `2 x RX analogiques` et `1 x demodulateur DMR`, sans creer artificiellement un deuxieme demodulateur dans le SCT3258.

Le schema historique associe les deux premieres FI 38,550 et 38,850 MHz a des etages convertisseurs directs QA4818N. Une photo de la carte montre des **empreintes pour des filtres quartz supplementaires**, non equipees. Ce constat correspond a une position physique et non a la preuve qu'un filtre supplementaire ameliorerait le poste. Notre topologie RF doit distinguer l'etage reel, l'empreinte absente et la carte AM du PLUS.

Les tables BPF d'alignement sont une piste directe vers les commandes de DAC varactors. Une modification de blindage peut changer les capacites parasites et donc le suivi de filtrage. Un filtre non accorde pourrait expliquer une faible sensibilite hors bande sans que le synthese QA soit fautif.

**Mesures historiques, non caracterisation de nos appareils :** le guide donne des sensibilites de l'ordre de 0,18 uV VHF et 0,20 uV UHF en NFM pour son critere d'essai, et des niveaux TX autour de 58 W a 145,5 MHz et 43 W a 435 MHz en Turbo. Conserver la **methode**, la bande, les conditions et la provenance ; ne pas transformer ces chiffres en seuil d'acceptation rigide du GD32 PRO V1.21 ou du PLUS.

## 5. Carte GPS : deux coax et deux domaines de sauvegarde

Le guide historique illustre **deux mini-connecteurs coaxiaux** de la carte facade/CPU. L'un relie le SMA d'antenne GPS externe, l'autre est signale comme libre dans cette generation. Il ne faut ni le declarer relie au meme point RF ni presumer la presence des deux connecteurs sur chaque variante sans examiner la photo correspondante.

Le projet a deja documente les deux reserves RTC/GPS de la carte, la nature XH414HG et les domaines `VBAT`. Le nouveau detail a capter est donc la **topologie d'entree antenne**, les pistes RF, les composants d'adaptation et les interfaces passives de test. Le fonctionnement GNSS de l'OEM demeure valide.

## 6. Audio Bluetooth et traitement du microphone

Le texte VK7ZJA mentionne des options de routage du type **`BT + int mic`** et **`BT + int spk`**, et un usage d'un adaptateur audio Bluetooth externe avec un bouton PTT dedie. Elles suggerent une matrice de gestion de la source microphone et de la destination haut-parleur. Cela complete nos constats OEM `Speaker Mode`, GPIO PA7 et commande RF banque1/page0/0x25 ; cela ne fait pas des commandes `AT+AGHF` un schema audio exhaustif.

Le `Mic Enhance` decrite dans ce guide concerne l'audio transmis en DMR selon le profil teste, pas la reception ni necessairement l'audio analogique FM. Cette distinction indique ou rechercher les coefficients et les routines : chemin TX/codec et SCT3258, pas seulement l'amplificateur YD1517P du haut-parleur.

## 7. CPS, repartition logicielle et mise a jour des ressources

Le D578 possede plusieurs cibles de firmware et de donnees. **Ne pas tout presenter comme un CDD principal :**

- Application ARM du GD32 (firmware du poste et logicielle d'interface).
- Firmware du processeur DMR SCT3258 ; transfert distinct du contenu NAND codeplug.
- Module Bluetooth/LinkBoard ; eventuelle mise a jour distincte.
- Electronique du microphone filaire, mentionnee sous `Hand-Soft` dans les procedures historiques.
- Ressources graphiques du LCD dont les icones GPS, a distinguer de l'application MCU. Certaines archives historiques utilisent un conteneur `.spi` et un mode `UPDATE MODE` propre.

**Migration CPS :** l'export/import des canaux ne sauvegarde pas necessairement les options de configuration et certains parametres sensibles. L'outil OpenD578 doit conserver la version firmware, CPS, famille de MCU, MODE et version de structure de contacts, avec une politique explicite de conversion. Les commandes `PROGRAM/R/W/END` et les 64 octets d'enregistrement canal deja obtenus par simulation OEM sont des faits differents et **doivent rester conserves comme tels**.

La page DB1IG sur les codeplugs et son outil Contacts donnent un modele de flux CSV, filtre region/pays, avec plusieurs presentations de noms, mais ne prouvent pas le format binaire du contact D578 en NAND.

## 8. Autres pistes de tests et maintenance

- **Squelch et scanning** : differencier DMR simplex, DCDM et repetiteur, et le mode de reponse sur canal trouve. Il s'agit de fonctionnalites CPS/UI, pas de proprietes d'un seul QA4818N.
- **RDA FM broadcast** : le syntoniseur FM grand public est un circuit autonome ; sa plage de memoires peut differer de la plage de tuning manuel, ce qui justifie des tests de registre et de limites d'interface.
- **Icones GPS** : un paquet graphique peut utiliser un mode de mise a jour et une granularite differents du firmware MCU. Son existence prouve un protocole de chargement d'assets, pas son adresse exacte dans notre NAND.
- **Reprise apres echec de mise a jour** : documenter le mode recovery, les conditions d'alimentation et les pertes possibles de codeplug ; aucune procedure ecriture ne doit s'executer sans backup.
- **Refroidissement** : les modifications de ventilateur et boitier sont des choix de maintenance, non des instructions du firmware RF. Une commande de ventilateur OEM, si existante, devra etre recherchee separement.

## 9. Points de confusion ou de contradiction a ne pas fusionner

| Sujet | Ce qui est certain dans le projet | Ce qu'une source historique apporte | Decision documentaire |
|---|---|---|---|
| PTT | USART0 et trames filaires OEM decodes | Detection resistive sur profil CPS different | Deux profils, deux pilotes eventuels |
| QA4818N | Quatre banques serie et protocoles OEM fonctionnels | Affectation par etage theorique et reference 26 MHz | Valider la fonction, garder attribution des boitiers a relier |
| GPS | NMEA et fonction OEM disponibles | Deux connecteurs coax sur ancienne revision | Ne pas supposer les deux presents sur toutes les cartes |
| TEST | Code permissions et sequence OEM identifies | Noms historiques et exemples de valeurs | Conserver l'OEM comme preuve, etiqueter exemples externes |
| RDA | I2C/modulation documentes dans modele | Memoire FM broadcast potentiellement 76 MHz | Verifier registre de sous-bande par OEM |
| Airband | Carte RF PLUS supplementaire observee | Ampli/etage AM historique | Ne pas confondre avec RDA FM broadcast |
| 878 et D578 | Composants de meme famille | Outils et formats de codeplug proches | Pas de transplantation brute d'offset ni de firmware |

Voir la [matrice des 60 sujets](MATRICE_60_THEMES.md) pour le recoupement a l'echelle de chaque chapitre.
