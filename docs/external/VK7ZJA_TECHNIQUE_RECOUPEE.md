# VK7ZJA : donnees techniques extraites et recoupees

Source : Jason Reilly VK7ZJA, *AnyTone AT-D578UV mods and information*, edition 7.4 (20/10/2022), hebergee notamment sur [carstenbauer.net](https://radio.carstenbauer.net/578techmods.htm) et [reddicams.co.uk](https://www.reddicams.co.uk/radio/AnytoneJR/578techmods.htm). Les caracteristiques ci-dessous sont des **reformulations techniques**, pas une copie du texte de l'auteur.

## Architecture numerique et RF

| Sous-systeme | Observation source | Correspondance OpenD578 | Controle restant |
|---|---|---|---|
| MCU | GD32F303VKT6, Cortex-M4, 3 Mio flash interne, 96 Kio RAM ; certaines revisions ulterieures utilisent un autre fabricant | Le PRO de notre projet est confirme GD32 ; le PLUS de l'utilisateur aussi | Bien conserver la revision par carte, ne pas generaliser les brochages OEM |
| Bande de base DMR | SCT3258TD / processeur SiComm, oscillateur autour de 12,2 MHz | Fiches DMR HPI et sequences d'initialisation | Sens des bus et tables de configuration associees aux versions |
| Audio | TLV320AIC3204 et amplificateur YD1517P sur le PRO ancien | Monographies audio et differences PA1517G sur le PLUS | Raccorder les gains et mises en veille par trace OEM |
| RF analogique | 4 QA4818N avec reference 26 MHz : paire de synthese OL, paire de reception conversion directe apres premiere FI | Calculateur 0x29/0x2A et traceur QA4818N experimental | Attribution physique des quatre selections, registres verifiables pour chaque scenario |
| Premier etage FI | 38,550 et 38,850 MHz ; deux chaines de reception | Calculs de freq OL/FI et schema du site | Injection haute/basse et affectation A/B suivant la bande |
| Filtrage | Quatre cellules d'accord a varactors pour chaque entree VHF/UHF | BH2226FV et chaines de commande analogiques | Tensions/DAC par bande et par freq a extraire des traces |
| Puissance RF | Deux AFT05MP075N, chacun utilise pour une section de puissance VHF ou UHF | Deux PA independants deja repertories | Enveloppe thermique, bias et commande du PTT a qualifier |
| Broadcast FM | RDA5802N | Fiche RDA/I2C et banc | Bus reel et init OEM selon version |
| GPS | ATGM336H GPS + BeiDou, reception sur coax externe | Monographie GPS et simulation UART | Entrée de sauvegarde et chemin d'alimentation |
| NAND | TC58CVG1S3HRAIG 2 Gbit = 256 Mio | Dumps utilisateur et monographie NAND | Adressage logique, OOB et gestion des mauvais blocs |

Le schema historique mentionne une **troisieme chaine FI non peuplee** et des empreintes de filtres optionnelles. Ce sont des observations d'une carte ancienne, pas la preuve que les memes empreintes existent a l'identique sur les deux versions GD32 et PLUS.

## NAND : repartition historique a ne pas confondre avec un format confirme

| Plage logique selon VK7ZJA | Usage publie |
|---|---|
| `0x00000000–0x0014FFFF` | Polices alternatives |
| `0x00150000–0x00159FFF` | Image d'accueil constructeur |
| `0x0015A000–0x001FFFFF` | Icones couleur |
| `0x003E0000–0x0041FFFF` | Donnees non identifiees |
| `0x00420000–0x00434FFF` | Autres icones |
| `0x00435000–0x0043BFFF` | Police monochrome (usage incertain) |
| `0x00800000–0x02A9FFFF` | Codeplug hors base contacts DMR |
| `0x02AC0000–0x02AC9FFF` | Image d'accueil personnalisee |
| `0x02B00000–0x02B09FFF` | Fond BK1 |
| `0x02B80000–0x02B89FFF` | Fond BK2 |
| `0x02F00000–0x02F80679` | Ajustements RF et sauvegardes |
| `0x02FA0000–0x02FDFFFF` | Informations locales et sauvegardes |
| `0x02FE0000–0x03000000` | Usage indetermine |
| `0x05500000–0x07FFFFFF` (plage approximative) | Base IDs DMR |
| `0x0C8E0000–0x0FFFFFFF` (plage approximative) | Enregistrements DMR |

**Attention :** ces adresses de VK7ZJA concernent l'adressage logique du constructeur. Les dumps bruts utilisateur incluent eventuellement les pages OOB et erreurs ECC. Il ne faut pas transposer directement ces plages a un fichier de lecture physique sans definir la transformation.

## Sauvegardes RTC et GPS

La carte facade/CPU historique comporte deux reserves independantes : pres de la nappe pour le RTC et entre les potentiometres de volume pour le demarrage a chaud GPS. L'auteur donne la reference `XH414HG IV01E`. Notre documentation distingue ce marquage d'une pile CR non rechargeable et recoupe la categorie de condensateur rechargeable du fabricant. Les deux composants ont ete observes par l'utilisateur sur son PCB ; leur role est appuye par la source historique. Voir `docs/hardware/` et `docs/evidence/` pour les renvois.

## Microphone et audio

Le micro utilise des lignes serie et audio distinctes. Une adaptation de micro de table est decrite sur l'ancien 578, avec une commande PTT analogique entre broches 1 et 8 au travers d'une resistance d'au moins 1 kOhm lorsque `HandOpMode` est configure pour une detection de niveau. **Ce n'est pas le protocole UART du micro d'origine** et ce reglage ne doit pas etre transpose sans verification a un firmware OpenD578. Le chapitre historique distingue aussi les deux jacks haut-parleur (l'un coupe le haut-parleur interne et l'autre non).

## Maintenance, sauvegardes et erreurs

La source distingue : mode de programmation MCU, mode mise a jour des icones, mode test/calibration et mode mise a jour SCT3258. Les combinaisons de touches et l'effet sur la NAND peuvent varier suivant la generation. Le site conserve les profils PRO/PLUS et les observations effectives du poste. Lors d'une mise a jour firmware, le codeplug doit etre reconstruit dans une version CPS compatible. La sauvegarde de l'alignement est prioritaire avant toute tentative d'effacement ou de restauration.

L'outil Flash Utility de G4EML et les procedures de restauration signalees dans la source utilisent historiquement une granularite de 256 Kio et un decalage d'adresse de 0x20000 pour certaines ecritures. **Ne pas utiliser ces constantes comme API d'ecriture universelle** : elles sont documentees comme comportements d'outil et peuvent provoquer des corruptions. Cette monographie ne fournit aucune sequence automatique de restauration.

## Preuves photographiques a conserver

La source illustre au moins : arriere de carte afficheur avec GPS/Bluetooth ; arriere sans carte Bluetooth ; face avant et MCU sous LCD ; carte RF dessus/dessous ; filtres a quartz 38 MHz ; deux reserves RTC/GPS ; connecteurs audio ; remplacement connecteur antenne ; blindages RF ; antenne GPS interne. Les images doivent etre sauvegardees **avec leur fichier HTML et les legendes d'origine** dans l'archive privee, et rester liees a leur auteur sur GitHub.
