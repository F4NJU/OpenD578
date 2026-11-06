# Espace de developpement des firmwares alternatifs

La nouvelle arborescence `firmware/` est reservee au developpement autonome. **Aucun binaire installable ou flashable n'est livre** par le site initial.

## Proposition minimale

- `firmware/hal/` : GPIO/ADC, LCD, NAND en lecture, UART microphone/GPS, audio et RF, pilotes bases sur les registres, pas sur la RAM constructeur.
- `firmware/app/` : demarrage, VFO, memoires, interface LCD, FM et CTCSS, GPS et APRS TX, gestion des erreurs.
- `firmware/tests/` : tests du banc hors ligne, traces de simulation, assertions sur les tailles et les registres, validation sans TX physique.

**Premier objectif fonctionnel :** interface VFO et canaux FM, RX/TX analogique et CTCSS, sauvegarde des memoires avec protection des etalonnages et APRS TX. **Ensuite :** APRS RX et DMR. Le mode satellite utilisant les canaux `SAT:` peut etre conserve comme extension additive si les ressources RF/UI sont qualifiees.

Les peripheriques externes **Bluetooth ET12, BT01 et BP-02** sont traites dans [le plan de pilotes Bluetooth](BLUETOOTH_PILOTES_BT01_PTT.md). Une couche UART et un automate PTT fail-safe sont proposes ; aucun transport BT complet ni cartographie de GPIO physique n'est affirme.

Le banc `bench/run_hardware.py` permet deja de tester une application ARM distincte sans hook vers le firmware OEM. Les limites de simulation ne valent pas validation sur poste. Consulter [README](../../README.md), [roadmap](../ROADMAP.md), [emulateur](../EMULATOR.md), [zones memoire](../02_CPU_FLASH_BOOT_USB_SWD.md) et [strategie satellite](../05_SATELLITE_CODE_INTEGRATION_EXP06.md).

## Sous-système RF expérimental QA4818N

Le code `firmware/rf/qa4818n_frequency.[ch]` construit une paire `0x29/0x2A` selon le format candidat AT1846S. `qa4818n_transport.[ch]` transmet seulement à un backend de test injecté, par défaut désactivé. Le décodage des transactions OEM est dans `tools/qa4818n_trace.py`. Rien n'est prêt pour piloter les quatre boîtiers physiques, ni pour émettre.

[Monographie RF et protocole](../hardware/QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md).
