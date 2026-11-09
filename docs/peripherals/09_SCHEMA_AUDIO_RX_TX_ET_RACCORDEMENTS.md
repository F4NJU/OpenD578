# Audio RX/TX — schéma bloc et raccordements du banc

Jean-Philippe (F4EGM) — 9 novembre 2026 — PRO GD32 V1.21.

Le menu **Audio RX/TX** ouvre un schéma SVG zoomable. Il montre l’ensemble fonctionnel, de l’antenne aux HP et du microphone à l’antenne, sans masquer les raccordements encore ouverts. Les traits bleus sont les commandes OEM établies ; les traits verts sont les transferts PCM effectivement raccordés dans ce banc ; les pointillés orange gardent visibles les trajets dont le raccordement exact ou la réponse est encore indéterminé.

## Raccordement ajouté : U2429 avec les commandes réellement reçues

Le fichier WAV d’essai entre explicitement aux bornes IN1/IN2 du modèle U2429. Les échantillons sortent sur OUT1/OUT2, atténués suivant les mots série que le firmware émet sur **PA13 DATA / PA14 CLOCK**. Les commandes sont validées par le décodeur du latch, pas par la position du curseur de volume de la page.

Le traitement conserve l’horodatage : les échantillons antérieurs à une nouvelle commande utilisent l’ancien gain, les suivants le nouveau. Une commande invalide conserve le gain précédent. La coupure U2429 produit un gain nul. Une entrée sans commande de gain connue est refusée, sans inventer de volume initial. Les deux canaux restent indépendants, sauf commande commune OEM.

Dans le panneau **Audio · traversée de l’atténuateur U2429**, choisir un WAV PCM16 de 12 secondes maximum. Un WAV mono est affecté au port choisi ; un WAV stéréo fournit gauche à IN1 et droite à IN2. Démarrer le firmware et lui laisser régler le volume avant cet essai. Exécuter le CPU pour faire progresser le temps virtuel. Le bouton **Écouter / exporter OUT** restitue uniquement les échantillons déjà traités.

Ce fichier est la sortie nominale du composant : **ce n’est pas encore le son du haut-parleur du poste**. L’ordre des amplificateurs et l’affectation permanente des sources à ces entrées ne sont pas inventés. Le temps reprend 120 millions d’unités virtuelles par seconde, sans prétendre au cycle matériel. Les transitoires RC, le bruit et la réponse des amplis ne sont pas modélisés par cette simple atténuation.

## Réception, de A à Z

1. Le signal d’antenne traverse la présélection et les chaînes RF de réception. Les banques sont sélectionnées par PB5/PB2/PC13/PE1, avec PB3 horloge et PB4 SDIO. Leurs rôles LO/FI ne sont pas attribués par leur seul numéro.
2. Les réglages de réception incluent le registre de gain/volume 0x44 ; sa loi en dB reste inconnue. La démodulation FM et le trajet qui fournit les sorties audio A/B ne sont pas remplacés par une copie de l’entrée micro.
3. Les potentiomètres PC2/ADC12 et PC5/ADC15 sont acquis par l’OEM. Sa quantification fournit un niveau 0 à 32, puis les codes de volume série. Le niveau 0 correspond à la coupure.
4. Le U2429 règle séparément les deux atténuations nominales de 0 à −83 dB. Pour un gain en tension : `G = 10^(−A/20)`. Une atténuation de 20 dB multiplie l’amplitude par 0,1.
5. Les commandes HP sont distinctes : PA7=1 coupe le HP poste ; banque 1 / page 0 / 0x25 bit 4=1 coupe le HP micro. Les modes Mic/Radio/Both produisent ces combinaisons, avec les conditions et maintiens OEM.
6. Les amplificateurs MC34119, YD1517 (PRO) ou PA1517 (PLUS), les deux HP et les prises externes forment la fin fonctionnelle du trajet. Leur matrice exacte reste visible en pointillés sur le schéma. Elle n’est pas assimilée aux canaux 1 et 2 du volume sans preuve.

## Émission, du micro à l’antenne

Le réglage AnaMic combine deux commandes : sélecteur RF 0x18 et ajustement du code MIC propre au poste, chargé depuis la NAND. En Level 1 à 6, les ajustements sont respectivement `+1, −2, 0, 0, +1, +1` et les sélecteurs 2 à 7. Le mot page 1 / 0x17 est `0x0200 | (MIC_appliqué << 3)`, avec les comportements de débordement OEM conservés dans les tests. Ce sont des codes, pas des dB.

Les paramètres MODV1/MODU retrouvés commandent le champ de modulation de 0x40, selon la bande du scénario étudié. CTCW se retrouve dans 0x51. Les filtres, limiteurs et transferts physiques ne sont pas déduits du seul code numérique. La consigne TX PA4/DAC0 et les portes PE6/PC4/PD0 sont séparées du gain micro ; une consigne DAC ne donne pas des watts.

Les tonalités et l’APRS TX disposent aussi de la sortie PB9/TIMER3_CH3 en PWM. Le point de mélange analogique avec la modulation n’est pas fermé arbitrairement. Le ROS reste un critère de protection encore ouvert.

## Codec, corrections, égalisation et signalisation

Les demandes au TLV320AIC3204 passent par le HPI du SCT. Les champs connus incluent PGA micro (pas de 0,5 dB), gains numériques ADC/DAC, gains des sorties HPL/HPR/LOL/LOR et champs AGC. Le SCT reçoit trois sections de correction RX et trois TX à 24 kHz, coefficients signés Q14, et des gains Q11/Q12. La fonction nominale des filtres est déjà disponible isolément ; l’ordre du trajet audio effectif, les saturations et l’état interne DSP ne sont pas établis pour toutes les routes.

Le banc n’applique donc pas automatiquement ces filtres à la voix FM simplement parce qu’ils sont reçus au démarrage. Les transitions micro FM VHF/UHF analysées ne changent pas le flux de demandes SCT enregistré.

La branche **PC0/ADC10 → ADC → DMA → SRAM → décodeurs OEM** est un chemin distinct, raccordé à la source WAV de signalisation RX du banc. Le GD32 ne doit pas être présenté comme le processeur PCM universel de toute la voix FM.

## Vue éclatée et QA : corrections associées

Les deux modèles PRO/PLUS reprennent désormais les 80 GPIO de la table courante dans les connexions du MCU. Sa fiche affiche les 86 signaux utiles, avec références et limites. Les IDs historiques des composants et connexions sont conservés pour les photos et anciens liens.

Les quatre pages QA sont nommées par **banque logique et CS**. Les anciens noms LO A/B et FI 1/2 restent seulement des IDs historiques. La commande de fréquence OEM est **0x38 bas puis 0x39 haut**, en unités de 10 Hz, et non les exemples AT1846S historiques 0x29/0x2A. Un nouvel encodeur C indépendant est intégré dans `firmware/rf/qa4818n_oem_frequency.c`, avec tests ; il ne pilote pas le poste.

Voir [état QA courant](../hardware/QA4818N_ETAT_OEM_20261109.md), [tableau IO](../hardware/io/TABLEAU_IO_D578.md), [contrats audio](AUDIO_LIAISONS_LOGIQUES_OEM_V013.md) et [calibrations](07_CALIBRATIONS_AUDIO_OEM_V121.md).
