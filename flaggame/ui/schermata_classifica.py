"""Schermata della classifica, filtrabile per modalità, livello e area."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtGui import QPen
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QHeaderView, QStackedWidget,
                               QStyledItemDelegate, QStyleOptionViewItem, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from .. import testi
from ..classifica import Classifica, Risultato
from ..partita import formatta_tempo
from .componenti import Card, Segmenti, etichetta, pulsante
from .grafica import disegna_icona, imposta_icona
from .schermata_home import crea_combo, etichetta_sezione
from .tema import GRASSETTO, SEMIBOLD, font, tema

TOP = 10
TUTTE = "__tutte__"
RUOLO_EVIDENZIA = Qt.ItemDataRole.UserRole + 1


class DelegatoClassifica(QStyledItemDelegate):
    """Disegna lo sfondo della riga appena salvata e la linea tra le righe
    (il foglio di stile ignorerebbe il colore di sfondo delle celle)."""

    def paint(self, painter, option, index):
        painter.save()
        if index.data(RUOLO_EVIDENZIA):
            painter.fillRect(option.rect, tema().c("primario_tenue"))
        painter.setPen(QPen(tema().c("bordo"), 1))
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        painter.restore()
        opzione = QStyleOptionViewItem(option)
        opzione.rect = option.rect.adjusted(10, 0, -10, 0)
        super().paint(painter, opzione, index)

    def sizeHint(self, option, index):
        base = super().sizeHint(option, index)
        return QSize(base.width() + 28, base.height())


def icona_medaglia(posizione: int, dpr: float) -> QIcon:
    """Cerchio oro/argento/bronzo con il numero della posizione."""
    colore = {1: "oro", 2: "argento", 3: "bronzo"}[posizione]
    lato = 28
    pix = QPixmap(int(lato * dpr), int(lato * dpr))
    pix.fill(Qt.GlobalColor.transparent)
    pix.setDevicePixelRatio(dpr)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(tema().c(colore))
    p.drawEllipse(QRectF(1, 1, lato - 2, lato - 2))
    p.setPen(QColor("#FFFFFF"))
    p.setFont(font(14, GRASSETTO))
    p.drawText(QRectF(0, 0, lato, lato), Qt.AlignmentFlag.AlignCenter, str(posizione))
    p.end()
    return QIcon(pix)


class VuotoClassifica(QWidget):
    """Messaggio mostrato quando non ci sono risultati."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.addStretch(1)
        self.icona = QWidget()
        self.icona.setFixedSize(64, 64)
        self.icona.paintEvent = self._disegna_icona
        lay.addWidget(self.icona, 0, Qt.AlignmentFlag.AlignHCenter)
        titolo = etichetta(testi.CLASSIFICA_VUOTA, "forte")
        titolo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(titolo)
        sotto = etichetta(testi.CLASSIFICA_VUOTA_SUGGERIMENTO, "secondario")
        sotto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sotto)
        lay.addStretch(2)

    def _disegna_icona(self, evento):
        p = QPainter(self.icona)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(tema().c("superficie_alt"))
        p.drawEllipse(QRectF(0, 0, 64, 64))
        disegna_icona(p, "trofeo", QRectF(16, 16, 32, 32), tema().c("testo_terziario"), 2.0)


class SchermataClassifica(QWidget):
    """Top 10 per combinazione, con il risultato appena salvato evidenziato."""

    indietro = Signal()

    def __init__(self, classifica: Classifica, parent=None):
        super().__init__(parent)
        self.setObjectName("schermata")
        self.classifica = classifica
        self.evidenzia: str | None = None
        self._livelli: list[tuple[str, str]] = []
        self._aree: list[tuple[str, str]] = []
        self._costruisci()

    def _costruisci(self):
        radice = QVBoxLayout(self)
        radice.setContentsMargins(30, 22, 30, 22)
        radice.setSpacing(6)

        testa = QHBoxLayout()
        testa.setContentsMargins(10, 0, 10, 0)
        self.btn_indietro = pulsante(testi.INDIETRO, "fantasma")
        imposta_icona(self.btn_indietro, "indietro", "testo_secondario")
        self.btn_indietro.clicked.connect(self.indietro)
        testa.addWidget(self.btn_indietro)
        testa.addSpacing(8)
        titoli = QVBoxLayout()
        titoli.setSpacing(0)
        titoli.addWidget(etichetta(testi.CLASSIFICA_TITOLO, "titolo"))
        titoli.addWidget(etichetta(testi.CLASSIFICA_SOTTOTITOLO, "sottotitolo"))
        testa.addLayout(titoli)
        testa.addStretch(1)
        radice.addLayout(testa)
        radice.addSpacing(10)

        filtri = QHBoxLayout()
        filtri.setContentsMargins(10, 0, 10, 0)
        filtri.setSpacing(24)
        colonna = QVBoxLayout()
        colonna.setSpacing(6)
        colonna.addWidget(etichetta_sezione("Modalità"))
        self.seg_modalita = Segmenti([("flag", testi.MODALITA["flag"]),
                                      ("country", testi.MODALITA["country"]),
                                      (TUTTE, testi.CLASSIFICA_TUTTE_MODALITA)], altezza=42)
        colonna.addWidget(self.seg_modalita)
        filtri.addLayout(colonna)
        colonna = QVBoxLayout()
        colonna.setSpacing(6)
        colonna.addWidget(etichetta_sezione(testi.HOME_SEZIONE_LIVELLO))
        self.combo_livello = crea_combo()
        self.combo_livello.setMinimumHeight(42)
        self.combo_livello.setMinimumWidth(180)
        colonna.addWidget(self.combo_livello)
        filtri.addLayout(colonna)
        colonna = QVBoxLayout()
        colonna.setSpacing(6)
        colonna.addWidget(etichetta_sezione(testi.HOME_SEZIONE_AREA))
        self.combo_area = crea_combo()
        self.combo_area.setMinimumHeight(42)
        self.combo_area.setMinimumWidth(200)
        colonna.addWidget(self.combo_area)
        filtri.addLayout(colonna)
        filtri.addStretch(1)
        radice.addLayout(filtri)
        radice.addSpacing(6)

        card = Card(padding=14)
        lc = card.lay
        self.pagine = QStackedWidget()
        self.tabella = QTableWidget()
        self.tabella.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabella.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tabella.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabella.setShowGrid(False)
        self.tabella.setWordWrap(False)
        self.tabella.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.tabella.verticalHeader().setVisible(False)
        self.tabella.verticalHeader().setDefaultSectionSize(48)
        self.tabella.setIconSize(QSize(28, 28))
        self.tabella.horizontalHeader().setHighlightSections(False)
        self.tabella.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tabella.setItemDelegate(DelegatoClassifica(self.tabella))
        self.pagine.addWidget(self.tabella)
        self.vuoto = VuotoClassifica()
        self.pagine.addWidget(self.vuoto)
        lc.addWidget(self.pagine, 1)
        self.lbl_posizione = etichetta("", "info")
        self.lbl_posizione.hide()
        lc.addWidget(self.lbl_posizione, 0, Qt.AlignmentFlag.AlignLeft)
        radice.addWidget(card, 1)

        self.seg_modalita.cambiato.connect(lambda *_: self.aggiorna())
        self.combo_livello.currentIndexChanged.connect(lambda *_: self.aggiorna())
        self.combo_area.currentIndexChanged.connect(lambda *_: self.aggiorna())
        tema().cambiato.connect(lambda *_: self.aggiorna())

    # ------------------------------------------------------------- dati

    def configura(self, livelli: list[tuple[str, str]], aree: list[tuple[str, str]]) -> None:
        self._livelli = livelli
        self._aree = aree
        for combo, voci, tutte in ((self.combo_livello, livelli, testi.CLASSIFICA_TUTTI_LIVELLI),
                                   (self.combo_area, aree, testi.CLASSIFICA_TUTTE_AREE)):
            combo.blockSignals(True)
            combo.clear()
            for chiave, nome in voci:
                combo.addItem(nome, chiave)
            combo.addItem(tutte, TUTTE)
            combo.blockSignals(False)

    def mostra(self, modalita: str | None, livello: str | None, area: str | None,
               evidenzia: str | None = None) -> None:
        """Seleziona la combinazione da mostrare (None = tutte)."""
        self.evidenzia = evidenzia
        self.seg_modalita.blockSignals(True)
        self.seg_modalita.imposta_valore(modalita or TUTTE)
        self.seg_modalita.blockSignals(False)
        for combo, valore in ((self.combo_livello, livello), (self.combo_area, area)):
            combo.blockSignals(True)
            indice = combo.findData(valore or TUTTE)
            combo.setCurrentIndex(max(0, indice))
            combo.blockSignals(False)
        self.aggiorna()

    def _filtri(self) -> dict:
        def valore(v):
            return None if v in (None, TUTTE) else v
        return {"modalita": valore(self.seg_modalita.valore()),
                "livello": valore(self.combo_livello.currentData()),
                "area": valore(self.combo_area.currentData())}

    def _nome(self, voci, chiave) -> str:
        return dict(voci).get(chiave, chiave)

    def aggiorna(self) -> None:
        filtri = self._filtri()
        righe = self.classifica.filtra(**filtri)
        visibili: list[tuple[int, Risultato] | None] = list(enumerate(righe[:TOP], start=1))
        posizione_nuovo = None
        if self.evidenzia:
            posizione_nuovo = next((i for i, r in enumerate(righe, start=1) if r.id == self.evidenzia), None)
            if posizione_nuovo and posizione_nuovo > TOP:
                visibili.append(None)  # riga "…"
                visibili.append((posizione_nuovo, righe[posizione_nuovo - 1]))
        if posizione_nuovo:
            self.lbl_posizione.setText(testi.CLASSIFICA_TUO_RISULTATO.format(pos=posizione_nuovo))
            self.lbl_posizione.show()
        else:
            self.lbl_posizione.hide()

        if not righe:
            self.pagine.setCurrentWidget(self.vuoto)
            return
        self.pagine.setCurrentWidget(self.tabella)

        colonne = ["pos", "nome", "percentuale", "tempo", "data"]
        if filtri["modalita"] is None:
            colonne.append("modalita")
        if filtri["livello"] is None:
            colonne.append("livello")
        if filtri["area"] is None:
            colonne.append("area")
        t = self.tabella
        t.clear()
        t.clearSpans()
        t.setColumnCount(len(colonne))
        t.setHorizontalHeaderLabels([testi.CLASSIFICA_COLONNE[c].upper() for c in colonne])
        t.setRowCount(len(visibili))
        dpr = self.devicePixelRatioF()
        for riga, voce in enumerate(visibili):
            if voce is None:
                item = QTableWidgetItem("…")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(tema().c("testo_terziario"))
                t.setItem(riga, 0, item)
                t.setSpan(riga, 0, 1, len(colonne))
                t.setRowHeight(riga, 30)
                continue
            pos, r = voce
            valori = {
                "pos": "" if pos <= 3 else str(pos),
                "nome": r.nome,
                "percentuale": f"{round(r.percentuale)}%   ({r.giuste}/{r.totale})",
                "tempo": formatta_tempo(r.tempo),
                "data": self._data(r.data),
                "modalita": testi.MODALITA.get(r.modalita, r.modalita),
                "livello": self._nome(self._livelli, r.livello),
                "area": self._nome(self._aree, r.area),
            }
            for col, chiave in enumerate(colonne):
                item = QTableWidgetItem(valori[chiave])
                allinea = Qt.AlignmentFlag.AlignVCenter
                allinea |= Qt.AlignmentFlag.AlignCenter if chiave == "pos" else Qt.AlignmentFlag.AlignLeft
                item.setTextAlignment(allinea)
                if chiave == "pos" and pos <= 3:
                    item.setIcon(icona_medaglia(pos, dpr))
                if chiave in ("nome", "percentuale"):
                    f = font(15, GRASSETTO if chiave == "percentuale" else SEMIBOLD)
                    item.setFont(f)
                else:
                    item.setForeground(tema().c("testo_secondario"))
                if r.id == self.evidenzia:
                    item.setData(RUOLO_EVIDENZIA, True)
                    item.setForeground(tema().c("testo"))
                t.setItem(riga, col, item)

        testa = t.horizontalHeader()
        testa.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for col, chiave in enumerate(colonne):
            if chiave == "pos":
                testa.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
                t.setColumnWidth(col, 64)
            elif chiave == "nome":
                testa.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
            else:
                testa.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        # la posizione è centrata anche nell'intestazione
        intest = t.horizontalHeaderItem(0)
        if intest:
            intest.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    @staticmethod
    def _data(iso: str) -> str:
        try:
            return datetime.fromisoformat(iso).strftime(testi.CLASSIFICA_FORMATO_DATA)
        except ValueError:
            return iso
