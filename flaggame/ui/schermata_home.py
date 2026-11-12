"""Schermata iniziale: scelta di modalità, livello e area."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QButtonGroup, QComboBox, QHBoxLayout, QLabel, QListView,
                               QSizePolicy, QVBoxLayout, QWidget)

from .. import testi
from ..dati import AREA_MONDO
from ..generatore import InfoCombinazione
from .componenti import (CardModalita, Segmenti, contenitore_centrato, etichetta, imposta_ruolo,
                         pulsante)
from .grafica import illustrazione_country, illustrazione_flag, imposta_icona, pixmap_logo


def crea_combo() -> QComboBox:
    """QComboBox con una vista a elenco (necessaria per lo stile delle voci)."""
    combo = QComboBox()
    combo.setView(QListView())
    combo.setCursor(Qt.CursorShape.PointingHandCursor)
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
    return combo


def etichetta_sezione(testo: str) -> QLabel:
    lbl = etichetta(testo.upper(), "sezione")
    f = lbl.font()
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
    lbl.setFont(f)
    return lbl


class Logo(QLabel):
    """Logo disegnato, ridisegnato se cambia la densità dello schermo."""

    def __init__(self, lato: int, parent=None):
        super().__init__(parent)
        self.lato = lato
        self.setFixedSize(lato, lato)
        self._aggiorna()

    def _aggiorna(self):
        self.setPixmap(pixmap_logo(self.lato, self.devicePixelRatioF()))

    def showEvent(self, evento):
        self._aggiorna()
        super().showEvent(evento)


class SchermataHome(QWidget):
    """Home: titolo, card delle modalità, livello, area e pulsanti principali."""

    gioca = Signal(str, str, str)       # modalità, livello, area
    apri_classifica = Signal()
    apri_impostazioni = Signal()
    selezione_cambiata = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("schermata")
        self._info: Callable[[str, str], InfoCombinazione] | None = None
        self._livelli: list[tuple[str, str]] = []
        self._aree: list[tuple[str, str]] = []
        self._livello_aree = ""   # livello per cui è stato riempito il menu delle aree
        self._costruisci()

    # ------------------------------------------------------------- layout

    def _costruisci(self):
        contenuto = QWidget()
        lay = QVBoxLayout(contenuto)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # intestazione
        testa = QHBoxLayout()
        testa.setSpacing(16)
        testa.addWidget(Logo(60))
        titoli = QVBoxLayout()
        titoli.setSpacing(2)
        titoli.addWidget(etichetta(testi.TITOLO_APP, "titolo"))
        titoli.addWidget(etichetta(testi.SOTTOTITOLO_APP, "sottotitolo"))
        testa.addLayout(titoli)
        testa.addStretch(1)
        self.btn_classifica = pulsante(testi.HOME_CLASSIFICA)
        imposta_icona(self.btn_classifica, "trofeo", "testo_secondario")
        self.btn_impostazioni = pulsante(testi.HOME_IMPOSTAZIONI)
        imposta_icona(self.btn_impostazioni, "ingranaggio", "testo_secondario")
        testa.addWidget(self.btn_classifica)
        testa.addWidget(self.btn_impostazioni)
        lay.addLayout(testa)
        lay.addSpacing(26)

        # modalità
        sez = etichetta_sezione(testi.HOME_SEZIONE_MODALITA)
        sez.setContentsMargins(4, 0, 0, 0)
        lay.addWidget(sez)
        lay.addSpacing(2)
        carte = QHBoxLayout()
        carte.setContentsMargins(-6, 0, -6, 0)
        carte.setSpacing(8)
        self.card_flag = CardModalita(testi.MODALITA["flag"], testi.DESCRIZIONE_MODALITA["flag"],
                                      illustrazione_flag)
        self.card_country = CardModalita(testi.MODALITA["country"], testi.DESCRIZIONE_MODALITA["country"],
                                         illustrazione_country)
        self.gruppo_modalita = QButtonGroup(self)
        self.gruppo_modalita.setExclusive(True)
        self.gruppo_modalita.addButton(self.card_flag)
        self.gruppo_modalita.addButton(self.card_country)
        self.card_flag.setChecked(True)
        carte.addWidget(self.card_flag)
        carte.addWidget(self.card_country)
        lay.addLayout(carte, 1)
        lay.addStretch(0)  # riceve spazio solo quando le card hanno raggiunto l'altezza massima
        lay.addSpacing(18)

        # livello e area
        scelte = QHBoxLayout()
        scelte.setSpacing(32)
        col_liv = QVBoxLayout()
        col_liv.setSpacing(8)
        col_liv.addWidget(etichetta_sezione(testi.HOME_SEZIONE_LIVELLO))
        self.segmenti_livello = Segmenti([], altezza=46, pixel_font=15)
        self.segmenti_livello.setMinimumWidth(460)
        col_liv.addWidget(self.segmenti_livello)
        self.descr_livello = etichetta("", "terziario")
        col_liv.addWidget(self.descr_livello)
        scelte.addLayout(col_liv, 3)

        col_area = QVBoxLayout()
        col_area.setSpacing(8)
        col_area.addWidget(etichetta_sezione(testi.HOME_SEZIONE_AREA))
        self.combo_area = crea_combo()
        self.combo_area.setMinimumWidth(240)
        self.combo_area.setMinimumHeight(46)
        col_area.addWidget(self.combo_area)
        col_area.addWidget(etichetta(" ", "terziario"))
        scelte.addLayout(col_area, 2)
        lay.addLayout(scelte)
        lay.addSpacing(22)

        # barra in basso
        barra = QHBoxLayout()
        barra.setSpacing(14)
        self.info = etichetta("", "info")
        self.info.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        barra.addWidget(self.info)
        barra.addStretch(1)
        suggerimento = etichetta(testi.HOME_SUGGERIMENTO_TASTI, "terziario")
        barra.addWidget(suggerimento)
        self.btn_gioca = pulsante(testi.HOME_GIOCA, "grande")
        imposta_icona(self.btn_gioca, "gioca", "su_primario", 18)
        self.btn_gioca.setMinimumWidth(190)
        barra.addWidget(self.btn_gioca)
        lay.addLayout(barra)

        esterno = QVBoxLayout(self)
        esterno.setContentsMargins(40, 30, 40, 30)
        esterno.addWidget(contenitore_centrato(contenuto, 1120))

        # segnali
        self.gruppo_modalita.buttonToggled.connect(lambda *_: self._aggiorna())
        self.segmenti_livello.cambiato.connect(lambda *_: self._aggiorna())
        self.combo_area.currentIndexChanged.connect(lambda *_: self._aggiorna())
        self.btn_gioca.clicked.connect(self._gioca)
        self.btn_classifica.clicked.connect(self.apri_classifica)
        self.btn_impostazioni.clicked.connect(self.apri_impostazioni)

    # -------------------------------------------------------------- dati

    def configura(self, livelli: list[tuple[str, str]], aree: list[tuple[str, str]],
                  info: Callable[[str, str], InfoCombinazione],
                  modalita: str, livello: str, area: str) -> None:
        """Imposta livelli e aree disponibili e la selezione iniziale."""
        self._info = info
        self._livelli = livelli
        self._aree = aree
        self.segmenti_livello.blockSignals(True)
        self.segmenti_livello.imposta_voci(livelli)
        for id_liv, _ in livelli:
            self.segmenti_livello.imposta_abilitato(id_liv, info(id_liv, AREA_MONDO).giocabile)
        ids = [l[0] for l in livelli]
        if livello not in ids or not info(livello, AREA_MONDO).giocabile:
            livello = next((l for l in ids if info(l, AREA_MONDO).giocabile), ids[0] if ids else "")
        self.segmenti_livello.imposta_valore(livello)
        self.segmenti_livello.blockSignals(False)
        (self.card_country if modalita == "country" else self.card_flag).setChecked(True)
        self._riempi_aree(area)
        self._aggiorna()

    def _riempi_aree(self, area_preferita: str | None = None) -> None:
        """Riempie il menu delle aree, disattivando quelle senza bandiere nel livello scelto."""
        livello = self.segmenti_livello.valore() if self._livelli else ""
        self._livello_aree = livello
        attuale = area_preferita or self.area()
        self.combo_area.blockSignals(True)
        self.combo_area.clear()
        modello = self.combo_area.model()
        for i, (id_area, nome) in enumerate(self._aree):
            info = self._info(livello, id_area) if self._info else None
            giocabile = bool(info and info.giocabile)
            testo = nome if giocabile else testi.HOME_AREA_NON_DISPONIBILE.format(area=nome)
            self.combo_area.addItem(testo, id_area)
            modello.item(i).setEnabled(giocabile)
        indice = self.combo_area.findData(attuale)
        if indice < 0 or not modello.item(indice).isEnabled():
            indice = 0
        self.combo_area.setCurrentIndex(indice)
        self.combo_area.blockSignals(False)

    # ---------------------------------------------------------- selezione

    def modalita(self) -> str:
        return "country" if self.card_country.isChecked() else "flag"

    def livello(self) -> str:
        return self.segmenti_livello.valore()

    def area(self) -> str:
        return self.combo_area.currentData() or AREA_MONDO

    def _aggiorna(self) -> None:
        if not self._info or not self._livelli:
            return
        if self.livello() != self._livello_aree:
            self._riempi_aree()
        livello, area = self.livello(), self.area()
        self.descr_livello.setText(testi.DESCRIZIONE_LIVELLI.get(livello, ""))
        info = self._info(livello, area)
        if not info.giocabile:
            self.info.setText(testi.HOME_NON_GIOCABILE)
            imposta_ruolo(self.info, "errore")
        elif info.ridotta:
            testo = (testi.HOME_AVVISO_UNA if info.domande == 1
                     else testi.HOME_AVVISO_POCHE.format(n=info.domande))
            self.info.setText(testo)
            imposta_ruolo(self.info, "avviso")
        else:
            self.info.setText(testi.HOME_INFO_DISPONIBILI.format(n=info.disponibili, d=info.domande))
            imposta_ruolo(self.info, "info")
        self.btn_gioca.setEnabled(info.giocabile)
        self.selezione_cambiata.emit(self.modalita(), livello, area)

    def _gioca(self) -> None:
        if self.btn_gioca.isEnabled():
            self.gioca.emit(self.modalita(), self.livello(), self.area())

    def keyPressEvent(self, evento):
        if evento.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._gioca()
        else:
            super().keyPressEvent(evento)
