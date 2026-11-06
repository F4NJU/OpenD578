# CPS, programmation PC et codeplug du D578

**Cible de référence : AnyTone AT-D578UV PRO à GD32F303, application OEM V1.21 (19 juin 2024).**

Cette section rassemble les indices provenant de l'analyse de l'image constructeur, de l'exécution de cette image dans le banc OpenD578 V11.7, des tests du petit éditeur CPS V11.6, et des implémentations tierces. Elle concerne **le protocole de programmation du poste**, pas le protocole d'un éventuel firmware OpenD578 autonome.

## Documents

1. [USB CDC et contrôleur GD32](USB_CDC_GD32_V121.md) : descripteurs, endpoints, énumération, bus et limites de simulation.
2. [Protocole CPS OEM](PROTOCOLE_OEM_V121.md) : PROGRAM, identification, READ, WRITE, END, longueurs, checksums, fin différée.
3. [Structure des canaux et zones mémoire](CODEPLUG_CANAL_OEM_V121.md) : champs de 64 octets, BCD, NAND, éléments inconnus et précautions.
4. [Banc et CPS intégré](CPS_ARCHITECTURE_SIMULATION.md) : chemin exact des octets, sources, procédures Windows/PTY, étendue des essais.
5. [Compatibilité PRO/PLUS et firmware alternatif](COMPATIBILITE_PRO_PLUS.md) : variantes, codes produit, protocoles à ne pas mélanger.
6. [Plan de qualification](CPS_QUALIFICATION.md) : cas positifs, erreurs, perte d'alimentation, écritures différées, conservation des étalonnages.

Références conservées du banc : [USB_CPS_V11_5.md](../USB_CPS_V11_5.md), [CPS_INTEGRE_V11_6.md](../CPS_INTEGRE_V11_6.md), [USB_V121_DESCRIPTORS.json](../USB_V121_DESCRIPTORS.json), [validation_v11_6.json](../validation_v11_6.json), [CHANGELOG_V11_7.md](../CHANGELOG_V11_7.md).

## Matériel et logiciels concernés

```text
CPS constructeur Windows / qdmr / client de test
                  |
       port série USB CDC (GD32 28E9:018A)
                  |
         pile USB de l'application OEM
                  |
           gestionnaire CPS OEM
                  |
      accès logique NAND (canaux et réglages)
                  |
       NAND physique / ECC / copies de secours
```

Le mode de mise à jour du MCU (`UPDATE`, `.spi`/`.CDI`/`.CDD`) est **distinct** du mode de programmation CPS. Les deux ne doivent pas partager les mêmes tests d'écriture. La mise à jour du modem DMR/SCT3258 constitue encore un **troisième chemin**.

## Niveaux de preuve

- **Firmware OEM exécuté en simulation** : les octets sont transmis au contrôleur USB, puis pris en charge par le programme constructeur ; le modèle NAND reçoit les commandes de ce programme.
- **Essai CPS intégré** : un groupe de 32 enregistrements lu et modifié dans le banc, nom retrouvé après une nouvelle session et une finalisation complète.
- **Lecture physique** : observations de l'utilisateur sur le vrai poste. La compatibilité de tous les transferts avec le CPS Windows **n'est pas certifiée par le banc**.
- **Documentation tierce** : qdmr et les cartographies publiées sont des points de comparaison, pas une preuve que tous les firmwares V1.21/2.08 stockent exactement les mêmes champs.

## Ce que le dépôt fournit

- Sources publiques du banc V11.7 comprenant le pont `bench/cps_bridge.py`, le client `bench/cps_probe.py`, le modèle hôte `bench/usb_cdc.py`, le contrôleur `bench/usbd_host.py`, le parseur de canaux `bench/web/mini_cps_protocol.js` et leurs tests.
- Outil **hors ligne, lecture seule** `tools/cps_trace_audit.py` pour analyser les journaux JSONL du pont sans exposer les octets de codeplug dans le rapport produit.
- Aucun exécutable propriétaire CPS, aucune image OEM, aucune base de contacts, aucun codeplug ni étalonnage individuel.

## Première règle pour écrire un firmware alternatif

Conserver la zone calibration OEM et toute donnée dont la fonction n'est pas démontrée. Une émulation du dialogue CPS ne suffit pas : une écriture doit être atomique ou récupérable, respectueuse des pages NAND et de leur ECC, puis vérifiée après un véritable redémarrage. Tant que ces conditions ne sont pas satisfaites, conserver le pilote alternatif en **lecture seule**.
