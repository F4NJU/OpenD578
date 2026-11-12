# �tat du travail CPS - 12 novembre 2026

## Qualification r�elle OEM/CPS r�ussie - 12 novembre 2026

Le parcours r�el Flash + NAND + SCT, serveur Python HTTP et client TypeScript
CPS a r�ussi en lecture seule avec le moteur natif interactif du banc.
Le d�marrage a atteint application_running � 52 270 001 instructions,
132 707 pixels et 8,445 secondes simul�es. Le moteur publi� est bien native.
PROGRAM a re�u QX/ACK, l'identit� D578UV a �t� v�rifi�e, 128 r�ponses R de
16 octets ont pass� les contr�les d'adresse et de checksum : 2 048 octets,
soit 32 emplacements de la premi�re page. END a re�u ACK.
Le transport compte 131 trames soumises, aucune W ; les cinq empreintes source
ont �t� recontr�l�es et restent identiques. Aucun poste physique utilis�.

Les acc�l�rateurs native_gate.c et lcd_bridge.c sont inchang�s. Compilation
portable Windows par Clang/LLD de Zig 0.15.2 ; sept tests des DLL r�ellement
charg�es passent (interruptions, affichage et entr�es NAND). Le script de
construction Windows �vite les probl�mes de cache du pilote Zig/MinGW.
Les 45 tests CPS et les quatre tests Python pr�c�dents restent leurs r�sultats
h�te s�par�s : ils ne constituent pas � eux seuls cette qualification r�elle.

Rapport public sans donn�es de canaux :
`qualification/native-readonly-2026-11-12.json`. Reproduction :
`NATIVE_WINDOWS_QUALIFICATION.md`. Captures, DLL et r�sultats bruts restent locaux.

Port�e : premi�re page OEM uniquement, identification, transport de lecture et
END. Le d�codage complet des noms/fr�quences, les autres pages, l'import automatique,
la reprise fonctionnelle apr�s END, le navigateur graphique et le poste physique
restent � qualifier. Ne pas assimiler ce r�sultat au CPS du nouveau firmware
OpenD578 ni � une qualification de la partie DMR. Prochaine �tape : comparer
les champs d�cod�s � une r�f�rence du CPS du banc avant de proposer leur import.

## Historique : essais Python ant�rieurs au succ�s natif

Le serveur Python et son API HTTP ont �t� ex�cut�s avec les captures authentifi�es
et le SCT complet. Le client CPS attend le signal `application_running` avant
PROGRAM : cette condition n'a pas �t� atteinte et aucune trame CPS n'a �t� envoy�e.

Un essai de 90 secondes avec les options Python habituelles a atteint environ
14 millions d'instructions et 43 584 pixels. Un essai exploratoire de 300 secondes,
avec le mode interactif et l'acc�l�ration d'horloge d�j� propos�s par le banc,
a atteint 48 240 000 instructions, 100 984 pixels et 8,38 secondes simul�es.
Le firmware dessine et progresse ; le r�sultat est une expiration de budget,
pas la preuve d'un blocage d�finitif. `application_running` reste faux.
L'activation exploratoire du mode interactif pour Python dans le serveur a �t�
retir�e : aucune modification du mod�le mat�riel n'est livr�e.

Le script `tools/qualify_cps_python.mjs` rend l'essai reproductible avec le serveur
non modifi�, une attente born�e et un rapport sans donn�es de canaux. Il utilise
le v�ritable client CPS et l'API du banc ; il ne cr�e aucune r�ponse OEM.
Les cinq empreintes source sont inchang�es. Les 45 tests Node du CPS et les deux
tests Python des ressources statiques passent, ainsi que les deux tests d'archive.
La lecture USB, l'identification et END sur firmware r�el restent � qualifier.
Prochaine action technique : qualifier le d�marrage sur le moteur natif pr�vu
par le banc, ou pr�voir un essai Python plus long avec un budget explicite.

## Reprise de qualification - �tat v�rifi� le 12 novembre

Lors de la reprise initiale, la qualification USB/CPS �tait en attente ; les captures sont
d�sormais disponibles et authentifi�es. Le bon chemin est
`browser-bench/samples/F4EGM.zip` (majuscules), sur Telectroboy/OpenD578, commit
`391490e21ebedd0edf295d4ed4ccd63ab8f16054`. Le pr�c�dent 404 venait de la casse.
L'archive de passation ancienne est d�pass�e selon F4EGM.

Le ZIP a �t� r�cup�r�, son blob Git v�rifi� et les quatre fichiers contr�l�s par
taille et SHA256 : Flash 3 Mio, NAND 256 Mio, OOB 8 Mio, ECC 128 Kio. L'application
V1.21 extraite de la Flash correspond aussi � l'empreinte du d�p�t. Copies de
travail locales dans `capture-inputs/`, laiss�es intactes pendant les essais.

Sur le PC de Maxime, le lancement a aussi �chou� : Python 3.15, d�pendance
`numpy==2.3.5` t�l�charg�e sous forme source, compilation impossible faute de
compilateur. **F4EGM confirme utiliser Python 3.13.5.** Un Python 3.13.5 portable
isol� a maintenant �t� pr�par� dans `runtime/python3135/`, sans modifier les
Python syst�me. Toutes les d�pendances �pingl�es du banc y sont install�es et
importables, dont NumPy 2.3.5 (wheel binaire, sans compilation).
L'indication g�n�rale � Python 3.11 ou plus r�cent � ne garantit pas que toutes
les d�pendances �pingl�es disposent d'un paquet binaire pour l'interpr�teur choisi.

**Travail repris � la demande de l'utilisateur avec les captures.** Une copie
compl�te de `feature/cps-core` est disponible dans `integration/`.
Les obstacles observ�s sont maintenant pr�cis :

- **Pr�requis SCT r�solu** : `SCT3258TD_UpdateFlash_V2_01_07BF.hex` est fourni
  s�par�ment dans `browser-bench/samples/` du d�p�t amont, commit
  `8c7f2b5ff4df83fa9bef7a64fc5a597d61ace57f`. T�l�charg� et authentifi� par le
  banc (603 102 octets, SHA256 d5ada473af891b6c707978f0b9dde81324afcc4af27348d3bcdf70615ab19407).
  Tous les contr�les d'entr�es du parcours OEM Python passent d�sormais. Ce fichier
  est une r�f�rence du mod�le de composant ; aucun d�veloppement DMR n'est entrepris.
- Le parcours OEM `run_lcd.py`, moteur Python 3.13.5, a maintenant ex�cut�
  200 000 instructions et atteint son budget pr�vu (PC 0x0808ADFA), avec sept
  buffers NAND. Aucun pixel ni lecture CPS compl�te � ce stade : poursuivre la
  qualification du d�marrage, puis USB. Ne plus demander ce fichier � F4EGM.
- Un essai r�el par `run_hardware.py`, moteur Python, a ex�cut� 69 119 instructions
  puis s'est arr�t� sur `RF SPI has multiple active chip selects`, PC 0x0800870C,
  �criture GPIOB 0x40010C00. Ne pas masquer cette limite par une r�ponse invent�e.
- Le chemin WebAssembly a �t� initialis� mais l'essai a �t� interrompu sans
  lecture CPS compl�te ; ne pas le pr�senter comme une qualification r�ussie.

Voir `F4EGM_CAPTURE_CHECK.md` pour les empreintes, le protocole d'essai et les
limites. On peut continuer le CPS hors ligne ind�pendamment de ces points.

## Ce qui existe

- �diteur TypeScript local et fichier HTML autonome ; JSON/CSV, canaux, zones,
  VFO, s�lection multiple, historique, sauvegarde de session.
- Adaptateur OEM en lecture seule pour le banc Python, servi sous `/cps/` ;
  identification et groupes de 32 emplacements. Tests h�te r�ussis, qualification r�elle de la premi�re page
  obtenue avec les images priv�es, voir le r�sultat en t�te de ce document. Aucun W ou acc�s m�moire direct.
- Le firmware autonome RX FM alpha du d�p�t ne poss�de pas encore de CPS.

## Derni�re livraison hors ligne - CPS 0.6

- Listes de scan : membres ordonn�s et priorit� optionnelle, �dition et validation.
- Format PC v2 avec conversion explicite des fichiers v1, sans modifier l'original.
- Puissance en liste d�roulante avec niveaux personnalis�s conserv�s ; d�calage
  relais et TX ind�pendante ; cr�ation en s�rie avec aper�u ; bilan avant export.
- Import CSV externe avec association des colonnes, unit�s explicites, aper�u
  pagin�, erreurs, doublons, s�lection des lignes et zone de destination.
  Identifiants neufs ; ajout atomique annulable. Import natif OpenD578 conserv�.
- Contrat de donn�es destin� au firmware neuf : proposition � relire avec F4EGM,
  et non une d�claration de fonctionnalit�s d�j� disponibles sur le poste.

45 tests Node r�ussis ; build modulaire et HTML autonome g�n�r�s, syntaxe du
bundle v�rifi�e. Les nouveaux parcours graphiques restent � v�rifier dans un
navigateur ; les calculs et r�gles sont test�s. La premi�re lecture OEM est qualifi�e ; les limites restantes sont d�taill�es en t�te.

Prochaines pistes : param�tres g�n�raux � convenir avec F4EGM, essais graphiques
sur des exports CSV r�els, puis comparaison des champs OEM et �largissement
de la qualification de lecture. Aucun deuxi�me faux poste n'est � d�velopper : r�utiliser le banc.
