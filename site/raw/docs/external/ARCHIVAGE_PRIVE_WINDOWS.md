# Sauvegarder localement les originaux et les photos sous Windows

L'archivage est **separe du depot GitHub public** afin de conserver les sources telles que publiees et de respecter les droits des photographes/auteurs. Aucune photo, HTML complet ou executable tiers ne sera absorbe dans le site OpenD578 par cette operation. La sauvegarde reste sur le disque de l'utilisateur.

## Une commande depuis PowerShell

Depuis la racine de `C:\GitHub\OpenD578`, lancer :

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\archive_sources_windows.ps1
```

Le script utilise Python disponible par `py -3`. Il parcourt les pages du domaine F1DMG accessibles depuis la racine, y compris `page-20.htm` et `/578a`, essaie aussi Wayback pour les adresses F1DMG connues si le serveur est indisponible, puis sauvegarde les pages VK7ZJA (theweeks, v7.4 et miroirs) et l’index documentaire OZ1DGQ, avec leurs images, feuilles de style, PDF locaux et liens vers d'autres documents.

Chaque execution cree un **nouveau sous-dossier horodate** sous `C:\GitHub\OpenD578_archives_privees\`. Aucun ancien jeu de fichiers n'est efface ou remplace.

Sorties : `originals/` (octets d'origine), `offline/` (liens vers les fichiers locaux quand ceux-ci sont presents), `index.html` pour consulter les pages, `manifest.json` (URL, date, taille, empreinte SHA-256), `checksum.sha256`, `links.txt` (tous les liens rencontres) et `INDEX.md` (inventaire, y compris les erreurs de connexion).

**Limites** : les serveurs inaccessibles ne peuvent pas etre archives magiquement. Les images chargees par scripts JS, par service tiers, ou via un lien de type Mega/Google Drive peuvent necessiter une recuperation manuelle. Les versions de chaque site peuvent differer. Cette capture n'est pas un aspirateur universel de tout Internet.

## Extensions et outils binaires

Les fichiers `.exe`, `.zip`, `.spi`, `.hex` etc. sont **inventories par leur URL**, mais pas recuperes par defaut. Pour les collecter volontairement a des fins de conservation privee :

```powershell
py -3 .\tools\archive_sources_privees.py --destination ..\OpenD578_archives_privees --sites theweeks vk7zja_v74 --include-tools
```

Ne jamais lancer automatiquement les programmes telecharges. Effectuer un antivirus et conserver les fichiers de firmware hors de GitHub, avec des empreintes SHA-256.

## Verification des sauvegardes

Dans le nouveau sous-dossier horodate :

```powershell
Get-Content .\f1dmg\INDEX.md
Get-Content .\theweeks\INDEX.md
Get-Content .\vk7zja_v74\INDEX.md
```

Ouvrir `index.html` dans chaque sous-dossier du site capture, puis consulter `manifest.json` pour les exceptions. Si F1DMG est inaccessible, comparer avec une [recherche Wayback](https://web.archive.org/web/*/http://f1dmg.free.fr/page-20.htm), ou chercher sur d'autres sauvegardes personnelles. Mettre a jour notre index de provenance lorsque de nouvelles pages sont effectivement retrouvees.

## Publication et trace de licence

L'archivage personnel ne confere pas de licence de republication. Ne pas copier automatiquement `originals/` vers `hardware/photos/` ni `site/` : ces chemins sont destines a nos propres photos, contenus et documents disposant d'un droit de diffusion identifie. Pour des photos F1DMG/VK7ZJA, demander l'autorisation des ayants droit ou utiliser un lien source. La documentation technique factuelle et les analyses originales OpenD578 restent librement publiables selon la licence du depot.
