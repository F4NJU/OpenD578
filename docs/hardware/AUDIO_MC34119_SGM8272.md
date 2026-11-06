# MC34119G et SGM8272 : petits étages analogiques

## MC34119G : amplificateur audio de faible puissance

Le MC34119 est une famille de circuits conçue pour piloter un petit haut-parleur **en pont / différentiel**, sans mettre nécessairement une borne du haut-parleur à la masse. L'inscription `MC34119G` permet de travailler sur le pinout de cette famille, mais la lettre finale et le fabricant de la pièce montée doivent être contrôlés sur photo.

| Broche, SOIC8 | Signal usuel MC34119 | Conséquence |
| ---: | --- | --- |
| 1 | CD | Désactivation / chip disable : état logique à relever |
| 2 | FC2 | Compensation / filtre, réseau RC externe |
| 3 | FC1 | Compensation / filtre, réseau RC externe |
| 4 | VIN | Entrée audio |
| 5 | VO1 | Sortie amplifiée 1 |
| 6 | VCC | Alimentation |
| 7 | GND | Masse |
| 8 | VO2 | Sortie amplifiée 2 |

Selon le fabricant et la révision, la dénomination des entrées de compensation peut varier ; vérifier le dessin correspondant au marquage physique. Il n'existe **pas de bus de registres numérique** pour ce composant. Son contrôle repose sur l'alimentation, la broche CD et la chaîne analogique.

La **prise microphone du D578** comporte une paire distincte `SP+` / `SP−` (contacts 4 et 7 selon manuel). Cette paire ne doit pas être reliée à GND par hypothèse. La possibilité que MC34119G commande un haut-parleur particulier est à **vérifier par suivi des pistes**, pas admise comme un fait.

## SGM8272 : double amplificateur opérationnel haute tension

Le fabricant SGMICRO spécifie une alimentation **4,5 à 36 V** en monotension, sortie rail-to-rail, et une pente maximale typique de **7 V/µs**. Il n'a **aucun registre ni bus série**. Les utilisations possibles comprennent gain audio, filtrage, boucle PLL, tampon de tension DAC et commande analogique de polarisation. **Aucune de ces utilisations n'est attribuée au D578 sans continuité.**

Brochage standard du **SGM8272 SOIC8 / MSOP8**, à contrôler sur la référence complète :

| Broche | Signal |
| ---: | --- |
| 1 | OUTA |
| 2 | −INA |
| 3 | +INA |
| 4 | −VS |
| 5 | +INB |
| 6 | −INB |
| 7 | OUTB |
| 8 | +VS |

Il faudra relever la résistance de contre-réaction, les condensateurs de boucle, les sources d'entrée, la tension d'alimentation et la destination des deux sorties. Si les sorties rejoignent des varicaps ou un étage PA, documenter les références de tension et les courbes usine, sans substituer une valeur générique.

## Accès depuis le firmware alternatif

- **MC34119 :** actionner au besoin un GPIO de disable seulement **après** avoir identifié la broche MCU et la polarité ; séquencer la veille pour éviter les claquements audio.
- **SGM8272 :** aucun pilote numérique direct. Agir sur le CNA ou GPIO qui alimente ses entrées, si l'on démontre cette liaison.
- **Réglage audio général :** ne pas confondre les valeurs de volume lues sur `PC2/PC5`, l'atténuateur UTC U2429 et les commandes de mute `PA7` / RF registre `0x25` observées par le banc.

## Vérifications manquantes

1. Position réelle des deux boîtiers ; mesure de VCC et polarité des commandes.
2. Connexions MC34119G aux haut-parleurs (sorties 5/8) et à la ligne CD (broche 1).
3. Circuit de compensation et fonctions des sorties SGM8272, notamment leurs plages de tension.
4. Correspondance entre réglages firmware et niveaux mesurés ; présence de filtrage de mute au démarrage.

## Sources

- SGMICRO : <https://www.sg-micro.com/product/SGM8272>
- Fiche SGM8272 : <https://www.sg-micro.com/rect/assets/c3746436-ddc0-4ac5-8b5c-a2f7cbbbfc90/SGM8271_SGM8272_SGM8274.pdf>
- MC34119, familles Motorola/ON/UTC à recouper avec le fabricant physique : <https://www.alldatasheet.com/view.jsp?Searchword=MC34119>
- Notice microphone du D578 : [liaison audio et voie de commande](../NOTICE_CHANGELOG_MICROPHONE_V11_8.md).
