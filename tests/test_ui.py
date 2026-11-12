"""Avvia l'interfaccia e verifica che ogni schermata si apra senza errori.

Se la variabile d'ambiente FLAGGAME_SCREENSHOT è impostata a una cartella,
salva lì uno screenshot (QWidget.grab) di ogni schermata, in tema chiaro e
scuro e alla dimensione minima della finestra.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

from flaggame import percorsi  # noqa: E402
from flaggame.partita import StatoPartita  # noqa: E402

from .conftest import CARTELLA_BANDIERE  # noqa: E402

CARTELLA_SCREENSHOT = os.environ.get("FLAGGAME_SCREENSHOT")
errori_qt: list[str] = []


def salva(widget, nome: str) -> None:
    pix = widget.grab()
    assert not pix.isNull()
    if CARTELLA_SCREENSHOT:
        Path(CARTELLA_SCREENSHOT).mkdir(parents=True, exist_ok=True)
        pix.save(str(Path(CARTELLA_SCREENSHOT) / f"{nome}.png"))


@pytest.fixture(scope="module")
def app():
    from PySide6.QtCore import qInstallMessageHandler, QtMsgType

    def gestore(tipo, contesto, messaggio):
        if tipo in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            errori_qt.append(messaggio)
    qInstallMessageHandler(gestore)
    from flaggame.ui.app import crea_applicazione
    applicazione = crea_applicazione([sys.argv[0]])
    yield applicazione
    qInstallMessageHandler(None)


@pytest.fixture
def eccezioni(monkeypatch):
    """Raccoglie le eccezioni nate dentro i gestori Qt (che altrimenti si perderebbero)."""
    raccolte = []
    monkeypatch.setattr(sys, "excepthook", lambda t, v, tb: raccolte.append(v))
    return raccolte


def nuova_finestra(larghezza=1240, altezza=820):
    from flaggame.ui.finestra import FinestraPrincipale
    f = FinestraPrincipale()
    f.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
    f.resize(larghezza, altezza)
    f.show()
    QTest.qWait(150)
    return f


def gioca_fino_alla_fine(f):
    """Risponde a tutte le domande (alternando giuste e sbagliate)."""
    while f.partita.stato != StatoPartita.FINITA:
        d = f.partita.domanda_corrente
        scelta = d.indice_giusto if d.numero % 3 else (d.indice_giusto + 1) % 4
        QTest.keyClick(f.gioco, Qt.Key.Key_1 + scelta)
        QTest.keyClick(f.gioco, Qt.Key.Key_Return)
    QTest.qWait(1100)


@pytest.mark.skipif(not CARTELLA_BANDIERE.is_dir(), reason="cartella flags non presente")
def test_tutte_le_schermate(app, eccezioni):
    errori_qt.clear()
    f = nuova_finestra()
    assert f.catalogo is not None
    assert f.stack.currentWidget() is f.home
    salva(f, "01_home")

    # clic sul livello Nerd, poi area America del Sud: avviso nel menu
    seg = f.home.segmenti_livello
    QTest.mouseClick(seg, Qt.MouseButton.LeftButton, pos=seg._segmento(3).center().toPoint())
    QTest.qWait(50)
    assert f.home.livello() == "nerd"
    assert f.home._livello_aree == "nerd"
    assert f.home.descr_livello.text() == "Solo bandiere quasi identiche tra loro. Buona fortuna!"
    assert "158" in f.home.info.text()
    f.home.combo_area.setCurrentIndex(f.home.combo_area.findData("america_sud"))
    assert f.home.info.property("ruolo") == "avviso"
    assert "3" in f.home.info.text()
    f.home.card_country.click()
    QTest.qWait(250)
    salva(f, "02_home_nerd_country_avviso")

    # Guess the Flag: il timer parte con la prima domanda
    f.avvia_partita("flag", "facile", "mondo")
    QTest.qWait(500)
    assert f.stack.currentWidget() is f.gioco
    assert f.partita.timer_in_corso
    salva(f, "03_gioco_flag")
    d = f.partita.domanda_corrente
    sbagliata = (d.indice_giusto + 1) % 4
    QTest.keyClick(f.gioco, Qt.Key.Key_1 + sbagliata)
    QTest.qWait(120)
    assert f.partita.stato == StatoPartita.FEEDBACK
    assert not f.partita.timer_in_corso            # timer in pausa durante il feedback
    assert f.gioco.pulsanti[sbagliata].stato == "sbagliata"
    assert f.gioco.pulsanti[d.indice_giusto].stato == "giusta"
    salva(f, "04_gioco_flag_feedback_sbagliata")
    QTest.qWait(1400)                               # avanzamento automatico
    assert f.partita.indice == 1 and f.partita.stato == StatoPartita.DOMANDA
    gioca_fino_alla_fine(f)
    assert f.stack.currentWidget() is f.riepilogo
    salva(f, "05_riepilogo")

    # salvataggio in classifica, con risultato evidenziato
    f.riepilogo.campo_nome.setText("Tester")
    f.riepilogo.btn_salva.click()
    QTest.qWait(450)
    assert len(f.classifica) == 1
    assert f.stack.currentWidget() is f.schermata_classifica
    assert f.schermata_classifica.evidenzia == f.classifica.tutti()[0].id
    salva(f, "06_classifica")
    f.schermata_classifica.btn_indietro.click()
    QTest.qWait(400)
    assert f.stack.currentWidget() is f.riepilogo
    assert not f.riepilogo.btn_salva.isEnabled()
    # punti del riepilogo = punti in classifica; risposte salvate per le statistiche
    salvato = f.classifica.tutti()[0]
    assert f.riepilogo.lbl_punti.text() == str(f.classifica.punti(salvato))
    assert len(salvato.risposte) == salvato.totale == 10
    assert sum(r.giusta for r in salvato.risposte) == salvato.giuste

    # Guess the Country, livello nerd
    f.avvia_partita("country", "nerd", "mondo")
    QTest.qWait(500)
    salva(f, "07_gioco_country")
    d = f.partita.domanda_corrente
    QTest.mouseClick(f.gioco.card[d.indice_giusto], Qt.MouseButton.LeftButton)
    QTest.qWait(120)
    assert f.partita.risposte[-1].giusta
    salva(f, "08_gioco_country_feedback_giusta")
    QTest.mouseClick(f.gioco, Qt.MouseButton.LeftButton)   # un clic fa proseguire
    QTest.qWait(250)
    assert f.partita.indice == 1

    # ESC: conferma, poi abbandono (non va in classifica)
    QTest.keyClick(f.gioco, Qt.Key.Key_Escape)
    QTest.qWait(250)
    assert f.gioco._conferma is not None
    assert not f.partita.timer_in_corso
    salva(f, "09_conferma_abbandono")
    f.gioco._conferma.no.click()
    QTest.qWait(100)
    assert f.partita.timer_in_corso
    partita = f.partita
    QTest.keyClick(f.gioco, Qt.Key.Key_Escape)
    QTest.qWait(250)
    f.gioco._conferma.si.click()
    QTest.qWait(450)
    assert f.stack.currentWidget() is f.home
    assert partita.stato == StatoPartita.ABBANDONATA
    assert len(f.classifica) == 1

    # impostazioni e classifica dalla home
    f.home.btn_impostazioni.click()
    QTest.qWait(400)
    assert f.stack.currentWidget() is f.schermata_impostazioni
    salva(f, "10_impostazioni")
    f.home.btn_classifica.click()
    QTest.qWait(400)
    f.schermata_classifica.mostra(None, None, None)
    QTest.qWait(100)
    salva(f, "11_classifica_tutte")
    assert "300 in Nerd" in f.schermata_classifica.lbl_spiegazione.text()

    # statistiche del giocatore appena salvato
    f.home.btn_statistiche.click()
    QTest.qWait(400)
    st = f.schermata_statistiche
    assert f.stack.currentWidget() is st
    assert st.pagine.currentWidget() is st.pagina_dati
    assert st.combo_giocatore.currentText() == "Tester"
    assert st.t_partite.lbl_valore.text() == "1"
    assert not st.grafico_continenti.isHidden() and st.nota_continenti.isHidden()
    assert st.griglia_ripasso.count() >= 1          # almeno una risposta sbagliata
    salva(f, "11b_statistiche")

    # tema scuro
    f.apri_impostazioni()
    QTest.qWait(350)
    f.schermata_impostazioni.seg_tema.imposta_valore("scuro")
    f.schermata_impostazioni.tema_cambiato.emit("scuro")
    QTest.qWait(200)
    assert f.impostazioni.tema == "scuro"
    salva(f, "12_impostazioni_scuro")
    f.vai_home()
    QTest.qWait(400)
    salva(f, "13_home_scuro")
    f.avvia_partita("flag", "difficile", "europa")
    QTest.qWait(500)
    QTest.keyClick(f.gioco, Qt.Key.Key_1 + f.partita.domanda_corrente.indice_giusto)
    QTest.qWait(100)
    salva(f, "14_gioco_flag_scuro")
    QTest.keyClick(f.gioco, Qt.Key.Key_Return)
    gioca_fino_alla_fine(f)
    salva(f, "15_riepilogo_scuro")
    f.riepilogo.campo_nome.setText("Notte")
    f.riepilogo.btn_salva.click()
    QTest.qWait(450)
    salva(f, "16_classifica_scuro")
    f.apri_statistiche()
    QTest.qWait(400)
    assert f.schermata_statistiche.combo_giocatore.currentText() == "Notte"
    assert f.schermata_statistiche.combo_giocatore.count() == 2
    salva(f, "16b_statistiche_scuro")
    f.avvia_partita("country", "intermedio", "oceania")
    QTest.qWait(500)
    salva(f, "17_gioco_country_scuro")
    f.gioco.abbandona()
    QTest.qWait(400)
    f._cambia_tema("chiaro")
    f.close()

    assert eccezioni == []
    assert [e for e in errori_qt if "QFont::setPointSize" not in e] == []


@pytest.mark.skipif(not CARTELLA_BANDIERE.is_dir(), reason="cartella flags non presente")
def test_dimensione_minima(app, eccezioni):
    f = nuova_finestra(1000, 700)
    assert f.width() >= 1000 and f.height() >= 700
    salva(f, "20_min_home")
    f.apri_statistiche()                              # nessuna partita salvata
    QTest.qWait(400)
    assert f.schermata_statistiche.pagine.currentWidget() is f.schermata_statistiche.vuoto
    assert f.schermata_statistiche.colonna_giocatore.isHidden()
    salva(f, "25_min_statistiche_vuote")
    f.vai_home()
    QTest.qWait(400)
    f.avvia_partita("flag", "intermedio", "mondo")
    QTest.qWait(500)
    salva(f, "21_min_gioco_flag")
    f.gioco.abbandona()
    QTest.qWait(400)
    f.avvia_partita("country", "facile", "mondo")
    QTest.qWait(500)
    salva(f, "22_min_gioco_country")
    gioca_fino_alla_fine(f)
    salva(f, "23_min_riepilogo")
    f.riepilogo.campo_nome.setText("Mini")
    f.riepilogo.btn_salva.click()
    QTest.qWait(450)
    f.apri_statistiche()
    QTest.qWait(400)
    salva(f, "26_min_statistiche")
    f.apri_impostazioni()
    QTest.qWait(400)
    salva(f, "24_min_impostazioni")
    f.close()
    assert eccezioni == []


@pytest.mark.skipif(not CARTELLA_BANDIERE.is_dir(), reason="cartella flags non presente")
def test_ritaglio_bordi(app, catalogo):
    """Niger 600x600 con bande trasparenti -> 600x360; Nepal su tela bianca -> forma verticale.
    Le altre bandiere (es. Giappone, Russia con il bianco sul bordo) restano intere."""
    from flaggame.ui.immagini import CacheImmagini, percorso_normale
    cache = CacheImmagini()
    cache.da_ritagliare = catalogo.percorsi_da_ritagliare()
    assert cache.da_ritagliare == {percorso_normale(CARTELLA_BANDIERE / c / "nepal.gif")
                                   for c in ("easy", "intermediate", "difficult/17")}
    niger = cache.dimensione(CARTELLA_BANDIERE / "easy" / "niger.png")
    assert (niger.width(), niger.height()) == (600, 360)
    nepal = cache.dimensione(CARTELLA_BANDIERE / "easy" / "nepal.gif")
    assert nepal.width() / nepal.height() < 0.9
    for nome, dim in (("japan.png", (275, 183)), ("russia.png", (275, 183)), ("poland.png", (480, 300))):
        d = cache.dimensione(CARTELLA_BANDIERE / "easy" / nome)
        assert (d.width(), d.height()) == dim, nome
    assert cache.pixmap(CARTELLA_BANDIERE / "easy" / "nepal.gif", 100, 100) is not None


def test_cartella_non_trovata(app, eccezioni, monkeypatch, tmp_path):
    monkeypatch.setattr(percorsi, "candidati_radice_bandiere", lambda: [tmp_path / "flags", tmp_path])
    f = nuova_finestra()
    assert f.catalogo is None
    assert f.stack.currentWidget() is f.schermata_cartella
    assert f.schermata_cartella.btn_scegli.isVisible()
    salva(f, "30_cartella_non_trovata")
    f.close()
    assert eccezioni == []
