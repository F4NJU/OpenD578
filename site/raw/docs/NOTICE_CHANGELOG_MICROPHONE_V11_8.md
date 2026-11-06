# OpenD578 V11.8 : installation, changelog et microphone

Date : 5 novembre 2026. Cible analysée : D578UV PRO, application GD32 V1.21.

Ce document rassemble les instructions de la mise à jour V11.8 et les résultats
sur le microphone. Il ajoute la nouvelle observation des deux voyants blancs.
Il complète la release déjà distribuée ; il ne constitue pas une nouvelle
version du banc et ne modifie pas rétroactivement son archive.

## 1. Installer la mise à jour

L’archive `OpenD578_MAJ_V11_8.zip` est une mise à jour publique à appliquer à
un banc V11.7 fonctionnel. Elle ne contient pas les images constructeur,
captures de reprise et bibliothèques natives nécessaires à un banc OEM autonome.

1. Fermer le banc et son serveur local, ainsi que le pont USB s’il est actif.
2. Garder une copie du dossier V11.7 fonctionnel.
3. Décompresser la mise à jour dans un dossier temporaire.
4. Copier **le contenu** de `OpenD578_MAJ_V11_8/` dans le dossier du banc V11.7.
   Accepter le remplacement des fichiers de code. Conserver les références
   privées et bibliothèques natives déjà installées.
5. Sous Windows, lancer `OUVRIR_BANC_WEB_V11_8.cmd`.
   Sous Linux, lancer `bash OUVRIR_BANC_WEB_V11_8.sh`.
6. Vérifier que le serveur annonce V11.8, puis démarrer le poste simulé.

Pour contrôler les commandes du microphone, connecter le microphone simulé,
puis observer les messages reçus après émission effective des octets UART.
Un état inconnu avant réception d’une trame complète est normal.

Pour le CPS Windows, conserver la paire de ports COM virtuels et le pont local
déjà validés : le pont et le CPS ouvrent chacun une extrémité différente.
Ne pas lancer simultanément un autre client qui programme le même poste simulé.
La validation USB de cette release porte sur l’identification et une lecture
mémoire ; elle ne qualifie pas toutes les écritures du CPS.

L’archive contient également `SOURCES_PUBLIQUES/OpenD578_source_V11_8.zip`,
qui conserve l’arborescence du dépôt pour publication des sources.
Dépôt : <https://github.com/Telectroboy/OpenD578>.

## 2. Changelog V11.8

### Dialogue avec le microphone

- Ajout d’un décodeur incrémental des messages radio vers microphone.
- Acquisition des octets à la fin effective de leur transmission USART0 simulée.
- Décodage partiel de la réception, des portes audio, de l’émission et de la
  sélection du canal principal dans les messages de 16 octets commençant par `53`.
- Affichage séparé des commandes RX/TX reçues pour les deux voies du microphone.
- Conservation des champs inconnus, de l’historique borné et des compteurs.
- Détection des trames incomplètes, mal terminées ou hors profil.
- Aucune réponse inventée par ce décodeur ; les octets `AA` isolés sont comptés.

### Audio analogique et sélection des haut-parleurs

- Parcours du menu constructeur par les touches et l’encodeur simulés.
- Comparaison de `Mic Spk`, `Radio Spk` et `Both` en réception active.
- Observation de PA7 et du registre RF banque 1/page 0/adresse `0x25`.
- Identification de deux commandes candidates de mute indépendantes.
- Exposition des registres bruts de gain `0x44`, sans conversion arbitraire en dB.
- Ajout des rapports et de la documentation de validation.

### Ce qui reste partiel

Le banc observe les commandes matérielles. Il ne route pas encore les
échantillons audio à travers une chaîne complète d’amplificateurs et de circuits
FM. Le microcontrôleur réel du microphone n’est pas exécuté. La présence
synthétique périodique `06` du modèle OEM demeure un mécanisme séparé et annoncé.
Le décodeur UART n’en est pas la source.

## 3. Inventaire physique corrigé

| Emplacement | Voyants | Fonction connue |
| --- | --- | --- |
| Poste | Un voyant rouge/vert | Réception et émission |
| Microphone | Deux voyants rouge/vert, A et B | Statut R/T des voies A et B |
| Microphone | Deux voyants blancs, A et B | VFO actuellement sélectionné, observation utilisateur |

Le manuel distingue bien les indicateurs `A/B Channel TX/RX Indicator` et
`Main Channel Indicator`. Les deux voyants blancs ne doivent donc pas être
confondus avec les deux voyants rouge/vert.

La V11.8 affiche le canal principal décodé. Ce complément documentaire ne
rajoute pas à lui seul une animation des deux LED blanches à l’interface.

## 4. Câblage de la prise microphone

Brochage publié dans le manuel D578UV, **vue de face de la prise selon son dessin**.
Les couleurs sont celles du document ; elles ne remplacent pas une vérification
sur le câble concerné. L’orientation d’une fiche vue côté contacts peut inverser
la lecture si l’on ne reprend pas le même point de vue.

| Broche | Couleur publiée | Désignation | Fonction distinguée |
| ---: | --- | --- | --- |
| 1 | Rouge | URX | Liaison série |
| 2 | Marron | 5 V | Alimentation du microphone |
| 3 | Jaune | UTX | Liaison série |
| 4 | Vert | SP+ | Audio du haut-parleur microphone |
| 5 | Noir | MIC GND | Référence microphone audio |
| 6 | Blanc | MIC | Signal microphone audio |
| 7 | Bleu | SP− | Autre conducteur du haut-parleur |
| 8 | Gris | GND | Masse logique |

Les noms URX/UTX sont reproduits tels quels : le sens côté radio ou côté
microphone doit être vérifié avant de raccorder un analyseur ou un adaptateur.
Le firmware radio utilise USART0 ; PA9/PA10 sont les broches TX/RX candidates
issues de sa configuration. Leur continuité jusqu’au connecteur reste à mesurer.

**MIC GND et GND ne sont pas supposés être une même piste. SP− ne doit pas être
assimilé à une masse.** Le connecteur fournit une paire dédiée au haut-parleur.
La topologie exacte de l’amplificateur et son éventuel fonctionnement en pont
restent à vérifier sur la carte.

La séparation des broches confirme l’existence d’un trajet audio distinct de
la liaison de commandes série. Les trames d’état décodées ne transportent pas
de voix PCM. Cela ne prouve pas que tout le trajet FM interne est analogique :
un codec ou le circuit de traitement radio peut intervenir avant les sorties.

## 5. Commandes du clavier vers le poste

Le modèle utilise une trame de huit octets :

```text
41 ptt touche_active appui_long code 00 00 06
```

Exemples :

```text
PTT appuyé : 41 01 00 00 00 00 00 06
PTT relâché: 41 00 00 00 00 00 00 06
```

| Touche | Code observé/modélisé |
| --- | ---: |
| 0 à 9 | Chiffre + 1 |
| * | 11 |
| # | 12 |
| SUB A/B | 13 |
| Haut | 16 |
| Bas | 17 |
| A, B, C, D | 26, 27, 28, 29 |

Le parseur constructeur se situe dans la zone `0x0808D97C..0x0808DC62`.
Un envoi `AA` apparaît dans le traitement d’une trame de touche. Son rôle
général dans l’ensemble du protocole reste partiel ; aucune réponse universelle
n’est déduite de cet octet seul.

## 6. Commandes du poste vers le microphone

Le constructeur de trame V1.21 est à `0x0808DC62`. Il remplit le tampon
`0x2000E454`, puis appelle l’envoi `0x0808D840` depuis `0x0808DD8C`.
Les offsets ci-dessous commencent à zéro.

| Offset | Interprétation établie ou partielle |
| ---: | --- |
| 0 | Début `0x53` |
| 1 | Activité de réception, voie 0 |
| 2 | Porte audio, voie 0 |
| 3 | Émission, voie 0 |
| 4 | Activité de réception, voie 1 |
| 5 | Porte audio, voie 1 |
| 6 | Émission, voie 1 |
| 7 | Canal principal : `0=A`, `1=B` |
| 8, 10 à 14 | Signification non qualifiée, valeurs conservées |
| 9 | `0x10` dans le profil observé |
| 15 | Fin `0x06` |

Les portes audio sont permutées selon le canal principal dans le code OEM.
Il faut distinguer voie de traitement principale/secondaire et affichage A/B.
Le bit RX ou TX reçu est une commande, pas une mesure de courant dans une LED.

### Les deux LED blanches : champ retrouvé

Le champ le plus directement associé à leur fonction est **l’octet 7**.
Le code copie le sélecteur natif `0x20004237` dans cet octet :

```text
0x0808DD6E : chargement de la base 0x20004214
0x0808DD70 : lecture d’un octet à base + 0x23
0x0808DD74 : écriture dans tampon + 7
0x0808DD8C : appel d’envoi de la trame de 16 octets
```

Le désassemblage a été revérifié pour ce document. La trace d’exécution
préexistante montre les deux états suivants, avec passage à B après SUB A/B :

```text
Principal A : 53 00 00 00 00 00 00 00 00 10 00 00 00 00 00 06
Principal B : 53 00 00 00 00 00 00 01 00 10 00 00 00 00 00 06
```

Le changement figure au pas d’instruction 77 255 217 dans cette trace.
La sélection reste B pendant l’émission, dont le champ TX est distinct :

```text
TX sur B    : 53 00 00 00 00 00 01 01 00 10 00 00 00 00 00 06
```

Trois éléments convergent : le champ du firmware, le manuel `MAIN A/B`, et ton
observation des deux LED blanches. **L’association octet 7 → sélection des LED
blanches est donc fortement étayée.** Le modèle de commande proposé est :

| Octet 7 reçu | LED blanche A commandée | LED blanche B commandée |
| ---: | --- | --- |
| 0 | Allumée | Éteinte |
| 1 | Éteinte | Allumée |
| Autre valeur ou trame invalide/incomplète | Indéterminée | Indéterminée |

Ce tableau exprime l’interprétation à implémenter, pas une mesure électrique.
Le numéro de GPIO interne au microphone, la polarité de ses sorties et son
éventuel circuit de commande des LED restent inconnus. L’analyse présentée
porte sur le firmware du poste, pas sur un firmware extrait du microphone.

Pour une validation définitive, une capture passive URX/UTX sur le matériel
pourrait comparer A, B, TX et RX avec les LED visibles. Elle permettrait aussi
de vérifier les délais et les autres champs sans modifier le poste.

### Voyants rouge/vert

Les champs réception et émission fournissent les commandes candidates vertes
et rouges des deux voies. L’interface les expose séparément de l’état physique,
qui reste non qualifié. Si RX et TX sont présents simultanément, le décodeur
ne fabrique pas une priorité de couleur non démontrée.

L’octet 12 vient d’un autre réglage natif. Il n’est pas attribué aux LED
blanches, à un gain ou au choix du haut-parleur sans preuve supplémentaire.

## 7. Sélection du haut-parleur : résultats

Menu : `Settings → Radio Set → Voice Func → Speaker Mode`.
Les choix sont `Mic Spk`, `Radio Spk` et `Both`. `Mic Spk Set` est un réglage
distinct de source, dont le routage complet reste à qualifier.

La table vocale `0x080C550C..0x080C5540` contient 14 entrées, dont Speaker Mode,
Mic Spk Set, Max Vol Level, DigiMic Level et AnaMic Level.

Le sélecteur Speaker Mode est `0x2000431B`, distinct du sélecteur principal
`0x20004237`. Le chemin `0x08090A86` commande PA7. Les routines `0x08072514`
et `0x08072544` passent par `0x08070A8C` et modifient des bits du registre RF
banque 1/page 0/adresse `0x25`.

Comparaison obtenue par les menus, en réception active :

| Choix | Sélecteur | PA7 | Registre RF | Bit 4 |
| --- | ---: | --- | --- | ---: |
| Mic Spk | 0 | Haut | 0xE6 | 0 |
| Radio Spk | 1 | Bas | 0xF6 | 1 |
| Both | 2 | Bas | 0xE6 | 0 |

Au repos, avec Both, PA7 est haut et le registre vaut `0xF0`.
Cela étaye deux commandes de coupure actives à un : PA7 pour le haut-parleur
du poste, et le bit 4 pour celui du microphone. Leur continuité vers les
amplificateurs reste à mesurer. Le bit 2 du même registre reste non attribué.

Le compteur de configuration codec est resté à 24 pendant cette comparaison.
Ce résultat oriente vers des commandes de mute distinctes ; il n’exclut pas
l’intervention du codec dans d’autres fonctions ou dans le trajet audio.

## 8. Fidélité du modèle et validation

Les adresses OEM de ce document sont des preuves d’analyse propres à V1.21.
Le modèle matériel ne doit pas les utiliser pour décider de ses sorties.

- Le décodeur microphone suit uniquement les octets UART effectivement transmis.
- L’observateur audio suit les sorties GPIO et les transactions RF décodées.
- Aucune écriture de RAM OEM n’a été utilisée pour forcer les choix de menu
  dans la comparaison des haut-parleurs.
- Une broche en entrée ou en fonction alternative n’est pas présentée comme
  une sortie GPIO pilotée.
- Les gains restent des valeurs brutes tant que leur loi n’est pas établie.

Validation réalisée pour V11.8 : **230 tests Python réussis**, contrôles Node
du CPS existant, puis application de la mise à jour sur une copie de V11.7.
Le contrôle de cette copie a confirmé une commande microphone reçue, PA7,
l’identification USB et une lecture de 16 octets à `0x02FA0000`.

Une séquence de 27 millions d’instructions supplémentaires a livré 12 trames
complètes au décodeur connecté, sans erreur de format, sans message hors profil
et sans débordement USART0. La transition A/B citée plus haut provient d’une
autre séquence ; elle n’est pas attribuée à tort à ces 12 messages.

Le CPS Windows original et les lanceurs Windows n’ont pas été exécutés ici.
Les menus ont été examinés sur les images LCD produites par le moteur.
Il n’y a pas eu de test automatisé de l’interface navigateur ni d’accès au
poste physique pour cette validation. Tous les anciens scénarios n’ont pas
été rejoués dans cette release.

## 9. Suite du travail

1. Ajouter aux observations de commande les deux LED blanches à partir de
   l’octet 7 reçu, avec état inconnu avant trame valide.
2. Confirmer le protocole et l’effet physique par capture passive sur le micro.
3. Identifier les amplificateurs, le câblage audio et les commutateurs de source.
4. Relier les commandes de mute et de gain aux échantillons réellement traités.
5. Qualifier ensuite la boucle FM, le CTCSS, le GPS, l’APRS TX et le satellite.

Le Bluetooth audio reste à développer. Le DMR reste hors de la campagne
analogique actuelle. Une réussite de décodage UART ne valide pas à elle seule
une chaîne FM ou APRS complète.

## 10. Références et traçabilité

- Application analysée : `D578UV_GD_V1.21_20240619.CDD`, base `0x08006000`.
- SHA-256 : `02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a`.
- Manuel D578UV, brochage et schéma du microphone, pages imprimées 7 et 8 :
  <https://www.csi-radios.com/content/support/AnyTone/AT-D578UV/User%20manual.pdf>.
- Sources du banc : `bench/microphone_control.py`, `bench/lab_inputs.py`,
  `bench/board_observations.py`, `bench/analog_audio_control.py`.
- Détails de release : `docs/CHANGELOG_V11_8.md`,
  `docs/MICROPHONE_UART_V11_8.md`, `docs/ANALOG_AUDIO_ROUTING_V11_8.md`,
  `docs/validation_v11_8.json`.
- Les nouvelles informations physiques sur les LED blanches proviennent de
  l’observation utilisateur du 5 novembre 2026.

Les images constructeur et les captures privées ne sont pas incorporées à ce
document. Les résultats de code et de simulation sont distingués des mesures
de continuité et des essais matériels qui restent à réaliser.
