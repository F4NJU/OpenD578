#!/usr/bin/env python3
"""Generate independent subject index (facts and links, no third-party prose)."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
TOPICS=[
("Contexte","Présentation générale","Inventaire de la famille D578 et limites de transposition entre révisions."),
("CPS / mémoire","Erreurs de bande","Le MODE inscrit dans le codeplug doit correspondre à celui du poste ; une mauvaise combinaison peut empêcher la programmation."),
("Variantes","Comparaison D578 et D878","Fonctions partagées et circuits spécifiques au mobile ; les deux firmwares ne sont pas interchangeables."),
("Variantes","Comparaison D578 et Alinco DR-MD500/520","Même famille matérielle, avec différences de commandes, profils et menus constructeur."),
("CPS / mémoire","Conseils d'utilisation du CPS","Choix du logiciel selon la version firmware et relecture des paramètres après changement de branche."),
("CPS / mémoire","Alertes antivirus sur le CPS","Documenter la provenance, les empreintes, les signatures et les faux positifs éventuels ; ne pas désactiver aveuglément les protections."),
("Façade / audio","Sélecteur des touches micro","La position du commutateur du microphone conditionne les commandes montée/descente."),
("Maintenance","Mise à jour du firmware principal","Distinguer sauvegarde codeplug, passage en mode update, écriture et restauration des données."),
("CPS / mémoire","Pilotes USB sous Windows","Identifier le mode USB et la correspondance avec le périphérique virtuel attendu par CPS."),
("Maintenance","Diagnostics des erreurs écran","Messages Band Error, données incompatibles, icônes absentes et cas de corruption au démarrage."),
("Contexte","Répertoire d'autres documentations","Archiver les liens sortants et vérifier leur pérennité."),
("GPS / APRS","Paramétrage APRS","Comparer réglages de trames et capacités du D578, sans mélanger TX APRS et RX APRS propre au PLUS."),
("Façade / audio","Répondre pendant un balayage","Préciser le retour sur le canal actif et les états de scan."),
("Maintenance","Réinitialisation du poste","Séparer remise à zéro utilisateur, calibrations et récupération après erreur."),
("DMR / Bluetooth","Compatibilité des modes de confidentialité DMR","Les formats entre constructeurs et modes ne sont pas tous interopérables ; le firmware alternatif n'a pas vocation à reproduire la fonction encryption."),
("Façade / audio","Écran et façade déportés","Étudier le câble plat de la façade et les contraintes de longueur, EMI et intégrité des signaux."),
("DMR / Bluetooth","Microphones Bluetooth","Évolution historique vers les BT01 et accessoires compatibles ; distinguer audio et commandes."),
("Contexte","Étiquettes et repères des touches","Informations ergonomiques utiles mais sans incidence sur le pilote MCU."),
("Façade / audio","Deux sorties haut-parleur","L'une coupe le haut-parleur interne et l'autre le laisse actif ; noter la différence mécanique."),
("Façade / audio","Prise micro et microphone de table","Connecteur RJ et adaptation PTT par résistance sur certaines révisions et selon option HandOpMode."),
("Contexte","Console d'alimentation et bureau","Accessoire d'intégration mécanique, non composant embarqué."),
("Façade / audio","Entrées/sorties audio via micro filaire","Pistes de modification pour interfaces numériques externes ; ne pas confondre niveau micro et niveau haut-parleur."),
("DMR / Bluetooth","Audio externe par module Bluetooth","Chemin audio et profil Bluetooth historique à qualifier face à la carte D868BT-SP/ET12."),
("DMR / Bluetooth","Télécommande PTT via oreillette","Des boutons de certains casques produisent des commandes exploitables ; tester réellement les événements BT01/BP-02."),
("Affichage","Images de fond personnalisées","Données graphiques en NAND et exigences de format pour l'affichage."),
("Façade / audio","Traitement du microphone","Vérifier dans le TLV320AIC3204 les gains, filtres et parcours audio permis par le firmware."),
("Façade / audio","Tonalités de signalisation","Table de sons et générateurs audio du firmware OEM, hors application RF principale."),
("DMR / Bluetooth","Numérotation et carnets EchoLink","Interaction CPS et base contacts, sans fonction nécessaire au pilote RF."),
("Maintenance","Combinaisons de touches au démarrage","Cartographier MCU update, icons, test mode, SCT update, reset séparément par génération."),
("CPS / mémoire","Sélection des bandes d'exploitation","MODE présent dans les zones configuration/codeplug, attention aux limites réglementaires."),
("RF","Extension historique de la réception","Firmware modifié ancien ; ne prouve pas les performances ni la présence de filtres RF sur toutes les versions."),
("RF","Mesures de sensibilité et de puissance","Des mesures historiques existent ; associer fréquence, niveau, déviation et appareil avant réutilisation."),
("RF","Réception de la bande aéronautique","Le PLUS possède une carte RF supplémentaire ; les anciens modèles ne reçoivent pas de manière équivalente."),
("RF","Balayage FM et DMR","Contraintes d'écoute, détection des porteuses et suivi des slots en DMR."),
("RF","Découpages de réception FM","Étudier les seuils RSSI, squelch et hystérésis plutôt que les seuls symptômes."),
("RF","Plage élargie du récepteur FM broadcast","RDA5802N distinct de la chaîne voix VHF/UHF ; plages à valider contre la datasheet."),
("Affichage","Polices et icônes","Polices et icônes stockées dans des plages NAND spécifiques, utiles au site et au futur firmware."),
("Affichage","Iconographie GPS","Fichiers graphiques distincts des transactions de position GPS."),
("Maintenance","Mode test et étalonnages","Paramètres puissance, squelch, alignement fréquence, courbe RSSI ; risque de dérégler le poste."),
("Maintenance","Utilitaire AT Options de G4EML","Lecture/écriture de réglages locaux historiques ; ne pas l'assimiler au protocole CPS complet."),
("Maintenance","Mot de passe au démarrage","Procédures de récupération historique ; garder les données de configuration séparées du code applicatif."),
("CPS / mémoire","Mot de passe de programmation CPS","Option de verrouillage de lecture/écriture distincte du mot de passe de démarrage."),
("Contexte","Documents d'homologation FCC","Photos internes et essais pour comparer révisions, sans traiter des schémas confidentiels comme disponibles."),
("RF","Photos de démontage de la carte","Vue CPU sous LCD, PCB RF dessus/dessous, filtres 38 MHz, carte Bluetooth et GPS."),
("GPS / APRS","Réserves d'alimentation RTC et GPS","Deux condensateurs de sauvegarde séparés sur la carte CPU historique ; rôle recoupé avec le relevé utilisateur."),
("Façade / audio","Modification du haut-parleur interne","Mesures historiques de gain sonore ; à replacer dans le contexte mécanique et électrique."),
("RF","Connecteur antenne SO-239 / N","Modification mécanique du connecteur de sortie RF, hors périmètre du firmware."),
("GPS / APRS","Antennes GPS internes","Connecteurs u.FL et volume libre dans la façade historique ; GPS externe demeure la référence de sensibilité."),
("RF","Refroidissement et circulation d'air","Orientation ventilateur, carénage et piste F1DMG /578a ; mesurer l'échauffement avant modification."),
("RF","Blindage complémentaire de réception","Empreintes de blindages et risque de déplacement des réglages de filtres à varactors."),
("RF","Liste des circuits et topologie du D578","GD32, SCT3258, TLV320AIC3204, QA4818N x4, RDA5802N, NAND, PA RF et GPS."),
("CPS / mémoire","Carte des plages NAND","Plages polices, fonds, contacts, codeplug, alignement et enregistrements à distinguer du brut OOB."),
("CPS / mémoire","Utilitaire de sauvegarde NAND","Readback des zones, métadonnées, granularités et décalages de certains outils historiques."),
("CPS / mémoire","Sauvegarde d'alignement propre au poste","Sauvegarder avant toute écriture les données RF non interchangeables entre unités."),
("Maintenance","Récupération d'un poste bloqué","Différencier rechargement d'un codeplug propre et effacement destructeur de la NAND."),
("Maintenance","Prévention des blocages","Version CPS/codeplug, charge GPS/roaming et comportements sur trames DMR atypiques."),
("CPS / mémoire","Structure des conteneurs CDD/CDI/SPI","Formats de mise à jour et alignement des écritures ; aucune écriture automatique fournie ici."),
("CPS / mémoire","Aide CPS en français","Anciennes aides English.HPT et pistes F1DMG ; versionner par CPS."),
("DMR / Bluetooth","Mise à jour interne SCT3258","Firmwares DMR propres au DSP/baseband, indépendants de l'application principale GD32."),
("Contexte","Pistes de développement futur","Traitement audio DSP, interface LCD, extensions de protocole ; projets non confondus avec des fonctions validées.")
]
assert len(TOPICS)==60,len(TOPICS)
out=ROOT/'docs/external'
source='https://radio.carstenbauer.net/578techmods.htm'
docs=[]
for i,(cat,title,summary) in enumerate(TOPICS,1):
 docs.append({'number':i,'category':cat,'title_fr':title,'summary_fr':summary,'source_url':source,'source_version':'7.4 (2022-10-20)','is_original_rewrite':True})
(out/'CHAPITRES_VK7ZJA.json').write_text(json.dumps(docs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
parts=['# VK7ZJA : table exhaustive des 60 sujets en français\n',
       'Index indépendant **des rubriques et des connaissances** de la version 7.4 (20 octobre 2022). Les descriptions sont des synthèses nouvelles ; consulter [la version source](https://radio.carstenbauer.net/578techmods.htm) pour les photos, valeurs supplémentaires et procédures historiques.\n',
       'Cette liste conserve aussi les sujets périphériques (étiquettes, boîtier, logiciels) afin de ne perdre aucune piste de recherche. Les sources historiques ne prouvent pas automatiquement le brochage d’une variante GD32 de 2024.\n']
for cat in dict.fromkeys(t[0] for t in TOPICS):
 parts.append(f'## {cat}\n')
 for d in docs:
  if d['category']!=cat:continue
  parts.append(f"### {d['number']:02d}. {d['title_fr']}\n\n{d['summary_fr']} [Source VK7ZJA v7.4]({d['source_url']}).\n")
(out/'INDEX_60_SUJETS_VK7ZJA.md').write_text('\n'.join(parts)+'\n',encoding='utf-8')
print('Generated',len(docs),'sections, md bytes', (out/'INDEX_60_SUJETS_VK7ZJA.md').stat().st_size)
