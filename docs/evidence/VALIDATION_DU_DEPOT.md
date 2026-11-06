# Validation du depot public, lot de preuves du 05/11/2026

Le controle de cette livraison a porte sur les **fichiers remis et les comportements de leur outillage documentaire**, et non sur une emission radio ou une programmation du poste.

| Test | Etat | Portee |
| --- | --- | --- |
| Inventaire CPU GD32 100 pins | Reussi | CSV de 100 broches, signaux annotés par provenance |
| Fichier KiCad reconstruit | Partiel | 100 pins et syntaxe structurelle controlees, non ouvert dans l'interface KiCad |
| Modeles materiels | Reussi | 2 modeles avec destinations de liens existantes, faits et hypotheses separes |
| Site Markdown -> HTML | Reussi | Liens locaux valides, lien vers documents sources, lecture integree |
| Registre des preuves | Reussi | IDs uniques, provenance, lien local existant et 29 affirmations classees |
| CPS trace decoder | Reussi | 4 tests locaux, aucune ecriture radio |
| Bluetooth protocol analyzers | Reussi | 5 tests locaux, aucun appairage materiel |
| Mini-CPS JavaScript | Reussi | Test Node des transformations de champs; pas de CPS physique |
| Audit publication | Reussi | Pas de binaire proprietaire ou dump dans les chemins publics |
| Banc complet Python/Unicorn | **Non verifie dans cette session** | Dependance `unicorn` absente et installation impossible sans acces PyPI; CI Github installe `bench/requirements.txt` et execute la suite |
| Releves physiques RTC/GNSS, GPIO RF/HPI/Bluetooth | **A faire** | Photo/multimetre/logic analyzer necessaires, aucune trace fabriquee |
| Firmware autonome flashable | **Non disponible** | Aucun fichier de mise a jour radio valide ou autorise |

La creation du ZIP peut etre controlee par les SHA-256 de `PACKAGE_MANIFEST_20261105.json`. Le fichier `site/` est genere automatiquement et ne doit jamais etre edite a la place de son Markdown source. Voir [les originaux manquants](../archives/ORIGINAUX_A_RECUPERER.md) et [le centre de preuves](INDEX.md).
