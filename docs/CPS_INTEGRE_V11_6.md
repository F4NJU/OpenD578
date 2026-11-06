# CPS intégré V11.6

L’onglet **CPS intégré** utilise les échanges USB du firmware exécuté : PROGRAM,
identification, lecture R, écriture W et END. Il ne lit ni ne modifie directement
la NAND. Aucun port COM virtuel n’est nécessaire pour cet onglet.

1. Fermer le CPS externe et son pont CONNECTER_CPS. Un seul client USB à la fois.
2. Démarrer le moteur OEM V1.21. Pour sauvegarder la NAND après arrêt normal,
   cocher cette option avant le démarrage.
3. Choisir un groupe de 32 emplacements parmi les 128 premiers et cliquer Lire.
4. Exporter éventuellement la dernière lecture en JSON. Cet export est propre
   au banc, sans import et incompatible avec le fichier CPS constructeur.
5. Modifier un nom existant (1 à 16 caractères ASCII imprimables), puis Écrire.
6. Après END, laisser le moteur finir les écritures NAND, arrêter puis redémarrer le moteur et relire. Un ACK
   ne suffit pas à prouver la finalisation ou la persistance après redémarrage.

Les fréquences RX/TX, le mode et la puissance sont affichés en lecture seule.
Les noms vides ou non reconnus ne sont pas éditables. Le bitmap des canaux actifs
n’est pas interprété : la liste présente des emplacements, pas une liste certifiée
de canaux activés. Zones, contacts, création/suppression, CTCSS, calibrations et
importation des codeplugs constructeur ne sont pas inclus.

Le format décodé est limité au codeplug D578UV constructeur. Un firmware
expérimental qui change ce format doit disposer de son propre adaptateur.
Le protocole USB connu ne constitue pas une compréhension de tous les champs.

## Écriture et erreurs

Chaque groupe correspond à une page logique de 2 048 octets. Avant écriture,
le CPS relit la page et la compare à l’instantané affiché. Il refuse une page
changée. Seuls les octets des noms sont modifiés ; le reste est conservé.
Les adresses sont bornées à 0x00800000–0x00801FFF (128 enregistrements de 64 octets).
Les réponses de lecture sont contrôlées : commande, adresse, longueur, checksum,
ACK. Les écritures ne sont pas répétées automatiquement après un échec ambigu.
Si un transfert d’écriture échoue, ne pas supposer la page cohérente : sauvegarder
le diagnostic, redémarrer le banc si nécessaire et relire avant de reprendre.
Il n’existe pas de verrou exclusif entre cet éditeur et un client externe :
la fermeture du pont est nécessaire. La comparaison avant écriture ne protège
pas contre un autre client qui écrit simultanément.

## Validation

Tests Node : BCD/fréquence avec offset, changement de nom, préservation des
champs voisins, refus des noms invalides, instantané périmé et modification
hors noms ; pas de répétition automatique de END après délai ambigu.
Le scénario d’intégration utilise le même module JavaScript que la page et
un vrai moteur OEM. Le compte rendu précise la portée exacte des essais.
L’interface graphique navigateur n’a pas été exercée automatiquement.

Référence de format consultée dans les sources qdmr :
https://github.com/hmatuschek/qdmr/blob/master/lib/anytone_codeplug.cc
et https://github.com/hmatuschek/qdmr/blob/master/doc/code/d578uv_channel.txt
Implémentation du banc indépendante, sans copie de code qdmr.

Une lecture maintient la programmation active pour permettre une modification ou
une autre lecture. Le bouton Terminer envoie END sans modifier les mémoires.
Après END, le retour immédiat à une session CPS reste non qualifié ; redémarrer
le moteur. Activer la persistance NAND avant démarrage pour conserver une écriture.

Résultat du scénario V11.6 : identification, lecture de 2 048 octets,
nouvelle entrée PROGRAM, comparaison avant écriture, changement d’un nom,
écriture complète et END, finalisation NAND, arrêt normal, redémarrage
applicatif sans capture RAM, puis identification et relecture intégrale.
La page relue correspond exactement à la page modifiée ; seuls les octets du
nom ciblé diffèrent de l’original. Voir validation_v11_6.json.
203 tests Python existants réussis, plus les contrôles Node du module CPS.
