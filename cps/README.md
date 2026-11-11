# CPS OpenD578 : cœur hors ligne

Première livraison : modèle TypeScript, validation, JSON versionné, conversion
MHz/Hz exacte et validation contre des capacités fournies par un adaptateur.
L'interface web, le CSV, le faux poste et les transports restent à développer.
Ce code ne dialogue avec aucun poste et n'écrit aucune mémoire radio.

## Vérification

Node.js 24 ou ultérieur, aucune dépendance à installer :

```powershell
cd cps
npm test
```

Node exécute ici le TypeScript par suppression des annotations. Cela ne remplace
pas une vérification statique par `tsc`, à ajouter avec l'outillage de l'éditeur.

## Utilisation

```typescript
import { parseCodeplug, serializeCodeplug } from './src/core/json.ts';
import { validateForDevice } from './src/core/capabilities.ts';

const codeplug = parseCodeplug(jsonText);
const savedText = serializeCodeplug(codeplug);
// Avant un futur transfert : capacités validées par l'adaptateur obligatoire.
const issues = validateForDevice(codeplug, deviceCapabilities);
```

`validateCodeplug` accepte une entrée inconnue et retourne des erreurs structurées
`{path, code, message}`. `parseCodeplug` et `serializeCodeplug` lèvent une
`CodeplugValidationError` si nécessaire. Aucune correction ni suppression de
champ n'est automatique. Les imports retournent de nouveaux objets.

Les capacités de test et le fichier d'exemple sont synthétiques. Ils ne sont pas
une description des capacités AT-D578 ou une configuration de relais local.

Contrat partagé : `../docs/cps/OPEND578_CPS_CONTRACT.md`.

## Développement

Le cœur est indépendant du banc et du firmware. Les évolutions sont préparées
sur une branche dédiée du fork avant proposition au dépôt amont.
Le contrat PC est implémenté ; les décisions firmware et protocole restent à
convenir avec F4EGM avant l'intégration à l'émulateur.
