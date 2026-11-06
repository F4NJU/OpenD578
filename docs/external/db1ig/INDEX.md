# DB1IG : revue croisee des connaissances AnyTone

**Revue du 6 novembre 2026.** Les pages examinees comprennent les miroirs VK7ZJA D578 v7.4 et D868/D878 v20, la synthese DMR, le guide de creation d'un codeplug, l'editeur de contacts et son mode d'emploi. La traduction allemande du miroir n'est **pas** une seconde preuve independante.

- [Inventaire des nouvelles decouvertes, source par source](AUDIT_CROISE_SOURCES.md) : evaluation technique et priorites OpenD578.
- [Complements techniques detailles](COMPLEMENTS_TECHNIQUES_D578.md) : microphone resistif, mises a jour, maintenance, radio, GPS, filtrage, calibration et controles.
- [Matrice comparative des 60 rubriques historiques](MATRICE_60_THEMES.md) : existant dans OpenD578, complement, provenance et action, sans supprimer l'ancien index.
- [Plan de validation et d'exploitation](PLAN_EXPERIMENTAL.md) : actions non destructives dans le firmware OEM et dans le banc, distinguant preuves et recoupements.
- [Registre des sources et decouvertes au format JSON](SOURCES_ET_DECOUVERTES.json) : identifiants stables et recherches futures.
- [Table CSV de comparaison](MATRICE_60_THEMES.csv) : filtrable dans un tableur.

Le [centre precedent des sources externes](../INDEX.md) et les [60 themes deja inventories](../INDEX_60_SUJETS_VK7ZJA.md) restent en place. Cette revue leur est **additive**. Les photos, textes integraux et binaires tiers ne sont pas copies dans le GitHub public sans autorisation. Les sources exactes sont liees dans chaque fiche.

## Regles pour les statuts

1. Un GPIO, une trame ou une fonction constates en execution OEM restent **valides pour le poste et la revision testes**.
2. Une information historique de VK7ZJA, meme detaillee, reste identifiee comme **reference D578 historique** tant qu'elle n'a pas ete mise en correspondance avec le PRO V1.21 ou le PLUS examine.
3. Une simulation de peripherique prouve le comportement du modele, sauf si les lectures/ecritures OEM correspondantes ont ete observees.
4. Les valeurs d'exemple d'un autre poste ne sont **jamais** les calibrations de l'unite etudiee.
5. Une traduction, un miroir ou une citation repetee n'est pas une preuve independante.

## Reprise des rubriques à développer

Les [21 fiches d’approfondissement](approfondissements/INDEX.md) complètent la matrice du 6 novembre. Elles relient chaque point aux documents OEM déjà présents et aux conditions de test.
