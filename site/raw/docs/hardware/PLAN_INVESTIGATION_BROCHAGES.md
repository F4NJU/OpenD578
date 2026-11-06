# Plan de mesures pour terminer le reverse engineering matériel

**But :** transformer les liens `unknown` / `hypothesis` du modèle OpenD578 en liaisons mesurées, avec une fiche de traçabilité. Ces étapes évitent d'écrire sur le matériel ou de forcer des GPIO sans connaître leur rôle.

## Ordre de priorité

| Priorité | Cible | Pourquoi | Preuve de sortie attendue |
| --- | --- | --- | --- |
| 1 | RDA5802N | Bus déjà représenté dans le banc (`PB6/PB7`) | Adresse, ACK réel, trames, pinout, audio |
| 2 | QA4818N ×4 / 26 MHz | Les contrôles RF conditionnent VFO, RX et satellite | Table banque SPI → boîtier → rôle A/B |
| 3 | U2429G et PA1517/YD1517 | Savoir comment les volumes et coupures atteignent le HP | Schéma de chaîne audio, M/SS, GPIO |
| 4 | BH2226 / SGM8272 | Risque d'être le circuit de pilotage d'accord RF, à vérifier | Affectation des huit sorties CNA et amplis |
| 5 | GPS / DMR / codec | Protocole, resets, horloges et chargement firmware | Échanges complets + mémoire de configuration |
| 6 | PA AFT05MP075N / L7805CV | Étagement, protection TX et rails | Arbre alimentation, PA séparés, sécurités |
| 7 | Carte PLUS airband | Uniquement si une carte PLUS est disponible | ID CI exact, connecteur, bus et AM RX |
| 8 | D868BT-SP / ET12 / BT01 / BP-02 | UART3 du banc connu, protocole radio et audio non mesures | Pinout et alim du support, capture AT, trames PTT et mode BT01 |

## Fiche de relevé à joindre à chaque connexion

```yaml
board: D578UV_PRO_GD32_V121
revision_pcb: a_relever
component_from: exemple_U_QA3
pin_from: inconnu
component_to: GD32F303
pin_to: inconnu
signal_name: hypothese
method: continuity_off_power | passive_capture | oem_trace | datasheet
instrument: modele_et_reglage
voltage_off_on: a_relever
frequency_or_timing: a_relever
capture_file: chemin_dans_repo
conclusion: inconnu
confidence: unknown
operator_date: YYYY-MM-DD
```

**Méthode recommandée :** photographie d'ensemble → gros plan et localisation broche 1 → continuité **poste hors tension et déchargé** → lecture passive d'un scénario de réception normal → mise en correspondance avec désassemblage OEM → fiche composant et lien mis à jour.

Le support Bluetooth D868BT-SP et son module blinde doivent etre photographies des deux faces sans demontage destructif. Capturer l'UART en ecoute haute impedance et distinguer la liaison sans fil BP-02 de l'audio BT01. Ne pas commander le PTT durant la qualification des bus : un faux etat active peut provoquer un TX non souhaite.

Les sondes de fréquence/oscillateur à 26 MHz peuvent modifier le fonctionnement d'un quartz. Utiliser une méthode de mesure faible capacité ou observer un signal tamponné. Éviter toute injection, écriture NAND, programmation OEM, alimentation externe des GPIO et **tout essai d'émission PA sans charge et protection RF adaptées**.

## Corrections du modèle

Dans `hardware/models/`, ajouter une preuve `physical` **seulement** si le brochage est mesuré. Employer `oem_trace` pour les GPIO déduits des instructions natives, `emulator` pour les bus uniquement reproduits par le banc, `datasheet` pour un comportement propre au circuit mais pas à la carte, `hypothesis` pour un lien supposé et `unknown` si le lien n'est pas qualifié.

Les adresses de routine `0x080...` sont des informations V1.21 et ne doivent **pas** conditionner les pilotes HAL de remplacement.
