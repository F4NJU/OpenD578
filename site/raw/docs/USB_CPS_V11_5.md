# USB CDC et pont CPS — V11.5

Le banc dispose désormais d’un hôte CDC ACM et d’un pont vers un port série
local. Les réponses sont celles du firmware exécuté. Le CPS Windows complet
n’a pas encore été exécuté : le transport ne vaut pas une certification de
compatibilité de tous ses échanges.

## Implémentation

- EP0 : descripteur initial, adresse, descripteur complet, configuration à
  plusieurs paquets, configuration active, SET_LINE_CODING 115200/8N1 et
  SET_CONTROL_LINE_STATE avec DTR/RTS activés.
- Les interfaces et endpoints bulk sont découverts dans les descripteurs reçus,
  sans imposer les adresses propres au D578 dans le client CDC.
- Bulk OUT : file bornée, découpage selon le maximum annoncé, attente ACK/NAK.
- Bulk IN : octets lus dans la PMA remplie par le firmware, historique borné et
  détection des pertes côté pont. Les écritures série partielles sont conservées.
- Session identifiée pour refuser une écriture d’un ancien client après reset.
- Le navigateur commande le serveur local ; le pont Python accède à son API.
  Windows exige une paire COM virtuelle ; POSIX peut créer un PTY sans pilote.
- Le contrôle USB est exécuté dans le thread CPU. Le serveur et le pont ne
  lisent ni n’écrivent directement la RAM ou la NAND du firmware.

Le mode Analyse OEM active le modèle UsbdHost à la demande, en conservant ses
registres/PMA existants, et livre IRQ20 au vrai vecteur. Le mode matériel utilise
le même hôte CDC, sans ajouter d’adresse de routine OEM au firmware expérimental.
Le moteur matériel et la liaison OEM utilisent le compteur natif déjà livré.
Les DLL Windows n’ont pas changé d’ABI ; leur exécution Windows reste à éprouver.

## Corrections du contrôleur

Le bit EP_KCTL d’un endpoint contrôle représente STATUS_OUT, pas un double
buffer bulk. Le modèle accepte le statut OUT vide et refuse un statut avec
charge utile. Un nouveau SETUP sur EP0 configuré peut être accepté malgré le
statut ordinaire NAK/STALL ; un paquet déjà reçu attend son traitement avant
écrasement. SETUP réinitialise les toggles et les deux directions de contrôle.
Les endpoints non configurés attendent au lieu de produire une fausse réponse.

Référence primaire : GD32F30x User Manual Rev2.9, contrôle USBD, pages 791–803 :
https://www.gd32mcu.com/data/documents/userManual/GD32F30x_User_Manual_Rev2.9.pdf
Le transport est au niveau transactions, sans PHY, CRC électrique ni erreurs
ou retransmissions DATA0/DATA1 détaillées. Le double buffer bulk et les transferts
isochrones restent explicitement non pris en charge.

## Résultats observés

Le firmware V1.21 énumère et fournit le VID/PID 28E9:018A, les endpoints 03 OUT,
81 IN et 82 de notification. L’hôte découvre cette dernière adresse mais ne
traite pas encore les notifications CDC. Il ne reproduit pas toutes les requêtes
optionnelles d’un pilote Windows (par exemple GET_LINE_CODING ou SEND_BREAK).

Par des octets transmis via un vrai PTY, le pont HTTP puis les interruptions
USB du firmware, les essais ont obtenu : PROGRAM → 51 58 06 ; identification
avec modèle D578UV ; lectures de blocs de 16 octets avec adresse, longueur et
somme de contrôle valides. La chaîne d’identification observée contient V111 ;
ce champ est rapporté tel quel, sans remplacer sa valeur par l’étiquette V1.21
de l’image authentifiée. Sa signification exacte reste à établir.

Le test d’un seul bloc modifié a reçu ACK mais la relecture immédiate conservait
l’ancienne valeur. L’envoi d’une page complète de 2 048 octets n’a pas suffi à
rendre la modification visible avant END. Après END, une opération NAND native
sur la page physique 4160 a eu exactement l’empreinte SHA256 de la page modifiée
attendue. L’ACK END arrive avant la fin des mises à jour de métadonnées : arrêter le moteur
à cet instant laisse un état incomplet. Après attente de la finalisation, sauvegarde
des pages et reset applicatif complet, le nom de canal modifié a été retrouvé
par une nouvelle lecture USB. Le redémarrage a pris environ 90 s sur le PC de test,
sans chargement de l’ancienne RAM OEM. Ce cycle a employé un client de validation,
pas le CPS constructeur. Les captures originales n’ont pas été modifiées.
Les empreintes et résultats figurent dans validation_v11_5.json.

Les temps dépendent de la charge du PC : l’entrée PROGRAM a pris environ 2–4 s,
les petits blocs lisibles généralement quelques dizaines à centaines de ms.
qdmr utilise un timeout de lecture de 1 s dans le code consulté ; une adaptation
du délai ou un moteur plus rapide peut donc être nécessaire pour ce client.
Le délai exact du CPS constructeur n’a pas été mesuré.

## Persistance

La case de conservation exporte les seules pages NAND modifiées à la sortie
normale du moteur. Le format vérifie sa géométrie, ses empreintes et l’identité
des sources avant de charger les pages. Il n’utilise pas pickle. Un état présent
impose un reset applicatif ; la reprise RAM OEM antérieure serait incohérente.
Un arrêt forcé ne garantit pas de checkpoint à jour. Ni la RAM ni la Flash interne
ne sont conservées par ce fichier.

185 tests automatisés passent ; l’archive aplatie est vérifiée séparément.
La syntaxe JavaScript et les références HTML ont été contrôlées. Le navigateur
et le micro PC n’ont pas été testés visuellement dans cette session.

## Validations restantes

- CPS AnyTone Windows, paire COM et sélection du port réels.
- Téléchargement / téléversement complet, toutes les commandes et données CPS.
- Autres champs mémoire, codeplugs complets et redémarrages après interruption
  d’une écriture ; un seul changement de nom a été validé après reset.
- Latence maximale, gros transferts, déconnexion pendant écriture et récupération.
- Appareils / firmwares autres que la V1.21 et profils CDC multiples.

Un succès du transport n’est pas une validation d’un firmware pour le poste réel.
