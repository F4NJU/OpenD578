# Centre documentaire F1DMG, VK7ZJA et ressources publiques AnyTone

Ce dossier ajoute les connaissances externes au projet **sans effacer ni remplacer** les analyses OEM, les traces, le banc ou les notices deja presentes. Il sert de guide de conservation et de recoupement, avec des versions identifiees.

## Acces par sujet

- [Fiches des sources, miroirs et dates](SOURCES_ET_VERSIONS.md) : F1DMG, theweeks.org, VK7ZJA 7.4, autres miroirs, FCC, constructeurs.
- [Index complet des 60 themes VK7ZJA](INDEX_60_SUJETS_VK7ZJA.md) : couverture des circuits, firmware, CPS, affichage, microphone, test mode, recuperation et modifications.
- [Architecture et valeurs techniques recoupees](VK7ZJA_TECHNIQUE_RECOUPEE.md) : chaine 38 MHz, QA4818N, composants, memoire NAND, reserves RTC/GPS.
- [CPS, bootloader, alignements et maintenance](MAINTENANCE_ET_PROTOCOLES_D578.md) : lecture/ecriture, formats historiques, risques, recoupements avec nos analyses.
- [F1DMG : pistes et etat de recuperation](F1DMG_RECUPERATION.md) : page 20, ancien chemin refroidissement et aides CPS francaises.
- [Inventaire des photographies et documents](PHOTOS_ET_DOCUMENTS_CIBLES.md) : vues PCB/facade et correspondance avec les fiches OpenD578.
- [Sauvegarde privee sous Windows](ARCHIVAGE_PRIVE_WINDOWS.md) : script de capture, provenance et empreintes, sans copie de materiel tiers dans GitHub.

## Accessibilite et droits

La documentation VK7ZJA de 2022 est accessible sur plusieurs **miroirs d'une meme oeuvre**. [La copie DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php) mentionne l'autorisation du titulaire pour son miroir. Cela ne constitue pas une licence generale autorisant des copies publiques additionnelles. **Le site F1DMG ne repondait pas aux essais du 6 novembre 2026**, donc nous ne pouvons pas declarer ses images et textes sauvegardes.

Pour eviter la perte d'originaux, l'outil `tools/archive_sources_privees.py` telecharge les HTML, images et documents accessibles **sur le PC de l'utilisateur** et conserve sans alteration les octets originaux, plus une version locale navigable et un manifeste avec SHA-256. La source publique OpenD578 contient les liens, les valeurs techniques, les analyses et nos propres textes ; les archives integralement copiees restent privees, sous les droits de leurs auteurs.

## Principe de preuve

- **Mesure materielle / firmware OEM execute** : valide pour la revision concernee.
- **Observation statique / simulation** : comportement etablit dans le perimetre des tests.
- **Documentation d'une autre revision** : source de comparaison, et non preuve de cablage sur le PRO GD32 de l'utilisateur.
- **Source historique indisponible** : reference notee, contenu non reconstitue artificiellement.

Conserver les contradictions entre versions et les relever dans le dossier de preuves plutot que de remplacer la vieille information par la plus recente.

## Revue DB1IG du 6 novembre 2026

La [revue des sources DB1IG](db1ig/INDEX.md) complete le present fonds sans supprimer les 60 rubriques VK7ZJA deja archivees. Elle fournit une [comparaison sujet par sujet](db1ig/MATRICE_60_THEMES.md), un [audit des nouvelles decouvertes](db1ig/AUDIT_CROISE_SOURCES.md), des [fiches techniques](db1ig/COMPLEMENTS_TECHNIQUES_D578.md) et un [plan d'exploitation](db1ig/PLAN_EXPERIMENTAL.md). Les traductions et miroirs sont distingues des preuves OEM du poste etudie.

## Revue RadioFoundry et approfondissements complets

- [129 affirmations RadioFoundry comparées au firmware D578](radiofoundry/INDEX.md), avec les écarts de version et les chemins DMR/codec/NAND.
- [Approfondissement individuel des 21 rubriques DB1IG auparavant résumées](db1ig/approfondissements/INDEX.md). Aucune rubrique historique n’a été retirée.
