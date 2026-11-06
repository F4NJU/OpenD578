# Changelog de consolidation : site et protocole CPS, 05/11/2026

## Sources réellement réunies

- Base du dépôt et documentation du site GitHub Pages antérieur : sources publiques V11.2, notices et relevés mis à jour.
- **Fusion du paquet public OpenD578 V11.7** : scripts de banc plus récents, hôte USB CDC, pont COM/PTY, CPS intégré, catalogues de 117 exigences, outils d'audit et rapports publics de validation.
- Documents récents conservés : LCD V11.8, boutons/GPIO/éclairages, microphone V11.8, composants RF, audio, Bluetooth D868BT-SP, BT01 et PTT BP-02.
- Deux variantes matérielles : D578UV PRO GD32 V1.21 et D578UV PLUS GD32 avec carte airband additionnelle.
- Documents CPS distincts : architecture USB, commandes et trames OEM, canal de 64 octets, compatibilité PRO/PLUS, essais et sources externes.
- **Outil de lecture passive** `tools/cps_trace_audit.py`, avec tests synthétiques et aucune commande vers le poste.
- Onglet CPS/USB dans le site statique ; nouveaux blocs PC/CPS et USB dans l'explorateur.

## Limites et état des sources

Les notices du banc **V11.8** décrivent des améliorations du microphone et du LCD, mais **les sources V11.8 complètes ne font pas partie des matériaux publics récupérés**. La base logiciel de banc assemblée ici est la V11.7. Aucune fonction introduite uniquement en V11.8 n'est annoncée comme testée dans le code V11.7.

Le firmware constructeur PRO V1.21 a été exécuté en simulation dans les campagnes référencées, et certains échanges CPS ont été observés. Ces observations n'autorisent ni une écriture sur le poste réel ni une annonce de compatibilité CPS Windows exhaustive.

Les mesures de connexion physique (GPIO, montage, oscillateur, quartz et interconnexions des circuits grattés) restent à effectuer. Les circuits QA4818N et KT09xx non marqués restent candidats lorsque leur identification n'est pas certaine.

## Validation avant publication

Les tests ciblés du site, de la cartographie matérielle, du mini-CPS JavaScript, du décodeur CPS et de l'audit Bluetooth sont déclarés dans le dossier d'attestation livré à la racine. Les tests matériels, les exécutables Windows, les campagnes sur l'OEM V1.21 ou sur le PRO/PLUS physique ne sont pas rejoués par cette construction de site.
