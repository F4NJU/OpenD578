# D578 PRO GD32 V1.21 — liaisons audio déduites du firmware

8 novembre 2026 — Jean-Philippe (F4EGM), projet OpenD578.

Le contrat de commande audio peut être reconstruit à partir du firmware : entrées acquises, sélection de chemin, gains, coupures et ordre des écritures. Le relevé complet des pistes et de la réponse analogique n'est pas un préalable à la réécriture de ces fonctions. Le banc sert à confronter cette réécriture aux comportements de l'OEM.

Cette étape apporte huit fonctions C comparées aux instructions OEM sur **62 402 cas**, sans différence, et un décodage passif des commandes dans le banc Web 0.13. Elle ne raccorde pas encore le flux sonore complet.

## Image de référence et méthode

La référence est la Flash complète PRO GD32 V1.21 de SHA-256 `e2f2483baf60e2bfcab656e25e949670713222591ef4d611d6089054819a750e`. Les adresses ci-dessous servent à reproduire l'analyse ; la réécriture C n'appelle aucune routine OEM et n'utilise aucune adresse SRAM fixe.

Deux sources de preuve se complètent :

- Les captures 0.11/0.12 proviennent d'un démarrage OEM avec les sauvegardes du projet, puis d'entrées GPIO/ADC/UART. Leurs menus, commandes et lectures NAND sont conservés. Aucune variable OEM n'y a été forcée.
- Le nouveau test différentiel exécute **des routines isolées** dans une instance Unicorn distincte, avec des paramètres et des données RAM de test explicites. Les appels terminaux RF/GPIO sont enregistrés, puis comparés à la réécriture C. Ce test n'est pas présenté comme un nouveau démarrage du poste. Ses données de test ne sont jamais importées par le banc Web.

Le second test vérifie les mots, leur ordre, la suppression des écritures redondantes et la conservation des bits voisins. Il ne vérifie pas les délais électriques entre fronts.

## Commandes retrouvées

| Fonction logique | Liaison ou commande émise | Routine OEM | Résultat établi |
| --- | --- | --- | --- |
| Deux volumes indépendants | U2429, DATA PA13, CLOCK PA14 | `0x0808C354`, `0x0808C3EC` | Mots série, sélection du canal, coupure, table des niveaux |
| Quantification du volume | Valeur acquise → niveau 0…32 | `0x0808B922` | Les 4 096 valeurs ADC 12 bits correspondent à la réécriture |
| Coupure du HP poste | PA7 = 1 coupe, PA7 = 0 ouvre | `0x08090A86`, `0x08090ADC` | Commande logique et combinaison des modes HP |
| Coupure du HP micro | Banque RF 1, page 0, registre `0x25`, bit 4 | mêmes routines, wrapper `0x08072544` | 1 coupe ; 0 ouvre |
| Préférence de chemin du micro | Même registre, bit 7 | `0x080929B6`, wrapper `0x08072574` | Dans l'application standard du réglage : MAIN met 1, SUB met 0 |
| Porte de routage complémentaire | Même registre, bit 2 | `0x080929B6`, `0x08090A22`, wrapper `0x08072514` | Dépend du mode HP, de SUB et du contexte ; ce n'est pas un sélecteur fixe A/B |
| Entrée et code micro FM filaire | Banque RF 0, reg. `0x18`, puis page 1 reg. `0x17` | `0x0806F07C` | Niveau utilisateur combiné au MIC usine, appliqué lors de la configuration TX |
| Calibrations par poste | Lecture NAND puis commandes RF | `0x0801A576` et routines RF | Les valeurs de la sauvegarde restent la source, sans gain usine ajouté par le banc |

La correspondance A → CH1 et B → CH2 de l'U2429 est observée dans les scénarios 0.11. L'attribution permanente de toutes les sources aux sorties nécessite de suivre aussi les commutations de rôle MAIN/SUB. Deux canaux de volume ne signifient pas deux haut-parleurs fixes.

## Modes des haut-parleurs

La routine d'ouverture produit le tableau suivant dans le chemin standard, hors maintien temporaire et hors mode spécial :

| Mode OEM | PA7 | PIO `0x25` bit 4 | Commande logique |
| --- | --- | --- | --- |
| Mic Spk | 1 | 0 | HP micro ouvert, HP poste coupé |
| Radio Spk | 0 | 1 | HP poste ouvert, HP micro coupé |
| Both | 0 | 0 | Deux sorties ouvertes |
| Coupure globale | 1 | 1 | Deux sorties coupées |

L'OEM écrit d'abord la commande du bit 4, si elle change, puis PA7. Le getter `0x08090A10` peut imposer Radio Spk par un état interne distinct du choix sauvegardé. Un maintien temporaire peut aussi empêcher l'ouverture. Ces conditions sont des paramètres explicites des fonctions C ; elles ne sont pas effacées pour simplifier le tableau.

## MAIN/SUB et les deux bits de routage

La routine `0x080929B6` établit, dans son chemin standard :

| Réglage appliqué | Bit 7 | Bit 2 |
| --- | --- | --- |
| MAIN | 1 | 0 |
| SUB avec Both et état de maintien secondaire à 0 | 0 | 1 |
| SUB dans les autres cas standard | 0 | 0 |

Une autre routine, `0x08090A22`, peut ensuite modifier le bit 2 : elle impose 1 pour Both + SUB, ou applique son argument dans les autres cas. La routine `0x08090A4C` peut modifier le bit 7 selon des états auxiliaires. **Lire un bit isolé ne suffit donc pas à reconstituer la source A/B effectivement audible.**

Les captures OEM en RX A confirment SUB `0x0066` → MAIN `0x00E6`, soit le seul changement du bit 7, avec bit 2 déjà à 1 dans les deux états. Cela explique pourquoi une simple table « bit 2 = voie A/B » aurait été incorrecte.

Le bit 7 révèle bien une commande de préférence MAIN/SUB. Le MCU pilote aussi des routes temporaires : le modèle Web présente les commandes reçues et laisse la source effective indéterminée tant que ces autres commutations ne sont pas raccordées. Il ne lit pas le menu en RAM pour fabriquer un résultat.

## Micro FM et calibration NAND

Dans le chemin filaire standard (`cfg+0x21 = 0`), le niveau utilisateur sélectionne deux champs différents :

| Niveau affiché | Sélecteur, reg. `0x18` | Ajustement du code MIC usine | Exemple avec MIC = 54 : page 1 reg. `0x17` |
| --- | --- | --- | --- |
| Level 1 | 2 | +1 | `0x03B8` |
| Level 2 | 3 | −2 | `0x03A0` |
| Level 3 | 4 | 0 | `0x03B0` |
| Level 4 | 5 | 0 | `0x03B0` |
| Level 5 | 6 | +1 | `0x03B8` |
| Level 6 | 7 | +1 | `0x03B8` |

Registre `0x18 = 0x0125 | (sélecteur << 11)` ; page 1 registre `0x17 = 0x0200 | (code appliqué << 3)`, réduit au mot de 16 bits. L'ordre émis est : reg. `0x18`, page 1, reg. `0x17`, retour page 0. Les six niveaux × les 64 valeurs de calibration MIC ont été comparés. Le calcul conserve les débordements de 16 bits de l'OEM aux valeurs extrêmes ; aucun écrêtage supplémentaire n'est annoncé comme identique à l'OEM.

Ce tableau décrit des **codes de commande**, pas une progression en dB. Le changement de sélecteur explique pourquoi le seul ajustement MIC ne décrit pas à lui seul le niveau micro. La formule ne doit pas être étendue au chemin spécial sans analyser ses autres branches.

Les captures 0.12 établissent Level 4 → Level 5 en TX VHF et Level 5 en TX UHF, avec MIC usine 54. La calibration MODV1 = 45 produit les bits bas 90 de reg. `0x40` en VHF ; MODU = 105 produit 210 en UHF. Les champs usine MIC/MODU/MODV1/CTCW proviennent des lectures NAND effectivement transmises au MCU. Aucune commande codec/SCT supplémentaire n'a été observée pendant ces transitions FM : le modèle ne doit pas envoyer automatiquement ce réglage à travers un traitement DMR.

## Réécriture pour le firmware libre

`firmware/hal/audio_control.h` et `.c` fournissent des fonctions C11 sans dépendance au firmware propriétaire : ouverture/coupure HP, préférence de chemin, deux commandes de routage contextuelles, réglage micro FM, quantification et encodage du volume. Elles produisent des plans d'opérations, avec un callback de transport fourni par le firmware libre. Le transport doit gérer la configuration GPIO, les verrous de bus et les impulsions électriques.

Les états dont le sens métier n'est pas encore établi restent explicitement identifiés dans l'en-tête. Ils ne sont pas renommés « Bluetooth », « squelch » ou « réception active » sur une supposition. Le backend reçoit aussi le choix transport RF direct/file, qui n'est pas une garantie de délai au cycle.

Une erreur du callback interrompt le plan et retourne le nombre d'opérations réussies. Après une erreur partielle, l'appelant déduit l'état courant de ce préfixe ; il ne valide pas le mot final d'un plan incomplet. Les fonctions ne commandent aucune mise en émission.

## Validation et suite

| Contrat comparé | Cas sans différence |
| --- | ---: |
| Ouverture HP | 12 288 |
| Application MAIN/SUB | 24 576 |
| Porte de routage bit 2 | 12 288 |
| Route auxiliaire bit 7 | 8 192 |
| Coupure globale | 512 |
| Micro FM standard | 384 |
| Quantification volume | 4 096 |
| Encodage volume, deux canaux | 66 |
| **Total** | **62 402** |

Reproduction depuis le paquet : `python3 preuves/routage_v013/compare_oem_audio.py CHEMIN_FLASH resultat.json`. Dépendances : Python, Unicorn et compilateur C11 `cc`. Le script contrôle l'empreinte de la Flash et compile les sources C du paquet dans un répertoire temporaire. Les résultats sont dans `preuves/routage_v013/audio_contract_differential.json`.

Le prochain travail utile consiste à suivre les autres commutations de sources et le traitement FM jusqu'à un trajet numérique continu dans le banc, puis à brancher les mêmes contrats sur les pilotes du firmware libre. La métrologie fine des amplificateurs et des HP peut venir ensuite. Les contacts de prises qui changent le trajet sans retour au MCU peuvent rester invisibles dans le firmware ; ils demandent un modèle d'environnement ou un contrôle matériel ciblé.

Un OEM fonctionnel dans le banc donnera une base de tests solide pour le firmware libre : mêmes entrées, mêmes commandes attendues et mêmes sauvegardes. La validation sur le poste restera nécessaire pour les effets matériels que le banc ne représente pas. Le DMR reste reporté.
