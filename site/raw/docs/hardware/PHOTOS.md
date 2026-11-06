# Photographies et vues de cartes

La vue initiale est **une carte logique eclatee**, non un plan d'implantation mesure. Le support photo accepte les faces de PCB et les zones cliquables, mais aucun emplacement ni piste n'a ete invente en l'absence de photographie calibree de la carte GD32 V1.21.

## References photographiques publiques

- [FCC T4K-D578UV, photographies internes](https://fccid.io/T4K-D578UV/Internal-Photos/Internal-Photos-4513250)
- [FCC T4K-D578UVIII, dossier](https://fccid.io/T4K-D578UVIII/)
- [D578 : vues de la carte de facade et du GPS](https://radio.carstenbauer.net/578techmods.htm)

Les vues FCC des premiers modeles ne doivent pas etre considerees comme un plan de la revision GD32 sans confrontation aux inscriptions des PCB. Les photos externes sont liees, pas republiees dans cette archive sans verification des droits de reproduction.

## Ajouter une photo sur le site

1. Deposer l'image dont on dispose des droits dans `hardware/photos/d578uv-pro-gd32-v121/`.
2. La photo apparait automatiquement dans l'onglet Photos. Pour ajouter des zones cliquables, ajouter un objet a `hardware/photos/d578uv-pro-gd32-v121/manifest.json` avec `file`, `title`, `side`, `source`, `note`.
3. Ajouter des `hotspots` en coordonnees pourcentage `{node, x, y, w, h}` apres verification sur image.
4. Pousser le commit sur GitHub. Le site reconstruit et presente la photo et ses zones cliquables automatiquement.

L'interface de clic renvoie aux memes fiches composant que la vue eclatee. L'image et les zones cliquables sont maintenues dans le meme depot.
