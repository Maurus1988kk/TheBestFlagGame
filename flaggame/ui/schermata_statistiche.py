"""Schermata delle statistiche personali: riepilogo, livelli, continenti,
andamento delle ultime partite e bandiere da ripassare."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from PySide6.QtCore import QEvent, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QGridLayout, QHBoxLayout, QScrollArea, QSizePolicy, QStackedWidget,
                               QToolTip, QVBoxLayout, QWidget)

from .. import testi
from ..classifica import Classifica
from ..dati import AREA_MONDO, Catalogo
from ..statistiche import BandieraDaRipassare, PuntoAndamento, Quota, calcola, giocatori
from .componenti import Card, EtichettaElisa, VistaBandiera, contenitore_centrato, etichetta, pulsante
from .grafica import disegna_icona, imposta_icona
from .immagini import CacheImmagini
from .schermata_home import crea_combo, etichetta_sezione
from .tema import SEMIBOLD, font, tema


# --------------------------------------------------------------------------- #
# Grafici
# --------------------------------------------------------------------------- #

class GraficoQuote(QWidget):
    """Una barra orizzontale per categoria con la percentuale di risposte giuste.

    Una sola serie, quindi un solo colore (il primario) e nessuna legenda: il
    titolo della card dice cosa si vede. I valori sono scritti con i colori del
    testo; il dettaglio (giuste su totale) compare passando il mouse.
    """

    ALTEZZA_RIGA = 34
    SPESSORE = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self._righe: list[tuple[str, Quota]] = []
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def imposta(self, righe: list[tuple[str, Quota]]) -> None:
        self._righe = list(righe)
        self.setFixedHeight(max(1, len(self._righe)) * self.ALTEZZA_RIGA)
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(280, max(1, len(self._righe)) * self.ALTEZZA_RIGA)

    def _colonne(self) -> tuple[float, float]:
        """Larghezza della colonna dei nomi e di quella dei valori."""
        nomi = QFontMetrics(font(14))
        # +4 di margine: con la larghezza esatta l'arrotondamento può far scattare i "…"
        larghezza_nomi = max((nomi.horizontalAdvance(n) for n, _ in self._righe), default=0) + 14 + 4
        larghezza_nomi = min(larghezza_nomi, self.width() * 0.45)
        larghezza_valori = max(QFontMetrics(font(14, SEMIBOLD)).horizontalAdvance("100%"),
                               QFontMetrics(font(13)).horizontalAdvance(testi.STAT_NON_GIOCATO)) + 12
        return larghezza_nomi, larghezza_valori

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = tema()
        h = self.ALTEZZA_RIGA
        lw, vw = self._colonne()
        x0, x1 = lw, self.width() - vw
        f_nome, f_valore, f_vuoto = font(14), font(14, SEMIBOLD), font(13)
        fm_nome = QFontMetrics(f_nome)
        for i, (nome, quota) in enumerate(self._righe):
            y = i * h
            p.setFont(f_nome)
            p.setPen(t.c("testo_secondario"))
            p.drawText(QRectF(0, y, lw - 14, h), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       fm_nome.elidedText(nome, Qt.TextElideMode.ElideRight, int(lw - 14)))
            barra = QRectF(x0, y + (h - self.SPESSORE) / 2, max(0.0, x1 - x0), self.SPESSORE)
            raggio = self.SPESSORE / 2
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(t.c("primario_tenue"))
            p.drawRoundedRect(barra, raggio, raggio)
            valore = QRectF(x1 + 12, y, vw - 12, h)
            if quota.totale:
                larghezza = barra.width() * quota.percentuale / 100
                if larghezza > 0:
                    p.setBrush(t.c("primario"))
                    p.drawRoundedRect(QRectF(barra.left(), barra.top(), max(larghezza, self.SPESSORE),
                                             self.SPESSORE), raggio, raggio)
                p.setFont(f_valore)
                p.setPen(t.c("testo"))
                p.drawText(valore, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                           f"{round(quota.percentuale)}%")
            else:
                p.setFont(f_vuoto)
                p.setPen(t.c("testo_terziario"))
                p.drawText(valore, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                           testi.STAT_NON_GIOCATO)

    def event(self, evento):
        if evento.type() == QEvent.Type.ToolTip:
            i = int(evento.pos().y() // self.ALTEZZA_RIGA)
            if 0 <= i < len(self._righe):
                nome, q = self._righe[i]
                testo = (testi.STAT_QUOTA_TOOLTIP.format(nome=nome, g=q.giuste, t=q.totale,
                                                         p=round(q.percentuale))
                         if q.totale else testi.STAT_QUOTA_TOOLTIP_VUOTA.format(nome=nome))
                QToolTip.showText(evento.globalPos(), testo, self)
            else:
                QToolTip.hideText()
            return True
        return super().event(evento)


class GraficoAndamento(QWidget):
    """Percentuale di risposte giuste delle ultime partite (linea con punti).

    Linea di 2 px, punti con un anello del colore della card, griglia sottile
    a 0/50/100%, etichetta solo sull'ultimo punto; il resto nel tooltip.
    """

    def __init__(self, descrivi: Callable[[PuntoAndamento], str], parent=None):
        super().__init__(parent)
        self._descrivi = descrivi
        self._punti: list[PuntoAndamento] = []
        self._sopra = -1
        self.setMouseTracking(True)
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def imposta(self, punti: list[PuntoAndamento]) -> None:
        self._punti = list(punti)
        self._sopra = -1
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(420, 160)

    def _area(self) -> QRectF:
        sinistra = QFontMetrics(font(12)).horizontalAdvance("100%") + 12
        return QRectF(sinistra, 12, max(1.0, self.width() - sinistra - 14), max(1.0, self.height() - 22))

    def _posizioni(self) -> list[QPointF]:
        a = self._area()
        n = len(self._punti)
        if n == 1:
            xs = [a.center().x()]
        else:
            xs = [a.left() + i * a.width() / (n - 1) for i in range(n)]
        return [QPointF(x, a.bottom() - p.percentuale / 100 * a.height()) for x, p in zip(xs, self._punti)]

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = tema()
        a = self._area()
        f_asse = font(12)
        p.setFont(f_asse)
        for valore in (0, 50, 100):
            y = round(a.bottom() - valore / 100 * a.height()) + 0.5
            p.setPen(QPen(t.c("bordo"), 1))
            p.drawLine(QPointF(a.left(), y), QPointF(a.right(), y))
            p.setPen(t.c("testo_terziario"))
            p.drawText(QRectF(0, y - 10, a.left() - 8, 20),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{valore}%")
        if not self._punti:
            return
        pos = self._posizioni()
        colore = t.c("primario")
        if len(pos) > 1:
            linea = QPainterPath(pos[0])
            for q in pos[1:]:
                linea.lineTo(q)
            area = QPainterPath(linea)
            area.lineTo(pos[-1].x(), a.bottom())
            area.lineTo(pos[0].x(), a.bottom())
            area.closeSubpath()
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(t.c("primario", 26))
            p.drawPath(area)
            p.setPen(QPen(colore, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(linea)
        for i, q in enumerate(pos):
            raggio = 5.5 if i == self._sopra else 4.0
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(t.c("superficie"))
            p.drawEllipse(q, raggio + 2, raggio + 2)
            p.setBrush(colore)
            p.drawEllipse(q, raggio, raggio)
        # etichetta sull'ultimo punto: dal lato opposto a quello da cui arriva la
        # linea (così non la copre), e comunque dentro il widget
        ultimo = pos[-1]
        testo = f"{round(self._punti[-1].percentuale)}%"
        f = font(13, SEMIBOLD)
        larghezza = QFontMetrics(f).horizontalAdvance(testo) + 4
        arriva_dall_alto = len(pos) > 1 and pos[-2].y() < ultimo.y()
        sopra, sotto = ultimo.y() - 28, ultimo.y() + 8
        if arriva_dall_alto:
            y = sotto if sotto + 20 <= self.height() else sopra
        else:
            y = sopra if sopra >= 0 else sotto
        x = min(ultimo.x() - larghezza / 2, self.width() - larghezza)
        p.setFont(f)
        p.setPen(t.c("testo"))
        p.drawText(QRectF(x, y, larghezza, 20), Qt.AlignmentFlag.AlignCenter, testo)

    def mouseMoveEvent(self, evento):
        pos = self._posizioni() if self._punti else []
        x = evento.position().x()
        vicino = min(range(len(pos)), key=lambda i: abs(pos[i].x() - x), default=-1)
        soglia = max(14.0, self._area().width() / max(1, len(pos) - 1) / 2)
        if vicino >= 0 and abs(pos[vicino].x() - x) <= soglia:
            if vicino != self._sopra:
                self._sopra = vicino
                self.update()
            QToolTip.showText(evento.globalPosition().toPoint(), self._descrivi(self._punti[vicino]), self)
        elif self._sopra != -1:
            self._sopra = -1
            QToolTip.hideText()
            self.update()
        super().mouseMoveEvent(evento)

    def leaveEvent(self, evento):
        if self._sopra != -1:
            self._sopra = -1
            self.update()
        super().leaveEvent(evento)


# --------------------------------------------------------------------------- #
# Pezzi della schermata
# --------------------------------------------------------------------------- #

class TesseraStat(Card):
    """Card piccola con un numero: titolo, valore grande, riga di dettaglio."""

    def __init__(self, titolo: str, parent=None):
        super().__init__(parent, raggio=16, padding=16)
        self.lay.setSpacing(2)
        self.lay.addWidget(etichetta_sezione(titolo))
        self.lbl_valore = etichetta("", "valore_stat")
        self.lay.addWidget(self.lbl_valore)
        self.lbl_sotto = EtichettaElisa("", "terziario")
        self.lay.addWidget(self.lbl_sotto)

    def imposta(self, valore: str, sotto: str) -> None:
        self.lbl_valore.setText(valore)
        self.lbl_sotto.setText(sotto)


class RigaRipasso(QWidget):
    """Una bandiera da ripassare: miniatura, nome, errori, con cosa è stata scambiata."""

    def __init__(self, cache: CacheImmagini, immagine, nome: str, errori: str, scambio: str, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 6, 8, 6)
        lay.setSpacing(12)
        miniatura = VistaBandiera(cache, rapporto=1.5, riquadro=False)
        miniatura.setFixedSize(66, 44)
        miniatura.imposta(immagine)
        lay.addWidget(miniatura)
        colonna = QVBoxLayout()
        colonna.setSpacing(0)
        colonna.addWidget(EtichettaElisa(nome, "forte"))
        colonna.addWidget(EtichettaElisa(errori, "secondario"))
        colonna.addWidget(EtichettaElisa(scambio, "terziario"))
        lay.addLayout(colonna, 1)


class MessaggioVuoto(QWidget):
    """Icona in un cerchio con titolo e suggerimento."""

    def __init__(self, icona: str, titolo: str, sotto: str, parent=None):
        super().__init__(parent)
        self._icona = icona
        lay = QVBoxLayout(self)
        lay.addStretch(1)
        self.cerchio = QWidget()
        self.cerchio.setFixedSize(64, 64)
        self.cerchio.paintEvent = self._disegna
        lay.addWidget(self.cerchio, 0, Qt.AlignmentFlag.AlignHCenter)
        for testo, ruolo in ((titolo, "forte"), (sotto, "secondario")):
            lbl = etichetta(testo, ruolo)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(lbl)
        lay.addStretch(2)

    def _disegna(self, evento):
        p = QPainter(self.cerchio)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(tema().c("superficie_alt"))
        p.drawEllipse(QRectF(0, 0, 64, 64))
        disegna_icona(p, self._icona, QRectF(16, 16, 32, 32), tema().c("testo_terziario"), 2.0)


def card_sezione(titolo: str) -> tuple[Card, QVBoxLayout]:
    card = Card(padding=18)
    card.lay.setSpacing(8)
    card.lay.addWidget(etichetta_sezione(titolo))
    return card, card.lay


# --------------------------------------------------------------------------- #
# Schermata
# --------------------------------------------------------------------------- #

class SchermataStatistiche(QWidget):
    """Statistiche del giocatore scelto, calcolate dai risultati della classifica."""

    indietro = Signal()

    def __init__(self, classifica: Classifica, cache: CacheImmagini, parent=None):
        super().__init__(parent)
        self.setObjectName("schermata")
        self.classifica = classifica
        self.cache = cache
        self.catalogo: Catalogo | None = None
        self._livelli: list[tuple[str, str]] = []
        self._aree: list[tuple[str, str]] = []
        self._costruisci()

    # ------------------------------------------------------------- layout

    def _costruisci(self):
        radice = QVBoxLayout(self)
        radice.setContentsMargins(30, 22, 30, 22)
        radice.setSpacing(6)

        testa = QHBoxLayout()
        testa.setContentsMargins(10, 0, 10, 0)
        self.btn_indietro = pulsante(testi.INDIETRO, "fantasma")
        imposta_icona(self.btn_indietro, "indietro", "testo_secondario")
        self.btn_indietro.clicked.connect(self.indietro)
        testa.addWidget(self.btn_indietro, 0, Qt.AlignmentFlag.AlignTop)
        testa.addSpacing(8)
        titoli = QVBoxLayout()
        titoli.setSpacing(0)
        titoli.addWidget(etichetta(testi.STAT_TITOLO, "titolo"))
        titoli.addWidget(etichetta(testi.STAT_SOTTOTITOLO, "sottotitolo"))
        testa.addLayout(titoli)
        testa.addStretch(1)
        self.colonna_giocatore = QWidget()
        cg = QVBoxLayout(self.colonna_giocatore)
        cg.setContentsMargins(0, 0, 0, 0)
        cg.setSpacing(6)
        cg.addWidget(etichetta_sezione(testi.STAT_GIOCATORE))
        self.combo_giocatore = crea_combo()
        self.combo_giocatore.setMinimumHeight(42)
        self.combo_giocatore.setMinimumWidth(220)
        cg.addWidget(self.combo_giocatore)
        testa.addWidget(self.colonna_giocatore)
        radice.addLayout(testa)
        radice.addSpacing(6)

        self.pagine = QStackedWidget()
        radice.addWidget(self.pagine, 1)

        # pagina con le statistiche (scorrevole alle dimensioni piccole)
        scorrimento = QScrollArea()
        scorrimento.setWidgetResizable(True)
        scorrimento.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        contenuto = QWidget()
        colonna = QVBoxLayout(contenuto)
        colonna.setContentsMargins(0, 0, 0, 0)
        colonna.setSpacing(0)

        tessere = QHBoxLayout()
        tessere.setSpacing(0)
        self.t_partite = TesseraStat(testi.STAT_PARTITE)
        self.t_giuste = TesseraStat(testi.STAT_GIUSTE)
        self.t_tempo = TesseraStat(testi.STAT_TEMPO)
        self.t_migliore = TesseraStat(testi.STAT_MIGLIORE)
        for tessera in (self.t_partite, self.t_giuste, self.t_tempo, self.t_migliore):
            tessere.addWidget(tessera, 1)
        colonna.addLayout(tessere)

        riga = QHBoxLayout()
        riga.setSpacing(0)
        card, lay = card_sezione(testi.STAT_ANDAMENTO)
        self.lbl_andamento = EtichettaElisa("", "terziario")
        lay.addWidget(self.lbl_andamento)
        self.grafico_andamento = GraficoAndamento(self._descrivi_partita)
        lay.addWidget(self.grafico_andamento, 1)
        riga.addWidget(card, 3)
        card, lay = card_sezione(testi.STAT_PER_LIVELLO)
        self.grafico_livelli = GraficoQuote()
        lay.addWidget(self.grafico_livelli)
        lay.addStretch(1)
        riga.addWidget(card, 2)
        colonna.addLayout(riga)

        riga = QHBoxLayout()
        riga.setSpacing(0)
        card, lay = card_sezione(testi.STAT_PER_CONTINENTE)
        self.grafico_continenti = GraficoQuote()
        lay.addWidget(self.grafico_continenti)
        self.nota_continenti = etichetta(testi.STAT_SENZA_DETTAGLIO, "terziario", a_capo=True)
        lay.addWidget(self.nota_continenti)
        lay.addStretch(1)
        riga.addWidget(card, 2)
        card, lay = card_sezione(testi.STAT_DA_RIPASSARE)
        self.nota_ripasso = etichetta("", "terziario", a_capo=True)
        lay.addWidget(self.nota_ripasso)
        self.griglia_ripasso_w = QWidget()
        self.griglia_ripasso = QGridLayout(self.griglia_ripasso_w)
        self.griglia_ripasso.setContentsMargins(0, 0, 0, 0)
        self.griglia_ripasso.setHorizontalSpacing(18)
        self.griglia_ripasso.setVerticalSpacing(2)
        self.griglia_ripasso.setColumnStretch(0, 1)
        self.griglia_ripasso.setColumnStretch(1, 1)
        lay.addWidget(self.griglia_ripasso_w)
        lay.addStretch(1)
        riga.addWidget(card, 3)
        colonna.addLayout(riga)
        colonna.addStretch(1)

        scorrimento.setWidget(contenitore_centrato(contenuto, 1180))
        self.pagina_dati = scorrimento
        self.pagine.addWidget(self.pagina_dati)
        self.vuoto = MessaggioVuoto("grafico", testi.STAT_VUOTA, testi.STAT_VUOTA_SUGGERIMENTO)
        self.pagine.addWidget(self.vuoto)

        self.combo_giocatore.currentIndexChanged.connect(lambda *_: self.aggiorna())

    # -------------------------------------------------------------- dati

    def configura(self, livelli: list[tuple[str, str]], aree: list[tuple[str, str]],
                  catalogo: Catalogo | None) -> None:
        """Nomi di livelli e aree, e il catalogo per nomi, continenti e immagini."""
        self._livelli = list(livelli)
        self._aree = list(aree)
        self.catalogo = catalogo

    def mostra(self, preferito: str = "") -> None:
        """Riempie l'elenco dei giocatori e mostra ``preferito`` (se ha partite)."""
        nomi = giocatori(self.classifica.tutti())
        chiave = " ".join(preferito.split()).casefold()
        indice = next((i for i, n in enumerate(nomi) if n.casefold() == chiave), 0)
        self.combo_giocatore.blockSignals(True)
        self.combo_giocatore.clear()
        self.combo_giocatore.addItems(nomi)
        self.combo_giocatore.setCurrentIndex(indice if nomi else -1)
        self.combo_giocatore.blockSignals(False)
        self.aggiorna()

    def _nome_bandiera(self, id_bandiera: str) -> str:
        if self.catalogo is not None and id_bandiera in self.catalogo.bandiere:
            return self.catalogo.nome(id_bandiera)
        return id_bandiera.title()

    def _immagine(self, id_bandiera: str):
        try:
            return self.catalogo.percorso(id_bandiera) if self.catalogo is not None else None
        except KeyError:
            return None

    def _continente(self, id_bandiera: str) -> str | None:
        if self.catalogo is not None and id_bandiera in self.catalogo.bandiere:
            return self.catalogo.bandiere[id_bandiera].continente
        return None

    def _descrivi_partita(self, punto: PuntoAndamento) -> str:
        r = punto.risultato
        try:
            data = datetime.fromisoformat(r.data).strftime(testi.CLASSIFICA_FORMATO_DATA)
        except ValueError:
            data = r.data
        return testi.STAT_PUNTO_TOOLTIP.format(
            data=data, modalita=testi.MODALITA.get(r.modalita, r.modalita),
            livello=dict(self._livelli).get(r.livello, r.livello), area=dict(self._aree).get(r.area, r.area),
            g=r.giuste, t=r.totale, p=round(r.percentuale), punti=punto.punti)

    def aggiorna(self) -> None:
        nome = self.combo_giocatore.currentText()
        self.colonna_giocatore.setVisible(self.combo_giocatore.count() > 0)
        if not nome:
            self.pagine.setCurrentWidget(self.vuoto)
            return
        continenti = [(k, n) for k, n in self._aree if k != AREA_MONDO]
        s = calcola(self.classifica, nome, self._continente,
                    [k for k, _ in self._livelli], [k for k, _ in continenti])
        if s.vuota:
            self.pagine.setCurrentWidget(self.vuoto)
            return
        self.pagine.setCurrentWidget(self.pagina_dati)

        self.t_partite.imposta(str(s.partite), testi.STAT_PARTITE_SOTTO)
        self.t_giuste.imposta(f"{round(s.percentuale)}%", testi.STAT_GIUSTE_SOTTO.format(g=s.giuste, t=s.risposte))
        self.t_tempo.imposta(testi.STAT_TEMPO_VALORE.format(s=s.tempo_medio), testi.STAT_TEMPO_SOTTO)
        if s.migliore is not None:
            r = s.migliore.risultato
            self.t_migliore.imposta(str(s.migliore.punti), testi.STAT_MIGLIORE_SOTTO.format(
                livello=dict(self._livelli).get(r.livello, r.livello),
                modalita=testi.MODALITA.get(r.modalita, r.modalita)))

        n = len(s.andamento)
        self.lbl_andamento.setText(testi.STAT_ANDAMENTO_UNA if n == 1 else testi.STAT_ANDAMENTO_SOTTO.format(n=n))
        self.grafico_andamento.imposta(s.andamento)

        nomi_livelli = dict(self._livelli)
        self.grafico_livelli.imposta([(nomi_livelli.get(q.chiave, q.chiave), q) for q in s.per_livello])

        dettaglio = s.partite_con_dettaglio > 0
        nomi_cont = dict(continenti)
        self.grafico_continenti.imposta([(nomi_cont.get(q.chiave, q.chiave), q) for q in s.per_continente])
        self.grafico_continenti.setVisible(dettaglio)
        self.nota_continenti.setVisible(not dettaglio)

        self._riempi_ripasso(s.da_ripassare, dettaglio)

    def _riempi_ripasso(self, bandiere: list[BandieraDaRipassare], dettaglio: bool) -> None:
        while self.griglia_ripasso.count():
            voce = self.griglia_ripasso.takeAt(0)
            if voce.widget():
                voce.widget().deleteLater()
        if not dettaglio or not bandiere:
            self.nota_ripasso.setText(testi.STAT_SENZA_DETTAGLIO if not dettaglio else testi.STAT_NESSUN_ERRORE)
            self.nota_ripasso.show()
            self.griglia_ripasso_w.hide()
            return
        self.nota_ripasso.hide()
        self.griglia_ripasso_w.show()
        for i, b in enumerate(bandiere):
            errori = (testi.STAT_SBAGLIATA_UNA.format(v=b.viste) if b.sbagliate == 1
                      else testi.STAT_SBAGLIATA.format(n=b.sbagliate, v=b.viste))
            scambio = testi.STAT_CONFUSA.format(nome=self._nome_bandiera(b.confusa_con)) if b.confusa_con else ""
            riga = RigaRipasso(self.cache, self._immagine(b.id), self._nome_bandiera(b.id), errori, scambio)
            self.griglia_ripasso.addWidget(riga, i // 2, i % 2)
