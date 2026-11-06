# Protocole CPS OEM : transactions série observées en V1.21

**Cette fiche documente exclusivement la variante PRO GD32 et les commandes réellement exercées par notre banc.** Les champs inconnus ne sont pas complétés à partir d'un autre protocole.

## 1. Transport et représentation

USB CDC ACM (voir [descripteurs](USB_CDC_GD32_V121.md)). L'interface transporte une suite d'octets, sans frontière de paquet applicatif garantie par USB. Le client doit réassembler les réponses selon les longueurs annoncées. Les adresses `R`/`W` sont transportées sur **4 octets, ordre big endian**. La longueur du bloc testée est de **16 octets**.

La communication PC ne donne pas directement les signaux d'accès à la NAND. Le firmware OEM traduit l'adresse logique et gère les pages et la finalisation.

## 2. Entrée en programmation

| Échange | PC -> radio | Radio -> PC | Statut |
| --- | --- | --- | --- |
| Initialisation | ASCII `PROGRAM` = `50 52 4F 47 52 41 4D` | `51 58 06` = `QX` + ETX `06` | Observé dans l'OEM simulé |
| Identification | `02` | réponse de 16 octets commençant par `49` (`I`) et finissant par `06`; contient `D578UV` | Observé |
| Terminer | ASCII `END` = `45 4E 44` | `06` | Observé ; acquittement avant la fin de toutes les écritures NAND |

Attention : l'octet `06` est le terminateur/ACK observé. Il ne faut pas inférer une interprétation universelle de tous les octets de réponse avant d'étudier les autres commandes.

L'identité relevée dans une session affichait la sous-chaîne `V111`. **Elle n'est pas convertie artificiellement en V1.21** : la valeur du champ demeure une donnée brute dont la sémantique exacte reste à caractériser.

## 3. Lecture : commande `R`

Requête de **6 octets** :

```text
52 AA AA AA AA LL
R  |-- adresse BE--| taille demandée (testée = 10 hex / 16 déc.)
```

Réponse pour 16 octets, soit **24 octets** :

```text
57 AA AA AA AA LL [16 octets de données] CC 06
W  |-- adresse BE--| 10  |------  données -----| checksum fin
```

Vérifications effectuées par le CPS intégré :

1. `réponse[0] == 0x57` ; adresse identique à la requête ; longueur déclarée `0x10` ; dernier octet `0x06`.
2. `somme(réponse[1..21]) mod 256 == réponse[22]` : somme de l'adresse, de la longueur et des 16 octets de données. Le marqueur `W` n'entre **pas** dans cette somme.
3. Rejeter une réponse incomplète, surnuméraire ou incorrecte ; ne pas la traiter comme des données valides.

Le script `bench/cps_probe.py` contrôle ces champs et affiche **uniquement l'empreinte SHA256** du bloc lu, pas le contenu.

## 4. Écriture : commande `W`

Pour 16 octets :

```text
57 AA AA AA AA 10 [16 octets de données] CC 06
W  |-- adresse BE--|  |------ charge ------| somme fin
```

La somme est celle des **4 octets d'adresse**, de la **longueur** et des **données**, modulo 256. La réponse observée pour une écriture de sous-bloc est `06`.

**Ne pas confondre ACK et persistance** : dans le banc, une écriture de 16 octets a pu être acquittée sans être encore relisible, car le firmware gère des modifications tamponnées de page NAND. `END` déclenche/finalise une série d'opérations, mais son ACK a lui-même précédé une partie de la mise à jour de métadonnées. Seule une nouvelle lecture après finalisation complète, arrêt propre et redémarrage permet de conclure à la persistance.

Le CPS intégré V11.6 écrit **128 sous-blocs de 16 octets** pour une page logique de 2048 octets, en préservant la page d'origine hors des caractères de nom ciblés. Il refuse les modifications hors des positions prévues et compare une nouvelle lecture à l'instantané précédent avant la tentative d'écriture. Il ne détecte pas les clients concurrents qui auraient modifié le poste entre la comparaison et l'écriture : **pas de verrou transactionnel général**.

## 5. Bornes vérifiées pour l'éditeur intégré

- Base des 128 premiers canaux : `0x00800000`.
- 4 groupes de 32 canaux, chaque groupe = **2048 octets** : `base + groupe * 0x800`.
- Chaque canal = **64 octets** ; nom à `+0x23` (`35` décimal), jusqu'à 16 caractères ASCII imprimables.
- Zone éditée par le mini-CPS : `0x00800000..0x00801FFF` inclus. Ce n'est **pas** la carte complète de la NAND ni la limite du codeplug OEM.

Voir [champs du canal](CODEPLUG_CANAL_OEM_V121.md) pour la structure complète des éléments partiellement identifiés.

## 6. Timings observés, sans garantie contractuelle

- Entrée `PROGRAM` : environ 2 à 4 secondes dans le banc V11.5 selon la charge PC.
- Lecture de sous-blocs : généralement plusieurs dizaines à centaines de millisecondes dans ce banc.
- Opération `END` : son ACK n'attend pas la fin de toutes les transactions NAND.
- Des timeouts trop courts peuvent interrompre des sessions valides ; **un timeout d'écriture ne doit jamais déclencher de répétition aveugle**.

Ces valeurs sont des résultats de simulation sur la machine utilisée, **pas des timings certifiés du matériel**.

## 7. Éléments encore inconnus

- Liste complète des sous-commandes/areas lues par le CPS Windows et leurs interprétations.
- Format et longueur des transactions non exercées ; en particulier programmation de contacts/DMR IDs, calibrations, fonds d'écran, messages et options.
- Gestion de verrouillage, de version, de compatibilité du codeplug et d'erreurs non récupérables.
- Sémantique et contrôles exacts d'une annulation ou déconnexion pendant une NAND WRITE/ERASE.
- Rôle de chaque champ restant de la réponse d'identification.
- Nombre de variantes du protocole entre les versions V1.20/V1.21 et V2.07/V2.08.

## 8. Références vérifiables

Sources **propres au projet** : `bench/web/mini_cps_protocol.js`, `bench/cps_bridge.py`, `bench/cps_probe.py`, `bench/web/test_mini_cps.cjs`, `docs/validation_v11_5.json`, `docs/validation_v11_6.json`, `docs/USB_CPS_V11_5.md`.

**À ne pas confondre** avec le protocole CPS du firmware **OpenGD77** (`R`/`W`/`X`/`C`), dont certaines lettres sont identiques mais dont le format, les sous-commandes et l'adressage sont différents : [spécification du protocole open firmware](https://radiofoundry.org/docs/spec/open-firmware-cps).
