# Plan de reprise reproductible et critères de passage

## D'abord, combler les octets de sources manquants

Retrouver depuis la bibliothèque ou le poste de travail les images OEM V1.21, full_flash_pass1/2, boot_A/B, capture NAND cinq BIN + logs, ZIP de code Phase60, l'archive cumulative Phase35, les deltas Phase38-47, les ZIP Phase52/53/54/56/57/58/59 et le KiCad V0.3. Les noms figurent dans `catalogue_bibliotheque_221.json`, avec `NOT_EXPORTED` si l'original est absent. Vérifier les SHA de référence avant de travailler. Ne pas prétendre qu'une archive énumérée est incluse.

## Suite simulateur PC, progression naturelle

1. **ADC0 + DMA0 ch0 :** le firmware s'arrête en PC `0x08007A9E` sur écriture à `0x40020008`. Comprendre `ADC0_RDATA 0x4001244C`, l'ordre des 7 canaux, la source de trigger, EOC, interruptions DMA et synchronisation; utiliser une configuration de tests définie et documentée, pas des constantes arbitraires présentées comme mesures réelles. Le buffer cible `0x2000DA76` compte 14 octets. Valider chaque transfert et les retours RTOS. Le codec audio AIC3204 n'est pas la périphérie ADC0 GD32.
2. **Afficheur LCD :** journaliser les écritures OLED/LCD OEM par registres GPIO et décoder la procédure d'initialisation et la séquence de pixels. Construire un affichage PC seulement quand largeur/hauteur/palette et bus sont prouvés. Boutons virtuels selon le mapping de la carte : Power (PA0/EXTI0 déjà trouvé), boutons P1-P6/MENU/EXIT, encodeur PC8/PC9 et PTT **uniquement après qualification**. Interdire l'écriture sur un vrai GPIO du poste depuis l'émulateur.
3. **GPS/audio/DMR :** lier des traces/états définis. Ne jamais inventer une trame GPS ou DMR en tant qu'entrée constructeur valide; utiliser si possible des captures représentatives anonymisées et vérifier le comportement dans la simulation. Séparer ADC GD32 de la communication du codec audio TLV320AIC3204.
4. **Mesure RAM** : scénarios veille, RX analogique, TX analogique, DMR RX/TX, APRS, menus, scan et transition/satellite; suivre stack min, 0/ZI, allocations RTOS, DMA et dépassements sur plusieurs motifs de SRAM, instrumenter les accès périphériques et mémoire. Ne pas calculer la consommation à partir du pourcentage de zéro ou de la seule table d'initialisation.

## Intégration firmware satellite, marche de validation

1. Identifier précisément le format de l'objet canal actif RAM et comparer à l'enregistrement codeplug 64 o; preuve dynamique des noms `SAT:` et du mode analogique. Aucune écriture sur la mémoire utilisateur.
2. Identifier un seul chemin d'entrée/sortie UI OEM et son système de synchronisation effectif; vérifier concurrence, erreurs d'acquisition, exceptions et retour des notifications écran. Préserver propriétaire exclusif LCD.
3. Identifier le vrai setter transactionnel RX/TX du transceiver en remontant depuis les appels bas niveau, puis lecture autoritaire PTT, TX actif, DMR busy, FM busy et état RF. Refus par défaut et restauration complète du contexte radio.
4. Proposer un emplacement Flash et une réservation RAM avec preuves d'absence d'utilisation OEM, contraintes d'effacement et de WCET. La marge Phase60 1 704 octets est **théorique**, la ROM stage n'est pas flashable.
5. Prouver une récupération indépendante sur matériel de test, incluant des cas d'application invalide, sans utiliser le poste principal en première validation; préserver boot et calibrations. Les lectures SWD et l'USB update ne prouvent pas cela.
6. Après toutes les preuves précédentes seulement, construire une vraie enveloppe OEM V1.21 et tester d'abord sur charge RF adaptée et puissance réduite, avec procédures de vérification et rollback prouvées. Conformité radio et allocations constructeur à contrôler.

## Critères NO-GO automatiques

- Fichier source/empreinte constructeur manquant ou différent.
- Firmware `ET_REL`, `ET_EXEC` offline, BSS à 0x30000000 ou ROM preview.
- Mutex LCD non qualifié ou page native APRS inconnue.
- Estado PTT/TX/busy inconnu, setter OEM non prouvé, restauration possible pendant TX.
- Espace Flash marqué FF sans preuve, NAND contenant zone codeplug/étalonnage non comprise.
- Boot recovery uniquement supposé ou dépendant de l'application en panne.
- Tests uniquement émulation PC mais présentés comme essai radio.

La règle générale est de continuer l'analyse et la simulation sans toucher au firmware du poste tant que ces points ne sont pas résolus. Le travail est un projet de reverse engineering matériel/logiciel, pas un patch USB prêt à transmettre.
