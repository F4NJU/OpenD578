# Sources externes : questions de maintenance et de protocoles utiles au firmware alternatif

## Les interfaces a distinguer

1. **USB CPS** : configuration et codeplug, avec les commandes effectivement recuperees dans `docs/cps/PROTOCOLE_OEM_V121.md`. Les outils G4EML de la page VK7ZJA donnent d'autres voies de lecture des donnees, mais ne constituent pas une preuve de leur implementation interne.
2. **Mode MCU UPDATE** : programmation du firmware applicatif. Ne pas le confondre avec un redemarrage normal, un mode icones ou la mise a jour SCT3258.
3. **Mise a jour des images/icones** : utilise des fichiers CDD et un protocole de chargement historique, avec granularite/alignment de blocs et parfois decalage d'adresse specifique a l'utilitaire.
4. **Mode SCT/DMR** : micrologiciel du processeur de bande de base, distinct de l'application du GD32. Source historique signale des versions de code SCT3258 et un mecanisme de maintenance propre.
5. **Test mode/alignement** : reglages de puissance, sensibilité, FI et filtre. Le poste de l'utilisateur dispose d'observations de son propre mode TEST, superieures aux suppositions tirees d'un ancien manuel.

## Codeplug et sauvegardes

La documentation ancienne insiste sur le triplet **branche firmware / version CPS / structure du codeplug**. Les incompatibilites ne se resument pas a un message Band Error : certains champs peuvent changer de sens sans aucun message explicite.

Dans OpenD578, une sauvegarde NAND d'un poste donne contient aussi des valeurs propres a l'unite. Les plages d'alignement historiques communiquees par VK7ZJA sont `0x02F00000–0x02F80679`, et les informations locales `0x02FA0000–0x02FDFFFF`. Leur presence historique a ete recoupee avec le projet, mais toute ecriture dans ces zones doit rester interdite tant que les offsets physiques, les sauvegardes, et l'integrite ECC ne sont pas qualifies.

Les observations du banc CPS PRO V1.21 sont distinctes de ces outils historiques : **USB CDC, commande PROGRAM, reponse 51 58 06, lectures R, ecritures W, sortie END**, avec ecriture des champs de canal teste dans la simulation. La presence de la commande `W` dans un simulateur n'autorise pas une ecriture sans sauvegarde sur un poste physique.

## Cartographie de facade et de RF

La bibliographie historique fournit des photos utiles pour comparer l'affectation des circuits. Dans les versions de l'utilisateur, nous disposons de traces OEM permettant de valider le pilotage fonctionnel du LCD, des boutons, du codeur, des potentiometres, des LED et du bus RF. Les photographies d'autres revisions sont des elements de recoupement, pas des motifs de retirer le statut « valide par firmware ».

L'etude des quatre QA4818N peut beneficier des schemas bloc VK7ZJA (deux oscillateurs locaux et deux etages FI/BB), mais l'identification exacte de la banque selectionnee est celle relevee dans le pilote du D578. Les calculs de registres `0x29/0x2A` doivent etre confrontees aux transactions OEM (pas seulement a la formule AT1846S).

## Modifications dangereuses documentees chez VK7ZJA

Le texte ancien contient aussi des procedes capables d'effacer des plages NAND, de modifier des calibrations ou d'augmenter la puissance au-dela des reglages constructeur. Pour la documentation OpenD578, conserver l'existence des procedures, leurs liens et leur analyse, sans convertir ces techniques en actions automatiques. Le depot public privilegie le **read-only**, les comparaisons de dumps et les tests hors ligne.

## Elements publics sans correspondance automatique avec le PRO V1.21

- Le marche comprend des cartes de revision AT32 plus recentes ; ne pas attribuer un brochage GD32 sans voir le microcontroleur.
- Les ecarts anciens D578 / D878 / Alinco ne prouvent aucune correspondance entre les firmwares.
- La presence d'un connecteur non equipe pour un airband futur ne prouve pas que la reception AM etait possible sur cette revision. Le PLUS de l'utilisateur possede une vraie carte RF additionnelle.
- Les anciens exemples de microphones Bluetooth ne sont pas une description du protocole BT01 ni du module ET12 du D578.

Voir aussi [l'index des 60 sujets](INDEX_60_SUJETS_VK7ZJA.md) et [les sources et versions](SOURCES_ET_VERSIONS.md).
