# RDA5802N : radio FM de radiodiffusion, interface GD32 et pilote autonome

**Cible :** D578UV PRO GD32 V1.21. **Identification :** composant marqué RDA5802N observé sur la carte, compatible avec la nomenclature indépendante de VK7ZJA. **Liaison exacte :** identifiée uniquement au niveau du modèle logiciel, pas par continuité électrique.

## 1. Fonction et variantes de boîtier

Le RDA5802N est un tuner FM de radiodiffusion (et non le récepteur VHF/UHF principal des communications radioamateur). Il contient la synthèse, une réception numérique basse FI, la stéréo, l'AGC, le RDS/RBDS, la détection de niveau, la recherche de stations et un traitement audio. La documentation RDA distingue `RDA5802N` QFN 24 contacts 4×4 mm, `RDA5802NS` QFN 20 contacts 3×3 mm et `RDA5802NM` QFN 12 contacts 2×2 mm. **Ne pas prendre le brochage de NS ou NM pour celui de N.** La fiche RDA mentionne la plage possible 50–115 MHz selon configuration de la famille, sans garantir les limites ou l'antenne réellement utilisées dans le D578.

La référence externe et la sortie audio peuvent être analogiques, et la famille annonce une interface audio numérique I²S. **Le trajet choisi sur la carte D578 est encore inconnu** : il faut suivre les pistes, résistances, condensateurs et sélecteurs jusqu'au codec et aux amplificateurs.

## 2. Ce que contient réellement le code public OpenD578

Source : `bench/fm_i2c.py`, classe `FmI2c`. Ce décodeur est **un modèle de protocole RDA5807 compatible**, pas un pilote RDA5802N certifié. Il reconstruit les transitions GPIO suivantes :

| Signaux surveillés par le banc | Origine | Niveau de preuve |
| --- | --- | --- |
| PB6 = SDA | Ports GPIO décodés par le banc | Simulation/firmware, continuité vers RDA non mesurée |
| PB7 = SCL | Ports GPIO décodés par le banc | Simulation/firmware, continuité non mesurée |
| Adresse I²C 7 bits `0x10` (octet écriture `0x20`) | Modèle RDA5807 compatible | Réponse ACK **émulée**, et non réponse matérielle |
| Écritures séquentielles à partir du registre `0x02` | Classe `FmI2c` | Décodage du modèle uniquement |
| Statut / lecture RSSI / RDS | Non implémentés | **Aucune lecture matérielle qualifiée** |

Le système doit enregistrer les octets réellement émis pendant l'activation de la fonction FM, la recherche de station, le réglage du volume et la désactivation. Le seul fait que le simulateur reconnaisse `0x10` ne prouve pas que le RDA5802N du poste est raccordé aux broches PB6 et PB7.

## 3. Séquence de reconstruction du pilote

1. Identifier le **boîtier** et le sens de la broche 1 sur photo, puis contrôler alimentation, découplage, quartz/référence et sorties audio hors tension.
2. Sur le poste allumé, mesurer passivement la fréquence et l'amplitude de SCL et SDA au plus près du tuner, sans déconnecter les résistances de tirage.
3. Comparer la capture logique aux transitions PB6/PB7 et consigner **adresse 7 bits / sens R-W / octets / ACK réels**.
4. Relever, sans écriture hors procédure, une activation, un changement de fréquence, la fonction seek, une modification du volume et la mise en veille.
5. Chercher dans le binaire V1.21 les appels et constantes associés à chaque paquet ; enregistrer l'adresse de routine, les arguments, l'ordre des écritures et le comportement d'erreur.
6. Reconstituer les registres avec **la révision précise de la datasheet RDA5802N**. Les tables RDA5807 ou RDA5802E ne sont pas une preuve de stricte compatibilité.
7. Implémenter `init`, `tune`, `seek`, `mute`, `volume`, `read_status`, `standby` et `reset` dans une HAL indépendante des adresses RAM OEM, puis tester la ligne de retour et les temporisations.

**Piège :** `ACK` du modèle logiciel ≠ `ACK` capturé sur circuit. Ne pas donner à un firmware alternatif des bits de commande copiés d'un autre tuner avant de vérifier leur effet.

## 4. Structure minimale pour un futur pilote

```c
struct rda5802_bus {
    int (*start)(void *ctx);
    int (*write)(void *ctx, unsigned char byte);
    int (*read)(void *ctx, unsigned char *byte, int ack);
    int (*stop)(void *ctx);
    void *ctx;
};

/* La couche basse doit être validée avant d'ajouter les tables de registres. */
int rda5802_probe_passive(struct rda5802_bus *bus);
int rda5802_write_verified(struct rda5802_bus *bus,
                           unsigned char addr7,
                           const unsigned char *data, unsigned count);
```

Ces prototypes sont des **interfaces à implémenter**, pas des fonctions testées sur le poste. Les en-têtes ne prescrivent aucune écriture initiale dans des registres inconnus.

## 5. Inconnues prioritaires

- Brochage exact QFN du composant monté et masse de référence des sondes.
- Rail 3,3 V ou autre tension réellement mesurée ; quartz et couplage RF antenne.
- Confirmation électrique PB6/PB7, présence d'autres circuits sur le bus, pull-ups.
- Rôle de la sortie audio dans la chaîne U2429 / TLV320 / amplificateurs.
- Emplacement de la configuration FM et de ses paramètres dans NAND ou Flash, si elle est persistante.
- Registres réellement employés et éventuelle réception RDS par le firmware V1.21.

## Références

- Documentation technique RDA Microelectronics, gamme RDA5802N (archives) : <https://static6.arrow.com/aropdfconversion/a8f661f9a3450ae778e55dd846bcc2cdbcb43c52/pgurl_detail_186.aspx.pdf>
- Inventaire D578, VK7ZJA : <https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php>
- Code à vérifier : `bench/fm_i2c.py`, `docs/04_RAM_ROUTINES_UI_RF_ET_BROCHAGE.md`.
