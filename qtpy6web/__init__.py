"""Une application qtpy6 (PyQt6) dans le navigateur, sous Pyodide-Qt : le code de l'application ne change pas, il
s'exécute en WebAssembly dans un élément de la page. Ce paquet est ce qu'il lui faut autour :

    navigateur()                     True sous Pyodide (``sys.platform == "emscripten"``) : l'interrupteur de tout le reste
    application(polices, defaut)     la QApplication, créée au besoin ; hors écran sans session graphique ; les polices
                                     livrées avec l'application dans le navigateur, qui n'en a aucune
    police_fixe(secours)             la police à chasse fixe : celle du système, ou ``secours`` dans le navigateur
    tactile                          détecter un écran au doigt, grossir les cibles, faire défiler au doigt
    dispositions                     des dispositions qui se replient quand la place manque (Disposition, Rangee)
    travailleur                      un Web Worker Pyodide sous la surface de QProcess (Travailleur, ProcessusWeb, Processus)
    stockage                         localStorage et téléchargement d'un fichier depuis l'application
    assembler                        l'archive que la page dépaquette : fichiers, paquets, distributions, polices
    sonde                            ``python -m qtpy6web.sonde`` : la page dans Firefox sans interface, journal et capture

Côté page, ``js/qtpy6web.js`` charge Pyodide-Qt et l'archive de l'application (``preparer``), ``js/travailleur.js`` est le
Worker, ``js/gabarit.html`` la page minimale. Rien ici n'importe ``js`` au niveau du module : le paquet s'importe tel quel
en natif, où tout est inerte."""

import os
import sys
from pathlib import Path

from qtpy6.QtGui import QFont, QFontDatabase
from qtpy6.QtWidgets import QApplication

__version__ = "0.1.0"
_APP = None


def navigateur():
    """Le code tourne dans le navigateur (Pyodide). Une fonction, pas une constante : un test peut forcer ``sys.platform``."""
    return sys.platform == "emscripten"


def application(polices=None, defaut=None):
    """La QApplication du processus, créée au besoin et rendue. Hors session graphique (ni DISPLAY ni WAYLAND_DISPLAY),
    ``QT_QPA_PLATFORM`` passe à ``offscreen`` : les tests et les exports tournent sans écran. Dans le navigateur, Qt n'a
    AUCUNE police système : les fichiers ``.ttf``/``.otf`` du dossier ``polices`` y sont chargés, et ``defaut`` (un QFont,
    ou ``("Noto Sans", 9)``) devient la police de l'interface. En natif, ni l'un ni l'autre ne s'appliquent : le système
    a les siennes."""
    global _APP
    if QApplication.instance() is None:
        if not navigateur() and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        _APP = app = QApplication(sys.argv[:1])  # gardée : sous PyQt6, une
        # QApplication dont la dernière référence Python disparaît est détruite, et toutes ses fenêtres avec elle
        if navigateur():
            for police in sorted(Path(polices).glob("*.[to]tf")) if polices else ():
                QFontDatabase.addApplicationFont(str(police))
            if defaut is not None:
                app.setFont(defaut if isinstance(defaut, QFont) else QFont(*defaut))
    return QApplication.instance()


def police_fixe(secours="Liberation Mono"):
    """La police à chasse fixe (éditeurs, consoles) : celle du système ; dans le navigateur, qui n'en a aucune, ``secours``
    (à livrer dans le dossier ``polices`` d'``application``) au corps de l'interface."""
    if navigateur():
        return QFont(secours, QApplication.font().pointSize())
    return QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
