# VK7ZJA : table exhaustive des 60 sujets en français

Index indépendant **des rubriques et des connaissances** de la version 7.4 (20 octobre 2022). Les descriptions sont des synthèses nouvelles ; consulter [la version source](https://radio.carstenbauer.net/578techmods.htm) pour les photos, valeurs supplémentaires et procédures historiques.

Cette liste conserve aussi les sujets périphériques (étiquettes, boîtier, logiciels) afin de ne perdre aucune piste de recherche. Les sources historiques ne prouvent pas automatiquement le brochage d’une variante GD32 de 2024.

## Contexte

### 01. Présentation générale

Inventaire de la famille D578 et limites de transposition entre révisions. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 11. Répertoire d'autres documentations

Archiver les liens sortants et vérifier leur pérennité. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 18. Étiquettes et repères des touches

Informations ergonomiques utiles mais sans incidence sur le pilote MCU. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 21. Console d'alimentation et bureau

Accessoire d'intégration mécanique, non composant embarqué. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 43. Documents d'homologation FCC

Photos internes et essais pour comparer révisions, sans traiter des schémas confidentiels comme disponibles. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 60. Pistes de développement futur

Traitement audio DSP, interface LCD, extensions de protocole ; projets non confondus avec des fonctions validées. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

## CPS / mémoire

### 02. Erreurs de bande

Le MODE inscrit dans le codeplug doit correspondre à celui du poste ; une mauvaise combinaison peut empêcher la programmation. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 05. Conseils d'utilisation du CPS

Choix du logiciel selon la version firmware et relecture des paramètres après changement de branche. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 06. Alertes antivirus sur le CPS

Documenter la provenance, les empreintes, les signatures et les faux positifs éventuels ; ne pas désactiver aveuglément les protections. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 09. Pilotes USB sous Windows

Identifier le mode USB et la correspondance avec le périphérique virtuel attendu par CPS. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 30. Sélection des bandes d'exploitation

MODE présent dans les zones configuration/codeplug, attention aux limites réglementaires. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 42. Mot de passe de programmation CPS

Option de verrouillage de lecture/écriture distincte du mot de passe de démarrage. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 52. Carte des plages NAND

Plages polices, fonds, contacts, codeplug, alignement et enregistrements à distinguer du brut OOB. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 53. Utilitaire de sauvegarde NAND

Readback des zones, métadonnées, granularités et décalages de certains outils historiques. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 54. Sauvegarde d'alignement propre au poste

Sauvegarder avant toute écriture les données RF non interchangeables entre unités. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 57. Structure des conteneurs CDD/CDI/SPI

Formats de mise à jour et alignement des écritures ; aucune écriture automatique fournie ici. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 58. Aide CPS en français

Anciennes aides English.HPT et pistes F1DMG ; versionner par CPS. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

## Variantes

### 03. Comparaison D578 et D878

Fonctions partagées et circuits spécifiques au mobile ; les deux firmwares ne sont pas interchangeables. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 04. Comparaison D578 et Alinco DR-MD500/520

Même famille matérielle, avec différences de commandes, profils et menus constructeur. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

## Façade / audio

### 07. Sélecteur des touches micro

La position du commutateur du microphone conditionne les commandes montée/descente. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 13. Répondre pendant un balayage

Préciser le retour sur le canal actif et les états de scan. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 16. Écran et façade déportés

Étudier le câble plat de la façade et les contraintes de longueur, EMI et intégrité des signaux. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 19. Deux sorties haut-parleur

L'une coupe le haut-parleur interne et l'autre le laisse actif ; noter la différence mécanique. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 20. Prise micro et microphone de table

Connecteur RJ et adaptation PTT par résistance sur certaines révisions et selon option HandOpMode. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 22. Entrées/sorties audio via micro filaire

Pistes de modification pour interfaces numériques externes ; ne pas confondre niveau micro et niveau haut-parleur. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 26. Traitement du microphone

Vérifier dans le TLV320AIC3204 les gains, filtres et parcours audio permis par le firmware. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 27. Tonalités de signalisation

Table de sons et générateurs audio du firmware OEM, hors application RF principale. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 46. Modification du haut-parleur interne

Mesures historiques de gain sonore ; à replacer dans le contexte mécanique et électrique. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

## Maintenance

### 08. Mise à jour du firmware principal

Distinguer sauvegarde codeplug, passage en mode update, écriture et restauration des données. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 10. Diagnostics des erreurs écran

Messages Band Error, données incompatibles, icônes absentes et cas de corruption au démarrage. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 14. Réinitialisation du poste

Séparer remise à zéro utilisateur, calibrations et récupération après erreur. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 29. Combinaisons de touches au démarrage

Cartographier MCU update, icons, test mode, SCT update, reset séparément par génération. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 39. Mode test et étalonnages

Paramètres puissance, squelch, alignement fréquence, courbe RSSI ; risque de dérégler le poste. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 40. Utilitaire AT Options de G4EML

Lecture/écriture de réglages locaux historiques ; ne pas l'assimiler au protocole CPS complet. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 41. Mot de passe au démarrage

Procédures de récupération historique ; garder les données de configuration séparées du code applicatif. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 55. Récupération d'un poste bloqué

Différencier rechargement d'un codeplug propre et effacement destructeur de la NAND. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 56. Prévention des blocages

Version CPS/codeplug, charge GPS/roaming et comportements sur trames DMR atypiques. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

## GPS / APRS

### 12. Paramétrage APRS

Comparer réglages de trames et capacités du D578, sans mélanger TX APRS et RX APRS propre au PLUS. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 45. Réserves d'alimentation RTC et GPS

Deux condensateurs de sauvegarde séparés sur la carte CPU historique ; rôle recoupé avec le relevé utilisateur. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 48. Antennes GPS internes

Connecteurs u.FL et volume libre dans la façade historique ; GPS externe demeure la référence de sensibilité. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

## DMR / Bluetooth

### 15. Compatibilité des modes de confidentialité DMR

Les formats entre constructeurs et modes ne sont pas tous interopérables ; le firmware alternatif n'a pas vocation à reproduire la fonction encryption. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 17. Microphones Bluetooth

Évolution historique vers les BT01 et accessoires compatibles ; distinguer audio et commandes. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 23. Audio externe par module Bluetooth

Chemin audio et profil Bluetooth historique à qualifier face à la carte D868BT-SP/ET12. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 24. Télécommande PTT via oreillette

Des boutons de certains casques produisent des commandes exploitables ; tester réellement les événements BT01/BP-02. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 28. Numérotation et carnets EchoLink

Interaction CPS et base contacts, sans fonction nécessaire au pilote RF. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 59. Mise à jour interne SCT3258

Firmwares DMR propres au DSP/baseband, indépendants de l'application principale GD32. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

## Affichage

### 25. Images de fond personnalisées

Données graphiques en NAND et exigences de format pour l'affichage. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 37. Polices et icônes

Polices et icônes stockées dans des plages NAND spécifiques, utiles au site et au futur firmware. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 38. Iconographie GPS

Fichiers graphiques distincts des transactions de position GPS. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

## RF

### 31. Extension historique de la réception

Firmware modifié ancien ; ne prouve pas les performances ni la présence de filtres RF sur toutes les versions. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 32. Mesures de sensibilité et de puissance

Des mesures historiques existent ; associer fréquence, niveau, déviation et appareil avant réutilisation. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 33. Réception de la bande aéronautique

Le PLUS possède une carte RF supplémentaire ; les anciens modèles ne reçoivent pas de manière équivalente. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 34. Balayage FM et DMR

Contraintes d'écoute, détection des porteuses et suivi des slots en DMR. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 35. Découpages de réception FM

Étudier les seuils RSSI, squelch et hystérésis plutôt que les seuls symptômes. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 36. Plage élargie du récepteur FM broadcast

RDA5802N distinct de la chaîne voix VHF/UHF ; plages à valider contre la datasheet. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 44. Photos de démontage de la carte

Vue CPU sous LCD, PCB RF dessus/dessous, filtres 38 MHz, carte Bluetooth et GPS. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 47. Connecteur antenne SO-239 / N

Modification mécanique du connecteur de sortie RF, hors périmètre du firmware. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 49. Refroidissement et circulation d'air

Orientation ventilateur, carénage et piste F1DMG /578a ; mesurer l'échauffement avant modification. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 50. Blindage complémentaire de réception

Empreintes de blindages et risque de déplacement des réglages de filtres à varactors. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

### 51. Liste des circuits et topologie du D578

GD32, SCT3258, TLV320AIC3204, QA4818N x4, RDA5802N, NAND, PA RF et GPS. [Source VK7ZJA v7.4](https://radio.carstenbauer.net/578techmods.htm).

