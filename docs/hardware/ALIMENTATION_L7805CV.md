# L7805CV : alimentation régulée +5 V et séquencement du D578

**Observation :** boîtier marqué `L7805CV` en format **TO-220**. Référence connue du régulateur linéaire de tension fixe +5 V, dont la variante STMicroelectronics est donnée pour un courant de l'ordre de 1,5 A **dans les limites d'échauffement, de dissipation et de chute de tension**.

## 1. Brochage du TO-220, à vérifier sur la photo

Vu de **face, inscription lisible, broches orientées vers le bas** sur la variante ST **L7805CV**, les contacts sont :

| Pin | Signal | Usage |
| ---: | --- | --- |
| 1 | IN | Entrée non régulée |
| 2 | GND | Référence masse |
| 3 | OUT | +5 V nominal sous conditions normales |
| Languette | Masse | Liaison de refroidissement et masse, selon boîtier ST |

La puissance dissipée peut être estimée par `P ≈ (VIN − 5 V) × IOUT`. Cette relation explique le besoin d'un radiateur et de condensateurs appropriés, mais **ne donne pas la consommation du poste**, inconnue pour cette branche.

## 2. Ce qui est connu sur la carte

Le bouton **Power** est une **entrée GPIO `PA0`** et ne coupe pas directement l'alimentation du GD32 pendant l'essai SWD réalisé. Cela prouve une possibilité de contrôle logique/sommeil, mais ne suffit pas à déterminer quelle ligne met sous tension le régulateur L7805CV.

Le connecteur microphone comprend une broche **5 V** (contact 2 du schéma constructeur). La sortie L7805CV pourrait participer à ce rail ; **aucune continuité n'a été mesurée** et le site garde cette liaison inconnue.

## 3. Vérifications à faire pour bâtir l'arbre d'alimentation

1. Hors tension, relever le fil d'entrée du 7805 jusqu'au relais, fusible et protection de polarité, en gardant la référence de masse ; mesurer la continuité du 5 V jusqu'à ses charges.
2. Identifier les éventuels transistors de commutation EN/standby et les régulateurs de **3,3 V** secondaires.
3. En fonctionnement normal, mesurer en trois points `VIN`, `VOUT`, masse, et les états quand Power est relâché/appuyé.
4. Relever les courants consommateurs avec instrumentation appropriée, sans court-circuiter ni ouvrir au hasard la ligne 5 V.
5. Documenter la mise sous tension du DMR, GPS, NAND, tuner FM, amplificateurs et afficheur par **mesures** séparées.

## 4. Ce que le GD32 commande

Un L7805CV n'a pas d'interface programmable. Son pilotage éventuel passe **en amont** par un MOSFET/relais/régulateur de validation encore inconnu. Un firmware alternatif doit éviter de désactiver sans preuve un rail alimentant la logique ou les mémoires.

## Références

- STMicroelectronics, famille L78 : <https://www.st.com/en/power-management/l7805.html>
- [Accès CPU/Power et SWD](../02_CPU_FLASH_BOOT_USB_SWD.md) ; [broche Power de façade](../FACADE_GPIO_BOUTONS_CODEUR_VOLUMES_ET_ECLAIRAGES.md).
