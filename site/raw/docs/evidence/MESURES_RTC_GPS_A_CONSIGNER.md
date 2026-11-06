# Fiche de mesures : deux sauvegardes du PCB CPU

La presence de sauvegardes sur la carte CPU est un **releve de l'utilisateur**. L'attribution RTC/arriere et GPS/avant, ainsi que `XH414HG IV01E`, proviennent d'une **documentation externe sur une autre revision D578**. Mesurer avant de figer le schema du PRO ou du PLUS.

## Identification, sans alimentation et sans injection

| Observation a noter | PRO GD32 V1.21 | PLUS GD32 (revision precise a consigner) |
| --- | --- | --- |
| Marquage du composant pres de la nappe (arriere) | a photographier | a photographier |
| Marquage du composant entre potentiometres (avant) | a photographier | a photographier |
| Diametre / hauteur / polarite / orientation | a mesurer | a mesurer |
| Tension residuelle aux bornes, instrument > 10 Mohm | a mesurer | a mesurer |
| Pin MCU VBAT (physique 6 LQFP100) -> sauvegarde RTC | a mesurer **hors tension et reserve dechargee** | a mesurer apres confirmation package MCU |
| Version exacte du ATGM336H et broche VBAT | a identifier | a identifier |
| Continuite composant GPS -> VBAT GNSS | a mesurer avec alimentation deconnectee | a mesurer avec alimentation deconnectee |
| Tension sur reserve RTC et GPS avec alimentation connectee, sans bouton POWER | a mesurer sans court-circuit | a mesurer sans court-circuit |
| Comportement heure apres une coupure prolongée | a observer | a observer |
| Temps premier fix GPS a froid / apres redemarrage court | a observer | a observer |

**Securite electrique :** ne pas utiliser le test de continuite sur un composant encore charge ; ne pas placer une CR2032 en remplacement d'un condensateur XH414HG ; ne pas raccorder une alimentation de laboratoire directement a la reserve. Les tests de tension en fonctionnement ne se font que si l'acces physique est sur, avec pointes isolees et masses identifiees.

## Preuves a archiver

- `hardware/photos/pro-gd32/...` ou `hardware/photos/plus-gd32/...` : photos nettes des deux faces, des deux composants et de la reference du module GPS.
- Tableau local de mesures : tension, temperature, alimentations, duree depuis derniere mise sous tension, instrument, date, numero de revision.
- Pour chaque mesure : chemin vers photo/trace, broche physique et sens du connecteur, reference datasheet, commentaire de l'operateur.
- Seules les mesures **effectivement realisees** doivent changer le statut des liaisons dans les JSON de l'explorateur.

Pour l'identification des pins GD32, lire [la carte de brochage KiCad reconstituee](../../hardware/kicad/README.md).
