# 02 - GPS/GNSS ATGM336H : interfaces, sauvegarde, NMEA et contrat firmware

> **RECONSTITUTION du 05/11/2026.** Le document historique homonyme n'est pas conserve octet pour octet. Les informations ci-dessous proviennent de l'observation de la reference ATGM336H, du banc et de sources externes. Le brochage et les parametres **propres au D578** restent partiels.

## 1. Constitution de la fonction GNSS

L'AnyTone D578 avec GPS est equipe d'un module **ATGM336H**, capable selon variantes de GPS et BeiDou (BDS). Ce module n'est ni le RDA5802N (tuner FM) ni le processeur principal GD32. Une carte fille/antenne GPS externe est reliee au module par une liaison RF coaxiale. La fiche externe de VK7ZJA donne aussi un emplacement pour une possible antenne interne, non peuplee sur les cartes observees a l'epoque.

Trois espaces/etats sont a distinguer :

1. **Etat interne du GNSS** : horloge, almanach/ephemerides et donnees de hot start dans son domaine de sauvegarde (ne pas appeler cet espace la NAND de 256 Mio du GD32).
2. **RAM OEM GD32** : dernier fix, validite, heure et donnees de position exploitees par les fonctions radio/APRS ; leurs adresses sont a valider contre le firmware V1.21, pas deduites des noms de phrases NMEA.
3. **NAND/Flash radio** : parametres utilisateur GPS/APRS et frequences de canal, servis par le CPS. L'adresse de chaque champ n'est **pas** prouvee ici par la presence du GPS.

## 2. Alimentation et maintien de l'horloge GPS

L'etude technique D578 fait etat de **deux sauvegardes sur le PCB afficheur/CPU**. Le second composant, devant entre les deux potentiometres, est destine au hot start GPS. Pour la reference XH414HG IV01E citee sur les cartes historiques, Seiko Instruments specifie un **condensateur rechargeable 0,08 F / 3,3 V max**, pas une CR2032. Voir `../hardware/SAUVEGARDE_RTC_GPS_XH414HG.md`.

La documentation d'un **ATGM336H-5N** decrit l'entree `VBAT` destinee au maintien RTC/SRAM (1,5 a 3,6 V). Elle decrit aussi `VCC`, `TXD`, `RXD`, `1PPS` et `ON/OFF` selon le boitier. **Le tableau de broches et les seuils du -5N ne doivent pas etre imposes sans verifier le suffixe et l'implantation du module monte sur D578**. Continuite vers la sauvegarde et polarite de la charge inconnues.

## 3. Liaison avec le GD32, ce qui est etabli

| Parametre | Valeur/observation | Statut |
| --- | --- | --- |
| Module | ATGM336H | Identifie dans la famille D578 et par le projet |
| Chemin de commande | Liaison serie UART logique entre GNSS et MCU, selon architecture de la famille | **A confirmer** sur broches PRO/PLUS |
| Debit de reference | `9600 8N1` dans des modules ATGM336H et dans des references de la famille AnyTone | **Pas de capture temporelle sur notre D578** |
| Signaux de module | TXD, RXD, GND, alimentation, sauvegarde, eventuellement PPS et ON/OFF | Interface de module ; affectation MCU physique inconnue |
| RTC/GPS backup | Sauvegarde GPS sur facade PCB CPU, distincte du RTC | Source externe, piste non mesuree |
| Communication du banc | Emulation GPS et cas d'erreur/perte de fix | **Modele**, pas mesure de bus |

Les broches `PA2/PA3` du GD32 peuvent implementer `USART1_TX/RX` par fonction alternative **selon datasheet**. Cela ne prouve absolument pas que ce D578 les utilise pour son GPS. **Ne pas attribuer ces GPIO au GPS** dans les schemas tant qu'une configuration USART OEM et la continuite ne sont pas concordantes.

## 4. Format NMEA 0183 et validations necessaires

Les phrases standard susceptibles d'etre utiles sont `GGA` (qualite de fix), `RMC` (position, statut, vitesse, temps), `GSA` (DOP/satellites utilises), `GSV` (satellites en vue) et `VTG` (route/vitesse). Le talker peut etre `GP`, `GN`, `BD`, `GL` suivant firmware et constellations, et **ne doit pas etre suppose fixe a `GP`**. Une phrase suit en general la forme `$<talker><type>,...*HH` avec checksum XOR des caracteres entre `$` et `*`.

### Validation du parseur du firmware alternatif

1. Attendre une phrase complete jusqu'a `CR/LF`, avec taille maximale fixe et sans depassement memoire.
2. Verifier `$`, nombre de champs et `*HH` ; refuser une phrase au checksum non conforme, sans utiliser un ancien champ comme valeur courante.
3. Pour `RMC`, verifier le statut de validite avant toute utilisation ; pour `GGA`, controler la qualite du fix et le type d'altitude. Ne pas convertir directement heure UTC en heure locale.
4. Traiter explicitement les dates manquantes, le passage minuit et les solutions invalides ; un « vieux fix » est un **fix invalide pour Doppler/APRS** si aucune fraicheur n'est attestee.
5. Accepter un flux en fragments, plusieurs phrases par interruption DMA et les pertes d'octets ; journaliser un compteur d'erreurs, pas toutes les positions sensibles par defaut.
6. Produire un objet immutable `gnss_fix{timestamp_utc, lat, lon, alt, speed, fix_quality, age_ms, provenance}` consomme par APRS et satellite ; ne pas relire en cours de trame des variables OEM disjointes.

## 5. Commandes de configuration : ne pas appliquer sans qualification

Des modules a base d'AT6558R publient la famille de commandes `$PCAS...` (par exemple mise a jour d'intervalle ou choix de constellations). Les valeurs supportees dependent **du firmware interne du module**. Une page GitHub sur un ATGM336H-5N decrit `$PCAS04` et `$PCAS10` avec plusieurs modes. Ce n'est **pas une preuve** que le module du D578 accepte exactement ces commandes ou qu'elles sont utilisees par l'OEM. L'analyse doit rechercher dans `D578UV_GD_V1.21_20240619.CDD` les chaines `PCAS`, `NMEA`, `GNRMC`, `GPGGA`, les tables d'initialisation et les references UART pour separer commandes OEM et simples formats documentes.

**Regle :** ne pas envoyer `$PCAS00` ou de commande de sauvegarde non volatile a un module de poste sans avoir recupere la configuration d'origine et qualifie son protocole.

## 6. Relations avec APRS, mode satellite et RTC

- L'APRS TX peut partir d'un fix GNSS quand il est valide ; la presence d'un flag « GPS enable » ne prouve pas un fix dequalite.
- Le suivi satellite demande **heure UTC juste et actuelle**, position d'observateur fiable, TLE valable et securite RF (PTT/busy). Ni NMEA seul ni hot start ne valident la periode de calcul.
- Un RTC correct peut subsister sans sauvegarde GNSS, et l'inverse ; le driver ne doit pas rendre le mode satellite actif tant que les deux sources temporelles n'ont pas ete comparees.
- La lecture des parametres CPS doit etre **en lecture seule** dans les etapes de recherche ; les octets de calibration et local information NAND doivent rester proteges.

## 7. Tests reproductibles et preuves a obtenir

| Test | Donnee attendue | Methode |
| --- | --- | --- |
| Identification module | Marquage complet et orientation pin 1 | Macro-photo de carte CPU |
| RX/TX UART | Sens TX module / RX GD32, debit et amplitudes | Analyseur logique passif haute impedance |
| Hot start | Presence tension de sauvegarde au demarrage et apres extinction | Multimetre sans injection |
| PPS (si cable) | Continuite et eventuelle periode 1 s | Mesure passive |
| Recovery position | Comportement sans antenne/sans fix | Scenario non-emissif + journaux horodates |
| CPS fields | Offsets et tailles V1.21 vs PLUS 2.x | Capture CPS lecture et diff schema avant/apres un parametre |

## 8. Sources

- Projet : `../04_RAM_ROUTINES_UI_RF_ET_BROCHAGE.md`, `../hardware/SAUVEGARDE_RTC_GPS_XH414HG.md`, `bench/scenarios/GPS_loss.json`, `bench/scenarios/GPS_PTT_APRS_incomplete.json`, `docs/cps/`.
- VK7ZJA, photographie ATGM336H et antenne : <https://radio.carstenbauer.net/578techmods.htm>.
- ATGM336H-5N reference et pin VBAT (document tiers a verifier sur sous-variant) : <https://upcommons.upc.edu/bitstreams/85590e00-83f0-4e78-8569-c8873263d87f/download>.
- Retour d'experience command set AT6558R : <https://github.com/cbrown350/ATGM336H-GNSS-Reader/blob/main/FINDINGS.md>.
- Datasheet GD32 LQFP100 : <https://www.gd32mcu.com/data/documents/datasheet/GD32F303xx_Datasheet_Rev3.0.pdf>.
