# USB du GD32F303 : CDC ACM, endpoints, accès du CPS

## 1. Cible et identification

- Poste étudié : **D578UV PRO GD32, firmware OEM V1.21**.
- Identifiants observés dans les descripteurs du firmware : **VID `0x28E9`, PID `0x018A`**, classe appareil `0x02`, USB Full Speed.
- Nom observé : `GD32 Virtual ComPort`. Le numéro de série `000000010000` a été rapporté ; ne pas supposer qu'il est unique ou qu'il identifie une version.
- Ces descripteurs sont communs à plusieurs contextes de démarrage. **Un VID/PID identique n'indique pas à lui seul « mode normal » ou « MCU Update ».**

La liste analysée est archivée en [USB_V121_DESCRIPTORS.json](../USB_V121_DESCRIPTORS.json). Les deux tables CDC retrouvées portent la même structure.

## 2. Configuration CDC OEM

| Élément | Valeur trouvée | Interprétation |
| --- | --- | --- |
| Configuration | 1, descripteur complet de 67 octets | Une fonction CDC à deux interfaces |
| Interface 0 | Class `0x02`, Subclass `0x02`, Protocol `0x01` | Contrôle CDC ACM |
| EP `0x82` | IN, interrupt, taille max 8 octets, intervalle 10 | Notifications CDC |
| Interface 1 | Class `0x0A` | Données CDC |
| EP `0x03` | OUT, bulk, paquet max 64 octets | PC vers GD32 |
| EP `0x81` | IN, bulk, paquet max 64 octets | GD32 vers PC |
| EP0 | taille max 64 octets | Requêtes contrôle USB |

Le débit nominal de ligne demandé par le banc est `115200 8N1` via `SET_LINE_CODING`; le flux est **USB natif**, et cette valeur ne démontre pas l'existence d'une UART physique de programmation. Le hôte envoie aussi `SET_CONTROL_LINE_STATE`, DTR et RTS activés.

## 3. Chemin des données

```text
COM Windows / ttyACM côté poste réel (ou PTY + pont côté simulation)
  -> transactions USB OUT / endpoint 0x03
  -> PMA USB du GD32 (modèle usbd_host)
  -> interruptions USB (IRQ20 dans le banc)
  -> pile USB et analyseur de commandes OEM
  -> accès NAND logique par les routines OEM
  -> réponse construite par l'OEM
  -> PMA, endpoint 0x81, USB IN
  -> client hôte
```

Le **pont CPS** de la simulation transporte uniquement les octets et n'interprète pas les commandes de lecture/écriture à la place de l'OEM. Cette règle est importante pour distinguer une simulation fidèle d'une réponse « fabriquée » à partir du dump NAND.

## 4. Contrôleur hôte de simulation

Fichiers : `bench/usbd_host.py` (transactions et registres/PMA), `bench/usb_cdc.py` (énumération CDC, échanges EP0 et bulk), `bench/usb_cdc_runtime.py` (liaison à l'exécution), `bench/cdc_channel.py` (transport de statut), `bench/web_server.py` et `bench/cps_bridge.py` (pont local).

Propriétés vérifiées par les tests V11.5 à V11.7 :

- Découverte de la configuration et des endpoints par analyse des descripteurs, sans imposer ces valeurs dans le client générique.
- Gestion de l'adresse USB, de la configuration, de `SET_LINE_CODING` et des lignes de contrôle.
- File OUT limitée, fragmentation selon la taille maximale de l'endpoint, erreurs d'ACK/NAK/STALL, canal de suivi borné.
- Détection d'un changement de session USB et refus de confondre une réponse tardive avec un nouveau moteur.
- Chaque transaction avance dans le **thread d'exécution CPU** ; le pont HTTP ne modifie pas directement la RAM ou la NAND.

Limitations explicites : pas de PHY USB électrique, pas de modèle complet des CRC et bascules DATA0/DATA1, pas de prise en charge générale du double buffer bulk/isochronous, notifications CDC non exploitées en profondeur, requêtes optionnelles Windows non couvertes entièrement. Une énumération réussie par ce hôte logiciel ne valide pas une pile USB de firmware alternatif sur le poste.

## 5. Séquence minimale testée

1. Énumérer le poste virtuel et obtenir `ready`.
2. Envoyer les 7 octets ASCII `PROGRAM` au bulk OUT.
3. Recevoir `51 58 06` au bulk IN.
4. Envoyer `02`, recevoir 16 octets d'identité ; modèle `D578UV`.
5. Envoyer un ordre `R` (adresse sur 4 octets big endian et longueur).
6. Recevoir `W`, adresse, longueur, données, checksum, terminateur `06`.

Exemple **de client en lecture** : `python3 bench/cps_probe.py --read-address 0x02FA0000`. L'adresse est une zone de configuration logique conservée dans le compte rendu ; ce test n'est pas une méthode générale pour lire arbitrairement les données privées d'un appareil.

## 6. Ce qui doit encore être mesuré

- Captures USB du CPS Windows sur le **poste physique**, en lecture seulement, depuis le début de la session jusqu'à `END`.
- Réponses aux requêtes de contrôle CDC que le simulateur ne reproduit pas.
- Timings maximaux et comportement à la déconnexion et au changement de port COM.
- Trafic et descripteurs exacts du PLUS GD32 V2.08 : ne pas extrapoler les adresses de la branche PRO.

Références : [qdmr](https://github.com/hmatuschek/qdmr), [source AnyTone officielle](https://anytoneusa.com/Downloads/), [manuel GD32F30x](https://www.gd32mcu.com/data/documents/userManual/GD32F30x_User_Manual_Rev2.9.pdf).
