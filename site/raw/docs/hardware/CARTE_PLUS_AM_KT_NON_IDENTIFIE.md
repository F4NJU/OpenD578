# D578UV PLUS : carte RF supplémentaire, CI KT09?5R et réception AM

**Observation comparative :** la version **PLUS** comporte une petite carte enfichable au voisinage du RDA5802N, avec un circuit marqué approximativement `KT0905R` ou `KT09S5R`, une entrée RF, une référence quartz et quelques composants. Le connecteur correspondant **n'est pas implanté sur la version PRO** rapportée. Le second marquage `B9129` peut être un code de fabrication ; son interprétation n'est pas vérifiée.

## 1. Ce qu'on peut inférer

Les sources historiques D578 prévoient une **voie AM bande aéronautique** supplémentaire sur le PLUS, contrairement à la réception FM limitée du PRO. La position de la carte et l'entrée RF sont cohérentes avec cette fonction. **Aucun élément disponible ne prouve néanmoins que le circuit KT09?5R est un récepteur AM complet**, plutôt qu'un sous-ensemble de cette voie. Il ne faut pas le confondre avec le RDA5802N FM de radiodiffusion, ni le module Bluetooth/APRS de certaines variantes.

Les recherches de référence exacte sur `KT0905R` et `KT09S5R` n'aboutissent pas à une fiche fabricant certaine. Les composants KTMicro `KT0915` ou `KT0903` possèdent des registres et fréquences propres : **aucun de leurs pilotes ne doit être attribué** à la carte PLUS sans photo confirmant l'identité.

## 2. Fonction de la carte à caractériser

| Élément visible | Fait rapporté | Analyse restante |
| --- | --- | --- |
| Petit PCB RF côté PLUS | Présent | Numéro de carte, faces et couches |
| CI marqué KT0905R / KT09S5R (?) | Marquage partiellement lu | Photo macro, boîtier, dimensions et logo |
| Quartz | Présence visible | Fréquence, réseau de charge, liaison au CI |
| Entrée RF | Présente | Source : filtre, préampli, commutateur, antenne |
| Connecteur au PCB principal | Présent sur PLUS | Nombre de contacts, pin 1, tensions, GND, audio, data, IRQ |
| Empreintes PRO | Connecteurs absents selon observation | Comparaison des pistes et composants non implantés |

## 3. Procédure de comparaison PRO / PLUS

1. Prendre une photo perpendiculaire, macro et éclairée, de **chaque face du PCB additionnel**, avec le repère broche 1 et le quartz lisible.
2. Compter les contacts et numéroter le connecteur **depuis un repère physique**, pas à partir d'un dessin arbitraire.
3. Poste hors tension, relever masses, alimentation, couplage RF et audio à travers la nappe / connecteur.
4. En usage RX AM uniquement, capturer passivement les signaux numériques de la carte avec sondes adaptées, si l'utilisateur possède le PLUS et si les tensions sont confirmées.
5. Si le PLUS utilise une ligne I²C, identifier adresse et registres par **trames observées** et recherche de leur product ID, sans recopie depuis le KT0915.
6. Comparer le firmware PRO et PLUS, notamment la présence d'un initialiseur AM, d'une table de bande aéronautique, de GPIO de reset/enable, de mute/audio et de test de présence du module.

## 4. Impact sur un firmware alternatif PRO

Le firmware peut réserver l'API `airband_rx` et indiquer `hardware_absent` sur PRO. Ajouter uniquement du code ne créera **ni le circuit manquant ni sa chaîne analogique**, et le brochage de la version PLUS n'est pas transposable sans adaptation. Une première étape logicielle utile consiste à **détecter la présence effective du module sans écriture intrusive**, après identification du bus.

## Sources

- Historique D578, bande aéronautique prévue pour PLUS : <https://www.theweeks.org/tmp/FILES/Anytone-Mods/578mods.htm>
- Relevé utilisateur sur les PCB PRO et PLUS (novembre 2026), à accompagner de photographies.
