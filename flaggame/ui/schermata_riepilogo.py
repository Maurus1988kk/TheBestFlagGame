"""Schermata di fine partita: punteggio, tempo, elenco risposte, salvataggio."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLineEdit, QScrollArea, QVBoxLayout, QWidget

from .. import testi
from ..classifica import LUNGHEZZA_MAX_NOME
from ..generatore import MODALITA_STATO
from ..partita import Partita, RispostaData, formatta_tempo
from .componenti import (AnelloPercentuale, Card, EtichettaElisa, VistaBandiera, etichetta, pulsante,
                         separatore)
from .grafica import disegna_icona, imposta_icona
from .immagini import CacheImmagini
from .schermata_home import etichetta_sezione
from .tema import tema


class SimboloEsito(QWidget):
    """Piccolo cerchio verde con spunta o rosso con croce."""

    def __init__(self, giusta: bool, parent=None):
        super().__init__(parent)
        self.giusta = giusta
        self.setFixedSize(26, 26)

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        colore = tema().c("successo") if self.giusta else tema().c("errore")
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(tema().c("successo_tenue") if self.giusta else tema().c("errore_tenue"))
        p.drawEllipse(QRectF(self.rect()).adjusted(1, 1, -1, -1))
        disegna_icona(p, "check" if self.giusta else "croce", QRectF(6, 6, 14, 14), colore, 2.6)


class RigaRisposta(QWidget):
    """Una domanda nel riepilogo: miniatura, risposta giusta, risposta data."""

    def __init__(self, risposta: RispostaData, modalita: str, cache: CacheImmagini, ultima: bool,
                 parent=None):
        super().__init__(parent)
        self.ultima = ultima
        d = risposta.domanda
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 10, 8, 10)
        lay.setSpacing(14)

        numero = etichetta(str(d.numero), "terziario")
        numero.setFixedWidth(20)
        numero.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(numero)

        miniatura = VistaBandiera(cache, rapporto=1.5, riquadro=False)
        miniatura.setFixedSize(78, 52)
        miniatura.imposta(d.risposta.immagine)
        lay.addWidget(miniatura)

        testi_col = QVBoxLayout()
        testi_col.setSpacing(2)
        nome = EtichettaElisa(d.risposta.nome, "forte")
        testi_col.addWidget(nome)
        if risposta.giusta:
            sotto = EtichettaElisa(testi.RIEPILOGO_RISPOSTA_GIUSTA, "secondario")
        else:
            sotto = EtichettaElisa(testi.RIEPILOGO_TUA_RISPOSTA.format(nome=risposta.opzione_scelta.nome),
                                   "secondario")
        testi_col.addWidget(sotto)
        lay.addLayout(testi_col, 1)

        if modalita == MODALITA_STATO and not risposta.giusta:
            scelta = VistaBandiera(cache, rapporto=1.5, riquadro=False)
            scelta.setFixedSize(54, 36)
            scelta.imposta(risposta.opzione_scelta.immagine)
            scelta.setToolTip(risposta.opzione_scelta.nome)
            lay.addWidget(scelta)

        tempo = etichetta(testi.RIEPILOGO_SECONDI.format(s=risposta.tempo), "terziario")
        tempo.setMinimumWidth(52)
        tempo.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(tempo)
        lay.addWidget(SimboloEsito(risposta.giusta))

    def paintEvent(self, evento):
        if not self.ultima:
            p = QPainter(self)
            p.setPen(QPen(tema().c("bordo"), 1))
            p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)


class SchermataRiepilogo(QWidget):
    """Riepilogo della partita appena conclusa."""

    salva = Signal(str)
    gioca_ancora = Signal()
    menu = Signal()

    def __init__(self, cache: CacheImmagini, parent=None):
        super().__init__(parent)
        self.setObjectName("schermata")
        self.cache = cache
        self.partita: Partita | None = None
        self._salvato = False
        self._costruisci()

    def _costruisci(self):
        radice = QVBoxLayout(self)
        radice.setContentsMargins(30, 22, 30, 22)
        radice.setSpacing(4)

        testa = QHBoxLayout()
        testa.setContentsMargins(10, 0, 10, 0)
        testa.setSpacing(8)
        testa.addWidget(etichetta(testi.RIEPILOGO_TITOLO, "titolo"))
        testa.addSpacing(10)
        self.chip_modalita = etichetta("", "chip")
        self.chip_livello = etichetta("", "chip")
        self.chip_area = etichetta("", "chip")
        for chip in (self.chip_modalita, self.chip_livello, self.chip_area):
            testa.addWidget(chip, 0, Qt.AlignmentFlag.AlignVCenter)
        testa.addStretch(1)
        radice.addLayout(testa)
        radice.addSpacing(4)

        corpo = QHBoxLayout()
        corpo.setSpacing(4)

        # colonna sinistra: punteggio e salvataggio
        sinistra = Card(padding=22)
        sinistra.setFixedWidth(400)
        ls = sinistra.lay
        ls.setSpacing(6)
        self.anello = AnelloPercentuale(lato=164)
        ls.addWidget(self.anello, 0, Qt.AlignmentFlag.AlignHCenter)
        ls.addSpacing(4)
        self.lbl_giudizio = etichetta("", "titolo_medio")
        self.lbl_giudizio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ls.addWidget(self.lbl_giudizio)
        self.lbl_giuste = etichetta("", "secondario")
        self.lbl_giuste.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ls.addWidget(self.lbl_giuste)
        ls.addSpacing(10)

        stat = QGridLayout()
        stat.setHorizontalSpacing(12)
        stat.setVerticalSpacing(4)
        stat.addWidget(etichetta(testi.RIEPILOGO_TEMPO, "secondario"), 0, 0)
        self.lbl_tempo = etichetta("", "forte")
        stat.addWidget(self.lbl_tempo, 0, 1, Qt.AlignmentFlag.AlignRight)
        stat.addWidget(etichetta(testi.RIEPILOGO_TEMPO_MEDIO, "secondario"), 1, 0)
        self.lbl_medio = etichetta("", "forte")
        stat.addWidget(self.lbl_medio, 1, 1, Qt.AlignmentFlag.AlignRight)
        stat.addWidget(etichetta(testi.RIEPILOGO_PUNTI, "secondario"), 2, 0)
        self.lbl_punti = etichetta("", "forte")
        stat.addWidget(self.lbl_punti, 2, 1, Qt.AlignmentFlag.AlignRight)
        ls.addLayout(stat)
        ls.addSpacing(10)
        ls.addWidget(separatore())
        ls.addSpacing(10)

        ls.addWidget(etichetta(testi.RIEPILOGO_NOME, "forte"))
        self.campo_nome = QLineEdit()
        self.campo_nome.setPlaceholderText(testi.RIEPILOGO_NOME_SEGNAPOSTO)
        self.campo_nome.setMaxLength(LUNGHEZZA_MAX_NOME)
        self.campo_nome.returnPressed.connect(self._salva)
        self.campo_nome.textChanged.connect(self._aggiorna_salva)
        ls.addWidget(self.campo_nome)
        self.btn_salva = pulsante(testi.RIEPILOGO_SALVA, "primario")
        imposta_icona(self.btn_salva, "trofeo", "su_primario", 18)
        self.btn_salva.clicked.connect(self._salva)
        ls.addWidget(self.btn_salva)
        ls.addStretch(1)
        riga = QHBoxLayout()
        self.btn_menu = pulsante(testi.RIEPILOGO_MENU, "fantasma")
        imposta_icona(self.btn_menu, "casa", "testo_secondario")
        self.btn_ancora = pulsante(testi.RIEPILOGO_GIOCA_ANCORA)
        imposta_icona(self.btn_ancora, "ricarica", "testo_secondario")
        riga.addWidget(self.btn_menu)
        riga.addStretch(1)
        riga.addWidget(self.btn_ancora)
        ls.addLayout(riga)
        corpo.addWidget(sinistra)

        # colonna destra: elenco delle risposte
        destra = Card(padding=18)
        ld = destra.lay
        ld.setSpacing(6)
        ld.addWidget(etichetta_sezione(testi.RIEPILOGO_LE_TUE_RISPOSTE))
        self.scorrimento = QScrollArea()
        self.scorrimento.setWidgetResizable(True)
        self.scorrimento.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.elenco = QWidget()
        self.lay_elenco = QVBoxLayout(self.elenco)
        self.lay_elenco.setContentsMargins(0, 0, 6, 0)
        self.lay_elenco.setSpacing(0)
        self.scorrimento.setWidget(self.elenco)
        ld.addWidget(self.scorrimento, 1)
        corpo.addWidget(destra, 1)
        radice.addLayout(corpo, 1)

        self.btn_menu.clicked.connect(self.menu)
        self.btn_ancora.clicked.connect(self.gioca_ancora)

    # ------------------------------------------------------------- dati

    def mostra(self, partita: Partita, nome_modalita: str, nome_livello: str, nome_area: str,
               ultimo_nome: str, punti: int) -> None:
        self.partita = partita
        self.chip_modalita.setText(nome_modalita)
        self.chip_livello.setText(nome_livello)
        self.chip_area.setText(nome_area)
        perc = partita.percentuale
        self.anello.imposta(perc)
        self.lbl_giudizio.setText(next(t for soglia, t in testi.RIEPILOGO_GIUDIZI if perc >= soglia))
        modello = testi.RIEPILOGO_GIUSTE_UNA if partita.giuste == 1 else testi.RIEPILOGO_GIUSTE
        self.lbl_giuste.setText(modello.format(g=partita.giuste, t=partita.totale))
        self.lbl_tempo.setText(formatta_tempo(partita.tempo()))
        self.lbl_medio.setText(testi.RIEPILOGO_SECONDI.format(s=partita.tempo() / partita.totale))
        self.lbl_punti.setText(str(punti))

        self.campo_nome.setEnabled(True)
        self.campo_nome.setText(ultimo_nome)
        self.btn_salva.setText(testi.RIEPILOGO_SALVA)
        imposta_icona(self.btn_salva, "trofeo", "su_primario", 18)
        self._salvato = False
        self._aggiorna_salva()

        while self.lay_elenco.count():
            voce = self.lay_elenco.takeAt(0)
            if voce.widget():
                voce.widget().deleteLater()
        for i, r in enumerate(partita.risposte):
            self.lay_elenco.addWidget(RigaRisposta(r, partita.modalita, self.cache,
                                                   ultima=i == len(partita.risposte) - 1))
        self.lay_elenco.addStretch(1)
        self.scorrimento.verticalScrollBar().setValue(0)

    def _aggiorna_salva(self) -> None:
        self.btn_salva.setEnabled(not self._salvato and bool(self.campo_nome.text().strip()))

    def _salva(self) -> None:
        if self.btn_salva.isEnabled():
            self.salva.emit(self.campo_nome.text().strip())

    def segna_salvato(self) -> None:
        self._salvato = True
        self.campo_nome.setEnabled(False)
        self.btn_salva.setText(testi.RIEPILOGO_SALVATO)
        imposta_icona(self.btn_salva, "check", "testo_terziario", 18)
        self._aggiorna_salva()

    def showEvent(self, evento):
        super().showEvent(evento)
        if not self._salvato:
            self.campo_nome.setFocus()
            self.campo_nome.selectAll()
