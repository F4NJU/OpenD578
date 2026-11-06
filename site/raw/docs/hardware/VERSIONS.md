# Versions de cartes

La documentation de reference des routines couvre le **D578UV PRO - GD32 V1.21**. Le modele PLUS integre les observations materielles du **GD32F303** sans transposer les adresses et routines de la V1.21 PRO. La presence de composants identiques sur les variantes UV, UV PLUS, UVIII ou les versions a MCU non-GD32 n'autorise pas a fusionner les registres, memoires ni brochages.

Chaque nouvelle variante doit posseder un fichier independant dans `hardware/models/`, avec un `id` unique, sa reference de carte, un `updated` et les fiches/connexions qui lui sont propres. Le script de publication decouvre automatiquement ces fichiers JSON et ajoute la variante au selecteur.

Les pages des documents indiquent leur portee; les valeurs OEM V1.20 ne sont pas interchangeables avec V1.21. Les fichiers de constructeur ne sont pas redistribues pour cela.


## Écarts PRO / PLUS relevés

| Élément | D578UV PRO GD32 V1.21 | D578UV PLUS observé |
| --- | --- | --- |
| Ampli audio principal | YD1517P | UTC PA1517G |
| Module RF additionnel de réception AM | Connecteurs non implantés selon observation utilisateur | Carte fille avec entrée RF, quartz, CI KT09?5R non identifié |
| Quatre CI LQFP32 grattés | Quatre observés, famille QA4818N probable | À confirmer pour cette révision |
| RDA5802N | Observé | Voisinage de la carte fille rapporté |
| MCU / firmware | GD32F303VKT6, V1.21 etudiee | GD32F303 identifie sur le PLUS ; suffixe/firmware exacts encore a consigner |

Voir [carte PLUS](CARTE_PLUS_AM_KT_NON_IDENTIFIE.md), [comparaison Bluetooth](BLUETOOTH_PRO_PLUS_D878_COMPARAISON.md) et selectionner le modele PLUS dans l'explorateur. Aucun brochage PRO n'est transpose par defaut.

Le support Bluetooth **D868BT-SP** et son module blinde ne sont pas automatiquement identifies comme la carte RF AM du PLUS. Les firmwares Bluetooth ET12, BT01, GD32 et DMR constituent des domaines de mise a jour distincts.
