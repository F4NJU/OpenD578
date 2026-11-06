# Journal des erreurs, corrections, résultats négatifs et frontières de preuve

Ce journal doit être lu AVANT de reprendre un patch. Il évite la répétition des fausses pistes déjà écartées et distingue les preuves des noms donnés aux routines.

| Incident / hypothèse d'origine | Correction ou résultat actuel | Conséquence |
|---|---|---|
| « 96 % de la RAM est occupée ». | Les 94 432 octets sont **initialisés ou remis à zéro à l'entrée**, réserves tas/pile incluses. Une RAM toute à zéro peut être entièrement réservée. | Aucune mesure RAM maximale réelle en FM, TX, DMR, APRS ni multitâche. |
| « Le haut RAM est occupé car les mots 0x20017801, 0x20017904, 0x20017F21 apparaissent ». | L'analyse Thumb montre des instructions LDRB/MOVS à ces positions. Ce sont de **faux positifs** de recherche de pointeurs. | 3 872 octets du haut de SRAM restent candidats, **non certifiés libres**. |
| Écart Unicorn avec `UC_HOOK_MEM_WRITE`. | Divergence observée dans un décodage Thumb conditionnel. Variante écartée; comparaison indépendante A5/5A et décodeur Python. | Ne pas déclarer un dépassement RAM sans preuve indépendante. |
| Révéler le boot sans horloge, puis forcer un passage de fonction. | V1 bloque normalement sur RCU_CTL; V2 modélise IRC8M/HXTAL/PLL et traverse SystemInit sans patch ni saut. | N'utiliser que le modèle d'horloge documenté, pas un forced return. |
| Trancher arbitrairement la valeur PA15 à l'arrêt V2. | PA15 participe au bus NAND. V3 fournit les bits commandés par la NAND à partir du dump réel, au rythme des GPIO OEM. | Les 58 buffers sont vérifiés après lecture, sans injection directe en SRAM. |
| Sans Power, le poste semble « bloqué » avant l'application. | V3 atteint `WFI 0x080089AA`, SLEEPDEEP activé. [UTILISATEUR] Power est un bouton relié au MCU, pas un interrupteur d'alimentation. | Simuler PA0 EXTI0 front descendant/IRQ6; ne pas bypasser le sommeil. |
| Port série NAND traité comme simple SPI 1 fil. | Le firmware utilise réellement `0x3B` de cache read **dual output** SO1/SO0; les lignes sont PB14/PA15. | Émuler les deux bits et les fronts, pas uniquement un MISO 1 fil. |
| Une valeur ECC 0x20 serait une page lisible/intègre. | 437 pages signalées non corrigées, dont 10 non triviales, 192 tout zéro. | Sauvegarde NAND non garantie restaurable. |
| Rapport antérieur : 238 pages marqueurs ECC20. | Reclassement: 225+10=**235** marqueurs, 192 pages tout zéro et 10 pages non triviales, total 437. | Garder le résultat corrigé et l'erreur documentée. |
| Blocs NAND entièrement FF = stockage TLE libre. | L'image contient codeplug, annuaire, ressources et configuration; usure et allocation OEM inconnues. | Zéro allocation NAND satellite décidée. |
| `0x0804EAC6` ou `0x080857AE` serait un setter radio. | Le premier copie des structures VFO/canal en RAM; le second manipule des enregistrements mémoire externe paginée. | Ne pas les utiliser pour Doppler. |
| `0x0808AB18` suffit pour régler une fréquence. | Pilote de commande série de registre 16 bits, pas transaction RX/TX complète, pas validation RF. | Setter OEM encore inconnu. |
| Déduire PTT de la chaîne texte « PTT », d'un GPIO ou de flags simulés. | Chaînes Bluetooth et lecteurs GPIO présents; aucun câblage/signal d'état PTT/TX/busy qualifié. | Etat inconnu = refus de commande RF. |
| Cache `radio_safe` suffit avant QSY. | Phase32 a introduit relecture de busy/PTT à l'instant exact de proposition RF. | Vérification live obligatoire, y compris avant restauration RF. |
| `0x080387DA` serait écriture LCD brute. | Phase43 : cette fonction émet la **commande LCD 0x11**, pas des octets données. | Ne pas s'y brancher comme framebuffer. |
| `0x200001C8 / 0x200001EC / 0x200001F8` seraient un verrou. | Variables de notification/tempo. Le sémaphore LCD réel repéré est `0x20000128`, avec règles RTOS à qualifier. | Pas de mutex inventé; une seule propriété OEM. |
| 37 acquisitions LCD contre 38 releases = release surnuméraire. | Analyse de Phase44: 37 paires adjacentes et un suffixe atteint par saut, pas une anomalie prouvée. | Tracer les chemins et codes de retour avant tout hook. |
| `SAT:` dans nom codeplug signifie nom à même offset dans l'objet RAM. | `+0x23` est un offset connu de l'enregistrement codeplug 64 o selon qdmr; mapping de la **structure active RAM** non prouvé. | Aucune lecture native RAM du nom dans Phase60. |
| La Phase60 ELF ET_EXEC est un firmware à flasher. | ELF purement construit, BSS volontairement dans 0x30000000 invalide, pas d'API OEM câblée et ROM stage 14 680 o. | `NO_GO`, aucun `.spi/.CDI/.CDD` modifié. |
| Les 4 pages proches de 0x080F0000 sont libres parce que peu de modifications. | Elles contiennent une table CJK et une page d'effacement peut toucher du code/ressource. | Placement Flash non autorisé. |
| Flash 3 Mio et boot lus = récupération garantie. | Aucune écriture/restore d'application invalide n'a été essayée et qualifiée. | Avant toute modification, valider recovery indépendant. |
| USB normal et MCU UPDATE ont des descripteurs différents. | Même VID/PID `28e9:018a` observé selon les modes. Une étiquette d'archive Phase32 désignait à tort mode MCU alors qu'il s'agissait de mode normal. | Ne pas attribuer un mode à un simple ID USB. |
| Mod de firmware V1.16n/V2.03n réutilisable sur V1.21 GD. | Les mods externes n'apportent pas de preuve d'ABI compatible; versions/radios différentes. | Comparer uniquement stock/mod de même modèle/release. |
| ADC rencontré lors du boot = AIC3204 audio. | Accès `ADC0` interne GD32 à `0x4001244C` + DMA0 vers SRAM; le TLV320AIC3204 est un codec audio séparé. | Étudier les sept voies/trigger DMA GD32 en premier. |
| Relever GPIO ISTAT/OCTL doit révéler LED. | Capture V1.2/V1.3 sans transition sur bits échantillonnés malgré essais de Power; le MCU reste alimenté. | Ne pas piloter les GPIO au hasard; continuer traçage électrique logique. |
| Le modèle V3 montre le LCD. | Il traverse le code et les opérations de bus LCD; il **ne restitue pas de framebuffer ou une fenêtre cliquable**. | Émulateur PC avec boutons, GPS, audio, DMR à développer. |
| Les lignes de test V3 représentent du temps réel. | Le compteur est virtuel, `idle-clock-scale 64` accélère seulement les boucles de veille du modèle. | N'inférer aucun WCET ni fluidité embarquée. |

## Erreurs de provenance et problèmes d'archives

Une partie des ZIP anciens de passation et des gros dumps ont été repérés dans la bibliothèque, mais leur export binaire a été refusé. Les fichiers textuels récupérés n'ont pas nécessairement l'intégralité du fichier original, même s'ils sont lisibles. Exemple mesuré : passation phase47 déclarée 255 491 octets, export de texte 85 101 octets, terminant après les premières annexes. Il ne faut pas remettre cet export comme « 255 Ko intégral ».

L'archive produite le 04/11 conserve les originaux qu'il a été possible de matérialiser, avec SHA. Pour les autres, elle consigne **nom et absence** plutôt que forger des fichiers ZIP vides ou des .bin avec des zéros. Un successeur doit demander ou retrouver les octets exacts dans Library pour toute modification concrète du firmware.
