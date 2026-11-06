# Refus d’accès Windows pendant un transfert CPS — V11.5.3

Le relevé utilisateur confirme PermissionError / Errno 13 sur usb_cdc.json,
pendant une session encore active (commande USB_CDC_WRITE, séquence 2020).
Les reprises de lecture de V11.5.2 ne suffisent pas si le refus d’accès dure.

## Correction

Le serveur du banc ne lit plus usb_cdc.json. Il lance son moteur avec un canal
stdout privé et un lecteur dédié. Le moteur y publie ses états CDC ; le serveur
les conserve en mémoire et répond directement à l’API et à la page web.
L’ancien fichier n’est ni lu, ni supprimé, ni réécrit pendant ce fonctionnement.
La présence d’un fichier verrouillé à cet emplacement n’intervient donc plus
dans les échanges du CPS.

Le flux transporte les états USB et les octets réellement extraits de la PMA,
sans générer de réponse AnyTone. Le serveur vérifie la cohérence des compteurs
et de la longueur de l’historique. Un ancien moteur ne peut pas remplacer les
états du moteur courant. Un canal fermé ou sans état récent reste une erreur
explicite ; une ancienne valeur ready n’est pas présentée comme un état actuel.

Le client demande un résumé quand il attend l’ACK USB et seulement les nouveaux
octets quand il lit une réponse, au lieu de retransmettre l’historique entier
à chaque interrogation. La fenêtre de réception reste bornée à 65 536 octets ;
une perte par dépassement de cette fenêtre n’est pas masquée.

Un lien « Exporter le diagnostic USB en mémoire » apparaît dans USB & UART.
Une capture USB finale peut être écrite après l’arrêt normal, dans
results/web/usb_cdc_final.json. C’est un export facultatif, indépendant du flux
pendant le transfert. Les essais CLI autonomes sans --cdc-stdio conservent
l’ancien export de suivi pour les scripts de recherche ; le lanceur web utilise
toujours le nouveau canal.

## Utilisation

Extraire V11.5.3 dans un nouveau dossier, lancer le banc et démarrer son firmware,
puis lancer CONNECTER_CPS.cmd avec le côté du port virtuel réservé au pont.
La paire de ports virtuels déjà installée reste utilisable. Garder le moteur
et le pont ouverts pendant le transfert. Retenter la lecture depuis le début ;
la reprise exacte d’un téléchargement interrompu à 94 % n’est pas implémentée.

Si le CPS échoue encore, exporter le diagnostic USB depuis la page et joindre
le journal CPS lancé avec --log. Le nouveau diagnostic doit indiquer
status_source: worker_pipe_memory. Le CPS Windows complet et le pilote de ports
virtuels restent à éprouver sur le PC utilisateur ; le test prolongé ne remplace
pas cette validation.

Validation : 203 tests passent dans l’archive préparée. Un essai de 3 000
lectures via PTY → pont → HTTP → USB → firmware a vérifié chaque adresse,
longueur et somme de contrôle, avec usb_cdc.json remplacé par un dossier
inutilisable comme fichier de suivi. Les 48 000 octets utiles ont été reçus
sans erreur ; la fenêtre d’historique a été dépassée sans perte côté client.
Ce test a pris environ 229 s sur le PC de validation. Les résultats figurent
dans validation_v11_5_3.json. Windows et le CPS constructeur n’ont pas été
exécutés dans cet environnement ; le test couvre le trajet et la lecture prolongée.
