# Banc Web OpenD578 0.15.1

Ouvrir depuis le site GitHub Pages : /simulator/. Pour travailler localement, servir la racine avec `python3 -m http.server 8000 --bind 127.0.0.1`, puis ouvrir /browser-bench/.

Le moteur ARM WebAssembly et ses sources sont fournis. Charger les sauvegardes demandées par le guide intégré ; les données restent dans le navigateur. L’écran affiche les pixels produits par le firmware chargé. Le DMR reste différé.

Cette intégration reprend le correctif des couleurs BGR et les optimisations vérifiées de journalisation MMIO et d’ADC. Les mesures disponibles montrent environ 1,10× sur une exécution OEM bornée et 3,31× sur le microbenchmark ADC ; cela ne résout pas à lui seul la lenteur signalée et ne prouve pas le temps réel.

La suite logicielle intégrée compte 117 tests. La chaîne PCM complète, le ROS physique et la réception APRS analogique via BHT restent ouverts. Voir LIMITES.md, le guide dans index.html et docs/ETAT_CONFIRME_20261109.md à la racine du dépôt. Les essais de routines isolées ne remplacent pas une validation complète sur poste.

## Complément audio PC0

120 tests logiciels réussis après ajout de la source WAV PCM16 vers ADC10. Elle passe par l’ADC/DMA du programme ; il s’agit de l’acquisition de signalisation RX, pas du microphone ni d’un transport voix FM complet. Les acquisitions sont exportables. Les contrats C audio sont intégrés dans firmware/hal/audio_control.c et comparés sur 62 402 cas OEM isolés sans différence. Voir docs/peripherals/08_AUDIO_FM_TRANSPORT_ET_VALIDATION.md.
