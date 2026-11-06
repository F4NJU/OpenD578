# Sauvegarde AnyTone : bilan et controle d'integrite

## Provenance

Archive utilisateur: `20261106T102717Z.zip`, generee le 6 novembre 2026. Racine interne `20261106T102717Z/`. Elle comprend les HTML **originaux**, les fichiers enregistres, des copies `offline/`, des indexes et des manifests. Un fichier original est considere present uniquement lorsqu'il figure dans le ZIP **et** que son contenu correspond au SHA-256 enregistre par le telechargeur.

| Fonds | Ressources reussies | Tentatives en erreur | Pages HTML | Images | PDF/DOC (type indique) |
| --- | ---: | ---: | ---: | ---: | ---: |
| F1DMG | 458 | 53 | 211 | 218 | 15 |
| VK7ZJA : DB1IG | 99 | 0 | 1 | 64 (y compris ressources graphiques du site) | 0 |
| VK7ZJA : Carstenbauer v7.4 | 47 | 6 | 1 | 46 | 0 |
| VK7ZJA : Reddicams | 47 | 6 | 1 | 46 | 0 |
| OZ1DGQ/QSL | 2 | 5 | 1 | 1 | 0 |
| TheWeeks | 0 | 1 | 0 | 0 | 0 |
| **Total** | **653** | **71** | **215** | **375** | **15** |

Le ZIP contient **1008 entrees** et environ **163 Mo de donnees decompressees**. Le nombre de pages de F1DMG est trompeur: les listes de repertoires Apache ont ete rapatriees avec de multiples variantes de tri `?C=...;O=...`; le crawl ne represente pas 211 articles AnyTone distincts. Parmi les pages avec texte pertinent identifiees, `page-20.htm` et `page-22.htm` sont les principales. Une dizaine de milliers d'octets de HTML peut aussi correspondre a un repertoire, pas a une documentation technique.

**Controle effectue:** les 653 fichiers a etat HTTP 200 sont presents et correspondent individuellement au SHA-256 de leur entree `manifest.json`. Aucun nom de fichier du ZIP ne se repete. Cela confirme l'integrite de la sauvegarde et de son inventaire, **pas** la validite technique de toutes les affirmations des auteurs.

## Limites objectives

- Pour F1DMG, 53 echecs de collecte, dont des anciennes URL 404 (`/578a`, `/578b`) et d'autres fichiers de sections sans rapport avec le D578.
- La page TheWeeks echoue pour un certificat TLS refuse sur le PC collecteur (`CERTIFICATE_VERIFY_FAILED`). Le contenu historique de VK7ZJA se trouve sur plusieurs autres miroirs recuperes.
- Les miroirs Carstenbauer et Reddicams perdent six images chacun, car le telechargeur n'encode pas les espaces des URL. Cinq de ces images sont recuperables directement dans la copie DB1IG; le cas `578 head connections.jpg` reste absent de la sauvegarde.
- QSL/OZ1DGQ: trois erreurs d'URL non encodee et deux documents introuvables (404). Les rapports FCC en PDF ne font pas partie de cette collecte.
- La page `RadioFoundry` et les documents `qdmr` et `CodeplugStudio` ne figurent pas dans ce ZIP. Leur connaissance est presente dans des *documents du depot*, pas dans ces originaux sauvegardes.
- Les ZIP/RAR, codeplugs `.rdt`, fichiers d'aide `.HPT` et videos `.mpg` accessibles par des liens de F1DMG ont en majorite ete **ignores par le filtre d'extensions de l'outil**. Ils ne doivent pas etre marques definitivement inaccessibles.

## Recoupement photographique

Le miroir DB1IG contient 64 ressources graphiques au sens large. Pour les **46 images** de D578 ayant le meme nom dans DB1IG et Carstenbauer, les empreintes SHA-256 sont identiques. Ce sont donc, pour ces images, des copies exactes et non deux mesures independantes. Les photographies d'anciennes cartes doivent conserver leur attribution de revision.

Les fichiers CSV de listes de contacts de plusieurs dizaines de Mo sont archives, mais leur contenu est date et comporte potentiellement des identifiants de correspondants. Les garder prives et ne pas les publier comme un codeplug de reference universel.
