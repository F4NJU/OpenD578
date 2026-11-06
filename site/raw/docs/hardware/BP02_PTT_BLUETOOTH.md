# Bouton PTT Bluetooth AnyTone : BP-02, appairage et surete d'emission

Le **BP-02** (nom de modele utilise dans le manuel BT01) est un emetteur de commandes PTT Bluetooth **separe du microphone BT01**. Il ne constitue pas une liaison audio et n'encode pas, a notre connaissance, les echantillons de voix. Il peut etre associe au D578 pour piloter l'emission avec un casque ou le BT01.

## 1. Modele fonctionnel documente

| Fonction menu | Comportement |
| --- | --- |
| `BT PTT Pair` | Appairage du bouton avec le poste par le module Bluetooth interne. |
| `PTT Name` | Nom d'appairage du bouton. |
| `PTT Hold` OFF | PTT momentane : enfonce = demande TX ; relache = RX. |
| `PTT Hold` ON | PTT verrouillable : une pression active, la pression suivante desactive. |
| `PTT Sleep` | Mise en veille configurable (environ 1 a 4 min ou infinie suivant guide). |
| `PTT BatVolt` | Niveau batterie expose par l'interface du poste. |

Le guide BT01 decrit une sequence **d'abord appairer le BP-02 au D578, puis le microphone BT01** pour le mode mains-libres avec PTT externe. Cela ne signifie pas que le BP-02 est appaire au BT01 directement : la liaison de controle passe par le **poste**.

## 2. Machine a etats d'un pilote alternatif (conception, PAS protocole capture)

```text
NON_APPAIRE --(pair confirme)--> REPOS
REPOS --(PTT ON et RF autorisee)--> TX_DEMANDE
TX_DEMANDE --(controle RF valide)--> TX_ACTIVE
TX_ACTIVE --(PTT OFF / timeout / deconnexion / coupure)--> REPOS / INHIBIT
Tout etat --(defaut critique)--> TX_INTERDIT, PTT force OFF
```

Ne pas utiliser uniquement un evenement `PTT pressed` sans traiter le `PTT released`/expiration. En mode verrouille, une deconnexion doit forcer la fin d'emission. Le firmware alternatif doit conserver une **duree maximale locale de TX** independante des profils radio BT, ainsi que les verrous frequences et modes de la chaine RF. Un paquet Bluetooth n'est jamais une autorisation suffisante a activer la puissance RF.

## 3. Ce qu'il faut retrouver dans l'OEM V1.21

- Commandes d'activation de l'appairage PTT et recherche d'adresse/nom.
- Format et canal de retour des evenements bouton, de la batterie, des expirations et de la deconnexion.
- Stockage du profil `PTT Hold` et du nom dans codeplug/NAND (offsets encore inconnus).
- Ordre des arbitrages entre PTT filaire, PTT BT01, BP-02, VOX, DMR et ACL TX.
- Protection de TX si radio hors bande, canal RX-only, perte de Bluetooth, alimentation instable ou erreur modem.

## 4. Mesures faisables sans emission RF

1. Dans le menu PTT, verifier la version, appairer puis lire le nom et la batterie.
2. Activer `PTT Hold` ON/OFF et tracer la communication serie **passivement** sans autoriser la RF (poste en configuration RX-only sous controle).
3. Comparer les evenements appui/relache, deux pressions, reveil de veille, deconnexion, reconnexion et batterie faible.
4. Realiser les essais TX uniquement avec installation RF instrumentee, charge adaptee et conditions radioamateur autorisees ; ne pas provoquer d'emission sur un canal quelconque depuis le banc de recherche.

## 5. Sources

- AnyTone, Bluetooth(BT) UserGuide D578 : <https://www.csi-radios.com/content/support/AnyTone/AT-D578UV/BT%20manual.pdf>
- AnyTone, BT01 User Guide : <https://support.bridgecomsystems.com/hubfs/Tech%20%28AnyTone%29/BT01_user_manual_221121.pdf>
- QDMR, options `pttLatch` et `pttSleepTimer` : <https://static.dm3mat.de/qdmr/manual/ch04s04.html>
