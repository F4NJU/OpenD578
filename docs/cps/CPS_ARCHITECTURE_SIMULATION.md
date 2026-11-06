# CPS dans le banc V11.7 : architecture, lancement et fichiers sources

## 1. Ce qui est réellement fourni

Le banc exécute l'application AnyTone OEM V1.21 dans une simulation de CPU et de périphériques. Son hôte USB observe les descripteurs et les transactions de cette application. Il ne réimplémente pas les réponses OEM en inventant une lecture du dump NAND.

La source publique V11.7 a été réintégrée ici depuis `OpenD578_source_V11_7.zip`, lui-même contenu dans l'archive de qualification V11.7. Cette version est la **base exécutable publique disponible**. Les notices V11.8 du LCD et du microphone ont été conservées mais ne signifient pas que leurs modifications de banc sont toutes présentes dans les sources V11.7.

### Chemin des octets

```text
CPS constructeur Windows --> port COM10 (exemple)
                                |
                 paire de ports COM virtuels, externe au dépôt
                                |
                         port COM11
                         cps_bridge.py
                                |
                localhost /api/usb/* (web_server.py)
                                |
                   file CDC (usb_cdc.py)
                                |
                  transactions USBD / PMA
                                |
                 firmware OEM V1.21 exécuté
                                |
                  gestionnaire NAND du GD32
                                |
                         nand_overlay.py
```

Sous Linux, `cps_bridge.py --pty` fournit `/dev/pts/N` à un client qui autorise la sélection manuelle du chemin de port ; il ne se présente **pas** comme un périphérique USB 28E9:018A.

Le CPS **intégré dans le navigateur** utilise le même chemin USB, mais **sans port COM** : `web/mini_cps.js` -> `web/mini_cps_protocol.js` -> API USB -> firmware exécuté. Ce n'est pas un clone complet du logiciel AnyTone.

## 2. Sources à lire (les chemins sont dans `bench/`)

| Fichier | Rôle |
| --- | --- |
| `usbd_host.py` | Requêtes de contrôle et transactions IN/OUT du contrôleur USBD simulé, lecture des données PMA |
| `usb_cdc.py` | État hôte, énumération CDC, configuration, endpoints et files bulk |
| `usb_cdc_runtime.py`, `cdc_channel.py` | Association du moteur CPU à la session USB et son suivi |
| `web_server.py`, `web_endpoint.py` | API locale, contrôle des clients et identification du serveur actif |
| `cps_bridge.py` | Pont transparents COM/PTY <-> HTTP/CDC ; journal optionnel des octets |
| `cps_probe.py` | Identification et lecture **seule** de 16 octets, contrôle d'adresse et checksum |
| `web/mini_cps_protocol.js` | `PROGRAM`, identification, `R`, `W`, `END`, décodage de 32 canaux/page, modification nom seulement |
| `web/mini_cps.js`, `web/cps_link.js` | Interface CPS intégrée et connexion au moteur |
| `web/test_mini_cps.cjs` | Tests hors ligne des BCD, noms, snapshots périmés, protection des champs voisins et non-répétition de END |
| `test_usb_cdc.py`, `test_cps_endpoint.py`, `test_cdc_channel.py` | Tests hôte USB, API, transport et état des sessions |
| `nand_overlay.py`, `nand_state.py` | Couche de pages et persistance des modifications si activée |

Il ne faut **pas** appeler `mini_cps_protocol.js` un pilote NAND. Il génère et vérifie des échanges série CPS. Le firmware OEM réalise les transactions NAND par ses propres routines.

## 3. Tests sans matériel

Depuis la racine du dépôt, après installation des dépendances du banc :

```sh
node bench/web/test_mini_cps.cjs
python3 -m unittest discover -s bench -p 'test_usb_cdc.py' -v
python3 -m unittest discover -s bench -p 'test_cps_endpoint.py' -v
python3 -m unittest discover -s tools -p 'test_cps_trace_audit.py' -v
```

Les tests nécessitant `unicorn`, `capstone` et parfois `pyserial` ou `numpy` ne doivent pas être déclarés réussis lorsqu'ils n'ont pas réellement été lancés. Le `site` GitHub Pages est indépendant de ces bibliothèques lourdes.

## 4. Lancer le banc et faire une lecture

Le banc exige des entrées locales propriétaires qui ne sont **pas** contenues dans le dépôt public : image application GD32 V1.21, références NAND, éventuellement l'état de reprise. Le lire-moi et les lanceurs `bench/OUVRIR_BANC_WEB.*` expliquent l'environnement. L'image OEM utilisée est identifiée par son SHA256 dans `docs/02_CPU_FLASH_BOOT_USB_SWD.md`.

Démarrage : `bench/OUVRIR_BANC_WEB.sh` sous Linux ou `bench/OUVRIR_BANC_WEB.cmd` sous Windows. Dans l'interface, lancer la simulation appropriée, puis connecter l'hôte CDC. Le client de test `bench/cps_probe.py` lit un bloc de contrôle en **lecture seule** :

```sh
cd bench
python3 cps_probe.py --read-address 0x02FA0000
```

**Ne pas** lancer simultanément le CPS intégré, un pont COM et un autre client de test. Le serveur n'impose pas un verrou exclusif inter-processus sur toutes les opérations.

## 5. Pont Windows et Linux

Windows : créer une paire COM virtuelle avec un logiciel adapté ; configurer le CPS pour `COM10` et `cps_bridge.py` pour l'autre extrémité (`COM11`) ; ne pas faire ouvrir deux processus sur le même côté. Le pont sait préparer le mode CPS avant de rendre la liaison au CPS, afin de limiter les délais lors du premier `PROGRAM`.

```sh
cd bench
python cps_bridge.py --port COM11 --prepare
```

Linux :

```sh
cd bench
python3 cps_bridge.py --pty
```

Le pont affiche le nom du PTY. L'option `--log` produit un journal JSONL contenant les **octets complets de la communication CPS**. Ce journal peut révéler identifiants, fréquences, messages, contacts et paramètres d'étalonnage. Il doit rester hors du dépôt public. `tools/cps_trace_audit.py` permet d'en extraire un **résumé technique sans charge utile**.

## 6. Écriture : étendue réelle de la validation

Le scénario V11.6 a : identifié la radio simulée ; lu une page logique de 2048 octets ; modifié seulement le champ nom d'un canal ; réécrit la page ; émis `END` ; laissé finir le code OEM et ses métadonnées NAND ; sauvegardé l'overlay ; redémarré l'application depuis la Flash, sans la RAM de reprise ; relu et comparé la page entière. Le contrôle a confirmé que **seuls les octets du nom ciblé avaient changé**.

Ce résultat ne vérifie ni la totalité des champs CPS, ni toutes les fonctions du logiciel Windows, ni la résistance à une coupure électrique au milieu d'une programmation. Les changements sur un poste réel sont hors de ce scénario.

## 7. Procédure de qualification physique (lecture seule)

Commencer par une sauvegarde constructeur ; noter les identifiants de firmware, le VID/PID, le descripteur CDC, le modèle retourné et les temps de réponse ; capturer une session de **lecture** terminée proprement. Comparer les groupes d'adresses et checksums au protocole de ce dossier. Ne pas utiliser de commande de test qui modifie les calibrations, de bouton TX ni de mise à jour firmware lors de cette campagne.

Sources : [V11.5](../USB_CPS_V11_5.md), [V11.6](../CPS_INTEGRE_V11_6.md), [V11.7](../CHANGELOG_V11_7.md), [descripteurs](../USB_V121_DESCRIPTORS.json).
