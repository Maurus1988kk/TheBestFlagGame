"""Schermata di gioco per Guess the Flag e Guess the Country."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QRectF, Qt, QTimer, QVariantAnimation, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from .. import testi
from ..generatore import MODALITA_STATO, Domanda
from ..partita import Partita, RispostaData, StatoPartita, formatta_tempo
from .componenti import (CardBandiera, IndicatoreAvanzamento, PulsanteRisposta, VistaBandiera,
                         chiedi_conferma, contenitore_centrato, dissolvi, etichetta, imposta_ruolo,
                         pulsante)
from .grafica import disegna_icona, imposta_icona
from .immagini import CacheImmagini
from .tema import tema

DURATA_FEEDBACK_MS = 1200


class BarraTempo(QWidget):
    """Barretta che si svuota durante il feedback (mostra quando si prosegue)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._valore = 0.0
        self.setFixedSize(160, 4)
        self._anim = QVariantAnimation(self)
        self._anim.valueChanged.connect(self._muovi)

    def _muovi(self, v):
        self._valore = float(v)
        self.update()

    def avvia(self, durata: int):
        self._anim.stop()
        self._anim.setDuration(durata)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.start()

    def ferma(self):
        self._anim.stop()

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect())
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(tema().c("bordo"))
        p.drawRoundedRect(r, 2, 2)
        p.setBrush(tema().c("primario"))
        p.drawRoundedRect(QRectF(r.left(), r.top(), r.width() * self._valore, r.height()), 2, 2)


class IconaOrologio(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(26, 26)
        self.attivo = True

    def paintEvent(self, evento):
        p = QPainter(self)
        colore = tema().c("primario") if self.attivo else tema().c("testo_terziario")
        disegna_icona(p, "orologio", QRectF(self.rect()), colore, 2.2)


class SchermataGioco(QWidget):
    """Mostra le domande, gestisce risposte, feedback, timer e tasti rapidi."""

    finita = Signal(object)        # Partita completata
    abbandonata = Signal(object)   # Partita interrotta (non va in classifica)
    risposta_data = Signal(bool)   # per i suoni

    def __init__(self, cache: CacheImmagini, avanzamento_automatico: Callable[[], bool], parent=None):
        super().__init__(parent)
        self.setObjectName("schermata")
        self.cache = cache
        self._auto = avanzamento_automatico
        self.partita: Partita | None = None
        self._conferma = None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._timer_display = QTimer(self)
        self._timer_display.setInterval(50)
        self._timer_display.timeout.connect(self._aggiorna_tempo)
        self._timer_feedback = QTimer(self)
        self._timer_feedback.setSingleShot(True)
        self._timer_feedback.timeout.connect(self.prosegui)
        self._costruisci()

    # ------------------------------------------------------------- layout

    def _costruisci(self):
        radice = QVBoxLayout(self)
        radice.setContentsMargins(32, 20, 32, 22)
        radice.setSpacing(6)

        # barra superiore: abbandona | etichette | tempo
        barra = QHBoxLayout()
        barra.setSpacing(10)
        self.btn_abbandona = pulsante(testi.GIOCO_ABBANDONA, "fantasma")
        imposta_icona(self.btn_abbandona, "indietro", "testo_secondario")
        self.btn_abbandona.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_abbandona.setToolTip("Esc")
        self.btn_abbandona.clicked.connect(self.chiedi_abbandono)
        sinistra = QWidget()
        ls = QHBoxLayout(sinistra)
        ls.setContentsMargins(0, 0, 0, 0)
        ls.addWidget(self.btn_abbandona)
        ls.addStretch(1)
        barra.addWidget(sinistra, 1)

        self.chip_modalita = etichetta("", "chip")
        self.chip_livello = etichetta("", "chip")
        self.chip_area = etichetta("", "chip")
        centro = QHBoxLayout()
        centro.setSpacing(6)
        for chip in (self.chip_modalita, self.chip_livello, self.chip_area):
            centro.addWidget(chip)
        barra.addLayout(centro)

        destra = QWidget()
        ld = QHBoxLayout(destra)
        ld.setContentsMargins(0, 0, 0, 0)
        ld.setSpacing(8)
        ld.addStretch(1)
        self.icona_orologio = IconaOrologio()
        ld.addWidget(self.icona_orologio)
        self.lbl_tempo = etichetta("00:00.0", "timer")
        self.lbl_tempo.setMinimumWidth(116)
        ld.addWidget(self.lbl_tempo)
        barra.addWidget(destra, 1)
        radice.addLayout(barra)

        # avanzamento
        riga_av = QHBoxLayout()
        riga_av.addStretch(1)
        self.avanzamento = IndicatoreAvanzamento()
        riga_av.addWidget(self.avanzamento)
        riga_av.addSpacing(14)
        self.lbl_contatore = etichetta("", "contatore")
        riga_av.addWidget(self.lbl_contatore)
        riga_av.addStretch(1)
        radice.addLayout(riga_av)
        radice.addSpacing(8)

        # pagine delle due modalità
        self.pagine = QStackedWidget()
        self.pagine.addWidget(self._pagina_flag())
        self.pagine.addWidget(self._pagina_country())
        radice.addWidget(self.pagine, 1)

        # feedback
        self.zona_feedback = QWidget()
        self.zona_feedback.setFixedHeight(64)
        lf = QHBoxLayout(self.zona_feedback)
        lf.setContentsMargins(0, 0, 0, 0)
        lf.setSpacing(16)
        lf.addStretch(1)
        colonna = QVBoxLayout()
        colonna.setSpacing(6)
        self.lbl_esito = etichetta("", "esito_giusto")
        self.lbl_esito.setAlignment(Qt.AlignmentFlag.AlignCenter)
        colonna.addWidget(self.lbl_esito)
        riga_barra = QHBoxLayout()
        riga_barra.addStretch(1)
        self.barra_tempo = BarraTempo()
        riga_barra.addWidget(self.barra_tempo)
        riga_barra.addStretch(1)
        colonna.addLayout(riga_barra)
        self.lbl_suggerimento = etichetta(testi.GIOCO_SUGGERIMENTO_AVANTI, "terziario")
        self.lbl_suggerimento.setAlignment(Qt.AlignmentFlag.AlignCenter)
        colonna.addWidget(self.lbl_suggerimento)
        lf.addLayout(colonna)
        self.btn_avanti = pulsante(testi.GIOCO_AVANTI, "primario")
        imposta_icona(self.btn_avanti, "avanti", "su_primario", 16)
        self.btn_avanti.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.btn_avanti.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_avanti.clicked.connect(self.prosegui)
        lf.addWidget(self.btn_avanti)
        lf.addStretch(1)
        radice.addWidget(self.zona_feedback)
        self._nascondi_feedback()

    def _pagina_flag(self) -> QWidget:
        pagina = QWidget()
        lay = QVBoxLayout(pagina)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        self.vista_bandiera = VistaBandiera(self.cache, rapporto=1.62, margine=0.09, raggio=22)
        self.vista_bandiera.setMinimumSize(380, 220)
        lay.addWidget(self.vista_bandiera, 1)
        domanda = etichetta(testi.GIOCO_DOMANDA_FLAG, "domanda")
        domanda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(domanda)
        lay.addSpacing(4)
        griglia_w = QWidget()
        griglia = QGridLayout(griglia_w)
        griglia.setContentsMargins(0, 0, 0, 0)
        griglia.setHorizontalSpacing(10)
        griglia.setVerticalSpacing(6)
        self.pulsanti: list[PulsanteRisposta] = []
        for i in range(4):
            btn = PulsanteRisposta(i + 1)
            btn.clicked.connect(lambda _=False, i=i: self._clic_opzione(i))
            griglia.addWidget(btn, i // 2, i % 2)
            self.pulsanti.append(btn)
        lay.addWidget(contenitore_centrato(griglia_w, 940))
        return pagina

    def _pagina_country(self) -> QWidget:
        pagina = QWidget()
        lay = QVBoxLayout(pagina)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        domanda = etichetta(testi.GIOCO_DOMANDA_COUNTRY, "domanda")
        domanda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(domanda)
        self.lbl_stato = etichetta("", "stato_nome")
        self.lbl_stato.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_stato.setWordWrap(True)
        lay.addWidget(self.lbl_stato)
        lay.addSpacing(8)
        griglia_w = QWidget()
        griglia = QGridLayout(griglia_w)
        griglia.setContentsMargins(0, 0, 0, 0)
        griglia.setSpacing(6)
        self.card: list[CardBandiera] = []
        for i in range(4):
            card = CardBandiera(i + 1, self.cache)
            card.clicked.connect(lambda _=False, i=i: self._clic_opzione(i))
            griglia.addWidget(card, i // 2, i % 2)
            self.card.append(card)
        for i in range(2):
            griglia.setRowStretch(i, 1)
            griglia.setColumnStretch(i, 1)
        lay.addWidget(contenitore_centrato(griglia_w, 1000), 1)
        return pagina

    # ------------------------------------------------------------ partita

    def avvia(self, partita: Partita, nome_modalita: str, nome_livello: str, nome_area: str) -> None:
        """Prepara la schermata; il timer parte con ``mostra_prima_domanda``."""
        self.partita = partita
        self.chip_modalita.setText(nome_modalita)
        self.chip_livello.setText(nome_livello)
        self.chip_area.setText(nome_area)
        self.pagine.setCurrentIndex(1 if partita.modalita == MODALITA_STATO else 0)
        self._mostra_domanda(partita.domande[0], anima=False)
        self.lbl_tempo.setText(formatta_tempo(0))
        self.cache.precarica(o.immagine for o in partita.domande[0].opzioni)

    def mostra_prima_domanda(self) -> None:
        """Chiamata quando la schermata è visibile: fa partire il cronometro."""
        if self.partita is None or self.partita.stato != StatoPartita.PRONTA:
            return
        self.partita.avvia()
        self._timer_display.start()
        self._aggiorna_tempo()
        self.setFocus()

    def _mostra_domanda(self, domanda: Domanda, anima: bool = True) -> None:
        if anima:
            dissolvi(self.pagine.currentWidget())
        self._nascondi_feedback()
        if self.partita.modalita == MODALITA_STATO:
            self.lbl_stato.setText(domanda.risposta.nome)
            for card, opzione in zip(self.card, domanda.opzioni):
                card.imposta(opzione.immagine)
        else:
            self.vista_bandiera.imposta(domanda.risposta.immagine)
            for btn, opzione in zip(self.pulsanti, domanda.opzioni):
                btn.setText(opzione.nome)
                btn.imposta_stato("normale")
        self.lbl_contatore.setText(testi.GIOCO_DOMANDA.format(n=domanda.numero, tot=self.partita.totale))
        self._aggiorna_pallini()

    def _aggiorna_pallini(self) -> None:
        p = self.partita
        stati = []
        for i in range(p.totale):
            if i < len(p.risposte):
                stati.append("giusta" if p.risposte[i].giusta else "sbagliata")
            elif i == p.indice and p.stato in (StatoPartita.DOMANDA, StatoPartita.PRONTA):
                stati.append("corrente")
            else:
                stati.append("attesa")
        self.avanzamento.imposta(stati)

    def _widget_opzioni(self):
        return self.card if self.partita.modalita == MODALITA_STATO else self.pulsanti

    def _clic_opzione(self, indice: int) -> None:
        if self.partita is None or self._conferma is not None:
            return
        if self.partita.stato == StatoPartita.DOMANDA:
            self.rispondi(indice)
        elif self.partita.stato == StatoPartita.FEEDBACK:
            self.prosegui()

    def rispondi(self, indice: int) -> RispostaData | None:
        """Registra la risposta, mostra il feedback e mette in pausa il timer."""
        if self.partita is None or self.partita.stato != StatoPartita.DOMANDA:
            return None
        risposta = self.partita.rispondi(indice)
        self._aggiorna_tempo()
        giusto = risposta.domanda.indice_giusto
        for i, w in enumerate(self._widget_opzioni()):
            if i == giusto:
                w.imposta_stato("giusta")
            elif i == indice:
                w.imposta_stato("sbagliata")
            else:
                w.imposta_stato("spenta")
        self._aggiorna_pallini()
        self._mostra_feedback(risposta)
        self.risposta_data.emit(risposta.giusta)
        # durante la pausa carichiamo già le immagini della domanda successiva
        if not self.partita.ultima_domanda:
            prossima = self.partita.domande[self.partita.indice + 1]
            self.cache.precarica(o.immagine for o in prossima.opzioni)
        return risposta

    def _mostra_feedback(self, risposta: RispostaData) -> None:
        if risposta.giusta:
            self.lbl_esito.setText("✓  " + testi.GIOCO_GIUSTO)
            imposta_ruolo(self.lbl_esito, "esito_giusto")
        else:
            self.lbl_esito.setText("✗  " + testi.GIOCO_SBAGLIATO.format(nome=risposta.domanda.risposta.nome))
            imposta_ruolo(self.lbl_esito, "esito_sbagliato")
        self.lbl_esito.show()
        ultima = self.partita.ultima_domanda
        self.btn_avanti.setText(testi.GIOCO_RISULTATI if ultima else testi.GIOCO_AVANTI)
        if self._auto():
            self.barra_tempo.show()
            self.barra_tempo.avvia(DURATA_FEEDBACK_MS)
            self.lbl_suggerimento.hide()
            self.btn_avanti.hide()
            self._timer_feedback.start(DURATA_FEEDBACK_MS)
        else:
            self.barra_tempo.hide()
            self.lbl_suggerimento.hide()
            self.btn_avanti.show()

    def _nascondi_feedback(self) -> None:
        self._timer_feedback.stop()
        self.barra_tempo.ferma()
        self.lbl_esito.setText("")
        self.barra_tempo.hide()
        self.lbl_suggerimento.hide()
        self.btn_avanti.hide()

    def prosegui(self) -> None:
        """Passa alla domanda successiva (il timer riparte) o chiude la partita."""
        if self.partita is None or self.partita.stato != StatoPartita.FEEDBACK or self._conferma is not None:
            return
        self._timer_feedback.stop()
        domanda = self.partita.avanti()
        if domanda is None:
            self._timer_display.stop()
            self._aggiorna_tempo()
            self.finita.emit(self.partita)
            return
        self._mostra_domanda(domanda)
        self._aggiorna_tempo()

    def _aggiorna_tempo(self) -> None:
        if self.partita is None:
            return
        self.lbl_tempo.setText(formatta_tempo(self.partita.tempo()))
        attivo = self.partita.timer_in_corso
        imposta_ruolo(self.lbl_tempo, "timer" if attivo else "timer_pausa")
        if self.icona_orologio.attivo != attivo:
            self.icona_orologio.attivo = attivo
            self.icona_orologio.update()

    # ---------------------------------------------------------- abbandono

    def chiedi_abbandono(self) -> None:
        if self.partita is None or self._conferma is not None:
            return
        if self.partita.stato in (StatoPartita.FINITA, StatoPartita.ABBANDONATA):
            return
        self.partita.sospendi()
        feedback_attivo = self._timer_feedback.isActive()
        self._timer_feedback.stop()
        self.barra_tempo.ferma()
        self._aggiorna_tempo()

        def esito(si: bool):
            self._conferma = None
            if si:
                self.abbandona()
            else:
                self.partita.riprendi()
                if feedback_attivo:
                    self._timer_feedback.start(600)
                self.setFocus()

        self._conferma = chiedi_conferma(self.window().centralWidget(), testi.GIOCO_CONFERMA_TITOLO,
                                         testi.GIOCO_CONFERMA_TESTO, testi.GIOCO_CONFERMA_SI,
                                         testi.GIOCO_CONFERMA_NO, esito)

    def abbandona(self) -> None:
        """Interrompe la partita senza chiedere conferma."""
        if self.partita is None:
            return
        self._timer_display.stop()
        self._timer_feedback.stop()
        self.partita.abbandona()
        self.abbandonata.emit(self.partita)

    # ------------------------------------------------------------- input

    def keyPressEvent(self, evento):
        tasto = evento.key()
        if self.partita is None or self._conferma is not None:
            return super().keyPressEvent(evento)
        if tasto == Qt.Key.Key_Escape:
            self.chiedi_abbandono()
        elif Qt.Key.Key_1 <= tasto <= Qt.Key.Key_4:
            self._clic_opzione(tasto - Qt.Key.Key_1)
        elif tasto in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.prosegui()
        else:
            super().keyPressEvent(evento)

    def mousePressEvent(self, evento):
        # un clic in un punto qualsiasi durante il feedback fa proseguire
        if self.partita is not None and self.partita.stato == StatoPartita.FEEDBACK:
            self.prosegui()
        super().mousePressEvent(evento)

    def ferma(self) -> None:
        """Ferma i timer (es. quando si lascia la schermata)."""
        self._timer_display.stop()
        self._timer_feedback.stop()
