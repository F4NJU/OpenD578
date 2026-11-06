# Amplification audio : YD1517P (PRO) et UTC PA1517G (PLUS)

**Observation :** boîtier marqué `YD YD1517P` sur le D578UV PRO et `UTC PA1517G` sur le PLUS. Ces composants relèvent de la famille d'amplificateurs **stéréo 2×6 W classe B**. La fonction électrique d'une broche peut être comparable, sans démontrer que les boîtiers ou l'intégration sont identiques.

## 1. Comparaison fonctionnelle des broches

Sur les versions **DIP18** publiées par UTC et YD, les neuf premières positions sont compatibles en fonction ; de nombreuses autres broches sont des masses thermiques ou de puissance.

| Pin (DIP18/HSIP9 selon version) | Fonction constructeur |
| ---: | --- |
| 1 | Entrée amplificateur 1 `−INV1` |
| 2 | Masse signal `SGND` |
| 3 | Filtrage de rejet d'ondulations `SVRR` |
| 4 | Sortie amplificateur 1 `OUT1` |
| 5 | Masse puissance `PGND` |
| 6 | Sortie amplificateur 2 `OUT2` |
| 7 | Alimentation `VCC` |
| 8 | Commande `M/SS` (mute / standby) |
| 9 | Entrée amplificateur 2 `−INV2` |
| 10 à 18 | Masse ou contacts de dissipation selon boîtier DIP18 |

**Ne pas connecter directement OUT1/OUT2 à la masse** : la documentation D578 historique décrit un montage push-pull / pont de deux canaux destiné à fournir davantage de puissance acoustique. Le 12 W annoncé dans ce montage décrit l'architecture publiée, **pas une puissance mesurée sur la carte PRO ou PLUS de l'utilisateur**. Il faut lire le schéma de brochage correspondant **au boîtier effectivement observé** pour lever toute ambiguïté.

## 2. Quels liens avec le firmware ?

Le `YD1517P`/`PA1517G` n'a pas de registres numériques. La commande logicielle de veille/mute pourrait atteindre `M/SS` via une sortie GPIO, un transistor ou un circuit de sélection audio.

Le banc V11.8 observe un mode `Speaker Mode` avec trois choix `Mic Spk`, `Radio Spk`, `Both`, et distingue :

- **GD32 PA7** : sortie associée au mute du haut-parleur poste dans l'exécution OEM ; continuité vers broche 8 **non mesurée**.
- **Registre RF banque 1 / page 0 / adresse 0x25, bit 4** : autre commande de coupure liée au haut-parleur microphone, mais son chemin physique **non démontré**.
- Potentiomètres PC2/PC5 → ADC interne ; atténuateur U2429G → voies audio ; ces signaux ne sont pas équivalents à une sortie de puissance.

La chaîne complète peut comprendre codec, attenuateur, amplificateur de commande et 1517, sans que l'ordre effectif soit encore prouvé.

## 3. Vérification PRO / PLUS

1. Identifier si PA1517G est dans le boîtier **DIP18, DIP20 ou HSIP9-B** ; la famille UTC existe en plusieurs formats, et l'absence d'un nombre de broches ne prouve pas un composant différent.
2. Contrôler VCC broche 7 et les masses avec le poste à l'arrêt, puis relever la tension de repos sous alimentation.
3. Capturer le **niveau de la broche 8** pour les modes `Mic Spk`, `Radio Spk` et `Both` sans forcer l'activation ou l'émission.
4. Relever les connexions des sorties 4/6 jusqu'au haut-parleur et des entrées 1/9 jusqu'au préamplificateur.
5. Comparer PRO et PLUS uniquement à **boîtier, implantation, résistances et alimentation équivalents**.

## Sources

- UTC PA1517 (PDF constructeur à rechercher) : <https://www.unisonic.com.tw/>
- Exemple de fiche PA1517 avec description et brochage : <https://dtsheet.com/doc/1507666/datasheet>
- Synthèse indépendante de l'amplification D578 : <https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php>
- [Microphone et sélection du haut-parleur](../NOTICE_CHANGELOG_MICROPHONE_V11_8.md).
