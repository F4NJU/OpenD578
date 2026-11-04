# Moteur satellite OpenGD77, code compilé et stratégie d'intégration

## Architecture satellite recherchée

Le portage est une **fonction additionnelle**, pas un remplacement du firmware AnyTone par OpenGD77. Le moteur orbital OpenGD77/PLAN13 et les routines de passes sont isolés en composants C. Les TLE sont sélectionnés à la demande, mis en cache pour **un satellite actif**, avec au plus 25 entrées TLE potentielles dans l'adaptateur. Le constructeur conserve l'interface, les timers, les fréquences et la sécurité RF; le module satellite propose des résultats, sans écrire directement dans le transceiver.

Décision de charge : **8 itérations PLAN13 au plus par tranche**, **100 ms entre tranches** de recherche, aucun thread nouveau. Budget d'affichage de la page Selected `D578_UI_MAX_OPS=8`, au lieu de 16 initialement. Le contrat RF invalide toute proposition si UI indisponible, génération changée, RTC/GPS/TLE non fiables, PTT ou busy. Phase32 a corrigé une erreur de validation : demander l'état busy/PTT vivant juste **avant** toute proposition RF, et ne jamais utiliser seul un booléen `radio_safe` mis en cache.

## Versions et métriques sans confusion

| Date / phase | Code / tests | Statut |
|---|---|---|
| Phase9 | Moteur PLAN13: 30/30 résultats AOS/LOS alignés avec OpenGD77 sur jeu de vecteurs. | Validation hôte relative à l'upstream, non à une orbite réelle moderne. |
| Phase26 | 18 modules compilés Cortex-M4 `-Os`, 16 503 o code/const non liés, 288 BSS, 133 tests Python; audit 43 TBB/TBH. | `ET_REL` non flashable. |
| Phase38-47 | 21 modules, 19 129 o code/const non liés après réduction Phase40, BSS 288, 28 symboles externes non résolus. | `ET_REL`, ne pas utiliser comme firmware. |
| Phase52 | 22 modules, 20 039 o texte/const non liés, BSS 288, 28 références externes, tests Doppler/restore simulés. | Préparation intégration, non flashable. |
| Phase53 | Outil `audit_v121.py` et 12 tests unitaires, réellement présents dans ce dossier et rejoués avec succès. | Aucun patch radio. |
| Phase54/56/57/58/59 | Archives EXP02 à EXP05, softfloat, ROM stage et préintégration, existantes dans Library. | Octets non récupérés ici, éviter conclusions supplémentaires. |
| Phase60 EXP06 | 30 sources liées pour Cortex-M4 Thumb `-Oz`, softfloat, ELF `ET_EXEC` texte/const **14 680 o**, BSS **288 o**, sans externe non résolu ni instruction FPU; aperçu ROM à `0x080F0000`. | **Pass-through inactif; aucun .CDD/.CDI/.spi modifié.** |

## Phase60, conception `SAT:IDENTIFIANT` documentée par le README original récupéré

- `phase60/src/d578_sat_channel_trigger.{h,c}` : nom sur **16 caractères**, préfixe `SAT:` et identifiant comme `ISS` ou `SO50`, lecture **sans écriture** d'un record codeplug de **64 octets**, extraction BCD RX/TX et refus de canal numérique ou de valeurs manifestement fausses. La position du nom `+0x23` est documentée par qdmr **dans le record codeplug** uniquement. Elle **n'est pas vérifiée dans la structure RAM OEM de la mémoire courante**. Le CTCSS reste à la charge de l'OEM.
- `phase60/src/d578_sat_tle_select.{h,c}` : recherche de TLE au maximum dans **25 slots**, jamais création de TLE arbitraire ni mise en marche si éphéméride périmée ou absente.
- `phase60/src/d578_sat_popup_model.{h,c}` : composition des lignes textuelles `SAT:SO50`, `RX 436.79500`, `TX 145.85000`, **sans appel LCD**.
- `phase60/audit_oem_ui_v121.py` : contrôle des ancrages UI et du sémaphore dans les octets de l'image constructeur.
- `phase60/build_exp06.py` : liaison des 30 sources, aperçu à `0x080F0000` et point d'entrée UI `0x080F3244`, simple relais constructeur **inactif**.
- 26 tests de détection, 6 cas d'affichage, 5 recherches TLE sous tests normaux/UBSan, plus 100 000 cas adversariaux sous chacun des deux modes, trois mutations OEM invalides rejetées. Tout cela est **rapporté par le README Phase60**, non rejoué ici car le ZIP de cette phase n'a pas été récupéré.
- Budget Flash: **4 pages candidates 16 384 o**, **14 680 o** à loger, marge théorique **1 704 o**, mais les quatre pages contiennent une table CJK; **ce n'est pas une zone vierge** et le risque de propriété/effacement demeure. Emplacement non autorisé.
- RAM: **608 o état persistant satellite non alloué**, pile additionnelle non bornée. L'ELF utilise une adresse BSS sentinelle `0x30000000` **invalide volontairement**. Aucune exécution matérielle possible depuis ce build.

**Important :** cette livraison contient le README original exporté en texte, mais **PAS** les `.c/.h` exacts de la Phase60, le `.elf`, ni le `satellite_rom_ONLY_STAGE60.bin`. Un petit parser de référence a été réécrit dans `08_OUTILS_REPRISE/` pour illustrer le contrat et tester le principe; **ce code de référence n'est pas le code historique Phase60 et ne doit pas être assimilé à celui-ci**.

## Pourquoi l'intégration ne peut toujours pas être activée

1. Struct active channel OEM RAM: pointeur `0x2000071C` et mode à `+0x08` observés, mais ABI du champ nom RAM non confirmée, même si le nom codeplug est à `+0x23`.
2. Aucune interface OEM validée pour obtenir un bail LCD exclusif, identifier avec certitude la page APRS, saisir/restituer proprement l'état de l'UI, et gérer les concurrentes natives.
3. Les vrais getters PTT/busy RX/DMR, le setter atomique RX+TX, les limites RF et les conditions de fin de transmission sont **non prouvés**. Les routines BCD et GPIO documentées ne suffisent pas.
4. Aucun fournisseur TLE OEM, horloge UTC étalonnée ni observateur GPS sûr n'est relié dans l'application. Un TLE arbitraire ne doit pas être accepté pour faire tourner le moteur.
5. Aucune adresse Flash libre, RAM sûre ou stratégie de rollback indépendante n'est certifiée. Les blobs de prévisualisation ne doivent jamais être injectés.

## Traitement Doppler exigé

Lire l'horloge et la position, propager le TLE, calculer la vitesse radiale, construire **une proposition** RX/TX dans l'unité et l'arrondi attendus de l'OEM, vérifier en contexte les limites et l'état RF, puis demander une transaction OEM qualifiée quand RX/TX sont autorisés. Sur désélection, panne de TLE, perte GPS, interruption d'UI ou sortie du mode, restaurer **tous** les champs radio sauvegardés; une restauration pendant TX est aussi interdite. Aucune fréquence Doppler n'est écrite dans codeplug, Flash haute ou NAND.

La compatibilité avec APRS et la reprise de l'affichage de trame reçue restent une **piste**, pas une API documentée. Un simple préfixe `SAT:` dans une mémoire est une bonne entrée ergonomique mais ne remplace pas la qualification des invariants hardware.

## Sources à retrouver

`D578_SAT_V121_EXP06_PHASE60_SAT_CHANNEL_NONFLASHABLE_2026-11-03.zip` (375 046 o selon la bibliothèque), `D578_SAT_V121_EXP05_PHASE59_INTEGRATION_NONFLASHABLE_2026-11-03.zip`, `D578_SATELLITE_V121_PHASE52_INTEGRATION_LOGICIELLE_2026-11-03.zip`, l'archive cumulative contenant Phase47 et la CDD V1.21 authentifiée. Vérifier le hash avant toute compilation. Ne jamais utiliser le `.spi` d'une autre branche radio comme base d'un patch V1.21.
