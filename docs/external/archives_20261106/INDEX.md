# Archive utilisateur du 6 novembre 2026 : inventaire, resultats et lacunes

Audit effectue sur l'archive privee `20261106T102717Z.zip` fournie par le mainteneur, et comparaison avec le depot OpenD578 consolide a la meme date (revue RadioFoundry/DB1IG). Cette rubrique est un ajout, **aucun ancien resultat n'a ete remplace**.

**Ne pas ajouter l'archive originale de 113 Mio au depot GitHub public** avant clarification des droits de republication, notamment pour les photos, documents et listes de contacts. Elle reste disponible localement chez son proprietaire. Les chemins et hashes donnent un moyen de retrouver et verifier chaque original.

- [Bilan quantitatif et preuves d'integrite](BILAN_ARCHIVE_ET_INTEGRITE.md)
- [F1DMG : deux pages et documents reels nouvellement recuperes](F1DMG_APPORTS_REELS.md)
- [F1DMG : relevés pratiques, offset, scan, ventilation et modifications photos](F1DMG_RELEVES_PRATIQUES.md)
- [VK7ZJA : comparer les versions, les photos et les miroirs](VK7ZJA_MIROIRS_ET_DIFFERENCES.md)
- [Tableau de correspondances avec les analyses OpenD578](ECARTS_AVEC_DEPOT.md)
- [Liste des acquisitions encore a faire, classées par priorite](RECUPERATION_ET_PRIORITES.md)

## Provenance et discipline de preuve

Le fichier utilisateur contient la sauvegarde *reelle* des pages. Pour chaque preuve: utiliser `summary.json`, le `manifest.json` de sa source, l'URL, le SHA-256 et le chemin relatif sous `originals/`.

Les descriptions d'operations OEM et les photographies de cartes d'anciennes revisions ne remplacent pas les tables GPIO, UART et NAND **deja validees par l'execution du firmware D578 PRO GD32 V1.21**. Les astuces d'utilisation CPS ne doivent pas etre presentees comme des structures binaires decouvertes dans le codeplug. Les procedures de reconfiguration et d'etalonage restent historiques et ne sont pas des consignes d'ecriture sur un poste sans sauvegarde.

## Correction d'une affirmation precedente

La notice ancienne `docs/external/F1DMG_RECUPERATION.md` indiquait que F1DMG etait inaccessible depuis notre outil Web. **L'archive importee confirme maintenant la sauvegarde effective des pages `page-20.htm` et `page-22.htm` avec leurs images et plusieurs fichiers.** Les deux affirmations correspondent a deux modes d'acces differents, pas a des versions concurrentes du materiel.
