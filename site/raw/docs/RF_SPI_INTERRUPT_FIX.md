# Arrêt RF SPI et interruptions — V11.4.1

L’erreur « RF SPI GPIO frame differs from OEM call arguments » est un contrôle
croisé : la transaction réellement décodée sur GPIO est comparée aux arguments
observés à l’entrée des routines OEM V1.21.

Un défaut de l’observateur a été reproduit : un arrêt avant exécution pour livrer
une interruption laissait quand même FrontRunner enregistrer une attente SPI.
La reprise sur la même instruction enregistrait une deuxième attente. Après la
première transaction, l’attente en trop décalait les comparaisons suivantes.
Le contrôle était ainsi capable de rejeter une transaction GPIO correcte.

Correction : les observateurs n’enregistrent plus ces appels lorsque la couche
parente a déjà arrêté l’exécution avant l’instruction. Protection également dans
les observateurs LCD et les couches de télémétrie Lab/Bench. Les contrôles de
bits, de nombre d’horloges et de cohérence SPI ne sont pas désactivés.

Le test test_interrupted_observers reproduit une interruption à l’entrée RF,
puis la reprise et deux écritures différentes. Il échoue sur le code antérieur
(commit 2c4426a) et passe avec la correction. Un deuxième test injecte un véritable
écart et vérifie que le banc s’arrête encore, avec le détail attendu/reçu.

L’erreur conserve désormais les champs attendus et reçus dans RF_control_spi /
last_mismatch du diagnostic JSON, ainsi que les huit dernières trames et le
nombre d’appels en attente. Ce détail est conservé avant consommation de la file.

Limite de reproduction : deux essais OEM avec GPS activé (30 millions d’instructions
supplémentaires à 1 Hz, puis 100 millions à 4 Hz) n’ont pas reproduit l’incident
signalé. Ils ont effectué respectivement 3 816 et 12 181 contrôles SPI, sans
passage observé dans l’ordonnanceur APRS. Le déclenchement APRS automatique du
poste utilisateur n’est donc pas couvert par ces deux essais. Le défaut trouvé
peut expliquer le message mais l’attribution définitive de cet incident demande
le diagnostic de la session concernée, s’il persiste.

Pour un nouvel arrêt : Démarrage & mesures → Exporter le dernier diagnostic.
Ne pas retirer les contrôles SPI pour poursuivre un essai qui n’est pas compris.
