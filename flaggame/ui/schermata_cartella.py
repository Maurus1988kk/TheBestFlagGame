"""Schermata mostrata quando la cartella delle bandiere non viene trovata."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from .. import testi
from .componenti import Card, etichetta, imposta_ruolo, pulsante
from .grafica import disegna_icona, imposta_icona
from .tema import tema


class IconaCartella(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(72, 72)

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(tema().c("avviso_tenue"))
        p.drawEllipse(QRectF(self.rect()))
        disegna_icona(p, "cartella", QRectF(18, 18, 36, 36), tema().c("avviso"), 2.0)


class SchermataCartella(QWidget):
    """Messaggio chiaro con il pulsante "Scegli cartella…"."""

    scegli = Signal()
    riprova = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("schermata")
        radice = QVBoxLayout(self)
        radice.addStretch(1)
        riga = QHBoxLayout()
        riga.addStretch(1)
        card = Card(padding=30, raggio=22)
        card.setFixedWidth(620)
        lay = card.lay
        lay.setSpacing(10)
        lay.addWidget(IconaCartella(), 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(6)
        titolo = etichetta(testi.CARTELLA_TITOLO, "titolo_medio")
        titolo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(titolo)
        self.lbl_testo = etichetta("", "secondario", a_capo=True)
        self.lbl_testo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.lbl_testo)
        self.lbl_percorso = etichetta("", "terziario", a_capo=True)
        self.lbl_percorso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_percorso.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(self.lbl_percorso)
        self.lbl_errore = etichetta("", "errore", a_capo=True)
        self.lbl_errore.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_errore.hide()
        lay.addWidget(self.lbl_errore)
        lay.addSpacing(10)
        pulsanti = QHBoxLayout()
        pulsanti.addStretch(1)
        self.btn_riprova = pulsante(testi.CARTELLA_RIPROVA)
        imposta_icona(self.btn_riprova, "ricarica", "testo_secondario")
        self.btn_scegli = pulsante(testi.CARTELLA_SCEGLI, "primario")
        imposta_icona(self.btn_scegli, "cartella", "su_primario")
        pulsanti.addWidget(self.btn_riprova)
        pulsanti.addWidget(self.btn_scegli)
        pulsanti.addStretch(1)
        lay.addLayout(pulsanti)
        riga.addWidget(card)
        riga.addStretch(1)
        radice.addLayout(riga)
        radice.addStretch(2)
        self.btn_scegli.clicked.connect(self.scegli)
        self.btn_riprova.clicked.connect(self.riprova)

    def mostra(self, cartelle_livelli: list[str], cercato_in: str, errore: str = "") -> None:
        self.lbl_testo.setText(testi.CARTELLA_TESTO.format(cartelle=", ".join(cartelle_livelli)))
        self.lbl_percorso.setText(testi.CARTELLA_CERCATO_IN.format(percorso=cercato_in))
        self.lbl_errore.setText(errore)
        self.lbl_errore.setVisible(bool(errore))
        imposta_ruolo(self.lbl_errore, "errore")
