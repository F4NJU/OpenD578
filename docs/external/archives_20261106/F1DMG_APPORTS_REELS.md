# F1DMG : ce qui a ete reellement retrouve dans le ZIP

Le site auparavant difficile a charger en direct est maintenant represente par deux HTML principaux et des documents annexes. Cette fiche est une synthese originale des faits disponibles. Les octets, photos et fichiers de l'auteur restent dans l'archive privee.

## Pages principales

- `f1dmg/originals/f1dmg.free.fr/page-20.htm`, source <http://f1dmg.free.fr/page-20.htm>: 53 661 octets, 34 balises image. Contient des liens vers les mises a jour, options, zones, contacts, parametres utilisateur, photos et aides de programmation D578/D878.
- `f1dmg/originals/f1dmg.free.fr/page-22.htm`, source <http://f1dmg.free.fr/page-22.htm>: 136 785 octets, 44 balises image. Presente les differences de versions PRO/PLUS, les procedures BT01, les liens vers VK7ZJA, les aides CPS et les documents SMS.
- Parmi les autres pages HTML utiles du site, la racine relie surtout ces deux rubriques. Les autres pages explorees portent majoritairement sur radio-sondes, meteo, bricolages ou annuaires, pas sur la carte du D578.

## Documents conserves et leur vraie portee

### Modes de demarrage et menu TEST

Original: `f1dmg/originals/f1dmg.free.fr/D578-REGLAGES.doc` (26 624 octets).

Le document liste notamment le mode de mise a jour principal avec **MENU+EXIT**, puis les combinaisons `P1+Dial`, `P2+Dial`, `P3+Dial`, `P4+Dial`, `P5+Dial`, `MENU+Dial` et `EXIT+Dial` pour les ressources d'affichage, le reset, le GPS, le mode TEST, le Bluetooth et la mise a jour SCT. Il distingue trois niveaux d'acces TEST. Ce contenu **recoupe** le guide VK7ZJA et les analyses OEM existantes. Il est utile comme traduction / document historique, mais ne fait pas une seconde mesure independante du GPIO.

### Migration firmware, baseband et codeplug

Original: `f1dmg/originals/f1dmg.free.fr/page-20/MISE_A_JOUR_D578.doc` (17 920 octets).

La procedure presente un enchainement historique complet : export des objets CPS, mise a jour du firmware principal, remise a zero, mise a jour optionnelle du SCT3258, puis des ressources d'icones, installation de la version CPS compatible, lecture d'un poste remis a zero, reimport des objets, verification et ecriture des options, restauration des images et sauvegarde du nouveau codeplug. Le texte remercie VK7ZJA; ce contenu n'est pas une confirmation independante de son guide.

**Apport OpenD578:** documenter cette succession comme *contrat de migration* entre branches CPS, a rapprocher du protocole USB deja analyse. La procedure n'est pas une autorisation de flasher le poste PRO V1.21 avec des images d'autres generations.

### Versions historiques et Bluetooth BT01

Original: `f1dmg/originals/f1dmg.free.fr/Mises_a_jour_pour_BT01.pdf` (185 025 octets, une page texte).

La fiche distingue un D578 PRO et un PLUS, les versions historiques de SCT `V2.01.07BF`, les branches CPS `>=1.17` pour PRO et `>=2.04` pour PLUS, et le fichier `B707_Audio_AGHF_ET12_QX-V10043.bin`. Elle signale la coexistence de MCU **AT** et **GD** ainsi que des variantes de firmware Bluetooth marquees 19043 et 10043. Sa transcription contient une graphie `V177` (presumee erreur historique, ne pas la rectifier silencieusement); elle ne garantit pas les exigences des versions actuelles.

**Attention technique:** le document parle d'« update BT01 » et d'un fichier `ET12`. Il faudra distinguer le firmware du microphone **BT01** de celui du module radio Bluetooth **D868BT-SP/ET12** du D578. L'archive n'apporte pas le programme binaire lui-meme et ne demontre pas a quel microcontroleur precise il est destine.

### Roaming : parametres de configuration et effets fonctionnels

Original: `f1dmg/originals/f1dmg.free.fr/CMD-Roaming.doc` (13 824 octets).

F1DMG donne un exemple de configuration: `GPS ON`, `GPS Roaming ON`, zone de roaming preselectionnee, `Auto Roaming ON`, `Fixed Time Set 2`, `Repeater Check ON`, `Intervals Set 50`, `Reconnections 2`, `Outrange KIND`, `Effect Wait 2`. Il signale que l'option GPS Roaming peut faire passer l'affichage en VFO A seul, avec restauration du double affichage A/B lorsque l'option est desactivee. Les **unites**, formats internes et compatibilites de ces nombres ne sont pas justifies dans le document.

**Apport:** modele des interactions d'etat GPS/Roaming/VFO, utile a la documentation de l'interface OEM. Ne pas prendre cet exemple d'un operateur comme un parametrage par defaut de tous les appareils.

### Messages SMS DMR

Original: `f1dmg/originals/f1dmg.free.fr/Cmd-SMS-Anytone-2c.pdf` (558 763 octets, cinq pages dont le contenu est principalement image). La premiere page mentionne les options `SMS Confirmation`, `TX Allow = Always`, `DMR Mode = Repeater`, ainsi que plusieurs fonctions a desactiver selon la configuration de test et des commandes de configuration BrandMeister de l'epoque. Le document `SMS-d878.pdf` (3 pages) est egalement present.

**Apport:** tests des options CPS / commandes utilisateur, distincts des primitives du protocole USB CPS et du transport des trames SMS par le SCT3258. Les valeurs de serveurs et TG de 2022 sont des donnees historiques non garanties actuelles.

### Exemple de programmation des touches

Original: `f1dmg/originals/f1dmg.free.fr/TouchesD578.pdf` (1 010 068 octets, une page majoritairement graphique, date manuscrite 2022).

F1DMG y renseigne ses **propres** affectations des touches P1-P6, des touches PA-PD du microphone, de l'appui long et de la selection de canal. Il distingue visuellement les commandes de la facade et celles du microphone. Ceci constitue un exemple d'ergonomie et de representation de CPS, **pas** une table GPIO. Les affectations peuvent etre personnalisees.

## Photographies archivees avec valeur documentaire

- `D578-PROTECTION-ROS.png` : **photographie d'une zone de PCB et de points de soudure** rattachee a la protection ROS. Ce n'est pas une mesure de seuil ou un schema certifie.
- `DEBRID_578.jpg` : illustration de configuration logicielle des bandes; ne demontre pas la couverture RF physique.
- `578a.jpg` : photo de l'ajout d'un **deflecteur de ventilateur**; `578b.jpg` : grille et ventilateur du poste. Ce sont les images pertinentes pour la modification de refroidissement evoquee par F1DMG.
- `page-20/01Mb.jpg`, `page-20/02Mb.jpg`, `page-20/03Mb.jpg` : composants et modification de microphone avec jack/interrupteur; ne pas confondre avec le microphone OEM ni BT01.
- `page-20/boutons3.jpg` : modification visuelle des boutons et de la facade.
- `RAZ-ANYTONE.png` : proposition de raccordement RESET au GD32 explicitement **non essayee** par son auteur; a conserver comme hypothese et non comme pinout valide.
- `ROAMING.png` : illustration de l'interface utilisateur CPS, a attribuer a sa revision.

La [fiche des observations pratiques F1DMG](F1DMG_RELEVES_PRATIQUES.md) distingue les details de ces images et les hypotheses non testees. Les originaux restent dans l'archive privee.

## Ressources volontairement non publiees

Les CSV volumineux de listes de contacts sont conserves par F1DMG. Ils peuvent etre anciens, inclure des identifiants individuels, et ne representent pas un format binaire NAND. Les fichiers de codeplug `.rdt`, firmware, HPT et les archives ZIP/RAR correspondantes n'ont pas ete captures par le script utilise. Voir [reprises a effectuer](RECUPERATION_ET_PRIORITES.md).
