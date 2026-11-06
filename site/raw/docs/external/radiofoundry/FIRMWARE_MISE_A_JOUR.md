# Mise à jour OEM, CPS, bootloader et récupération par variante

Source : [RadioFoundry, section 3](https://radiofoundry.org/docs/spec/hardware-anytone) ; références locales : [bootloader V1.21](../../peripherals/05_BOOTLOADER_24K_DUMP_VECTEURS_USB_FMC_DEVELOPPEMENT_OPEN_SOURCE.md), [USB CPS](../../cps/PROTOCOLE_OEM_V121.md), [compatibilité PRO/PLUS](../../cps/COMPATIBILITE_PRO_PLUS.md).

## 1. Trois logiciels indépendants dans le poste

Le MCU GD32 démarre son bootloader OEM et ensuite l'application. Le SCT3258 a son **firmware interne** plus un bootstrap envoyé à chaque reset par le MCU. Les modules Bluetooth/LinkBoard et le contrôleur du microphone possèdent eux aussi des chemins de mise à jour ou une version logicielle spécifique. Les ressources d'icônes ne doivent pas être prises pour un firmware applicatif. Une mise à jour SCT n'est pas un remplacement de bootloader GD32.

## 2. Conteneurs et protocole de chargement

L'étude externe distingue `.spi` (fichier présenté à l'outil CPS), `.CDI` (métadonnées et identité) et `.CDD` (image). Les tailles varient avec la version : `.spi` peut mesurer 14 ou 51 octets, `.CDI` environ 278 octets dans certains packages firmware. Des jeux d'icônes utilisent d'autres tailles. Le binaire CDD peut contenir une table de vecteurs Cortex-M lisible, mais cela ne prouve pas que le chargeur accepte toute image arbitraire.

RadioFoundry décrit un dialogue `UPDATE` suivi de **paquets de 32 octets avec checksum additif** pour les firmwares étudiés. Dans notre propre banc, la programmation CPS des données utilise **un autre état** : `PROGRAM`, `R`, `W`, `END`, avec des contrôles de blocs. Il faut créer deux décodeurs et deux jeux de tests séparés ; ne pas envoyer `UPDATE` lors d'un test de lecture CPS.

Le nombre `921600` visible dans le logiciel QX est une indication d'interface utilisateur, pas une preuve que le câble USB fait fonctionner un UART matériel à ce débit. Le chemin demeure USB CDC, dont le débit virtuel peut être arbitraire.

## 3. Différence fondamentale du boot GD32 V1.21

| Édition | Boot/application | Source de preuve |
|---|---|---|
| Images D868/D878 anciennes citées par RadioFoundry | Boot 16 Kio, appli vers `0x08004000` | Source comparative autre modèle |
| **Notre D578 PRO GD32 V1.21** | **Boot 24 Kio**, application à `0x08006000` | Dump SWD réel + comparaison avec CDD V1.21 |
| D578 PLUS AT32 | Famille MCU différente et fichiers séparés | Version externe, **non** notre unité PLUS GD32 |

Nous avons également observé l'exécution en **MCU UPDATE** et une limitation du chargeur constructeur aux premières adresses de Flash accessibles pendant le transfert. Les mécanismes de protection de dépassement restent à vérifier. Le firmware alternatif satellite ne doit **pas** être assemblé à l'adresse `0x08004000` pour cette unité.

## 4. Séquences matérielles et précautions

- D578 : l'étude externe mentionne `MENU+EXIT` pour accéder à l'UPDATE MCU. Notre analyse a déjà identifié ce mode et l'accès SWD sous cet état.
- Entrée SCT : les guides historiques donnent `MENU+DIAL` sur D578 ; une combinaison `# + touche supérieure` concerne d'autres membres de la famille. Ne pas exporter le raccourci du portable à la façade du D578.
- L'option de réinitialisation après mise à jour peut **effacer le codeplug** ; sauvegarder `.rdt` et options CPS avant action.
- `BOOT0`/ROM : la présence de fonctions de boot ROM dans la famille GD32 ne garantit pas que BOOT0 soit accessible sur PCB. Notre voie de lecture valide est le SWD dans MCU UPDATE ; ne pas proposer de recovery ROM garanti.
- Le changement de MCU GD32/AT32 implique des images incompatibles, même si le produit commercial possède le même nom.

## 5. Qualification demandée

Construire un parseur **hors ligne** du triplet `.spi/.CDI/.CDD`, une vérification du checksum en lecture, des vecteurs d'adresse et du modèle. Lire les valeurs d'identité du poste et confronter à la cartographie SWD V1.21 avant d'envisager la moindre écriture. Conserver les charges utiles OEM propriétaires **hors GitHub** avec leurs empreintes. Aucun fichier de ce dossier n'est un firmware flashable.
