# Runtime ARM WebAssembly du banc OpenD578

`unicorn_arm.js` contient le JavaScript d’initialisation et le WASM incorporé. Le banc n’a pas besoin de npm ou d’un CDN pour fonctionner.

Ce runtime est recompilé à partir d’Unicorn.js et d’Unicorn. Les références, l’empreinte et les correctifs sont dans `../../sources_runtime/`.

La sélection Cortex-M4 est relue avant tout mappage mémoire. La construction préserve le modèle demandé au lieu de le remplacer par Cortex-M33. Les blocs de traduction sont limités à 32 instructions et le tableau des temporaires WASM32 à 2 048 entrées, avec contrôle avant débordement. Ces paramètres concernent le traducteur ; ils ne remplacent aucune instruction du firmware.

Les sources correspondantes sont fournies dans l’archive source et les avis de licence sont conservés.

Amont : https://github.com/AlexAltea/unicorn.js
