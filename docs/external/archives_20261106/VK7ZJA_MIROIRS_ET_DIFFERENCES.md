# VK7ZJA : versions preservees et differences entre miroirs

## Ce que contient le fichier utilisateur

Les copies de la documentation D578 de VK7ZJA v7.4 (20 octobre 2022) sont presentes sur les trois sites suivants :

1. [DB1IG, miroir ayant recue l'autorisation de l'auteur](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), HTML 292 254 octets avec 99 fichiers sauvegardes dont 64 ressources graphiques (styles et icones du CMS compris).
2. [Carstenbauer, v7.4](https://radio.carstenbauer.net/578techmods.htm), HTML 195 697 octets et 46 photos sauvegardees.
3. [Reddicams, copie de la documentation](https://www.reddicams.co.uk/radio/AnytoneJR/578techmods.htm), HTML et 46 photos sauvegardees.

Leurs contenus sont issus du **meme auteur et de la meme documentation**. La presence de plusieurs copies n'etablit pas a elle seule une confirmation independante d'une donnee technique.

## Recoupement par contenu, pas uniquement par nom

Pour les 46 images avec le meme nom dans les collections DB1IG et Carstenbauer, les SHA-256 correspondent **octet pour octet**. Les reproductions permettent la conservation et le secours d'acces, pas une deuxieme observation de la carte.

Les copies Carstenbauer et Reddicams ont chacune six erreurs sur des URL d'image avec espace non encode :

- `578 BT Mic.jpg`
- `578 head connections.jpg`
- `578 KC8GL label.jpg`
- `578 speaker sockets.jpg`
- `578 speaker mod1.jpg`
- `578 speaker mod2.jpg`

DB1IG contient la plupart de ces sujets sous des noms normalises avec des tirets bas. En revanche, **`578 head connections.jpg` n'est pas dans les originaux conserves par cette collecte**. La copie Carstenbauer comprend encore le passage sur une nappe de 40 broches de la facade et fait reference a cette photographie; la transcription DB1IG ne reproduit pas ce passage/image a cet endroit. C'est une difference editoriale reelle entre les versions, et une raison de garder les deux HTML, meme lorsqu'ils portent tous deux l'etiquette v7.4.

Lien a reessayer en encodant les espaces : <https://radio.carstenbauer.net/578%20head%20connections.jpg> (presence sur le serveur non garantie par notre environnement).

## Cartes et architecture

Le texte historique indique: une MCU GD32F303VKT6, une NAND TC58CVG1S3HRAIG, un traitement DMR SCT3258, un codec TLV320AIC3204, quatre QA4818N a reference 26 MHz, un recepteur FM broadcast RDA5802N et des sauvegardes RTC/GPS separees. Des photos montrent une chaine superheterodyne, les blindages, le circuit IF et une ligne de filtrage supplementaire non peuplee.

**Comparaison OpenD578 :** ces composants et fonctions figurent deja dans les fiches materiel, et des bus GPIO/HPI/UART sont etablis par l'analyse OEM V1.21. Ce nouveau ZIP apporte surtout **les photographies et leur hash**, qui manquaient a notre corpus accessible localement. Il ne fournit pas de nouvelle capture de bus du poste de l'utilisateur.

## Documents et photos non contenus dans les trois miroirs

La page VK7ZJA contient des liens vers d'autres ressources: utilitaires AT Options, utilitaire de sauvegarde NAND, firmware DMR SCT3258, outils de recuperation, images FCC, fichiers firmware modifies, etc. **Ces liens ne prouvent pas que les fichiers eux-memes sont dans le ZIP**. Les trois manifests n'inventorient presque que le HTML et ses images.

Le miroir DB1IG ne represente pas l'archive de tout le site DB1IG: les pages `878mods`, `DMRbasics`, les articles de codeplug et l'editeur de contacts n'ont pas ete capturees lors de cette session.

## Preuve et interpretation

- OEM execute sur notre D578 PRO GD32 : valide pour notre revision, a conserver comme tel.
- Photo d'une ancienne revision VK7ZJA : position/architecture documentee pour la carte photographiee.
- Conseil de reparation ou valeur d'alignement VK7ZJA : exemple historique, pas une calibration a recopier.
- Deux copies identiques d'un fichier : redondance d'archivage, pas double confirmation.
