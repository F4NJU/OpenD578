# Voyant de statut : bus retrouvé et modèle V11.7

Le voyant était volontairement neutre : le banc ne connaissait pas son chemin
de commande. Le faire suivre d’une variable RX/TX OEM aurait masqué une panne
du pilote. Cette révision décode le signal série réellement envoyé.

## Recoupements

Le bootloader du dump complet contient une routine à `0x080042BA` : émission de
huit bits LSB d’abord, donnée PE3, horloge PE4. La boucle de mise à jour appelle
cette routine avec `0x00`, puis `0x10`. L’utilisateur observe le voyant rouge
clignotant dans ce mode. La routine applicative correspondante est autour de
`0x0808A400`, avec appels GPIO aux retours `0x0808A416`, `0x0808A424`,
`0x0808A42E`, `0x0808A43C` et `0x0808A454`.

Un scénario exécuté sur l’OEM V1.21 injecte une porteuse, la retire, presse le
PTT du microphone et le relâche. Les fronts GPIO donnent :

| Étape observée | Octet LSB-first | Vert, bit 3 | Rouge, bit 4 |
| --- | --- | --- | --- |
| Réception avec squelch ouvert | `0x4E` | 1 | 0 |
| Retour au repos | `0x46` | 0 | 0 |
| Émission | `0x56` | 0 | 1 |
| Retour au repos | `0x46` | 0 | 0 |

La liaison et la séquence sont donc établies dans le firmware exécuté.
La correspondance vert/rouge est une inférence croisée avec le comportement
physique décrit par l’utilisateur ; pas une mesure de continuité ni une
identification du circuit pilote. Les autres bits ne sont pas interprétés.
Les chronologies du squelch porteuse et de la porte audio ne sont pas
identiques : ce scénario ne démontre pas le comportement du voyant avec un
CTCSS incorrect ou dans tous les modes de balayage.

## Modèle

`bench/status_led.py` reçoit les changements de GPIOE. Il échantillonne PE3 sur
les fronts montants de PE4 quand les deux broches sont configurées en sortie,
assemble huit bits et expose l’octet brut. Il n’utilise ni PC OEM, ni pointeur
RAM OEM, ni indicateur logiciel de réception ou d’émission. Le mode matériel
partage ce même décodeur et accepte donc une autre disposition du firmware.

La page affiche rouge/vert/repos depuis cette commande décodée. Avant le premier
mot complet, l’état reste inconnu. Une reprise rapide avec l’ancienne capture
RAM n’invente pas la dernière commande du bus absent de cette capture.
Les bits partiels et l’historique borné sont annoncés. Les changements de mode
GPIO interrompent l’assemblage. Ce modèle de commande numérique ne reproduit
pas encore les courants, l’éventuel multiplexage ni les transitoires internes
d’un circuit physique dont la référence n’est pas identifiée.

Le test `LED_bus` vérifie l’ordre des stimuli et des quatre réponses depuis les
bits du bus. Une réponse de mauvaise couleur est un échec ; une trace tronquée
ou partielle reste incomplète. Ce test ne lit aucune variable OEM RX/TX.

Les LED du microphone restent inconnues. Des trames radio → microphone
commençant par `0x53` et longues de 16 octets ont été enregistrées, mais la
signification de leurs champs n’est pas qualifiée. Elles sont affichées brutes.
Le modèle OEM emploie aussi une présence/activité microphone synthétique
(`0x06` périodique) : cela ne prouve pas une émulation de son microcontrôleur,
ni que le microphone a exécuté les commandes des LED ou du haut-parleur.
