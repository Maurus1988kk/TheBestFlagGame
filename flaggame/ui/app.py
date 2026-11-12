"""Avvio dell'applicazione Qt e gestione degli errori imprevisti."""

from __future__ import annotations

import sys
import traceback
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QMessageBox

from .. import NOME_APP, VERSIONE, percorsi, testi
from .grafica import icona_app
from .tema import font


def _registra_errore(tipo, valore, tb) -> None:
    """Scrive l'errore in errori.log e lo mostra invece di chiudere in silenzio."""
    testo = "".join(traceback.format_exception(tipo, valore, tb))
    try:
        with open(percorsi.cartella_utente() / "errori.log", "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] {NOME_APP} {VERSIONE}\n{testo}")
    except OSError:
        pass
    sys.__excepthook__(tipo, valore, tb)
    if QApplication.instance() is not None:
        QMessageBox.critical(None, testi.ERRORE_TITOLO, f"{valore}\n\n{testo[-1500:]}")


def crea_applicazione(argv: list[str] | None = None) -> QApplication:
    """Crea (o restituisce) la QApplication con stile, font e icona."""
    app = QApplication.instance()
    if app is not None:
        return app
    if sys.platform == "win32":
        try:  # icona corretta nella barra delle applicazioni di Windows
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FlagGame.TheBestFlagGame.2")
        except (AttributeError, OSError):
            pass
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName(NOME_APP)
    app.setApplicationVersion(VERSIONE)
    app.setOrganizationName("FlagGame")
    app.setStyle("Fusion")
    app.setFont(font(14))
    app.setWindowIcon(icona_app())
    return app


def verifica() -> int:
    """Avvio di prova senza mostrare finestre: carica le bandiere, apre ogni
    schermata e gioca una domanda per modalità. Restituisce 0 se va tutto bene.
    Usato da build.bat per controllare l'eseguibile appena creato."""
    import os
    import shutil
    import tempfile
    cartella = tempfile.mkdtemp(prefix="flaggame-verifica-")
    os.environ["FLAGGAME_DATI_UTENTE"] = cartella  # non tocca i dati veri
    try:
        app = crea_applicazione()
        from .finestra import FinestraPrincipale
        finestra = FinestraPrincipale()
        finestra.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
        finestra.show()
        app.processEvents()
        if finestra.catalogo is None:
            return 2
        for modalita in ("flag", "country"):
            finestra.avvia_partita(modalita, "facile", "mondo")
            app.processEvents()
            finestra.gioco.mostra_prima_domanda()
            finestra.gioco.rispondi(0)
            finestra.grab()
            finestra.gioco.abbandona()
            app.processEvents()
        for schermata in (finestra.schermata_classifica, finestra.schermata_impostazioni, finestra.home):
            finestra.stack.mostra(schermata, anima=False)
            finestra.grab()
        finestra.close()
        return 0
    except Exception:  # noqa: BLE001 - qualsiasi errore fa fallire la verifica
        traceback.print_exc()
        return 1
    finally:
        shutil.rmtree(cartella, ignore_errors=True)


def avvia() -> int:
    """Punto di ingresso del programma."""
    sys.excepthook = _registra_errore
    app = crea_applicazione()
    from .finestra import FinestraPrincipale
    finestra = FinestraPrincipale()
    finestra.show()
    return app.exec()
