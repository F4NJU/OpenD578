# Lecture OEM r�elle avec les acc�l�rateurs Windows

R�sultat du 12 novembre 2026 : le client CPS TypeScript a effectu� une lecture
r�elle de la premi�re page via HTTP et USB CDC du banc, avec les captures OEM.
Voir `qualification/native-readonly-2026-11-12.json` pour les observations.
Ce test ne remplace pas une validation sur poste physique, ni le contr�le du
d�codage int�gral des canaux. Il ne valide pas le nouveau firmware OpenD578.

## Construction

Pr�parer Python 3.13.5 et les d�pendances �pingl�es du banc. Le Python 3.15 du
poste ne convient pas � cette installation �pingl�e de NumPy.

Le compilateur utilis� est la distribution portable officielle
[Zig 0.15.2 Windows x86_64](https://ziglang.org/download/0.15.2/zig-x86_64-windows-0.15.2.zip).
SHA256 de l'archive :
`3a0ed1e8799a2f8ce2a6e6290a9ff22e6906f8227865911fb7ddedc3cc14cb0c`.
Les t�l�chargements et binaires ne sont pas ajout�s au d�p�t.

Depuis la racine d'une copie compl�te du d�p�t, arr�ter le banc avant de
remplacer les DLL. Adapter les deux chemins d'ex�cutables :

```powershell
$benchPython = 'C:/chemin/python3135/python.exe'
$zigCompiler = 'C:/chemin/zig-x86_64-windows-0.15.2/zig.exe'
& $benchPython tools/build_bench_native_windows.py --zig $zigCompiler
```

Le script compile les sources existantes `bench/native_gate.c` et
`bench/lcd_bridge.c` en DLL Windows x64, sans les modifier. Clang et LLD sont
appel�s directement, sans CRT externe : ces ponts ne d�pendent que des rappels
fournis par Python/Unicorn. Les empreintes et commandes sont enregistr�es dans
les fichiers `.dll.build.json`. L'essai a �galement reconstruit les deux DLL
dans un r�pertoire s�par� pour v�rifier le script de construction.

Le pilote `zig cc` a �chou� ici sur ses fichiers de cache/MinGW ; l'appel direct
�vite cette d�pendance. Un ancien binaire TinyCC a �t� refus� au lancement par
Windows et n'est pas utilis� pour les DLL qualifi�es.

## Contr�les des ponts natifs

Les tests acceptent soit un compilateur via `CC`, soit les DLL d�j� construites :

```powershell
$env:OPEND578_NATIVE_GATE_LIBRARY = (Resolve-Path bench/native_gate.dll).Path
$env:OPEND578_LCD_BRIDGE_LIBRARY = (Resolve-Path bench/lcd_bridge.dll).Path
& $benchPython -m unittest discover -s bench -p test_native_masks.py -v
& $benchPython -m unittest discover -s bench -p test_lcd_bridge.py -v
```

Sept tests r�ussis, aucun ignor� : masque d'interruption, d�codage GPIO LCD,
couleurs RGB565, r�initialisation, file d'�v�nements, tra�age et entr�es NAND.
Ces tests sans capture restent distincts de l'ex�cution OEM ci-dessous.

## Essai r�el

Node 24 est n�cessaire pour charger les modules TypeScript du CPS.
Les captures authentifi�es et le SCT s�par� doivent �tre dans DOSSIER_CAPTURES.
Choisir un nouveau r�pertoire de r�sultat. Aucun autre client ne doit utiliser
la session que le script cr�e.

```powershell
$env:OPEND578_BENCH_ENGINE = 'interactive'
$env:OPEND578_BOOT_TIMEOUT_MS = '300000'
node tools/qualify_cps_python.mjs $benchPython DOSSIER_CAPTURES DOSSIER_RESULTATS_NEUF
```

`interactive` est le nom de l'option serveur qui active le moteur natif et les
horloges interactives existantes. Le mod�le mat�riel et ses r�ponses ne sont
pas remplac�s. Le rapport conserve cette option ; le statut du banc a confirm�
`execution_engine: native` durant l'essai.

Apr�s `application_running`, le client envoie PROGRAM, identit�, 128 lectures
R de 16 octets, puis END. La m�me allowlist de lecture est v�rifi�e � deux
niveaux. Le rapport compte les trames soumises au transport, pas une capture
�lectrique USB. L'essai r�ussi totalise 131 trames, aucune W, 2 048 octets,
32 emplacements et ACK de END. La reprise fonctionnelle apr�s END reste � tester.
Le script arr�te ensuite le processus qu'il a lanc� et retourne un code non nul
en cas d'�chec ou d'expiration du budget.

Les captures originales et les cinq SHA256 sont inchang�s apr�s l'essai.
Les donn�es brutes, images d'�cran et traces m�moire restent locales ; le rapport
public contient seulement les compteurs, empreintes et limites de qualification.
