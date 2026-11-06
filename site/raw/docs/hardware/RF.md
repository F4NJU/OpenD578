# Chaine RF : entree de recherche

La vue eclatee montre des blocs RF fonctionnels, pas encore une implantation des composants. Aucun niveau de puissance, broche de PA, type exact de synthese ou ligne de commutation n'est affiche comme mesure sans preuve.

**A relever :** transceiver(s), oscillateurs/TCXO, filtre(s) RX/TX, controle des VFO VHF et UHF, duplexage, amplificateurs, lignes PTT et detecteur de puissance, receptions FM/DMR, squelch/CTCSS, et zones memoire des etalonnages par bande.

Un firmware alternatif doit refuser TX tant que les etats autoritaires (PTT, TX actif, busy, RF et antenne) et la restitution apres erreur ne sont pas qualifies. La fonction satellite reste additive et ne doit pas modifier la NAND ni ignorer l'exclusivite des ressources RF.

**Sources :** [routines RF](../04_RAM_ROUTINES_UI_RF_ET_BROCHAGE.md), [decisions](../01_DECISIONS_ET_HISTORIQUE.md), [erreurs corrigees](../07_ERREURS_CORRECTIONS_HYPOTHESES_ET_NO_GO.md), [programmation/calibration](../PROGRAMMING_AND_CALIBRATION.md).

### Complément matériel

Consulter [QA4818N QUATRE CIRCUITS 26MHZ](QA4818N_QUATRE_CIRCUITS_26MHZ.md) et [audit des fonctions partielles](AUDIT_FONCTIONS_PARTIELLES.md).

Voir aussi [reconstruction des fréquences QA4818N et des registres 0x29/0x2A](QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md), avec analyseur de traces RF et tests de codage C.
