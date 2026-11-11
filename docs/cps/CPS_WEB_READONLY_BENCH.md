# CPS web et banc Python : première liaison en lecture seule

Cette livraison réutilise le banc Python V11.7 et son hôte USB CDC. Elle ne crée
aucun faux poste, aucune réponse de firmware et aucun accès direct à la NAND.
Le nouveau panneau est une inspection OEM distincte du codeplug éditable.

## Préparation

Utiliser une copie locale complète de la branche `feature/cps-core` du fork
F4NJU/OpenD578, avec les entrées privées déjà nécessaires au banc. Le dépôt
public et le fichier HTML autonome ne contiennent aucune image OEM.

Depuis la racine, compiler le CPS avec Node.js 24 ou ultérieur :

```sh
cd cps
npm run build
```

Lancer ensuite le banc Python comme d'habitude avec `bench/OUVRIR_BANC_WEB.cmd`
(Windows) ou son équivalent existant. Démarrer le moteur **OEM V1.21**, attendre
son démarrage et fermer les autres clients : CPS intégré, pont COM/PTY, sondes.
Le firmware autonome RX FM alpha ne possède pas encore de gestionnaire CPS.

Ouvrir **l'adresse exacte affichée par le banc**, suivie de `/cps/` : par exemple
`http://127.0.0.1:8765/cps/`. Le port peut être différent. Éviter de remplacer
127.0.0.1 par localhost : le banc vérifie l'origine exacte des requêtes POST.
Le bouton **Banc émulé** du fichier autonome propose aussi d'ouvrir cette page.
Le stockage de session de cette page et celui du fichier autonome sont distincts.

## Parcours

1. Cliquer **Banc émulé** dans le CPS servi par le banc.
2. Choisir 1–32, 33–64, 65–96 ou 97–128.
3. Cliquer **Identifier et lire**. La session fait PROGRAM, identité, 128
   lectures de 16 octets, puis END. Les réponses viennent du firmware exécuté.
4. Examiner les noms, RX/TX, modes et niveaux de puissance partiellement décodés.
5. Exporter éventuellement l'instantané d'inspection JSON.
6. **Redémarrer le moteur** avant toute nouvelle lecture. L'annulation ou un
   résultat ambigu impose aussi cette reprise ; aucune commande n'est rejouée.

La page complète et l'ACK de END sont nécessaires pour valider un instantané.
Un instantané antérieur reste horodaté et ne représente pas l'état courant du
poste. Un changement de moteur/session interrompt la lecture. Interrompre annule
les requêtes locales ; une commande déjà acceptée peut encore être exécutée.
Ce bouton ne commande pas l'arrêt du moteur.

## Portée du décodage

- Le modèle déclaré doit commencer par `I D578UV NUL` et finir par ACK. Les octets
  de version ne sont pas interprétés : cette identité ne certifie pas la V1.21
  ni la compatibilité PRO/PLUS. Le profil de lecture reste celui de la V1.21.
- Les lectures sont bornées à `0x00800000`–`0x00801FFF` : 128 emplacements de
  64 octets, en quatre pages de 2048 octets. Toute autre adresse est refusée.
- RX et décalage TX sont décodés en BCD, en unités de 10 Hz. BCD invalide,
  fréquence nulle ou décalage réservé produisent une valeur inconnue.
- Les noms sont interprétés uniquement s'ils sont ASCII imprimables. Les modes
  et puissances suivent le décodage partiel de `mini_cps_protocol.js`.
- Bitmap d'activité, tons, largeur FM, interdiction TX et zones non interprétés.
  Un emplacement affiché n'est pas un canal actif certifié.
- L'instantané `opend578-oem-readonly-v1` n'est pas un codeplug OpenD578 et n'est
  pas importé dans l'éditeur. Aucun champ manquant n'est inventé.

## Transport et protections

`bench/web_server.py` sert les fichiers compilés sous `/cps/`, via
`bench/cps_assets.py`. Les contrôles de jeton `X-Lab-Token` et d'origine sont
conservés ; aucune règle CORS ni écoute réseau étendue n'est ajoutée.
Le simulateur GitHub Pages ne fournit pas cette API Python.

Le client HTTP autorise configuration, état CDC, démarrage de l'hôte USB et
octets PROGRAM, identité, R borné et END. Aucune commande W, TX, mise à jour ou
calibration n'est émise. Cela ne prouve pas que le firmware ne réalise aucune
écriture interne de sa propre initiative. Aucun jeton ni flux brut n'est journalisé.

Le banc ne verrouille pas les différents clients USB entre eux. Le CPS refuse
une file occupée et détecte les octets inattendus, mais ne remplace pas cette
exclusivité. Fermer les autres clients est requis.

## Vérification et limites

```sh
cd cps
npm test
npm run build
npm run build:standalone
cd ..
python -m unittest discover -s bench -p test_cps_assets.py -v
```

Les fixtures vérifient le client hôte, pas un firmware : fragmentation, checksum,
identité, moteur/session, débordement, bornes, annulation et absence de W.
Les tests Python vérifient le confinement des fichiers et le build absent.

Le firmware OEM, ses entrées privées et le navigateur du banc n'ont pas été
exécutés ici. Le test d'intégration reste à faire sur la machine disposant du
banc et de ses captures : comparer les noms/fréquences au CPS intégré, vérifier
la reprise après END et l'absence de modification attribuable au client avec
les traces et empreintes du banc.
