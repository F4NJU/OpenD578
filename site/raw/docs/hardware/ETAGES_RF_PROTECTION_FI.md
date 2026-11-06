# Architecture RF D578 : protections, filtres varicaps et emplacement FI non equipe

## Architecture documentee sur D578 historique

Les relevages de VK7ZJA decrivent une entree d'alimentation protegee par **relais et diode** contre l'inversion de polarite, deux chaines RX independantes VHF/UHF avec **quatre etages de filtrage accordes par varicaps**, une premiere conversion heterodyne et deux filtres FI **38,550 et 38,850 MHz** suivis de recepteurs a conversion directe. Les quatre circuits QA4818N constituent les candidats etablis par la documentation familiale ; leur correspondance physique avec les boitiers grattes du poste est encore a tracer.

Les cartes de certaines revisions comportent les empreintes d'un **troisieme chemin FI non peuple** et de filtres supplementaires montables en cascade. Une empreinte non equipee ne prouve pas qu'une fonction est utilisable par simple ajout de pieces. Les editions anciennes etaient anterieures a certaines fonctions AM du PLUS.

## Correspondances possibles et pistes de recherche

| Zone | Evidence externe | Notre releve | Action avant toute conclusion |
| --- | --- | --- | --- |
| Relais / diode entree 13,8 V | VK7ZJA : protection polarite | L7805CV identifie par l'utilisateur | Identifier VIN, masse, commande relais, rails 5V et 3V3 par traces/releves |
| Varicaps RX | VK7ZJA : quatre filtres accordes par bande | BH2226FV H2226 et SGM8272 sur carte | Etablir la liaison analogique entre sorties CNA, amplis et commandes de syntonisation |
| Premiere FI | 38,550 / 38,850 MHz | Deux paires de LQFP32 grattes, 26.00 a proximite | Suivre chaque cristal, mixer, CS et sortie IF sans emission |
| FI supplementaire | Empreintes non peuplees sur revisions historiques | Non relevees sur nos PCB | Photos des deux faces sous blindage et comparaison avec FCC |
| Reception AM airband PLUS | Carte KT0905R/KT09S5R decrite par l'utilisateur | Connecteur absent sur PRO, present sur PLUS | Relever entree RF, oscillateur, numerotation contacteur et signaux sans hypothese de protocole |

**Ne pas confondre** presence de transistor PA / varicap et preuve de commande du GD32. Un firmware alternatif doit conserver la radio non emissive tant que les commandes, polarisation, limites RF et retours d'etat ne sont pas qualifies.

Sources : <https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php> ; <https://fccid.io/T4K-D578UV/Internal-Photos/Internal-Photos-4513250> ; <https://radiofoundry.org/docs/spec/hardware-anytone> ; `docs/hardware/QA4818N_QUATRE_CIRCUITS_26MHZ.md`.
