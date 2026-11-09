# Audio FM : commandes intégrées et transport PCM de test

Jean-Philippe (F4EGM) — 9 novembre 2026.

## Ce qui est désormais intégré

Les fonctions C audio auparavant présentes dans le paquet de recherche mais absentes du dépôt intégré sont ajoutées dans `firmware/hal/audio_control.c` et `.h`, avec `firmware/tests/test_audio_control.c`. Elles couvrent les coupures HP poste/micro, les commandes MAIN/SUB et leurs portes contextuelles, le micro FM standard, la quantification et les codes de volume. Le callback de transport arrête le plan à la première erreur et indique le préfixe réellement appliqué.

La comparaison avec les routines OEM V1.21 a été réexécutée : **62 402 cas, aucune différence**. Les fixtures sont des paramètres de tests isolés, jamais des états injectés dans le banc. Le firmware d’origine est contrôlé par son SHA-256. Script reproductible :

```bash
python3 tools/compare_oem_audio.py /chemin/full_flash_pass1.bin resultat.json
```

Il nécessite Python Unicorn et `cc`. Les sources C n’appellent pas l’OEM et ne dépendent pas d’adresses SRAM fixes. Le résultat est conservé dans [differential.json](../evidence/audio_20261109/differential.json).

## Nouvelle entrée audio effective sur PC0

La rubrique Audio de réception PC0 du simulateur charge un **WAV PCM16 mono ou stéréo**, de 8 à 192 kHz et de 12 secondes maximum. Elle produit un stimulus d’entrée ADC10 variant dans le temps. Le traitement suit le chemin :

**WAV → codes d’entrée PC0 → ADC0 canal 10 → DMA configuré par le programme → SRAM → traitement du programme chargé.**

Le banc n’écrit pas directement un buffer audio du firmware. Le programme garde la sélection des rangs ADC, le lancement des conversions, le descripteur DMA et sa destination. Si ADC10 n’est pas acquis, aucun résultat n’apparaît artificiellement dans sa RAM. Une source n’attend pas que l’ADC soit prêt et les échantillons perdus ne sont pas rejoués.

Pour une source stéréo, le mélange mono précède la conversion. La transformation est explicite :

`code = arrondi(polarisation + amplitude × moyenne_PCM16 / 32768)`.

Les valeurs par défaut 2048 et 1024 sont des **paramètres de scénario**, pas des mesures du poste, de son VREF ou d’un conditionnement analogique. Les valeurs hors plage sont refusées. En fin de fichier, la source reprend la polarisation choisie. Déconnecter la source ou effectuer un reset manuel efface aussi sa capture ; exporter les acquisitions auparavant. Un reset système/watchdog conservant le temps et les périphériques externes conserve la source.

Le calendrier reprend les unités virtuelles existantes : 120 millions d’unités par seconde et 64 unités par conversion dans le modèle ADC. Ce n’est pas une validation des horloges ADC ou de la fidélité en fréquence d’un signal sur le poste réel. L’export JSON contient les instants virtuels et codes réellement convertis ; la capture est bornée à 8192 entrées, avec indicateur de troncature.

**PC0 est une acquisition audio RX utilisée par les décodeurs de signalisation. Ce n’est ni l’entrée du microphone filaire, ni une preuve que la voix FM principale passe par le GD32.** Les potentiomètres et les touches ne sont pas réaffectés pour fabriquer une entrée audio. Une écriture statique ADC10 est refusée tant que cette source est active.

## Ce que montrent les captures FM existantes

La reprise de Both RX A, TX VHF Level 4, TX VHF Level 5 et TX UHF Level 5 donne dans chacun des fichiers les mêmes 43 demandes MCU→SCT, avec le même condensat de flux. Les captures indiquent `harness_OEM_state_writes=false`. Les niveaux micro FM et les calibrations VHF/UHF changent via les commandes RF décrites dans le [contrat audio V0.13](AUDIO_LIAISONS_LOGIQUES_OEM_V013.md), sans changement correspondant de ce flux SCT enregistré.

Cela établit une commande RF distincte pour ces transitions. **Cela ne démontre ni absence générale du SCT dans tous les modes FM, ni passage de la voix FM dans une interface PCM du GD32.** Le SCT reçoit aussi des commandes de filtres et de codec au démarrage. La documentation de l’interface CT3258 décrit des fonctions d’appel analogique ; leur existence n’attribue pas automatiquement ces routes au D578.

Voir [capture_recheck.json](../evidence/audio_20261109/capture_recheck.json) : fichiers sources, empreintes, temps virtuels, compte et condensat des commandes. Ces relevés historiques ne sont pas présentés comme une nouvelle exécution complète de l’OEM.

## Périmètre des vérifications

- Nouvelle entrée WAV : conversion PCM16, mélange stéréo, refus des fichiers tronqués et formats incompatibles, bornes et remplacement atomique.
- Source : cadence sans file de rattrapage, fin de fichier, limite mémoire de capture.
- Moteur ARM WebAssembly réel : le programme de test configure une séquence de sept canaux et un DMA ; ADC10 apparaît au bon demi-mot en SRAM, les autres canaux conservent leurs valeurs. Ce programme indépendant n’est pas un firmware OEM modifié.
- Ensemble du banc : **120 tests logiciels réussis**. Test C des contrats audio compilé avec `-Wall -Wextra -Werror -pedantic`, réussi.
- Référence OEM : **62 402 comparaisons de routines isolées**, zéro différence.

## Chaîne encore à fermer

| Segment | Acquis | Travail restant |
|---|---|---|
| Entrée audio PC0 vers GD32 | Stimulus PCM, conversions ADC et DMA effectifs | Décodeurs OEM et cadence matérielle à qualifier sur de nouveaux scénarios |
| Volumes | Commandes U2429 et fonction d’atténuation nominale | Attribution de toutes les sources et sorties physiques dans les commutations |
| Micro FM | Sélecteur RF et code MIC usine, ordre des écritures, C indépendant | Transfert réel de ces codes en gain/déviation dans le modèle RF |
| Codec / SCT | Demandes, champs de gain, coefficients EQ et fonction nominale | Chemin effectif des échantillons, état DSP, saturation et transitions |
| HP poste, micro et externe | Coupures logiques poste/micro | Matrice audio effective et contacts de prises externes |

Il reste donc un obstacle concret à un son FM complet fidèle : les commandes sont établies, mais leur raccordement aux échantillons de la chaîne RF/codec et à toutes les sorties n’est pas entièrement déterminé. Aucun mixeur de convenance ni conversion arbitraire des codes usine en dB n’est ajouté pour masquer ce manque. Le DMR reste différé. La nouvelle entrée PC0 est exploitable pour poursuivre cette analyse, mais elle ne clôture pas ce critère de validation.
