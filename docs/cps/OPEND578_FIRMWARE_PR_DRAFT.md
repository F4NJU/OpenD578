# Brouillon à soumettre après autorisation de Maxime

Cible : Telectroboy/OpenD578, branche main.
Source : F4NJU:feature/opend578-cps-readonly.
Statut : texte préparé, aucune PR amont ouverte.

Titre proposé : **Alpha RX FM : variante USB CDC en lecture seule pour le CPS**

L'alpha RX FM ne fournit pas encore de liaison CPS. Cette proposition ajoute une
variante opt-in qui s'identifie et expose les VFO A/B courants via son propre
protocole USB, sans firmware OEM ni capture NAND. Les binaires alpha existants
restent inchangés ; le nouveau rx_fm_cps.bin est une expérience de banc, pas un
paquet à flasher.

Le service versionné accepte seulement HELLO et VFOS. Il annonce explicitement
l'absence de modification VFO, mémoires, CTCSS/DCS, TX et persistance. Le pilote
USBD/PMA traite le sous-ensemble CDC testé en polling ; les identifiants USB sont
des identifiants de laboratoire, pas une allocation produit.

Le lot corrige aussi le quota d'attente du runner matériel : il était consommé
sur toute une exécution longue malgré la progression CPU/SysTick, et finissait
par bloquer le démarrage. Il est renouvelé uniquement après une progression CPU
réelle. Un test Thumb synthétique couvre ce cas, sans saut de code ni réponse de
périphérique inventée.

Validation : 8 contrôles du parseur C hôte et 8 tests du runner passent. Le vrai
binaire ARM énumère son USB, répond 145,500/435,000 MHz, puis 145,5125 MHz après
une action codeur. WRITE est refusé ; aucune commande observée ne lève PE6/PC4.
Une exécution continue de 10 millions d'instructions vérifie le correctif
d'attente. Empreintes et preuve ARM dans docs/evidence/rx_fm_cps ; procédure dans
firmware/experiments/rx_fm_alpha/CPS_READONLY.md.

Le client web et la preuve HTTP → CDC → ARM sont préparés séparément sur
F4NJU/OpenD578, branche feature/cps-core : deux lectures sur le même moteur,
seulement HELLO/VFOS, 63 tests CPS réussis. Cette PR est limitée au firmware,
au runner et à leurs preuves pour faciliter la relecture.

À relire avant poursuite : protocole expérimental, intégration du pilote polling
et étapes vers les mémoires/persistance. USB physique, réception RF et nouveau
parcours graphique ne sont pas qualifiés. Aucune fusion demandée automatiquement.
