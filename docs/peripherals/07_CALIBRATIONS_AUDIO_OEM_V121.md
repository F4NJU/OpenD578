# Audio et calibrations propres au poste — Web 0.12

**8 novembre 2026 — PRO GD32 V1.21, sauvegardes du projet.** La prise en compte des paramètres usine est vérifiée sur les transactions OEM en TX VHF et UHF. **La chaîne sonore complète reste non qualifiée : le paquet ne restitue pas encore un son fidèle de bout en bout.**

## Ce qui est appliqué depuis vos sauvegardes

L'OEM lit la NAND par ses GPIO, choisit sa copie et programme ses périphériques. Le modèle matériel ne lit aucune variable OEM pour choisir un gain et ne remplace aucun paramètre par une valeur nominale.

La routine `0x0801A576` sélectionne entre `0x02F60000` et `0x02F80000`, puis lit notamment 32 octets à l'offset 0 vers `0x200093F0` et 32 octets à l'offset `0x40` vers `0x20009410`. Ces adresses SRAM servent uniquement à l'analyse passive de la preuve. Les paramètres de fonctionnement du modèle viennent des transactions GPIO/HPI achevées.

La campagne retrouve la copie `0x02F60000`. Les 64 octets de ces deux premiers enregistrements concordent entre le fil NAND et les tampons OEM. L'observateur distingue le chargement interne d'une page NAND et les octets réellement transmis au MCU : un préchargement de 2 Kio ne fait pas apparaître artificiellement 2 Kio de paramètres « utilisés ».

## Réglages retrouvés dans le mode de service

Les libellés proviennent de la table OEM à `0x080C0B34`. Le dispatch TBB à `0x08065662` permet de relier chaque commande aux champs de calibration ci-dessous.

| Réglage de service | Mode OEM | Offset dans la copie sélectionnée | Valeur de votre capture | Qualification |
| --- | ---: | ---: | ---: | --- |
| MODU | 18 | `+0x05` | 105 | Lecture NAND et commande TX UHF vérifiées |
| MIC | 19 | `+0x19` | 54 | Lecture NAND et code micro appliqué vérifiés |
| TONEU | 20 | `+0x17` | 115 | Mapping statique et lecture NAND ; réponse de tonalité ouverte |
| TONEV2 | 21 | `+0x18` | 58 | Mapping statique et lecture NAND ; réponse de tonalité ouverte |
| CTCW | 22 | `+0x06` | 72 | Lecture et champ de commande de sous-audio retrouvés en TX |
| DCSW | 23 | `+0x07` | 56 | Mapping statique et lecture NAND ; émission DCS non qualifiée |
| MODV1 | 53 | `+0x45` | 45 | Lecture NAND et commande TX VHF vérifiées |
| MODV2 | 54 | `+0x57` | 100 | Mapping statique et lecture NAND ; transfert physique ouvert |

Ce sont des **codes bruts**, pas des dB, des volts ou une déviation en hertz. Le logiciel ne fixe aucune de ces valeurs dans les modèles de gain. L'interface les affiche seulement après leur lecture sur le fil et pour la Flash de référence reconnue. Une Flash différente conserve l'émulation et les observations brutes ; les libellés dépendant de cette version ne sont pas prétendus qualifiés.

La routine `0x0801A15E`, autrefois présentée comme un chargement candidat, appartient à l'initialisation des valeurs et appelle le chemin d'écriture `0x0808B32A`. Le chargement étudié ici utilise `0x0808B5A4` depuis `0x0801A594` et les appels suivants. Cette distinction corrige la description historique sans modifier l'OEM.

## Micro FM : le test en TX était nécessaire

| Cas obtenu par les commandes OEM | Réglage AnaMic | MIC usine lu | QA banque 0, page 0 / `0x18` | QA page 1 / `0x17` | Code micro appliqué |
| --- | ---: | ---: | --- | --- | ---: |
| TX VHF initial | Level 4 | 54 | `0x2925` | `0x03B0` | 54 |
| Menu Level 5 confirmé, avant TX | Level 5 | 54 | `0x2925` | `0x03B0` | 54 |
| TX VHF après changement | Level 5 | 54 | `0x3125` | `0x03B8` | 55 |
| TX UHF, mémoire ON0CS UHF | Level 5 | 54 | `0x3125` | `0x03B8` | 55 |

La routine `0x0806F07C` combine le réglage utilisateur et le champ MIC lu à l'offset `+0x19`. Dans ces cas, le sélecteur provient de la table OEM `0x080C090A`, puis le code de l'étage est encodé dans le mot `0x0200 | (code << 3)`. La formule décrit l'encodage observé ; elle ne certifie pas la loi analogique du QA4818.

L'application du nouveau réglage est différée jusqu'au TX dans cette campagne. Le test qui s'arrêtait à la confirmation du menu en 0.11 ne suffisait donc pas.

Le registre QA page 0 / `0x40` vaut `0x365A` en TX VHF : son octet inférieur vaut deux fois MODV1 (45). Il vaut `0x38D2` en TX UHF : l'octet inférieur vaut deux fois MODU (105). Le registre `0x51` vaut `0x90C8` ; ses sept bits bas retrouvent CTCW (72). Les bits supérieurs et leurs variantes suivent l'OEM, sans synthèse d'une valeur à partir du nom de canal.

Aucune nouvelle commande SCT ni écriture codec n'est observée dans ces transitions FM : les 24 demandes codec restent inchangées. Ce constat situe les commandes de gain étudiées dans le chemin QA ; il ne constitue pas une preuve de continuité physique de tous les signaux audio. Les gains et filtres documentés du SCT ne sont pas appliqués arbitrairement à cette chaîne FM.

## Accès au mode de réglage au boot

La nouvelle commande de façade **Maintenir P4 + appui codeur** agit uniquement sur les entrées de touches. Après chargement, maintenir ces entrées avant Reset, démarrer et utiliser Power au premier sommeil du MCU ; relâcher ensuite les touches. Elle ne modifie pas la NAND.

Dans la capture chargée, Full Test vaut zéro et le bit Band Select est désactivé. Le gate OEM conserve cette décision ; le démarrage avec la combinaison retombe sur l'écran d'exploitation, identique à la référence. Les calibrations restent lues et appliquées en fonctionnement ordinaire. Aucun octet de permission de service n'est forcé pour fabriquer l'accès.

## Changements livrés

- Traçage passif des octets NAND réellement transmis, de leurs pages et de la provenance capture/overlay.
- Tableau en lecture seule des huit réglages de service ; absence de données conservée comme « non lu ».
- Affichage distinct du MIC usine et du code micro effectivement écrit au QA.
- Décodage séparé des gains SCT Q16.11/Q16.12, du mode analogique et de la demande de calibration automatique de démodulation. Les champs non reçus restent inconnus.
- 112 tests logiciels réussis ; campagne OEM de 14 captures, démarrage à froid, TX VHF avant/après changement de niveau et TX UHF. Zéro overrun USART0 dans ces captures.

Les fichiers d'entrée ne sont pas écrits. Les empreintes de la Flash et de la NAND principale correspondent aux références originales ; les empreintes OOB/ECC sont également consignées. Les écritures normales de l'OEM restent dans l'overlay de la session. Le niveau utilisateur a été changé dans cet overlay ; aucune édition de calibration n'est injectée par le script.

## Reproduire

Depuis le dossier du paquet :

```
node --test browser-bench/tests/*.test.mjs
node preuves/replay_calibration_oem.mjs "/chemin/full_flash_pass1.bin" "/dossier/des/trois/NAND" resultats_calibration_v012
node preuves/verify_calibration_oem.mjs resultats_calibration_v012 > resume_calibration.json
```

La campagne exécute environ 3,74 milliards d'entrées d'instruction. Elle ne saute aucun délai ; sa durée réelle dépend du PC. Le core et les échanges sont ceux de `web0120r1`. Le rendu documentaire final est vérifié par rejeu des données et tests, sans nouveau contrôle visuel du panneau dans un navigateur. Les anciennes campagnes complètes CPS/GPS ne sont pas répétées ici.

## Données encore nécessaires pour clore toute la chaîne sonore

| Trajet | Ce qui manque encore |
| --- | --- |
| Micro filaire → QA → modulation FM | Loi physique des gains QA, filtres, limiteur et réponse de déviation aux codes appliqués |
| RX A/B → U2429 → amplis | Continuité des voies et réponse des étages analogiques ; la commande du volume seule ne donne pas cette réponse |
| HP poste, HP microphone, prises externes | Câblage des entrées/sorties U2429 et des amplis, sélection et contacts des deux prises sur cette révision |
| Tonalités, CTCSS/DCS, APRS | Formes d'onde et traitements à valider, distincts des codes de calibration retrouvés |
| Trajets qui utilisent le codec/SCT | Configuration interne et flux audio effectifs, à relever sur les liaisons concernées |

Les documents publics consultés et les monographies originales du projet laissent ces connexions ou lois non déterminées. Une réponse sonore complète avec des gains inventés ne répondrait pas au critère de fidélité. Aucun oscillateur ni boucle sonore générique n'est ajouté pour la faire passer pour terminée. Le DMR reste différé.
