# Session CDC déconnectée : suivi et diagnostic — V11.5.2

Le message « USB CDC session stopped or changed: disconnected » ne suffit pas
à déterminer la cause sur le PC utilisateur. La déconnexion réelle, le changement
de session et une impossibilité de lire le suivi doivent être distingués.

Un défaut a été reproduit dans l’API : toute erreur de lecture de usb_cdc.json
était transformée en « disconnected ». Un refus d’accès temporaire, notamment
un conflit de partage de fichier sous Windows, faisait donc échouer le testeur
alors que le modèle USB pouvait encore être connecté.

La V11.5.2 renvoie dans ce cas « unavailable » avec un motif et une indication
de reprise possible. Le client attend jusqu’à cinq secondes que le suivi redevienne
lisible. Il ne se reconnecte pas et ne rejoue pas les commandes déjà envoyées.
Avant la mise en file d’un nouvel envoi, le serveur peut retenter la lecture du
suivi pendant environ 100 ms ; l’envoi n’est mis en file qu’une seule fois.
Une vraie déconnexion reste un échec et son motif est enregistré. L’état expose
aussi la dernière commande CDC demandée et une identité du moteur, afin de
distinguer un arrêt du moteur, un redémarrage et USB_CDC_STOP.

Le testeur écrit désormais results/cps_probe_diagnostic.json en cas d’erreur.
Le rapport contient l’étape, les identités de session et les motifs observés ;
il ne contient pas le jeton d’accès ni les octets lus dans les mémoires.

## Essai utilisateur

Extraire la V11.5.2 dans un nouveau dossier, lancer son banc, sélectionner
Analyse OEM / Reprise rapide OEM / Interactif, puis démarrer la simulation.
Lancer TESTER_USB.cmd du même dossier. Il peut connecter l’hôte CDC lui-même.
Si le test échoue encore, joindre results/cps_probe_diagnostic.json pour connaître
la transition réellement observée sur ce PC. Le JSON d’état USB est également
visible dans l’onglet USB & UART.

Les tests simulent une PermissionError de partage sur le vrai endpoint HTTP,
vérifient le retour à la même session sans commande supplémentaire, ainsi
qu’une vraie déconnexion et la limite de durée des reprises. Le pilote et
l’environnement Windows réels restent à éprouver chez l’utilisateur.

Validation finale : 198 tests passent dans l’archive préparée. Un essai avec
le firmware OEM exécuté, détection automatique du port, identification et
lecture mémoire a également réussi. La cause précise de la capture utilisateur
reste à confirmer avec son diagnostic ; le refus d’accès a été simulé en test.
