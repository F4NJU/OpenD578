# Captures F4EGM - v�rification et premier essai r�el

Date : 12 novembre 2026. D�p�t amont : Telectroboy/OpenD578, commit
`391490e21ebedd0edf295d4ed4ccd63ab8f16054`.

## Entr�es authentifi�es

Chemin exact : `browser-bench/samples/F4EGM.zip` (respecter les majuscules).
Taille ZIP : 8 812 776 octets. SHA256 de l'archive :
`cc4f96fb71be8373ca5f5d38c93419db3cd1766098f1f7bd378d83bce44b66c9`.
Son identifiant de blob Git a aussi �t� recalcul� :
`f3f7f31eb68f47d89016a49badb70ca1c2f66fec`.

| Capture | Octets | SHA256 |
| --- | ---: | --- |
| full_flash_pass1.bin | 3145728 | e2f2483baf60e2bfcab656e25e949670713222591ef4d611d6089054819a750e |
| nand_main_256MiB.bin | 268435456 | 329d22165d234bf0df043e62af11397dea96327925b9db18f3c354230ff40945 |
| nand_oob64_8MiB.bin | 8388608 | 9a999b9fd13a02b45ed4d38e68f9e9c7d1095994c751e36e04f4a62b2e4c5106 |
| nand_ecc_status_128KiB.bin | 131072 | b40ebd3ebc3923f01d9d98a52a3b019b65785641ba76687127678b788ea793c6 |

Ces empreintes correspondent aux constantes du banc. `prepare()` extrait aussi
une application V1.21 de 1 020 300 octets, SHA256
`02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a`.

Le v�rificateur ajout� ne n�cessite aucune d�pendance externe et ne modifie ni
n'extrait les entr�es :

```sh
python tools/verify_f4egm_archive.py /chemin/F4EGM.zip
```

Deux tests unitaires accompagnent l'outil ; ils ne sont pas des essais firmware.

## Environnement Python pr�par�

Python portable officiel 3.13.5, isol� du syst�me. Paquets binaires install�s et
imports v�rifi�s : unicorn 2.1.4, capstone 5.0.9 (version de distribution), pillow
13.0.0, numpy 2.3.5, pyserial 3.5. Aucune compilation NumPy n�cessaire.
La version interne affich�e par le module capstone peut diff�rer de la m�tadonn�e
de sa distribution ; les d�pendances �pingl�es ont �t� contr�l�es par m�tadonn�e.

## Essais et limites distinctes

**Actualisation : fichier SCT retrouv� et valid�.** F4EGM l'a fourni s�par�ment
dans `browser-bench/samples/SCT3258TD_UpdateFlash_V2_01_07BF.hex` (amont
`8c7f2b5ff4df83fa9bef7a64fc5a597d61ace57f`). Taille 603 102 octets, SHA256
`d5ada473af891b6c707978f0b9dde81324afcc4af27348d3bcdf70615ab19407`.
`check_inputs()` et `prepare_sct_reference()` passent. Le blocage d'entr�e du
paragraphe 1 ci-dessous est historique et r�solu ; le ZIP conserve bien quatre
captures et le SCT est un cinqui�me fichier s�par�. Ce contr�le de r�f�rence
n'implique pas de d�velopper ou de qualifier le DMR.

Apr�s ajout du SCT, `run_lcd.py` (moteur Python, sans acc�l�ration LCD native,
budget 200 000 instructions) s'arr�te normalement sur `instruction_budget`,
PC `0x0808ADFA`, avec sept buffers NAND, aucun pixel et sans lecture CPS.
C'est une ex�cution OEM limit�e r�ussie, pas un d�marrage complet qualifi�.

1. **Banc Python OEM historique (`run_lcd.py`)** : sa v�rification pr�alable
   demande encore `SCT3258TD_UpdateFlash_V2_01_07BF.hex`. Ce fichier n'est pas
   dans le ZIP. Le dossier de quatre captures ne satisfait donc pas � lui seul
   `check_inputs()` pour ce parcours. Le bootstrap SCT de 2048 octets pr�sent dans
   la Flash ne remplace pas cette r�f�rence compl�te de 603 102 octets.
2. **Mod�le mat�riel Python (`run_hardware.py`)** : premier essai arr�t�
   volontairement au budget de 20 000 instructions ; puis budget de 1 000 000
   avec la touche POWER maintenue. Le second ex�cute r�ellement 69 119 instructions
   avant `RF SPI has multiple active chip selects` (cat�gorie `execution_boundary`),
   PC `0x0800870C`, �criture `0x33111144` sur GPIOB `0x40010C00`. Aucun pixel LCD
   n'avait encore �t� produit. Cette limite est conserv�e, pas contourn�e.
3. **WebAssembly existant** : initialisation et chargement effectu�s, essai ensuite
   interrompu ; aucune lecture USB/CPS compl�te obtenue. Ce n'est pas une preuve
   de panne du banc navigateur ni une validation r�ussie.

L'essai mat�riel charge la Flash � `0x08000000`, utilise le vecteur applicatif
`0x08006000`, les trois captures NAND et le bootstrap SCT extrait de la Flash �
l'offset `0xF56CC` (2048 octets). Le moteur est `python`, sans biblioth�que native
compil�e. Les donn�es NAND originales sont ouvertes par l'overlay du banc ; aucun
�tat NAND persistant ni transfert CPS d'�criture n'a �t� demand�. Les empreintes
des quatre copies source sont recontr�l�es apr�s les essais.

Il reste � clarifier avec F4EGM le parcours recommand� pour ces quatre fichiers
(banc navigateur actuel ou Python historique) et � r�soudre les pr�requis/limites
de ce parcours avant de qualifier identification, lecture et fermeture END du CPS.
Ce rapport ne contient ni noms de canaux ni donn�es personnelles des captures.


## Mise � jour : SCT et essai HTTP

Le SCT s�par� a �t� r�cup�r� et authentifi� ; il n'est plus � demander � F4EGM.
Les pr�requis Python sont install�s dans un runtime portable 3.13.5. Les essais
HTTP/OEM ont maintenant ex�cut� le firmware jusqu'� 48,24 millions d'instructions
et 100 984 pixels, sans atteindre application_running dans cinq minutes.
L'API HTTP fonctionne ; aucune transaction CPS n'a �t� lanc�e avant ce signal.
Voir PROJECT_STATUS.md pour les options exploratoires, limites et v�rifications.
Les observations anciennes ci-dessus restent l'historique des premiers essais.


## Dernier r�sultat : lecture r�elle r�ussie avec le moteur natif

Le 12 novembre, le d�marrage a atteint application_running avec les acc�l�rateurs
C existants compil�s sous Windows. Le client CPS a identifi� D578UV, lu les
2 048 octets de la premi�re page (32 emplacements), v�rifi� chaque r�ponse et
re�u ACK de END. 131 trames soumises, aucune W. Les cinq empreintes sont inchang�es.
Ce r�sultat remplace l'attente de qualification de transport indiqu�e dans
l'historique ci-dessus. Voir le rapport qualification/native-readonly-2026-11-12.json
et NATIVE_WINDOWS_QUALIFICATION.md pour sa port�e limit�e et la reproduction.
