# Reprendre les collectes incompletes sans perte de provenance

## Priorite A : ressources AnyTone citees mais non recuperees

L'analyse des liens des pages F1DMG `page-20.htm` et `page-22.htm` retrouve **19 URL de type fichier sans sauvegarde effective** (certaines exterieures au site F1DMG). Le CSV `F1DMG_LIENS_NON_RECUPERES.csv` dans le paquet d'audit donne les URLs completes, textes de lien et etats.

| Objet cite par F1DMG | URL d'origine | Importance |
| --- | --- | --- |
| Codeplug D578 V1.11 (`.rdt`) | <http://f1dmg.free.fr/Exemple-v1.11-2020.rdt> | Etude des champs et des migrations anciennes |
| Aides CPS francaises (`.zip`) | <http://f1dmg.free.fr/Help-TRADUCTION-FR-ANYTONED578-D878.zip> | Terminologie CPS et options accessibles |
| AT Options (`.rar`) | <http://f1dmg.free.fr/AT-Option-anytone-2a8.rar> | Historique des options de service et permissions |
| Firmware historique D578 (`.zip`) | <http://f1dmg.free.fr/D578UV-V119-2-OM.zip> | Reference de version, ne pas melanger les branches |
| Aide CPS HPT | <http://f1dmg.free.fr/D878-V301-UV-UVII-English.HPT> | Format d'aide/traduction constructeur |
| Video verrouillage micro (`.mpg`) | <http://f1dmg.free.fr/page-20/veroumicro.mpg> | Verification comportement utilisateur |
| Archive du microphone BT01 | <http://www.wouxun.us/Software/AnyTone-Software/BT01-BT-Microphone.zip> | Historique de distribution, composants a identifier |
| Codeplug AT168 satellite (`.rdt`) | <http://f1dmg.free.fr/AT168-OK-DMG-SATv105.rdt> | **Autre appareil**, ne pas traiter comme exemple de D578 |

Certains de ces contenus peuvent ne plus exister sur le serveur. Le fait qu'ils ne soient pas dans l'archive provient principalement du filtre du telechargeur, qui excluait par defaut les ZIP/RAR et ne reconnaissait pas `.rdt`, `.HPT`, `.mpg` comme fichier. Les URLs conservees ne garantissent **pas** leur disponibilite actuelle.

**Securite :** ne pas executer de binaire externe historique; relever l'origine, la date, la taille, le SHA-256 et examiner en lecture seule. Ne jamais envoyer sur un poste GD32 un firmware d'une autre branche.

## Priorite B : photos et miroirs

- [Photo nappe de facade 40 broches](https://radio.carstenbauer.net/578%20head%20connections.jpg) : le navigateur peut l'accepter si les espaces sont codes, l'ancienne archive ne l'a pas telechargee.
- `578 BT Mic.jpg`, `578 KC8GL label.jpg`, `578 speaker sockets.jpg`, `578 speaker mod1.jpg`, `578 speaker mod2.jpg` : les miroirs Carstenbauer/Reddicams ont echoue, mais DB1IG en conserve des copies sous des noms ajustes. Les 46 autres images partagees DB1IG/Carstenbauer sont strictement identiques par SHA.
- [TheWeeks](https://www.theweeks.org/tmp/FILES/Anytone-Mods/578mods.htm) : echec TLS. Ne pas desactiver la verification de certificat sans justification; conserver le lien et utiliser DB1IG/Carstenbauer comme miroirs disponibles.
- [Collection OZ1DGQ](https://qsl.net/oz1dgq/home-filer/anytone-hints.htm) : reessayer trois liens PDF en encodant leurs espaces; deux autres ont renvoye 404.

## Priorite C : couverture externe

- DB1IG : [D878mods](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_878mods.php), [DMR basics](https://db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_dmrbasics.php), pages d'export CPS et d'editeur de contacts. La presente archive contient seulement `578mods.php`.
- [RadioFoundry](https://radiofoundry.org/docs/spec/hardware-anytone) : contenu technique deja etudie dans OpenD578, mais page originale absente de ce ZIP.
- FCC : photos et rapports de certification `T4K-D578UV`, `T4K-D578UVIII` et revisions comparables, avec la reference exacte de chaque PCB.
- Depots open source `dmr-tools/codeplugs`, `qdmr`, `CodeplugStudio`, `anytone-flash-tools`: conserver versions, commits et licenses separement. Ne pas melanger code source tiers et reverses constructeur.

## Outil de collecte

Le code `tools/archive_sources_privees.py` du depot a ete corrige pour normaliser les URL contenant des espaces et pour reconnaitre `.rdt`, `.HPT`, `.mpg` et `.mp4` lorsque l'option de collecte des archives binaires est activee. Une configuration ciblee `f1dmg_anytone` capture les deux principales pages sans explorer des centaines de repertoires sans rapport. Les fichiers originaux restent archives **en prive** et une nouvelle execution ne doit pas ecraser le ZIP fourni.

Sous Windows, depuis la racine du depot, avec Python 3 :

```powershell
py -3 tools/archive_sources_privees.py --sites f1dmg_anytone vk7zja_v74 db1ig_anytone_related radiofoundry --include-tools --max-pages 30 --max-assets 1200 --destination "$HOME\Downloads\OpenD578_archives_privees"
```

Les liens externes de F1DMG (hebergeurs tiers) ne sont pas suivis automatiquement pour raison de provenance et de limites de domaine. Ils sont enumeres dans le CSV pour un archivage cible separe. L'outil peut rencontrer des erreurs 404, HTTPS ou de restrictions d'acces. Ces erreurs doivent etre conservees, jamais remplacees par de faux fichiers.
