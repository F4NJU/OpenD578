# Inventaire des photographies et fichiers a archiver

L'objectif est de **ne perdre aucune piece** : chaque photo ou document identifie dans les pages d'origine doit etre conserve avec son URL, legende, version et empreinte. Aucun de ces fichiers n'est copie dans le depot public sans autorisation.

## Illustrations VK7ZJA 578 (photos a retrouver dans les originaux)

| Sujet/legende de la source | Preuve technique recherchée | Correspondance OpenD578 |
|---|---|---|
| Vue arriere facade, Bluetooth et GPS installes | Placement carte D868BT-SP et ATGM336H, connecteurs GPS u.FL | `docs/hardware/BLUETOOTH_D868BT_SP_ET12.md` ; monographie GPS |
| Vue arriere facade sans Bluetooth | Pistes et points de raccordement de la carte fille | Cartographie MCU et bus Bluetooth |
| Vue face avant facade | Lignes de touches, LED, LCD et potentiometres | `docs/FACADE_GPIO_BOUTONS_CODEUR_VOLUMES_ET_ECLAIRAGES.md` |
| MCU sous LCD | Confirmation du boitier GD32 et de la geographie des GPIO | Brochage CPU et preuves OEM |
| PCB RF dessus | Etages PA, filtres, synthese et connecteurs | Monographie QA4818N et carte RF |
| PCB RF dessous | Circuits LQFP32 masques, FI et chaines A/B | Attribution des quatre QA4818N |
| Filtres quartz 38 MHz | Deux FI et empreintes non peuplees | `docs/hardware/QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md` |
| Reserves de la facade CPU | Sauvegarde RTC versus GPS et references visibles | Dossier preuves RTC/GPS |
| Prise micro et schema micro de bureau | Separation masse audio/masse logique et adaptation PTT | `docs/NOTICE_CHANGELOG_MICROPHONE_V11_8.md` |
| Sorties audio et haut-parleur | Difference de coupure interne/externe | Monographie audio |
| Amelioration blindage RF | Blindages additionnels et ajustement varactors | Chaînes RF ; calibrations |
| Antenne GPS interne | Emplacements u.FL et implantation possible | Monographie GPS |
| Circuit ventilateur/deflecteur | Piste F1DMG `/578a` | Refroidissement ; mesures thermiques |

## Autres ressources a indexer

- Documentation VK7ZJA ancienne : <https://www.theweeks.org/tmp/FILES/Anytone-Mods/578mods.htm>
- Version VK7ZJA 7.4 : <https://radio.carstenbauer.net/578techmods.htm>
- Autre miroir : <https://www.reddicams.co.uk/radio/AnytoneJR/578techmods.htm>
- Copie PDF : <https://www.radiomanual.info/schemi/Vari/Alinco_DR-MD500_DR-MD520_AnyTone_AT-D578UV_mods_and_information_VK7ZJA_2023.pdf>
- Collection D578 et documents FCC : <https://qsl.net/oz1dgq/home-filer/anytone-hints.htm>
- Photos d'homologation (revision ancienne) : <https://fccid.io/T4K-D578UV/Internal-Photos/Internal-Photos-4513250>
- F1DMG, page 20 : <http://f1dmg.free.fr/page-20.htm>
- F1DMG, ancien complement refroidissement : <http://f1dmg.free.fr/578a>

## Organisation conseillee dans l'archive privee

Conserver **l'original** dans `originals/` et la consultation locale dans `offline/`. Ne pas renommer arbitrairement les images : leurs noms de fichiers, chemins et hashes sont utiles pour detecter les duplicates et restaurer des liens anciens. Relier ensuite les constats dans les fiches OpenD578 par URL et numero de photo, sans reproduire les photos dans GitHub.

## Etat du 6 novembre 2026

Les adresses et legendes ont ete recoupees dans les index de sources. Les fichiers images originaux ne sont **pas encore captures dans cet environnement** : les acces HTTP directs necessaires aux telechargements echouent et F1DMG ne repond pas. Le script de sauvegarde destine a Windows effectue cette collecte depuis une connexion externe et produit un journal precis de ce qu'il a effectivement pu recuperer.
