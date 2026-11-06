# Quatre LQFP32 grattés : QA4818N, horloges 26 MHz et récepteurs à FI

**Observation de la carte étudiée :** quatre boîtiers à 32 broches, deux visibles et deux sous blindages, marquages effacés. L'un est proche d'un oscillateur marqué `26.00` (26 MHz, hypothèse à confirmer par mesure).

**Identification par comparaison :** l'étude VK7ZJA d'un D578 nomme **quatre QA4818N**. Cette correspondance est solide à l'échelle de la famille, mais **les quatre circuits individuels de la révision PRO GD32 V1.21 ne sont pas identifiés électriquement**. Il ne faut pas transformer la position photographique en fonction A/B sans suivi de pistes.

## 1. Architecture du récepteur documentée sur la famille D578

- Deux synthétiseurs servent d'oscillateurs locaux pour les voies A et B.
- Les deux autres circuits traitent la réception après un premier changement de fréquence ; la carte emploie des filtres de FI à **38,550 MHz et 38,850 MHz** selon la voie / la chaîne. L'attribution exacte d'une FI à A ou B n'est pas déduite de cette seule mention.
- L'étage RF avant les filtres possède des sélections VHF/UHF et un préfiltrage à varicaps décrit dans l'étude VK7ZJA.
- Une possibilité de troisième chaîne FI non implantée est documentée sur certaines cartes.
- Les QA4818N partagent un *pinout annoncé comme compatible AT1846S*. Cela ne signifie ni registres identiques à 100 %, ni séquences d'initialisation interchangeables.

## 2. Bus radio dans les sources de simulation

Source : `bench/rf_spi.py`, classe `RfSpi`. Le banc récupère un protocole de **24 bits** : **8 bits d'adresse/commande + 16 bits de valeur**, avec sélection de page par registre `0x7F`. Il surveille un bus bit-bang partagé et **quatre sélections logiques**.

| Signal sur GD32, tel que reconstruit par le banc | Rôle du modèle | Limite |
| --- | --- | --- |
| `PB3` | Horloge du bus RF | Aucun lien direct à la broche d'un QA mesuré |
| `PB4` | Données bidirectionnelles | Sens lecture/écriture à vérifier sur PCB |
| `PB5` | CS banque logique 0, actif bas | Attribution à QA physique inconnue |
| `PB2` | CS banque logique 1, actif bas | Attribution à QA physique inconnue |
| `PC13` | CS banque logique 2, actif bas | Attribution à QA physique inconnue |
| `PE1` | CS banque logique 3, actif bas | Attribution à QA physique inconnue |

Un conflit apparent avec d'autres emplois de `PB3/PB4` (par exemple éclairage de façade) **doit être résolu par l'ordre d'initialisation, les activations de CS et les traces physiques**, pas par fusion d'office des deux bus.

**Registres du modèle :** `0x44` est utilisé pour le gain/volume, `0x7F` pour la page. Les lectures `0x0C`, `0x60`, `0x61`, `0x65`, `0x67` peuvent retourner des valeurs **synthétiques** de statut radio au repos. Les interprétations de ces registres découlent des consommateurs OEM, pas d'une validation complète du QA4818N réel.

Le document `docs/04_RAM_ROUTINES_UI_RF_ET_BROCHAGE.md` repère notamment l'écriture de fréquence dans la paire `0x29/0x2A` et la routine native `0x0808AB18` ; ces adresses sont **propres à l'application V1.21**.

## 3. AT1846S : comparaison de brochage, pas identification définitive

Dans une fiche AT1846S, l'interface de commande série porte les signaux : `SCLK` broche **2**, `SDIO` broche **3**, `MODE` broche **7**, `SENB` broche **8**. La référence d'horloge est sur `XTAL1` broche **5** et `XTAL2` broche **6**. Ce tableau est **à vérifier sur chaque boîtier réellement monté** ; on ne doit pas brancher un programmateur sur un numéro de pin calculé par analogie.

Le mode de sélection 2 fils / 3 fils du circuit et la polarité d'une lecture doivent être établis par la forme d'onde. La présence de quatre sélections actives basses dans le modèle soutient l'hypothèse d'une interface série à sélection séparée, sans prouver que les quatre circuits sont tous QA4818N.

## 4. Inventaire des boîtiers de la carte PRO

| Repère documentaire | Emplacement rapporté | Hypothèse fonctionnelle | Preuve nécessaire |
| --- | --- | --- | --- |
| U_QA1 | LQFP32 visible côté zone FI | Synthétiseur ou réception FI | Suivi de RF/IF et CS |
| U_QA2 | LQFP32 visible face inférieure | Synthétiseur ou réception FI | Suivi des filtres 38 MHz et CS |
| U_QA3 | LQFP32 sous blindage, côté 1 | Synthétiseur ou réception FI | Photo macro, continuité, RF/horloge |
| U_QA4 | LQFP32 sous blindage, côté 2 ; voisin 26.00 | Synthétiseur ou réception FI | Oscillateur, sortie IF, CS |

Les quatre repères ne sont pas des références de sérigraphie relevées. Ils servent à éviter que deux circuits soient confondus dans les mesures.

## 5. Méthode d'attribution sans modifier la radio

1. Photographier chaque face avec les blindages retirés, une règle visible et des repères permanents par position.
2. Poste hors tension : relever résistance/continuité entre la sortie de chaque sélection et le contact `SENB` candidat de chaque boîtier, **sans injecter de courant externe dans les lignes alimentées**.
3. Mesurer en fonctionnement normal la fréquence de l'oscillateur `26.00` avec une sonde haute impédance/faible capacité adaptée ; ne pas charger directement le quartz. Le marquage seul ne démontre pas qu'un circuit donné reçoit cette horloge.
4. Capturer passivement CS/CLK/SDIO pendant la sélection A/B, changement VHF/UHF et syntonisation. Enregistrer le n° de banque et la fréquence affichée, comparer les registres `0x29/0x2A`.
5. Associer chaque boîtier au filtre FI et à la voie audio, sans effectuer d'émission RF.
6. Créer dans le modèle une liaison `physical` seulement après continuité mesurée, ou `oem_trace` quand seule la routine est vérifiée.

## 6. Ce qui empêche encore un pilote complet

Restent les brochages spécifiques du QA4818N, la configuration d'horloge, les registres propres au QA, les paramètres usine de déviation/squelch/gain, la séparation VFO A/B, le mapping RF switch/varicaps, les resets IRQ et le timing exact de mise en service. **Les séquences AT1846S constituent une référence d'analyse, pas un firmware QA4818N prêt à flasher.**

## Références

- VK7ZJA, documentation technique du D578 : <https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php>
- Documentation AT1846S, repères de broches et registres : <https://www.alldatasheet.com/view.jsp?Searchword=AT1846S>
- Sources OpenD578 : `bench/rf_spi.py`, `docs/04_RAM_ROUTINES_UI_RF_ET_BROCHAGE.md`.

## Reconstruction fréquence / séquences RF (6 novembre 2026)

L'analyse du bus 24 bits, la formule candidate AT1846S (`0x29`/`0x2A`), les calculs de LO en première FI 38,550/38,850 MHz, les méthodes de corrélation des quatre banques et le pilote de test autonome sont dans [**QA4818N, reconstruction des registres et du PLL**](QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md). Les exemples calculés ne sont **pas** une capture OEM du poste ; le mapping physique reste ouvert.
