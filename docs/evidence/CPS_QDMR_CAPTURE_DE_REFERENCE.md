# CPS AnyTone D578 : reference externe qdmr et protocole observe dans le banc

## Un echantillon public, independant du simulateur OpenD578

Le manuel qdmr, chapitre 8, exemple 8.2, publie une session **de lecture de codeplug sur un AT-D578UV**. Le protocole utilise les commandes ASCII `PROGRAM`, `R` et des reponses commençant par `W`. Extrait technique minimal reecrit :

```text
PC >  50 52 4F 47 52 41 4D           # PROGRAM
D578<  51 58 06                       # QX + 06
PC >  02                             # identification
D578<  49 44 35 37 38 55 56 ... 06   # ID578UV...
PC >  52 02 64 00 00 10              # R addr=0x02640000, 16 octets
D578<  57 02 64 00 00 10 [16] CC 06  # W addr/longueur/donnees/checksum/end
```

La documentation du banc OpenD578 V11.5/V11.6 reconnait le meme type d'echange ; le resultat est donc **corrobore par une source tiers**, et non uniquement par des reponses synthetiques. L'ID `V110` de l'exemple externe ne doit pas etre transforme en identifiant de firmware `V1.21` : les champs d'identification, versions CPS et version d'image sont distincts.

## Format et checksum

| Requete `R` | Reponse `W` |
| --- | --- |
| `0x52 | addrBE32 | N8` | `0x57 | addrBE32 | N8 | data[N] | sum8 | 0x06` |

Dans les trames publiques et les traces du banc, `sum8 = (sum(octets adresse 4) + N + sum(data[N])) & 0xff`, hors marqueur `W`. Une reponse valide prouve un bloc de donnees au sens du protocole ; elle ne prouve pas une NAND physiquement saine si le chipset remonte un statut ECC non corrige.

## Particularites qui doivent rester en tests separes

- Le CPS Windows et les outils libres ne traversent pas necessairement les regions NAND dans le meme ordre ni avec les memes options.
- L'ecriture OEM `W ... checksum ... 06`, son ACK et `END` ont ete modelises avec tamponnement : **ACK avant persistance possible**.
- Le mini-CPS utilise la zone 0x00800000 et edite **seulement le nom de canaux de 64 octets**, offset +0x23, a l'interieur des 128 premiers enregistrements ; il n'est pas un CPS complet.
- Les offsets et registres de calibration ne doivent pas etre rendus editables par ce front-end tant que leur taille, CRC, redondance et restauration ne sont pas qualifies.
- Les captures brutes de CPS du poste reel, lecture puis ecriture, manquent a la publication. Des logs contenant indicatifs, ID DMR ou contacts doivent etre anonymises avant publication.

## Tests locaux et preuves

`tools/cps_trace_audit.py` controle les traces de paquets, `tools/test_cps_trace_audit.py` ses tests. `bench/cps_bridge.py`, `bench/usb_cdc.py`, `bench/web/mini_cps_protocol.js` et `bench/web/test_mini_cps.cjs` permettent la reproduction sur banc. Il n'y a **aucun test de programmation d'un poste physique** dans cette documentation.

Sources : <https://static.dm3mat.de/qdmr/manual/ch08.html> ; <https://github.com/hmatuschek/qdmr> ; <https://github.com/dmr-tools/codeplugs> ; `docs/cps/PROTOCOLE_OEM_V121.md`.
