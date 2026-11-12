"""Schermata delle impostazioni: tema, suoni, avanzamento, cartelle, dati."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from .. import NOME_APP, VERSIONE, testi
from ..persistenza import Impostazioni
from .componenti import (Card, EtichettaElisa, Interruttore, Segmenti, contenitore_centrato, etichetta,
                         pulsante, separatore)
from .grafica import imposta_icona
from .schermata_home import etichetta_sezione


def riga_impostazione(titolo: str, descrizione: str, *controlli: QWidget,
                      percorso: bool = False) -> tuple[QWidget, object]:
    """Riga con titolo e descrizione a sinistra e i controlli a destra.
    Con ``percorso=True`` la descrizione è un percorso accorciato al centro."""
    riga = QWidget()
    lay = QHBoxLayout(riga)
    lay.setContentsMargins(0, 12, 0, 12)
    lay.setSpacing(16)
    testi_col = QVBoxLayout()
    testi_col.setSpacing(2)
    testi_col.addWidget(etichetta(titolo, "forte"))
    if percorso:
        descr = EtichettaElisa(descrizione, "secondario", Qt.TextElideMode.ElideMiddle)
    else:
        descr = etichetta(descrizione, "secondario", a_capo=True)
    testi_col.addWidget(descr)
    lay.addLayout(testi_col, 1)
    for c in controlli:
        lay.addWidget(c, 0, Qt.AlignmentFlag.AlignVCenter)
    return riga, descr


class SchermataImpostazioni(QWidget):
    """Preferenze dell'utente. Ogni modifica viene salvata subito."""

    indietro = Signal()
    tema_cambiato = Signal(str)
    suoni_cambiati = Signal(bool)
    auto_cambiato = Signal(bool)
    scegli_cartella = Signal()
    cartella_predefinita = Signal()
    apri_cartella_dati = Signal()
    azzera_storico = Signal()
    svuota_classifica = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("schermata")
        self._costruisci()

    def _costruisci(self):
        radice = QVBoxLayout(self)
        radice.setContentsMargins(30, 22, 30, 22)
        radice.setSpacing(6)

        testa = QHBoxLayout()
        testa.setContentsMargins(10, 0, 10, 0)
        btn = pulsante(testi.INDIETRO, "fantasma")
        imposta_icona(btn, "indietro", "testo_secondario")
        btn.clicked.connect(self.indietro)
        testa.addWidget(btn)
        testa.addSpacing(8)
        testa.addWidget(etichetta(testi.IMPOSTAZIONI_TITOLO, "titolo"))
        testa.addStretch(1)
        radice.addLayout(testa)
        radice.addSpacing(6)

        scorrimento = QScrollArea()
        scorrimento.setWidgetResizable(True)
        scorrimento.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        carte = QWidget()
        colonna = QVBoxLayout(carte)
        colonna.setContentsMargins(0, 0, 0, 0)
        colonna.setSpacing(0)

        # Aspetto e partita
        card = Card(padding=22)
        lay = card.lay
        lay.setSpacing(0)
        lay.addWidget(etichetta_sezione(testi.IMP_ASPETTO))
        self.seg_tema = Segmenti([("chiaro", testi.IMP_TEMA_CHIARO), ("scuro", testi.IMP_TEMA_SCURO)],
                                 altezza=40)
        self.seg_tema.setFixedWidth(220)
        lay.addWidget(riga_impostazione(testi.IMP_TEMA, testi.IMP_TEMA_DESCR, self.seg_tema)[0])
        lay.addWidget(separatore())
        lay.addSpacing(14)
        lay.addWidget(etichetta_sezione(testi.IMP_GIOCO))
        self.int_suoni = Interruttore()
        lay.addWidget(riga_impostazione(testi.IMP_SUONI, testi.IMP_SUONI_DESCR, self.int_suoni)[0])
        lay.addWidget(separatore())
        self.int_auto = Interruttore()
        lay.addWidget(riga_impostazione(testi.IMP_AUTO, testi.IMP_AUTO_DESCR, self.int_auto)[0])
        lay.addWidget(separatore())
        self.btn_storico = pulsante(testi.IMP_AZZERA_STORICO)
        imposta_icona(self.btn_storico, "ricarica", "testo_secondario")
        riga, self.descr_storico = riga_impostazione(testi.IMP_STORICO, testi.IMP_AZZERA_STORICO_DESCR,
                                                     self.btn_storico)
        lay.addWidget(riga)
        colonna.addWidget(card)

        # Dati
        card = Card(padding=22)
        lay = card.lay
        lay.setSpacing(0)
        lay.addWidget(etichetta_sezione(testi.IMP_DATI))
        self.btn_cartella = pulsante(testi.IMP_CARTELLA_SCEGLI)
        imposta_icona(self.btn_cartella, "cartella", "testo_secondario")
        self.btn_predefinita = pulsante(testi.IMP_CARTELLA_PREDEFINITA, "fantasma")
        riga, self.lbl_cartella = riga_impostazione(testi.IMP_CARTELLA, "", self.btn_predefinita,
                                                    self.btn_cartella, percorso=True)
        lay.addWidget(riga)
        self.lbl_info_cartella = etichetta("", "terziario", a_capo=True)
        self.lbl_info_cartella.setContentsMargins(0, 0, 0, 10)
        lay.addWidget(self.lbl_info_cartella)
        lay.addWidget(separatore())
        self.btn_apri = pulsante(testi.IMP_APRI_CARTELLA)
        imposta_icona(self.btn_apri, "cartella", "testo_secondario")
        self.btn_svuota = pulsante(testi.IMP_SVUOTA_CLASSIFICA, "pericolo")
        riga, self.lbl_dati = riga_impostazione(testi.IMP_SALVATAGGI, "", self.btn_svuota, self.btn_apri,
                                                percorso=True)
        lay.addWidget(riga)
        colonna.addWidget(card)

        versione = etichetta(testi.IMP_INFO_VERSIONE.format(app=NOME_APP, v=VERSIONE), "terziario")
        versione.setAlignment(Qt.AlignmentFlag.AlignCenter)
        versione.setContentsMargins(0, 8, 0, 8)
        colonna.addWidget(versione)
        colonna.addStretch(1)
        interno = contenitore_centrato(carte, 900)
        scorrimento.setWidget(interno)
        radice.addWidget(scorrimento, 1)

        self.seg_tema.cambiato.connect(self.tema_cambiato)
        self.int_suoni.toggled.connect(self.suoni_cambiati)
        self.int_auto.toggled.connect(self.auto_cambiato)
        self.btn_cartella.clicked.connect(self.scegli_cartella)
        self.btn_predefinita.clicked.connect(self.cartella_predefinita)
        self.btn_apri.clicked.connect(self.apri_cartella_dati)
        self.btn_storico.clicked.connect(self.azzera_storico)
        self.btn_svuota.clicked.connect(self.svuota_classifica)

    def mostra(self, imp: Impostazioni, cartella_bandiere: str, info_cartella: str, dettagli_anomalie: str,
               cartella_dati: str) -> None:
        self.seg_tema.imposta_valore(imp.tema)
        self.int_suoni.imposta(imp.suoni)
        self.int_auto.imposta(imp.avanzamento_automatico)
        self.lbl_cartella.setText(cartella_bandiere)
        self.lbl_info_cartella.setText(info_cartella)
        self.lbl_info_cartella.setToolTip(dettagli_anomalie)
        self.btn_predefinita.setVisible(bool(imp.cartella_bandiere))
        self.lbl_dati.setText(cartella_dati)
        self.descr_storico.setText(testi.IMP_AZZERA_STORICO_DESCR)

    def segnala_storico_azzerato(self) -> None:
        self.descr_storico.setText(testi.IMP_STORICO_AZZERATO + " ✓")
