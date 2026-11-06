# Boucle audio et I/Q V11.4

Ouvrir le banc avec OUVRIR_BANC_WEB, puis l’onglet « Micro & I/Q ».
Le moteur MCU peut rester arrêté pour ce premier modèle de signal autonome.
Cliquer sur Enregistrer, autoriser le micro dans le navigateur, parler, puis
Terminer et simuler. La capture est limitée à 12 secondes. Le navigateur demande
la désactivation du contrôle automatique de gain, de la réduction de bruit et de
l’annulation d’écho ; leur disponibilité effective dépend du navigateur et du micro.
Un WAV PCM16 mono/stéréo peut aussi être chargé. Le fichier reçu se lit après
le délai choisi ; si la lecture automatique est bloquée, utiliser Lecture.

## Ce qui est réalisé

Audio micro → gain → filtrage vocal approximatif 300–3 000 Hz → préaccentuation
optionnelle 75 µs → limiteur → modulation FM → fichier TX I/Q → relecture →
canal (perte, décalage, bruit) → fichier RX I/Q → relecture → filtrage de canal →
discriminateur FM → désaccentuation → gain sortie → received.wav.
L’audio original n’est jamais utilisé comme raccourci pour produire le son reçu.
Les gains restent visibles : aucune normalisation automatique ne masque la saturation.
Le niveau numérique est normalisé et ne représente aucune puissance RF mesurée.
La préaccentuation et les filtres ne sont pas identifiés comme ceux du D578.
Le SNR est référencé à une amplitude TX unité avant les pertes du canal.

Les fichiers SigMF sont à 192 000 échantillons complexes/s, cf32_le : alternance
I float32 little endian, Q float32 little endian (8 octets/échantillon).
Le JSON contient paramètres, empreintes et limites. Les sessions sont conservées
localement sous results/web/audio ; supprimer les dossiers de session pour effacer
les enregistrements. Une capture de 12 s représente environ 37 Mo pour les deux I/Q.
Le délai d’écoute relève de l’interface ; ce modèle traite le clip hors temps réel.

## APRS

Le bouton APRS génère une trame AX.25 UI de diagnostic, NRZI, bit stuffing,
CRC-16/X25, AFSK Bell 202 à 1 200 bauds, 1 200/2 200 Hz. Elle traverse la même
modulation FM et les deux fichiers I/Q. Le récepteur recherche la phase symbole
sur l’audio démodulé et accepte uniquement les trames avec CRC valide.
Ce modem minimal n’est pas un TNC complet (pas de CSMA, digipeater, APRS-IS,
réémission ni interprétation complète des messages APRS).

## Limites et suite

Le micro PC ne traverse pas encore les commandes du firmware GD32, les registres
du codec ou le programme SCT3258. Aucune synchronisation avec le PTT ou l’état
RX/TX du MCU n’est revendiquée. Le DMA APRS OEM reste à modéliser séparément.
Les gains réglables simulent des étages idéalisés, sans mesure du schéma physique.
Le CTCSS est générable via l’API Python ; aucun décodeur CTCSS/squelch n’est
encore raccordé à cette boucle audio. Il ne faut pas confondre cette boucle avec
les entrées logiques RF de l’onglet Signaux ni le son de test OEM existant.

La fiche SCT3258 v2.0 décrit une chaîne FM numérique via un codec externe et
le DSP (sections 8 et 9). Le GD32 peut donc piloter le chemin sans transporter
les échantillons. Il reste à vérifier le routage du D578 concerné et ses bypass.
Source constructeur : https://cdn.hackaday.io/files/1642237026116832/SCT3258_datasheet_v2_0.pdf

La phonie DMR n’est pas implémentée : il faudra le vocodeur AMBE compatible,
les trames, la synchronisation TDMA et le codage de canal, puis la modulation
4FSK et sa réception. Une simple modulation 4FSK ne validerait pas la phonie DMR.

Validation : tests numériques de porteuse connue, corrélation audio FM, inversion
du résultat en conjuguant les I/Q, gains, fichiers/empreintes, CRC connu et CRC
corrompu, APRS depuis les I/Q enregistrés et accès HTTP. La capture réelle d’un
micro et l’écoute dans un navigateur restent à éprouver sur le PC utilisateur.
