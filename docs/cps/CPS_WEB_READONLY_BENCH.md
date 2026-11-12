# CPS web et banc Python : premi�re liaison en lecture seule

Cette livraison r�utilise le banc Python V11.7 et son h�te USB CDC. Elle ne cr�e
aucun faux poste, aucune r�ponse de firmware et aucun acc�s direct � la NAND.
Le nouveau panneau est une inspection OEM distincte du codeplug �ditable.

## Pr�paration

**Actualisation du 12 novembre** : F4EGM a fourni les quatre captures dans
`browser-bench/samples/F4EGM.zip` sur son d�p�t. Leurs empreintes sont v�rifi�es.
Ce jeu satisfait les captures Flash/NAND, mais pas la r�f�rence SCT compl�te
encore exig�e par ce parcours Python historique. Python 3.13.5 et les paquets
�pingl�s sont pr�ts dans un environnement local isol�. Consulter
[F4EGM_CAPTURE_CHECK.md](F4EGM_CAPTURE_CHECK.md) avant de poursuivre : ni le CPS
ni ce parcours de d�marrage ne sont encore qualifi�s de bout en bout.

Utiliser une copie locale compl�te de la branche `feature/cps-core` du fork
F4NJU/OpenD578, avec les entr�es n�cessaires au banc. Le fichier HTML autonome
ne contient aucune image OEM ; les captures sont � r�cup�rer s�par�ment.

Depuis la racine, compiler le CPS avec Node.js 24 ou ult�rieur :

```sh
cd cps
npm run build
```

Lancer ensuite le banc Python comme d'habitude avec `bench/OUVRIR_BANC_WEB.cmd`
(Windows) ou son �quivalent existant. D�marrer le moteur **OEM V1.21**, attendre
son d�marrage et fermer les autres clients : CPS int�gr�, pont COM/PTY, sondes.
Le firmware autonome RX FM alpha ne poss�de pas encore de gestionnaire CPS.

Ouvrir **l'adresse exacte affich�e par le banc**, suivie de `/cps/` : par exemple
`http://127.0.0.1:8765/cps/`. Le port peut �tre diff�rent. �viter de remplacer
127.0.0.1 par localhost : le banc v�rifie l'origine exacte des requ�tes POST.
Le bouton **Banc �mul�** du fichier autonome propose aussi d'ouvrir cette page.
Le stockage de session de cette page et celui du fichier autonome sont distincts.

## Parcours

1. Cliquer **Banc �mul�** dans le CPS servi par le banc.
2. Choisir 1-32, 33-64, 65-96 ou 97-128.
3. Cliquer **Identifier et lire**. La session fait PROGRAM, identit�, 128
   lectures de 16 octets, puis END. Les r�ponses viennent du firmware ex�cut�.
4. Examiner les noms, RX/TX, modes et niveaux de puissance partiellement d�cod�s.
5. Exporter �ventuellement l'instantan� d'inspection JSON.
6. **Red�marrer le moteur** avant toute nouvelle lecture. L'annulation ou un
   r�sultat ambigu impose aussi cette reprise ; aucune commande n'est rejou�e.

La page compl�te et l'ACK de END sont n�cessaires pour valider un instantan�.
Un instantan� ant�rieur reste horodat� et ne repr�sente pas l'�tat courant du
poste. Un changement de moteur/session interrompt la lecture. Interrompre annule
les requ�tes locales ; une commande d�j� accept�e peut encore �tre ex�cut�e.
Ce bouton ne commande pas l'arr�t du moteur.

## Port�e du d�codage

- Le mod�le d�clar� doit commencer par `I D578UV NUL` et finir par ACK. Les octets
  de version ne sont pas interpr�t�s : cette identit� ne certifie pas la V1.21
  ni la compatibilit� PRO/PLUS. Le profil de lecture reste celui de la V1.21.
- Les lectures sont born�es � `0x00800000`-`0x00801FFF` : 128 emplacements de
  64 octets, en quatre pages de 2048 octets. Toute autre adresse est refus�e.
- RX et d�calage TX sont d�cod�s en BCD, en unit�s de 10 Hz. BCD invalide,
  fr�quence nulle ou d�calage r�serv� produisent une valeur inconnue.
- Les noms sont interpr�t�s uniquement s'ils sont ASCII imprimables. Les modes
  et puissances suivent le d�codage partiel de `mini_cps_protocol.js`.
- Bitmap d'activit�, tons, largeur FM, interdiction TX et zones non interpr�t�s.
  Un emplacement affich� n'est pas un canal actif certifi�.
- L'instantan� `opend578-oem-readonly-v1` n'est pas un codeplug OpenD578 et n'est
  pas import� dans l'�diteur. Aucun champ manquant n'est invent�.

## Transport et protections

`bench/web_server.py` sert les fichiers compil�s sous `/cps/`, via
`bench/cps_assets.py`. Les contr�les de jeton `X-Lab-Token` et d'origine sont
conserv�s ; aucune r�gle CORS ni �coute r�seau �tendue n'est ajout�e.
Le simulateur GitHub Pages ne fournit pas cette API Python.

Le client HTTP autorise configuration, �tat CDC, d�marrage de l'h�te USB et
octets PROGRAM, identit�, R born� et END. Aucune commande W, TX, mise � jour ou
calibration n'est �mise. Cela ne prouve pas que le firmware ne r�alise aucune
�criture interne de sa propre initiative. Aucun jeton ni flux brut n'est journalis�.

Le banc ne verrouille pas les diff�rents clients USB entre eux. Le CPS refuse
une file occup�e et d�tecte les octets inattendus, mais ne remplace pas cette
exclusivit�. Fermer les autres clients est requis.

## V�rification et limites

```sh
cd cps
npm test
npm run build
npm run build:standalone
cd ..
python -m unittest discover -s bench -p test_cps_assets.py -v
```

Les fixtures v�rifient le client h�te, pas un firmware : fragmentation, checksum,
identit�, moteur/session, d�bordement, bornes, annulation et absence de W.
Les tests Python v�rifient le confinement des fichiers et le build absent.

Le parcours OEM r�el a r�ussi sur la premi�re page avec le moteur natif :
identit� D578UV, 32 emplacements, contr�le de chaque r�ponse et ACK de END.
Aucune W, captures originales inchang�es. Voir PROJECT_STATUS.md et
NATIVE_WINDOWS_QUALIFICATION.md. D�codage complet, navigateur graphique et
poste physique restent non qualifi�s.

Essai reproductible depuis la racine du d�p�t (Node 24 et Python avec les
versions �pingl�es dans bench/requirements.txt) :

```powershell
node tools/qualify_cps_python.mjs CHEMIN_PYTHON DOSSIER_CAPTURES DOSSIER_RESULTATS_NEUF
```

Le script d�marre son propre serveur local, attend au plus 300 secondes avant
la lecture puis arr�te son processus. La variable OPEND578_BOOT_TIMEOUT_MS permet
un budget de 1 000 � 600 000 ms. Un �chec rend un code non nul et qualification.json.
Ce rapport ne contient ni noms ni fr�quences. Les commandes USB passent par
l'allowlist du CPS et une seconde v�rification dans le transport du script.
Ne pas utiliser ce test en parall�le d'un autre client sur la m�me session.
