# Bluetooth : variantes D578 PRO/PLUS et piste de compatibilite D878

| Point | D578 PRO GD32 | D578 PLUS GD32 | D878 / D878UVII |
| --- | --- | --- | --- |
| MCU principal | GD32F303VKT6 observe | **GD32F303 observe sur le poste utilisateur** (suffixe exact du boitier a inscrire sur photo) | Autre revision GD32F303, ressources et firmware distincts |
| Bluetooth radio | Present selon manuel et observation | Present selon manuel ; support physique exact a attribuer | Modules historiques a base BK3260 sur certains D878 ; carte BT/APRS remaniee sur UVII |
| Marquage `D868BT-SP` | Releve sur carte Bluetooth du poste sans attribution ferme de variante | Meme remarque ; **ne pas supposer le meme PCB des deux D578** | Similarite de nom : piste, sans nomenclature pin-to-pin publiee |
| Module sous blindage | Petit PCB soude sur carte support ; SoC illisible | A confirmer pour cette carte par photo | L'identite du SoC du D578 **ne se deduit pas** du D878 |
| Firmware de module | Famille ET12, version connue V10043, commandes AT partielles du banc PRO | Famille ET12 documentee par AnyTone, version locale a relever | Variantes selon generation et module |
| Microphone BT01 | Compatible, appairage et mode distant | Compatible, appairage et mode distant | Non equivalent au micro controleur du D878 |
| PTT BP-02 | Compatible via poste | Compatible via poste | Similarite de fonction, trames non prouvees identiques |
| Carte APRS supplementaire | Non demontree sur PRO | Carte BT/APRS possible selon revision PLUS, *differente* de la carte RF AM | D878UVII : carte BT/APRS selon documentation de reverse engineering |
| Carte RF airband KT09?5R | Connecteur absent selon observation | Carte RF AM supplementaire ; independante du BT | Sans correspondance presumee |
| Firmware GD32 principal | Image propre au PRO V1.21 | **Firmware PLUS propre a sa variante**, ne pas reutiliser la V1.21 PRO sans analyse | Binaire D878 different |

L'association du support **D868BT-SP** a la famille D878 est *plausible* mais necessite la comparaison des references PCB, padout, connecteur, antenne, pistes et materiels sous blindage. Elle **ne prouve aucune compatibilite de firmware Bluetooth** et ne justifie aucune mise a jour croisee.

### Actions de confirmation rapides

1. Photo macro nette des deux faces D868BT-SP dans chaque variante et de son raccordement a la carte afficheur.
2. Photo du PCB Bluetooth soude sous blindage : taille, nombre de pads et antenne. Une ouverture du shield n'est pas requise pour documenter les connexions externes.
3. Capturer les versions exactes `Device Info` / BT / BT01 / APRS sans appliquer de mise a jour.
4. Relever si la carte `D868BT-SP` comporte aussi le circuit de reception APRS, en distinguant les traces et le connecteur de la carte AM aeronautique.

### References

- AnyTone, guide BT01 : <https://support.bridgecomsystems.com/hubfs/Tech%20%28AnyTone%29/BT01_user_manual_221121.pdf>
- RadioFoundry, architecture famille AnyTone : <https://radiofoundry.org/docs/spec/hardware-anytone>
- VK7ZJA, comparaison D868/D878 : <https://radio.carstenbauer.net/878techmods.htm>
- VK7ZJA, D578 cartes internes : <https://radio.carstenbauer.net/578techmods.htm>
- FCC D578 : <https://fccid.io/T4K-D578UV/Internal-Photos/Internal-Photos-4513168>
