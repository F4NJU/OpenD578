# Consolidation des preuves, 5 novembre 2026

Ce lot actualise **l'archive complete** OpenD578 destinee a un depot GitHub vide. Il contient les sources publiques V11.7, les notices V11.8 disponibles et les travaux documentaires nouveaux.

## Ajouts verifiables

- Deux sauvegardes sur PCB CPU documentees separement : RTC et GNSS hot start, avec localisations de VK7ZJA, fiche Seiko XH414HG `0,08 F / 3,3 V max`, branche historique MS412 non equivalente prouvee, mesures necessaires.
- Cinq monographies NAND, GPS, ADC/DAC, DMR et bootloader **reconstruites** depuis les analyses disponibles. Elles ne sont **pas** les octets des cinq fichiers historiques perdus.
- CSV GD32F303VKT6 LQFP100, 100 broches, positions physiques + roles proposes ; bibliotheque et feuille KiCad **reconstituees et non cablees**, non validees dans l'interface KiCad.
- Vue materielle PRO/PLUS : noeuds de sauvegarde RTC, GPS, protection alimentation, varicaps et FI reservee avec statut non confirme et documents lies.
- Registre `docs/evidence/CLAIMS.json`, typologie des preuves, capture CPS qdmr recoupee, retours de sources externes et grille de mesures.
- CI GitHub Pages : verification du catalogue et du brochage, en plus des tests CPS, Bluetooth, banc et des liens de documentation.

## Ce qui reste introuvable ou hors depot public

- Binaires physiques boot, NAND, flash OEM, etalonnages et codeplugs personnels : **non publies**.
- Sources compilables exactes de la Phase 60 EXP06 : **absentes** ; les rapports ne remplacent pas les sources.
- Ensemble executable du banc V11.8 : **absent**, les sources publiques V11.7 sont disponibles et les documents V11.8 recuperes.
- Ancien projet KiCad V0.3 et ancienne archive des cinq monographies : **non retrouves** ; les nouvelles reconstructions sont etiquetees.
- Continuites et formes d'ondes RTC, GPS, QA4818N, DAC, HPI et Bluetooth de **nos** deux cartes : mesures reelles encore a faire.

Consulter [les preuves](evidence/INDEX.md), [les originaux a recuperer](archives/ORIGINAUX_A_RECUPERER.md), [la fiche RTC/GPS](hardware/SAUVEGARDE_RTC_GPS_XH414HG.md), [le tableau 100 broches](../hardware/kicad/README.md) et [la matrice des sources](evidence/SOURCES_EXTERNES_RECROISEES_20261105.md).
