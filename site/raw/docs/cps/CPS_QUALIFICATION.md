# Plan de tests CPS D578 et critères de sécurité d'écriture

Le tableau ci-dessous distingue le niveau atteint dans le banc de la validation qui manque pour un firmware alternatif ou une utilisation sur un appareil. La réussite d'un test local ne transforme pas l'ensemble du poste en firmware réinscriptible.

| Contrôle | Situation dans les analyses V11.5-V11.7 | Critère final |
| --- | --- | --- |
| Énumération USB et CDC | Observée dans simulation | Descripteurs + endpoint + état après reset sur carte réelle |
| `PROGRAM` et identité | Réponse V1.21 observée | Identité de modèle et de révision, pas seulement ASCII générique |
| `R` de 16 octets | Réponse contrôlée dans banc | Contrôle longueur, adresse, somme, bornes, débit et temps |
| `W` et ACK bloc | Écriture d'un seul nom testée | Les secteurs voisins et états inconnus restent identiques |
| `END` et finalisation | Dépôt d'overlay après séquence OEM | Attendre fin physique de NAND et journal d'index, pas seulement ACK |
| Reset complet et relecture | Un cycle réussi sur banc | Plusieurs cycles sur matériel secondaire et coupures contrôlées |
| CPS Windows original | Lecture complète signalée par l'utilisateur ; pas exécutée dans la campagne automatisée | Captures session complète lecture/écriture supervisées |
| Éditeur 128 canaux | Noms seulement | RX/TX, CTCSS/DCS, bande, flags, modes, zones, scans, contacts |
| Codeplug PLUS V2.08 | Non qualifié par même suite | Matrice de formats propre au PLUS |
| Calibration RF | Cartes connues, conservation prévue | Hash avant/après, refus des écritures génériques dans ces régions |
| Perte de connexion USB | Scénarios partiels du pont | Aucune écriture invisible, relecture et retour sûr à une session |
| Perte d'alimentation | Non qualifié | Journal/rollback/ECC et secteur valide après reprise |
| CRC/ECC NAND | Géométrie et statuts relevés | Correction/erreur sans perte du codeplug ou des alignements |
| DMR ID / enregistrements | Adresses rapportées par sources externes | Validation spécifique de chaque zone, limite, format et capacité |

## Campagne de lecture recommandée

1. Consigner la **variante exacte** et les versions : MCU, baseband, BT, firmware et CPS.
2. Enregistrer une copie locale du codeplug avec le logiciel constructeur sans publier les données personnelles.
3. Lancer l'hôte CDC et collecter les descripteurs, puis une lecture d'une région de test connue.
4. Exporter un journal `--log` du pont en **local privé**. Le faire analyser avec `python3 tools/cps_trace_audit.py --input trace.jsonl --output resume.json`.
5. Vérifier séquences, tailles, checksums, longueurs, dépassements et erreurs de session dans ce résumé ; en cas d'anomalie, annoter le journal source en local.
6. Comparer un export de codeplug obtenu indépendamment, en masquant ses données avant publication.

## Campagne d'écriture (banc exclusivement jusqu'à qualification)

- Choisir un nom de canal dans une zone et une page **entièrement** comprises ; sauvegarder la page initiale et tous les secteurs jouxtants par empreintes.
- Réaliser une seule modification du champ nom ; lire immédiatement puis après `END`, puis après terminaison des métadonnées et après redémarrage.
- Conserver SHA256 d'avant/après sur les régions non modifiées, notamment données RF de la zone `0x02F00000...` et informations locales `0x02FA0000...`.
- Simuler une coupure en plusieurs points précis du cycle de page : avant programmation, après ACK de sous-bloc, après ACK de END, pendant mise à jour de métadonnées, après validation.
- Refuser les écritures par défaut sur les étalonnages, contacts et paramètres non interprétés ; ne jamais générer des octets zéro/FF pour « combler » une zone inconnue.

## Critères obligatoires avant un firmware OpenD578 programmable

- Empêcher une émission TX accidentelle lors d'un transfert USB ; pas de commande CPS assimilée à un PTT.
- Un seul maître d'écriture à la fois et transaction bornée (pas de pont concurrent).
- Contrôle de l'identité matérielle, de la révision et des limites de la mémoire avant toute commande NAND write/erase.
- Prise en charge des coupures et validation après redémarrage, ou fonctionnement **lecture seule**.
- Conservation indépendante de toutes les données propres au poste (calibrations, option bits, paramètres de sécurité).
- Tests de non-régression de l'USB après échec d'écriture, veille, réveil et changement d'alimentation.

## Traces et confidentialité

Les captures du trafic CPS contiennent parfois des contacts, des numéros DMR, des fréquences et des paramètres d'alignement. Le dépôt ne doit publier que des résumés anonymisés et des fixtures synthétiques. Le validateur `tools/cps_trace_audit.py` ne décode ni n'exporte les données de payload : il ne renvoie que le type d'opération, l'adresse, la longueur et le résultat du checksum.
