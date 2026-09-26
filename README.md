# qtpy6web

*Run a [qtpy6](https://github.com/SmartAudioTools/qtpy6) (PyQt6) application in the browser, unchanged, on
[Pyodide-Qt](https://github.com/JarrettSJohnson/pyodide-with-pyqt6) — documentation in French below.*

Une application écrite avec **qtpy6** (l'API de PySide6, sur PyQt6) tourne **telle quelle dans le navigateur** : Qt 6 et
PyQt6 compilés en WebAssembly (Pyodide-Qt) dessinent la fenêtre dans un élément de la page, le code Python de
l'application n'est pas modifié. Ce paquet est ce qu'il lui faut autour : le chargeur de la page, la `QApplication` et ses
polices, les cibles au doigt, un Web Worker qui tient lieu de `QProcess`, le stockage du navigateur, l'assemblage de
l'archive et une sonde Firefox sans interface pour vérifier le tout sans écran ni clic.

```python
# mon_application.py : le même fichier en natif et dans le navigateur
from qtpy6.QtWidgets import QPushButton
from qtpy6web import application, navigateur

def demarrer():
    app = application(polices="polices", defaut=("Noto Sans", 10))  # les polices livrées : le navigateur n'en a aucune
    fenetre = QPushButton("Bonjour")
    fenetre.show_full_screen() if navigateur() else fenetre.show()
    return app

if __name__ == "__main__":
    demarrer().exec()
```

```html
<div id="qt" style="position:fixed; inset:0"></div>
<script type="module">
  import { preparer } from "./qtpy6web.js";
  const py = await preparer(document.getElementById("qt"), {
    indexURL: "./pyodide-qt/",                                        // Pyodide-Qt
    archives: [{ url: "./app.zip", dossier: "/home/pyodide/app" }],  // le code, qtpy6, qtpy6web, les polices
  });
  py.pyimport("mon_application").demarrer();
</script>
```

Extrait du lecteur d'épreuves de SmartTeacher (septembre 2026), où
un lecteur Qt de 2 000 lignes (tableaux, éditeur de code avec exécution, graphes à tracer, SVG) s'est mis à tourner dans
le navigateur sans qu'une ligne de son interface change.

## Installation

```bash
pip install qtpy6web            # qtpy6 est tiré ; PyQt6 n'est PAS nécessaire en natif si PySide6 est là
pip install qtpy6web[sonde]     # + selenium, pour la sonde (Firefox et geckodriver viennent du système)
```

Python ≥ 3.10. Le paquet n'embarque **pas** Pyodide-Qt : la page le charge depuis l'URL `indexURL` (à côté d'elle, ou sur
un hôte qui autorise CORS). La version épinglée est dans `qtpy6web/versions.json` (Pyodide-Qt 0.29.3 : Qt 6.10.2, PyQt6
6.10.2, Python 3.13 ; le Pyodide ordinaire du worker : 314.0.7, Python 3.14) ; `preparer` compare celle qu'il a chargée
et écrit une ligne d'avertissement au journal si elles diffèrent. Pyodide-Qt est publié sous GPL v3 (celle de PyQt6) :
toute page qui le sert distribue PyQt6, et le code de l'application servi avec doit en tenir compte. Ce paquet-ci est MIT
et ne contient aucun binaire.

**Installation éditable (développement)** : si le dépôt est rangé sous un dossier déjà présent sur `sys.path` (un `.pth`
qui met `~/Python` ou `/DATA/Python` sur le chemin), le dossier du dépôt lui-même devient un paquet-espace de noms
`qtpy6web` que Python trouve avant le finder éditable de setuptools : `import qtpy6web` réussit et le paquet est vide
(`__file__ is None`). Installer alors en mode compat, qui écrit un `.pth` classique :

```bash
pip install -e . --no-deps --no-build-isolation --config-settings editable_mode=compat
```

## Ce que fait le paquet

| Où | Quoi |
|---|---|
| `qtpy6web.navigateur()` | `True` sous Pyodide (`sys.platform == "emscripten"`) : l'interrupteur de tout le reste. Une fonction, pas une constante, pour rester forçable par un test. |
| `qtpy6web.application(polices=None, defaut=None)` | La `QApplication`, créée au besoin et rendue (idempotente). Sans session graphique (ni `DISPLAY` ni `WAYLAND_DISPLAY`) elle passe en `offscreen` : tests et exports tournent sans écran. Dans le navigateur, où Qt n'a **aucune** police système, les `.ttf`/`.otf` du dossier `polices` sont chargés et `defaut` (`QFont` ou `("Noto Sans", 10)`) devient la police de l'interface. Elle garde une référence à l'application : sous PyQt6, une `QApplication` dont la dernière référence Python disparaît est détruite, et toutes ses fenêtres avec. |
| `qtpy6web.police_fixe(secours="Liberation Mono")` | La police à chasse fixe du système ; dans le navigateur, `secours`, à livrer dans `polices`. |
| `qtpy6web.tactile` | `detecte()` : un doigt parmi les pointeurs du navigateur (`any-pointer: coarse`). `activer(app, cible=44)` : boutons, listes, champs, cases montent à la taille d'une cible au doigt par une feuille de style **ajoutée** à celle de l'application, à appeler avant de construire les widgets. `marge()` : l'espace à mettre autour d'un widget d'une ligne pour en faire une cible. `defiler_au_doigt(zone)` : une `QScrollArea` que le doigt fait défiler (`QScroller` ; sans lui, un glisser fait 0 px). |
| `qtpy6web.dispositions` | `Disposition`, `Rangee` : des dispositions qui se **replient** quand la place manque. `QHBoxLayout` impose la somme de ses colonnes comme largeur minimale (mesuré : une barre de boutons à 574 px, une fenêtre à 451 px au minimum) ; `Rangee` passe à la ligne comme du texte. |
| `qtpy6web.travailleur` | Un Web Worker Pyodide piloté depuis l'application, ce qui tient lieu de sous-processus (section suivante). |
| `qtpy6web.stockage` | `lire(cle)`, `ecrire(cle, texte)`, `effacer(cle)` sur `localStorage` (du texte, quelques Mio, qui survit au rechargement) ; `telecharger(nom, contenu, mime, lien=None)`, le seul chemin vers le disque de l'utilisateur (tout de suite, ou par un `<a>` de la page qu'il clique). |
| `qtpy6web.assembler` | `assembler(archive, fichiers, paquets, distributions, polices)` écrit le zip que la page dépaquette : des fichiers, des paquets purs Python pris là où ils sont installés (`qtpy6`, `qtpy6web`, ceux de l'application), des distributions avec leurs métadonnées, des polices. `polices(*motifs)` : des globs, erreur si aucun fichier. |
| `qtpy6web.sonde` | `python -m qtpy6web.sonde page.html capture.png [--racine DIR] [--delai 120] [--etat fini] [--taille 1000x900] [--zoom 2] [--tactile]` : sert `--racine` en local, ouvre la page dans Firefox sans interface, attend `window.etat`, imprime `window.journal`, capture l'écran et écrit chaque image de `window.captures` (`{suffixe: png en base64}`) en `capture_<suffixe>.png`. Code de retour 0 si l'état attendu est atteint. |
| `js/qtpy6web.js` | `preparer(conteneur, {indexURL, archives, roues, env, sur_ligne})` : charge Pyodide-Qt et les archives en parallèle, dépaquette, charge les roues WebAssembly par URL (`roues`, pour une extension compilée : le lock de Pyodide-Qt est vide, ni `loadPackage("nom")` ni micropip), pose `env` (`QT_API=pyqt6` par défaut) et met chaque dossier d'archive dans `sys.path` ; rend l'objet Pyodide. `print` et `journal` : le journal horodaté (console, `window.journal`, `sur_ligne`) que lit la sonde. `rendu()` : attend quelques images pour qu'une capture voie la fenêtre. |
| `js/travailleur.js` | Le Worker (lu par `importlib.resources`, lancé depuis une URL `blob:`). |
| `js/gabarit.html` | La page minimale, à copier : conteneur `position: fixed; inset: 0` qui **a sa taille dès le chargement** (Qt la prend au démarrage ; `display: none` donne une fenêtre de 0 px, cacher par `visibility`), message d'attente, `window.etat`. |

### Le worker : un sous-processus sans processus

Le navigateur n'a pas de `QProcess`, et Qt-WASM tourne dans le fil de la page : un calcul long, le programme d'un
utilisateur, une boucle infinie y gèleraient l'écran. `Travailleur` lance un **Web Worker** avec un Pyodide ordinaire
(pas Pyodide-Qt), y dépaquette des archives, y importe un module, et appelle ses fonctions :

```python
from qtpy6web.travailleur import Travailleur

w = Travailleur("pyodide/", [("app.zip", "/home/pyodide/app")], "echo", parent=fenetre)
w.sortie.connect(lambda numero, texte: ...)    # ce que la fonction imprime, au fil de l'eau (même sans "\n")
w.termine.connect(lambda numero, retour: ...)  # le retour (dict, list, str, nombres, None convertis)
w.erreur.connect(lambda numero, texte: ...)    # la trace
w.expire.connect(lambda numero: ...)           # rien au bout de `delai`
numero = w.appeler("echo", "bonjour", delai=60)
w.tuer()                                       # le seul « Arrêter » qu'un navigateur connaisse ; le prochain appel relance
```

`ProcessusWeb` pose sur un `Travailleur` la surface de `QProcess` qu'un code écrit pour un sous-processus utilise
(`start`, `write`, `readAllStandardOutput`, `kill`, `readyReadStandardOutput`, `finished`) : chaque ligne écrite est passée
à `module.fonction(ligne)`, ce qu'il imprime est la sortie. `configurer(indexURL, archives, module, fonction, cwd)` lui
donne ses réglages une fois pour toutes, et `Processus` est `QProcess` en natif, `ProcessusWeb` dans le navigateur : le
code de l'application écrit `Processus(self)` et ne voit pas la différence. Les URL passées au worker sont relatives à la
**page** (le worker naît d'un `blob:` et n'a pas d'adresse propre : elles sont rendues absolues côté Python). Un
`import()` de `pyodide.mjs` depuis un autre hôte exige CORS.

## Rendre une application qtpy6 compatible

Rien à envelopper : c'est du Qt ordinaire, écrit pour un seul fil et sans boucle d'événements imbriquée.

1. **Pas d'`exec()` de boîte de dialogue** (`QDialog.exec`, `QMessageBox.question`, `QFileDialog.getOpenFileName`) : une
   boucle imbriquée n'existe pas en WebAssembly. `boite.open()` puis les signaux `accepted`/`finished` ; un menu
   contextuel par `menu.popup(pos)`, pas `menu.exec()`.
2. **Pas de threads** (`QThread`, `threading`, `multiprocessing`) : Pyodide-Qt est mono-fil (donc sans
   `SharedArrayBuffer`, donc sans en-têtes COOP/COEP : un serveur statique nu suffit). Un travail long va dans un
   `Travailleur`.
3. **`QProcess` → `Processus`**, et ce qui tournait dans le sous-processus devient un module importé par le worker, dont
   une fonction reçoit chaque ligne.
4. **Les fichiers** vivent dans le système de fichiers de Pyodide (en mémoire, perdu au rechargement) : ce qui doit
   survivre passe par `stockage.ecrire`, ce qui doit sortir par `stockage.telecharger`.
5. **Les polices** : livrer celles de l'interface et la fixe dans l'archive (`assembler(..., polices=...)`), les déclarer
   à `application(polices=..., defaut=...)`, `police_fixe()` pour les éditeurs. Sans cela Qt-WASM dessine avec sa police
   de secours, différente du natif.
6. **Le doigt** : `tactile.activer()` si `tactile.detecte()`, `defiler_au_doigt` sur les zones défilantes, `Rangee` là où
   une barre de boutons imposerait sa largeur à la fenêtre.
7. **La fenêtre principale en `show_full_screen()`** dans le navigateur : tout le conteneur, sans barre de titre (une
   fenêtre Qt-WASM ordinaire a une barre de titre dessinée par Qt, que l'utilisateur peut déplacer et fermer).
8. **PyQt6 sous le capot** : qtpy6 traduit l'API, mais pas ce que PyQt6 ne fait pas. Pas d'arguments nommés de propriétés
   dans les constructeurs (`QPlainTextEdit(read_only=True)` échoue : setters), et une méthode redéfinie en Python se
   teste en camelCase (`heightForWidth`) — l'appel snake_case tombe sur la méthode de base C++.

Puis `assembler` l'archive (code, `qtpy6`, `qtpy6web`, données, polices), copier `js/gabarit.html`, et vérifier par la
sonde : `python -m qtpy6web.sonde --racine . page.html capture.png`, en lisant la capture.

## L'exemple

`exemple/` est la preuve sans autre application : un compteur (`compteur.py`, un bouton, un affichage, une zone d'écho)
et un worker `echo.py` qui imprime une invite sans retour à la ligne, attend, répond et rend un dict.

```bash
# Pyodide-Qt dans exemple/pyodide-qt/ (pyodide-qt-0.29.3.0.zip de la release, dépaqueté) et un Pyodide ordinaire dans
# exemple/pyodide/ (le tarball npm `pyodide` 314.0.7, ou son dossier full/ du CDN) : ni l'un ni l'autre ne sont versionnés
python exemple/construire.py                                     # exemple/app.zip (517 Kio : qtpy6, qtpy6web, deux polices)
python -m qtpy6web.sonde --racine . "exemple/index.html?auto" capture.png
```

`?auto` clique le bouton depuis la page, attend l'écho, et pose `window.captures = {grab}` (le `grab()` de la fenêtre).
Mesuré le 26/09/2026 (Firefox sans interface, fichiers en local) : Pyodide-Qt chargé et archive dépaquetée en 1,2 s,
fenêtre montrée en 0,27 s de plus, worker prêt 1,2 s après son démarrage, écho revenu en 1,75 s (l'invite sans `\n` arrive
tout de suite, en message séparé), tas WebAssembly 35 Mio.

En natif : `python exemple/compteur.py` ouvre la même fenêtre (le worker ne s'y lance pas : `Travailleur` ne sert que
dans le navigateur).

## Tests

```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests -q   # natif : tout s'importe et est inerte hors navigateur
```

Ce que le navigateur fait vraiment se mesure avec la sonde sur `exemple/` (section précédente) : c'est le test
d'intégration, il demande Firefox, geckodriver et selenium.

## Pièges et mesures (Qt-WASM 6.10, Pyodide-Qt 0.29.3)

- **Téléchargement** : `pyodide.asm.wasm` fait 32 Mio, 9,9 en gzip, 8,6 en brotli ; l'hôte doit compresser (une classe
  de 30 postes à froid : 300 Mio si oui, 1,2 Gio sinon). Une archive d'application ne se compresse plus (zip).
- **Mémoire** : +360 Mio sur un Firefox de bureau pour une application de 2 000 lignes ; un téléphone d'entrée de gamme
  peut tuer l'onglet, d'où `stockage` pour reprendre au rechargement.
- **Listes déroulantes** : Qt-WASM 6.10 referme un `QComboBox` au relâchement qui suit l'appui d'ouverture (le
  relâchement tombe sur le cadre de la liste, personne ne le prend). Un filtre d'événements sur la liste, qui consomme ce
  relâchement, le corrige ; la sonde `--tactile` sert à le vérifier.
- **Clavier virtuel** : un clic dans un champ donne le focus à l'`<input>` caché de Qt (`inputmode=text`, le clavier d'un
  téléphone monte) ; une liste déroulante au `focus-helper` (`inputmode=none`).
- **Lecteur d'écran** : Qt-WASM n'expose que « boutons et cases à cocher » ; une vue complexe ne produit rien. Un usage
  accessible reste au DOM.
- **Ce que le navigateur ne fait plus** dans la fenêtre Qt : sélection et recherche dans le texte, traduction
  automatique, clic droit. Safari (iPad, iPhone) : déclaré pris en charge par Qt, non essayé ici.
- **Deux Pyodide** : la page (Pyodide-Qt, roues par URL seulement, ABI `cp313-cp313-pyemscripten_2025_0_wasm32`) et le
  worker (Pyodide ordinaire, Python 3.14) ; les deux versions sont dans `versions.json`.
- **`import js`** n'existe que dans le navigateur : jamais au niveau d'un module qui doit s'importer en natif (un test le
  garantit ici) ; dans le worker, `js` existe mais ni `document` ni `localStorage`.
- **La sonde** : Firefox ne descend pas sous 500 px de large (une largeur de téléphone se mesure en natif hors écran, ou
  avec `--zoom`) ; Chromium n'ouvre pas sans socket Unix, ce qu'un bac à sable peut interdire. Selenium Manager tente de
  télécharger geckodriver avant de prendre celui du système : sans réseau, ses messages sont du bruit, pas une panne.

## Hébergement

Pyodide-Qt (36 Mo, dont le `.wasm` de 32 : 9,9 en gzip) ne se versionne pas avec l'application ; il se sert d'un hôte
statique à part, avec CORS ouvert, parce que la page l'importe par `import()` de `pyodide.mjs` depuis une autre origine.
Le dépôt [qtpy6web-pyodide-qt](https://github.com/SmartAudioTools/qtpy6web-pyodide-qt) (GPL v3, comme PyQt6 qu'il
distribue) le publie sur GitHub Pages depuis la release épinglée, sans binaire versionné :

    indexURL: "https://smartaudiotools.github.io/qtpy6web-pyodide-qt/pyodide-qt/"

Le dossier local (`./pyodide-qt/`) reste le bon choix pour développer et pour la sonde : pas de réseau, et les mesures
de temps ne comptent que le chargement. Son README dit ce qu'il faut mesurer au premier déploiement (l'en-tête CORS, la
compression du `.wasm`) ; aucun en-tête d'isolation (COOP/COEP) n'est nécessaire, ce build est mono-fil.

## Licence

MIT (`LICENSE.txt`). Pyodide-Qt, que la page charge, est GPL v3 ; Pyodide est MPL 2.0 ; Qt est LGPL v3.
