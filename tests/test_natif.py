"""Hors navigateur, le paquet s'importe et se tient tranquille : rien ne touche à ``js``, ``Processus`` est QProcess, la
feuille tactile ne remplace rien, les dispositions se replient. Ce que le navigateur fait vraiment se mesure avec
``python -m qtpy6web.sonde`` sur ``exemple/`` (README)."""

import json
import sys
import zipfile
from pathlib import Path

import pytest
from qtpy6 import QtCore, QtGui, QtWidgets

import qtpy6web
from qtpy6web import assembler, dispositions, stockage, tactile, travailleur

RACINE = Path(__file__).resolve().parents[1]


def test_inerte_en_natif():
    assert not qtpy6web.navigateur()
    assert "js" not in sys.modules or sys.platform == "emscripten"
    assert travailleur.Processus is QtCore.QProcess
    assert not tactile.detecte()


def test_application_offscreen(app):
    assert QtWidgets.QApplication.instance() is app
    assert qtpy6web.application() is app  # idempotente
    assert isinstance(qtpy6web.police_fixe(), QtGui.QFont)


def test_feuille_tactile_concatenee(app):
    app.set_style_sheet("QLabel { color: red; }")
    try:
        assert tactile.marge() == 2
        tactile.activer(app, cible=44)
        assert tactile.ACTIF and app.style_sheet().startswith("QLabel { color: red; }")
        assert "min-height: 44px" in app.style_sheet()
        assert tactile.marge() == (44 - 26) // 2
    finally:
        tactile.ACTIF = False
        app.set_style_sheet("")


def test_rangee_se_replie(app):
    zone = QtWidgets.QWidget()
    rangee = dispositions.Rangee(6)
    zone.set_layout(rangee)
    for i in range(6):
        rangee.add_widget(QtWidgets.QPushButton("Bouton %d" % i))
    assert rangee.heightForWidth(200) > rangee.heightForWidth(1000)  # étroite : plusieurs lignes (camelCase : le
    # snake_case de PySide6 appelle ici la méthode de base, qui rend -1)


def test_versions_json():
    v = json.loads((RACINE / "qtpy6web" / "versions.json").read_text())
    assert {"pyodide_qt", "pyodide"} <= set(v) and v["pyodide_qt"]["abi"].startswith("cp")


def test_assembler(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n")
    zip_ = tmp_path / "app.zip"
    assembler.assembler(zip_, fichiers={"a.py": tmp_path / "a.py"}, paquets=("qtpy6web",))
    noms = zipfile.ZipFile(zip_).namelist()
    assert "a.py" in noms and "qtpy6web/js/travailleur.js" in noms and "qtpy6web/versions.json" in noms
    assert not any("__pycache__" in n for n in noms)


def test_stockage_hors_navigateur():
    with pytest.raises(ModuleNotFoundError):  # le module s'importe en natif ; ses fonctions, elles, veulent le navigateur
        stockage.lire("cle")
