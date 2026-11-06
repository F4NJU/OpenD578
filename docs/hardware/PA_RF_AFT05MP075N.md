# Deux AFT05MP075N : étages de puissance RF VHF et UHF

**Observation physique :** deux transistors NXP de puissance marqués `AFT05MP075N`. L'analyse publiée du D578 indique **un transistor pour la chaîne VHF, un pour UHF**. Cette attribution est crédible mais les positions exactes, les filtres et la commande de polarisation restent à suivre sur la révision PRO GD32 V1.21.

## 1. Technologie et limites d'interprétation

Le AFT05MP075N appartient à la famille **LDMOS RF NXP** adaptée aux bandes VHF/UHF. L'indication de 70 W dans les références commerciales qualifie **la capacité du transistor dans des conditions d'essai**, pas la puissance nominale émise par le poste. Les niveaux de puissance de l'émetteur dépendent de l'alimentation, de la polarisation de grille, de l'adaptation, du filtrage, de la température et du logiciel.

L'étage de puissance est **analogique**. Le GD32 ne dialogue pas avec un AFT05MP075N via UART, I²C ou SPI ; il contrôle indirectement les polarisations, la chaîne d'excitation RF, les commutations RX/TX, les protections et éventuellement la calibration.

## 2. Informations à relever

- Identification de la paire de **grilles / drains internes** suivant le boîtier retenu et le schéma exact NXP ; source généralement reliée au boîtier / masse thermique.
- Alimentation de drain en réception et en émission, découplage et séquence de mise en service.
- Source de polarisation de grille, régulation thermique, réseaux de contre-réaction et filtres de sortie.
- Mesure / protection de courant, tension, température et puissance directe/réfléchie.
- Liaisons de commande vers les éventuels DAC `BH2226`, opamp `SGM8272` et GPIO, **si elles existent après suivi de pistes**.
- Chemin de la sortie PA vers filtres passe-bas, commutateurs et connecteur antenne.

## 3. Ce que le firmware doit gérer

Un pilote TX devra posséder une **machine à états sécurisée** : contrôle d'alimentation, vérification du mode et de la bande, désactivation en RX, configuration RF, activation de la commande de polarisation uniquement pendant l'émission autorisée, et coupure immédiate en défaut. Toutes les calibrations sont propres au poste.

**Aucune valeur de tension de grille, de courant de repos, de gain, de puissance ou de temporisation d'attaque n'est fournie comme consigne de pilotage réel.** En particulier, ne pas déduire qu'un DAC 0–5 V peut être relié directement à la grille.

Les essais à prévoir se font d'abord sur banc de simulation et avec instrumentation RF/charge adaptée. Aucune recherche GPIO active et aucun signal TX ne doivent être exécutés sur la radio dans l'objectif de deviner une broche.

## Références

- NXP, produit AFT05MP075N : <https://www.nxp.com/part/AFT05MP075N>
- Architecture historique VK7ZJA : <https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php>
