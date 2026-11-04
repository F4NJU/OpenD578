# RAM, routines analysées, UI, RF, brochage

Les adresses sont celles de l'application constructeur **GD32 V1.21**, sauf indication explicite V1.20. Les symboles proposés sont des étiquettes analytiques et non des noms de fonction officiels décompilés. Pour chaque adresse, chercher les occurrences contextualisées dans `01_INDEX_MACHINE/addresses_with_context.jsonl`.

## SRAM GD32 V1.21, parcours exécuté en émulation le 04/11

| Plage inclusive | Octets | Preuve / signification |
|---|---:|---|
| `0x20000000..0x20001AD7` | 6 872 | Données initialisées par décompression, source Flash `0x080FE7A8` vers RAM, routine `0x0800616C`. |
| `0x20001AD8..0x20016ADF` | 86 024 | ZI hors réserves initiales, buffers/pools/tâches non entièrement reconstruits. |
| `0x20016AE0..0x20016CDF` | 512 | Réserve initiale heap C. |
| `0x20016CE0..0x200170DF` | 1 024 | Réserve initiale pile. |
| `0x200170E0..0x20017FFF` | 3 872 | Hors table init; pas écrit sur les scénarios, **PAS qualifié libre**. |

Table scatter `0x080FE678..0x080FE697`; source init `0x080FE7A8`, source ZI champ `0x080FF18C` non lu dans zéro; zéro à `0x080061C8`. Démarrage C `0x08006130`, transition application `0x0800620C`, arrivée main `0x08006654`. Routine `0x08006D54` renvoie des bornes r0=0x20016AE0, r1=0x200170E0, r2=r3=0x20016CE0. **94 432 octets initialisés / 98 304, ce n'est pas la consommation dynamique maximale.**

La conclusion précédente rejetant le haut RAM sur la base des mots `0x20017801`, `0x20017904`, `0x20017F21` était erronée : ce sont des concaténations de demi-mots Thumb `LDRB/MOVS`, pas des références mémoire. L'analyse a été corrigée en V1.

La Phase60 propose 608 octets d'état persistant satellite, non placés, et utilise intentionnellement BSS sentinelle **invalide** `0x30000000` dans l'ELF, pour bloquer toute interprétation de son placement comme utilisable. Ne pas placer les 608 octets dans le haut SRAM sur cette seule comparaison numérique.

## Index routines V1.21

| Adresse(s) | Rôle déduit | Etat |
|---|---|---|
| `0x08038488` / `0x08038466` | Constructeur worker UI; worker boucle de `0x0803846A` à `0x08038486`. | [STATIQUE] |
| `0x08038472` / `0x080AE3AE` | Attente/obtention événement worker UI, objet `0x20000124`. | [STATIQUE] |
| `0x08038482` -> `0x08037BE8` | Dispatcher/rendu OEM; Phase60 identifie 42 cas via TBB `0x08037D2A`. | [STATIQUE] |
| `0x080AF0F0` | Enregistrement du worker, par `0x080384A8`; pointeur Thumb `0x08038467`. | [STATIQUE] |
| `0x200000E5` | Sélecteur de vue OEM phase60. | [STATIQUE], ne pas écrire. |
| `0x2000071C` | Pointeur de canal actif OEM V1.21 phase60. | [STATIQUE], structure exacte inconnue. |
| `0x080AED66` / `0x080AEEC4` | Prise/restitution sémaphore RTOS OEM. | [STATIQUE], statut et acquisition à qualifier. |
| `0x20000128` | Handle sémaphore LCD OEM; crée via `0x0803848C -> 0x080AEC5A`. | [STATIQUE], pas API satellite approuvée. |
| `0x20001542` | Garde de phase RTOS utilisé par séquences sémaphore. | [STATIQUE], pas un verrou que l'on peut écrire. |
| `0x080387AC` | Commande LCD `0x10`. | [STATIQUE] |
| `0x080387DA` | Commande LCD `0x11` (correction Phase43), **pas données LCD brutes**. | [STATIQUE] |
| `0x08039096` / `0x0802126E` | Traitement graphique OEM partagé. | [STATIQUE] |
| `0x0808B672`, `0x0808B6F6` | Commandes LCD bas niveau; GPIO `0x40011800`, `0x40010C00`. | [STATIQUE] |
| `0x080393C6` -> `0x200001C8`, `0x200001EC`, `0x200001F8` | Notifications/temporisation, **pas mutex LCD**. | [STATIQUE] |
| `0x0805A094` | Décodage BCD candidat fréquence. | [STATIQUE], ABI non certifiée. |
| `0x0805A178`, `0x0805A1D6` | Validation plage/contexte fréquence, limites vers `0x20004214`. | [STATIQUE] |
| `0x0805A234`, `0x0805A316` | Calculs/choix de fréquence à partir d'un canal. | [STATIQUE], pas setters RF. |
| `0x200006F0` | Champ RAM fréquence OEM (10 sites d'écriture trouvés Phase46). | [STATIQUE], ne jamais forcer par `poke`. |
| `0x08033840`, `0x08033C7A` -> `0x0805A9F8` | Lecture et conversion décimale de la fréquence. | [STATIQUE] |
| `0x0805D50A` | Autre écrivain du champ `0x200006F0`. | [STATIQUE], condition à préciser. |
| `0x0804EAC6` | Copie RAM VFO/enregistrement canal, **pas** commande synthétiseur. | [STATIQUE] |
| `0x080857AE` / `0x080857CA` | Accès mémoire externe paginée/enregistrements 64 o, **pas setter radio**. | [STATIQUE] |
| `0x0808AB18` | Envoi de commande série / registre 16 bits vers circuit; séquence 0x29/0x2A. | [STATIQUE], transaction RF complète inconnue. |
| `0x0806E100`, `0x080709D2` | Ancrages RF et choix bande candidats selon audit Phase53. | [STATIQUE], pas ABI qualifiée. |
| `0x08008796`, `0x080087A8` | Lecteurs GPIO entrée bit / port 16 bits. | [STATIQUE], **PTT non identifié**. |
| `0x080087B0` | Lecture GPIO sortie OCTL, pas getter entrée. | [STATIQUE] |
| `0x0808CE72` | Copie OEM NAND vers Flash haute. | [STATIQUE], zone protégée. |
| `0x0808CC28`, `0x0808CC1C`, `0x0808CC0B` | Encodeur PC8/PC9, chemin EXTI candidat. | [STATIQUE] |
| `0x0808D70C`, `0x0808E310` | USART0 microphone PA9/PA10, initialisation et RX candidat. | [STATIQUE] |

UI: 37 sites d'acquisition et 38 de restitution du même handle LCD, avec 37 paires adjacentes et un saut spécial vers `0x080752DC`. Cela n'implique pas une restitution surnuméraire sans analyse de flot. Les états de retour `0,1,2,10,13,14` sont rapportés; aucun chemin sûr d'acquisition d'un « LCD lease satellite » n'est encore qualifié.

## Brochage en cours

Le tableau `TABLE_100_BROCHES_GD32F303VKT6.csv` et le schéma KiCad V0.3 existent dans Library mais leur original n'a pas été exporté. Le travail couvrait USB, GPIO, PA0 Power, GPS, encodeur, touches P1-P6, MENU/EXIT, micro/USART, OLED/LCD, NAND série, LED et RF. Hypothèses matérielles robustes pour la NAND, appuyées par la simulation du pilote : **PB8 = CS, PB15 = SCK, PB14 = MOSI/SO0, PA15 = MISO/SO1**. La simulation bit-série observe les niveaux effectivement commandés par l'OEM; cela ne remplace pas un contrôle de continuité sur la carte.

Compte rendu LED GPIO V1.2/V1.3 : en lecture seule, plusieurs centaines d'échantillons par port et zéro transition ISTAT/OCTL identifiée. Ne **PAS** piloter une broche GPIO pour allumer la LED sur cette seule preuve; le bouton Power ne coupe pas l'alimentation processeur. Aucun driver LED prouvé.

**Circuit TLV320AIC3204** : codec audio stéréo ADC/DAC interne, I2C/SPI pour les contrôles, interface audio série DSP/I2S/TDM; ce n'est pas l'ADC0 du GD32 qui déclenche le DMA à `0x4001244C`. La présence et le raccordement exacts de ce codec sur la variante de la carte doivent être vérifiés physiquement. Fiche TI : https://www.ti.com/product/TLV320AIC3204 .

## V1.20 uniquement : ne pas transplanter les offsets en V1.21

Tables menus analogiques/numériques `0x080C8808`, `0x080C8900`, `0x080C89F8`, sélecteur `0x0803B966`, descripteurs `0x080C887C`, `0x080C8974`, `0x080C8A6C`, noms/menu `0x0803B9AC`, `0x0803EB08`. Les offsets prouvent des relations dans cette image V1.20, pas les API OEM V1.21.
