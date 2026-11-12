"""Widget riutilizzabili disegnati a mano: card, bandiere, pulsanti, segmenti...

Ogni widget legge i colori dal tema corrente al momento del disegno, quindi
il cambio chiaro/scuro non richiede di ricrearli.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import (QEasingCurve, QEvent, QPointF, QPropertyAnimation, QRect,
                            QRectF, QSize, Qt, QVariantAnimation, Signal)
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QAbstractButton, QFrame, QGraphicsOpacityEffect, QHBoxLayout,
                               QLabel, QPushButton, QSizePolicy, QStackedWidget, QVBoxLayout,
                               QWidget)

from .grafica import disegna_icona, disegna_ombra
from .immagini import CacheImmagini
from .tema import SEMIBOLD, font, ripolish, tema

MARGINE_OMBRA = 10


def mescola(a: QColor, b: QColor, t: float) -> QColor:
    """Colore intermedio tra a e b (t da 0 a 1)."""
    t = max(0.0, min(1.0, t))
    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
        round(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


def etichetta(testo: str, ruolo: str | None = None, a_capo: bool = False) -> QLabel:
    """QLabel con un "ruolo" usato dal foglio di stile."""
    lbl = QLabel(testo)
    if ruolo:
        lbl.setProperty("ruolo", ruolo)
    lbl.setWordWrap(a_capo)
    return lbl


class EtichettaElisa(QLabel):
    """Etichetta su una riga che, se lo spazio non basta, accorcia il testo
    con "…" e mostra quello completo nel tooltip."""

    def __init__(self, testo: str = "", ruolo: str | None = None,
                 modo: Qt.TextElideMode = Qt.TextElideMode.ElideRight, parent=None):
        super().__init__(parent)
        self._completo = testo
        self._modo = modo
        if ruolo:
            self.setProperty("ruolo", ruolo)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(40)
        self._elidi()

    def setText(self, testo: str) -> None:  # noqa: N802 (nome dell'API Qt)
        self._completo = testo
        self._elidi()

    def testo_completo(self) -> str:
        return self._completo

    def _elidi(self) -> None:
        corto = self.fontMetrics().elidedText(self._completo, self._modo, max(10, self.width()))
        QLabel.setText(self, corto)
        self.setToolTip(self._completo if corto != self._completo else "")

    def sizeHint(self) -> QSize:
        base = super().sizeHint()
        return QSize(self.fontMetrics().horizontalAdvance(self._completo) + 4, base.height())

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._elidi()

    def changeEvent(self, evento):
        super().changeEvent(evento)
        if evento.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange):
            self._elidi()


def pulsante(testo: str, variante: str | None = None) -> QPushButton:
    """QPushButton con variante grafica (primario, grande, fantasma, pericolo...)."""
    btn = QPushButton(testo)
    if variante:
        btn.setProperty("variante", variante)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFocusPolicy(Qt.FocusPolicy.TabFocus)
    return btn


def imposta_ruolo(widget: QWidget, ruolo: str) -> None:
    if widget.property("ruolo") != ruolo:
        widget.setProperty("ruolo", ruolo)
        ripolish(widget)


def separatore() -> QFrame:
    linea = QFrame()
    linea.setProperty("ruolo", "separatore")
    linea.setFixedHeight(1)
    return linea


# --------------------------------------------------------------------------- #
# Animazione di "hover" condivisa
# --------------------------------------------------------------------------- #

class _ConHover:
    """Mixin: avanzamento animato 0→1 quando il mouse è sopra il widget."""

    def _init_hover(self, durata: int = 140):
        self._hover = 0.0
        self._anim_hover = QVariantAnimation(self)
        self._anim_hover.setDuration(durata)
        self._anim_hover.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_hover.valueChanged.connect(self._su_hover)

    def _su_hover(self, valore):
        self._hover = float(valore)
        self.update()

    def _anima_hover(self, verso: float):
        self._anim_hover.stop()
        self._anim_hover.setStartValue(self._hover)
        self._anim_hover.setEndValue(verso)
        self._anim_hover.start()

    def enterEvent(self, evento):
        if self.isEnabled() and getattr(self, "stato", "normale") == "normale":
            self._anima_hover(1.0)
        super().enterEvent(evento)

    def leaveEvent(self, evento):
        self._anima_hover(0.0)
        super().leaveEvent(evento)


# --------------------------------------------------------------------------- #
# Card
# --------------------------------------------------------------------------- #

class Card(QFrame):
    """Contenitore con sfondo, bordo sottile, angoli arrotondati e ombra leggera.

    Lascia ``MARGINE_OMBRA`` pixel intorno per disegnare l'ombra. Il contenuto
    va aggiunto a ``card.lay`` (QVBoxLayout già con i margini giusti).
    """

    def __init__(self, parent=None, raggio: int = 18, padding: int = 24, ombra: float = 1.0):
        super().__init__(parent)
        self.raggio = raggio
        self.forza_ombra = ombra
        m = MARGINE_OMBRA + padding
        self.lay = QVBoxLayout(self)  # layout interno: usare card.lay
        self.lay.setContentsMargins(m, m, m, m)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def rettangolo_card(self) -> QRectF:
        m = MARGINE_OMBRA
        return QRectF(self.rect()).adjusted(m, m, -m, -m)

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rettangolo_card()
        disegna_ombra(p, r, self.raggio, self.forza_ombra)
        p.setPen(QPen(tema().c("bordo"), 1))
        p.setBrush(tema().c("superficie"))
        p.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), self.raggio, self.raggio)


# --------------------------------------------------------------------------- #
# Bandiera
# --------------------------------------------------------------------------- #

def rettangolo_adattato(dimensione: QSize, area: QRectF) -> QRect:
    """Rettangolo (a pixel interi) con le proporzioni di ``dimensione``,
    il più grande possibile dentro ``area`` e centrato."""
    if not dimensione.isValid() or dimensione.isEmpty():
        dimensione = QSize(3, 2)
    s = QSize(dimensione)
    s.scale(max(1, int(area.width())), max(1, int(area.height())), Qt.AspectRatioMode.KeepAspectRatio)
    x = round(area.center().x() - s.width() / 2)
    y = round(area.center().y() - s.height() / 2)
    return QRect(x, y, s.width(), s.height())


def disegna_bandiera(p: QPainter, cache: CacheImmagini, percorso, area: QRectF, dpr: float,
                     raggio: float = 3.0) -> QRect:
    """Disegna la bandiera dentro ``area`` rispettandone le proporzioni,
    con un bordo grigio sottile (utile per le bandiere con parti bianche)."""
    dim = cache.dimensione(percorso) if percorso else QSize()
    r = rettangolo_adattato(dim, area)
    pix = cache.pixmap(percorso, r.width(), r.height(), dpr) if percorso else None
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    rf = QRectF(r)
    clip = QPainterPath()
    clip.addRoundedRect(rf, raggio, raggio)
    if pix is not None and not pix.isNull():
        p.setClipPath(clip)
        dx = (r.width() - pix.width() / pix.devicePixelRatio()) / 2
        dy = (r.height() - pix.height() / pix.devicePixelRatio()) / 2
        p.drawPixmap(QPointF(r.left() + dx, r.top() + dy), pix)
        p.setClipping(False)
    else:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(tema().c("superficie_alt"))
        p.drawRoundedRect(rf, raggio, raggio)
        disegna_icona(p, "bandiera", QRectF(rf.center().x() - 16, rf.center().y() - 16, 32, 32),
                      tema().c("testo_terziario"))
    p.setPen(QPen(tema().c("bordo_bandiera"), 1))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(rf.adjusted(0.5, 0.5, -0.5, -0.5), raggio, raggio)
    p.restore()
    return r


class VistaBandiera(QWidget):
    """Bandiera centrata in un riquadro di proporzioni fisse.

    ``rapporto`` è il rapporto larghezza/altezza del riquadro (non della
    bandiera): tutte le bandiere compaiono nello stesso riquadro, ciascuna con
    le sue proporzioni originali.
    """

    def __init__(self, cache: CacheImmagini, parent=None, rapporto: float | None = 1.6,
                 riquadro: bool = True, margine: float = 0.10, raggio: int = 20):
        super().__init__(parent)
        self.cache = cache
        self.percorso: Path | None = None
        self.rapporto = rapporto
        self.riquadro = riquadro
        self.margine = margine
        self.raggio = raggio
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def imposta(self, percorso: Path | None) -> None:
        self.percorso = percorso
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(480, 300)

    def rettangolo_riquadro(self) -> QRectF:
        m = MARGINE_OMBRA if self.riquadro else 0
        area = QRectF(self.rect()).adjusted(m, m, -m, -m)
        if self.rapporto:
            larghezza = min(area.width(), area.height() * self.rapporto)
            altezza = larghezza / self.rapporto
            area = QRectF(area.center().x() - larghezza / 2, area.center().y() - altezza / 2,
                          larghezza, altezza)
        return area

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rettangolo_riquadro()
        if self.riquadro:
            disegna_ombra(p, r, self.raggio, 1.0)
            p.setPen(QPen(tema().c("bordo"), 1))
            p.setBrush(tema().c("superficie"))
            p.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), self.raggio, self.raggio)
            pad = min(r.width(), r.height()) * self.margine
            area = r.adjusted(pad, pad, -pad, -pad)
        else:
            area = r
        disegna_bandiera(p, self.cache, self.percorso, area, self.devicePixelRatioF(),
                         raggio=4 if self.riquadro else 2)


# --------------------------------------------------------------------------- #
# Pulsanti di gioco
# --------------------------------------------------------------------------- #

STATI_RISPOSTA = ("normale", "giusta", "sbagliata", "spenta")


def _disegna_numero(p: QPainter, centro: QPointF, raggio: float, testo: str,
                    sfondo: QColor, colore: QColor, simbolo: str | None = None) -> None:
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(sfondo)
    p.drawEllipse(centro, raggio, raggio)
    if simbolo:
        lato = raggio * 1.15
        disegna_icona(p, simbolo, QRectF(centro.x() - lato / 2, centro.y() - lato / 2, lato, lato),
                      colore, 3.0)
    else:
        p.setPen(colore)
        p.setFont(font(int(raggio * 0.95), SEMIBOLD))
        p.drawText(QRectF(centro.x() - raggio, centro.y() - raggio, 2 * raggio, 2 * raggio),
                   Qt.AlignmentFlag.AlignCenter, testo)


def _colori_stato(stato: str, hover: float, premuto: bool):
    """(sfondo, bordo, spessore bordo, sfondo numero, colore numero, simbolo)."""
    t = tema()
    if stato == "giusta":
        return (t.c("successo_tenue"), t.c("successo"), 2.0, t.c("successo"), QColor("#FFFFFF"), "check")
    if stato == "sbagliata":
        return (t.c("errore_tenue"), t.c("errore"), 2.0, t.c("errore"), QColor("#FFFFFF"), "croce")
    sfondo = mescola(t.c("superficie"), t.c("superficie_hover"), hover)
    if premuto:
        sfondo = t.c("primario_tenue")
    bordo = mescola(t.c("bordo"), t.c("primario"), hover)
    num_sfondo = mescola(t.c("superficie_alt"), t.c("primario"), hover)
    num_colore = mescola(t.c("testo_secondario"), t.c("su_primario"), hover)
    return (sfondo, bordo, 1.0 + hover * 0.5, num_sfondo, num_colore, None)


class PulsanteRisposta(_ConHover, QAbstractButton):
    """Pulsante di risposta di Guess the Flag: numero (tasto rapido) + nome."""

    def __init__(self, numero: int, parent=None):
        super().__init__(parent)
        self.numero = numero
        self.stato = "normale"
        self._init_hover()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMinimumHeight(66)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def sizeHint(self) -> QSize:
        return QSize(320, 70)

    def imposta_stato(self, stato: str) -> None:
        self.stato = stato
        if stato != "normale":
            self._hover = 0.0
        self.update()

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.stato == "spenta":
            p.setOpacity(0.45)
        r = QRectF(self.rect()).adjusted(4, 3, -4, -6)
        sfondo, bordo, spessore, num_sf, num_col, simbolo = _colori_stato(
            self.stato, self._hover, self.isDown())
        disegna_ombra(p, r, 14, 0.6 + 0.6 * self._hover, 6, 2 + self._hover)
        p.setPen(QPen(bordo, spessore))
        p.setBrush(sfondo)
        p.drawRoundedRect(r.adjusted(spessore / 2, spessore / 2, -spessore / 2, -spessore / 2), 14, 14)
        raggio = 15
        centro = QPointF(r.left() + 20 + raggio, r.center().y())
        _disegna_numero(p, centro, raggio, str(self.numero), num_sf, num_col, simbolo)
        testo_r = QRectF(centro.x() + raggio + 16, r.top(), r.right() - centro.x() - raggio - 32, r.height())
        f = font(17, SEMIBOLD)
        p.setFont(f)
        p.setPen(tema().c("testo"))
        testo = QFontMetrics(f).elidedText(self.text(), Qt.TextElideMode.ElideRight, int(testo_r.width()))
        p.drawText(testo_r, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, testo)


class CardBandiera(_ConHover, QAbstractButton):
    """Opzione di Guess the Country: card cliccabile con la sola bandiera."""

    def __init__(self, numero: int, cache: CacheImmagini, parent=None):
        super().__init__(parent)
        self.numero = numero
        self.cache = cache
        self.percorso: Path | None = None
        self.stato = "normale"
        self._init_hover()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(200, 140)

    def sizeHint(self) -> QSize:
        return QSize(360, 230)

    def imposta(self, percorso: Path | None) -> None:
        self.percorso = percorso
        self.stato = "normale"
        self.update()

    def imposta_stato(self, stato: str) -> None:
        self.stato = stato
        if stato != "normale":
            self._hover = 0.0
        self.update()

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.stato == "spenta":
            p.setOpacity(0.4)
        sollevamento = 2.0 * self._hover if self.stato == "normale" else 0.0
        r = QRectF(self.rect()).adjusted(8, 6 - sollevamento, -8, -10 - sollevamento)
        sfondo, bordo, spessore, num_sf, num_col, simbolo = _colori_stato(
            self.stato, self._hover, self.isDown())
        if self.stato in ("giusta", "sbagliata"):
            spessore = 3.0
            sfondo = tema().c("superficie")
        else:
            sfondo = tema().c("superficie")
            spessore = 1.0 + self._hover
        disegna_ombra(p, r, 18, 0.8 + 0.9 * self._hover, 9, 3 + 2 * self._hover)
        p.setPen(QPen(bordo, spessore))
        p.setBrush(sfondo)
        p.drawRoundedRect(r.adjusted(spessore / 2, spessore / 2, -spessore / 2, -spessore / 2), 18, 18)
        pad = max(18.0, min(r.width(), r.height()) * 0.13)
        area = r.adjusted(pad + 8, pad, -pad - 8, -pad)
        disegna_bandiera(p, self.cache, self.percorso, area, self.devicePixelRatioF())
        # numero (tasto rapido) in alto a sinistra
        raggio = 13
        _disegna_numero(p, QPointF(r.left() + 12 + raggio, r.top() + 12 + raggio), raggio,
                        str(self.numero), num_sf if simbolo is None else tema().c("superficie_alt"),
                        num_col if simbolo is None else tema().c("testo_secondario"))
        if simbolo:
            colore = tema().c("successo") if self.stato == "giusta" else tema().c("errore")
            centro = QPointF(r.right() - 12 - 16, r.top() + 12 + 16)
            _disegna_numero(p, centro, 16, "", colore, QColor("#FFFFFF"), simbolo)


class CardModalita(_ConHover, QAbstractButton):
    """Card grande e selezionabile per scegliere la modalità di gioco."""

    def __init__(self, titolo: str, descrizione: str, illustrazione: Callable, parent=None):
        super().__init__(parent)
        self.titolo = titolo
        self.descrizione = descrizione
        self.illustrazione = illustrazione
        self._init_hover()
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(250)
        self.setMaximumHeight(430)

    def sizeHint(self) -> QSize:
        return QSize(440, 330)

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = tema()
        scelto = self.isChecked()
        r = QRectF(self.rect()).adjusted(MARGINE_OMBRA, MARGINE_OMBRA - self._hover * 2,
                                         -MARGINE_OMBRA, -MARGINE_OMBRA - self._hover * 2)
        disegna_ombra(p, r, 20, 1.0 + 0.8 * self._hover + (0.4 if scelto else 0), 10, 3 + 2 * self._hover)
        if scelto:
            bordo, spessore = t.c("primario"), 2.0
        else:
            bordo, spessore = mescola(t.c("bordo"), t.c("bordo_forte"), self._hover), 1.0
        p.setPen(QPen(bordo, spessore))
        p.setBrush(t.c("superficie"))
        p.drawRoundedRect(r.adjusted(spessore / 2, spessore / 2, -spessore / 2, -spessore / 2), 20, 20)

        # area illustrazione
        ill = QRectF(r.left() + 14, r.top() + 14, r.width() - 28, max(90.0, r.height() - 28 - 104))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(t.c("primario_tenue") if scelto else t.c("superficie_alt"))
        p.drawRoundedRect(ill, 14, 14)
        self.illustrazione(p, ill)

        # testi
        x = r.left() + 24
        y = ill.bottom() + 16
        p.setPen(t.c("testo"))
        p.setFont(font(21, SEMIBOLD))
        p.drawText(QRectF(x, y, r.width() - 48, 30), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   self.titolo)
        p.setPen(t.c("testo_secondario"))
        p.setFont(font(14))
        p.drawText(QRectF(x, y + 34, r.width() - 48, r.bottom() - y - 40),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                   self.descrizione)

        # spunta di selezione
        centro = QPointF(r.right() - 30, r.top() + 30)
        if scelto:
            p.setPen(QPen(t.c("superficie"), 3))
            p.setBrush(t.c("primario"))
            p.drawEllipse(centro, 14, 14)
            disegna_icona(p, "check", QRectF(centro.x() - 9, centro.y() - 9, 18, 18), QColor("#FFFFFF"), 3)
        else:
            p.setPen(QPen(mescola(t.c("bordo_forte"), t.c("primario"), self._hover), 2))
            p.setBrush(t.c("superficie"))
            p.drawEllipse(centro, 12, 12)


# --------------------------------------------------------------------------- #
# Controllo a segmenti
# --------------------------------------------------------------------------- #

class Segmenti(_ConHover, QWidget):
    """Pulsanti a segmento con indicatore animato (scelta esclusiva)."""

    cambiato = Signal(str)

    def __init__(self, voci: list[tuple[str, str]], parent=None, altezza: int = 44, pixel_font: int = 14):
        super().__init__(parent)
        self._voci = list(voci)
        self._disabilitati: set[str] = set()
        self._indice = 0
        self._sotto_mouse = -1
        self._pos = 0.0  # posizione animata dell'indicatore (indice float)
        self.altezza = altezza
        self.pixel_font = pixel_font
        self._init_hover()
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._muovi)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(altezza)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def _muovi(self, v):
        self._pos = float(v)
        self.update()

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(font(self.pixel_font, SEMIBOLD))
        larghezza = max((fm.horizontalAdvance(t) for _, t in self._voci), default=40) + 36
        return QSize(int(larghezza * len(self._voci) + 8), self.altezza)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def imposta_voci(self, voci: list[tuple[str, str]]) -> None:
        """Sostituisce le voci (senza emettere ``cambiato``)."""
        self._voci = list(voci)
        self._indice = 0
        self._pos = 0.0
        self.updateGeometry()
        self.update()

    def valore(self) -> str:
        return self._voci[self._indice][0] if self._voci else ""

    def imposta_valore(self, valore: str, anima: bool = False) -> None:
        for i, (chiave, _) in enumerate(self._voci):
            if chiave == valore:
                self._vai(i, anima, emetti=False)
                return

    def imposta_abilitato(self, chiave: str, abilitato: bool) -> None:
        if abilitato:
            self._disabilitati.discard(chiave)
        else:
            self._disabilitati.add(chiave)
        self.update()

    def _segmento(self, i: float) -> QRectF:
        r = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        larghezza = r.width() / max(1, len(self._voci))
        return QRectF(r.left() + i * larghezza, r.top(), larghezza, r.height())

    def _vai(self, i: int, anima: bool, emetti: bool = True) -> None:
        cambiato = i != self._indice
        self._indice = i
        self._anim.stop()
        if anima:
            self._anim.setStartValue(self._pos)
            self._anim.setEndValue(float(i))
            self._anim.start()
        else:
            self._pos = float(i)
        self.update()
        if cambiato and emetti:
            self.cambiato.emit(self._voci[i][0])

    def _indice_a(self, x: float) -> int:
        for i in range(len(self._voci)):
            if self._segmento(i).left() <= x < self._segmento(i).right():
                return i
        return -1

    def mouseMoveEvent(self, evento):
        i = self._indice_a(evento.position().x())
        if i != self._sotto_mouse:
            self._sotto_mouse = i
            self.update()

    def leaveEvent(self, evento):
        self._sotto_mouse = -1
        super().leaveEvent(evento)

    def mousePressEvent(self, evento):
        i = self._indice_a(evento.position().x())
        if i >= 0 and self._voci[i][0] not in self._disabilitati:
            self._vai(i, True)

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = tema()
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        raggio = min(12.0, r.height() / 2)
        p.setPen(QPen(t.c("bordo"), 1))
        p.setBrush(t.c("superficie_alt"))
        p.drawRoundedRect(r, raggio, raggio)
        ind = self._segmento(self._pos)
        disegna_ombra(p, ind, raggio - 3, 0.5, 4, 1)
        p.setPen(QPen(t.c("bordo") if not t.scuro else t.c("primario"), 1))
        p.setBrush(t.c("superficie") if not t.scuro else t.c("primario_tenue"))
        p.drawRoundedRect(ind, raggio - 3, raggio - 3)
        for i, (chiave, testo) in enumerate(self._voci):
            seg = self._segmento(i)
            if chiave in self._disabilitati:
                colore = t.c("testo_terziario", 120)
            elif i == self._indice:
                colore = t.c("primario") if not t.scuro else t.c("testo")
            elif i == self._sotto_mouse:
                colore = t.c("testo")
            else:
                colore = t.c("testo_secondario")
            p.setPen(colore)
            p.setFont(font(self.pixel_font, SEMIBOLD))
            p.drawText(seg, Qt.AlignmentFlag.AlignCenter, testo)


# --------------------------------------------------------------------------- #
# Interruttore on/off
# --------------------------------------------------------------------------- #

class Interruttore(QAbstractButton):
    """Interruttore a levetta con animazione."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(50, 28)
        self._pos = 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._muovi)
        self.toggled.connect(self._su_toggle)

    def _muovi(self, v):
        self._pos = float(v)
        self.update()

    def _su_toggle(self, stato: bool):
        self._anim.stop()
        self._anim.setStartValue(self._pos)
        self._anim.setEndValue(1.0 if stato else 0.0)
        self._anim.start()

    def imposta(self, stato: bool) -> None:
        self.blockSignals(True)
        self.setChecked(stato)
        self.blockSignals(False)
        self._pos = 1.0 if stato else 0.0
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(50, 28)

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = tema()
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(mescola(t.c("bordo_forte"), t.c("primario"), self._pos))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        d = r.height() - 6
        x = r.left() + 3 + (r.width() - d - 6) * self._pos
        p.setBrush(QColor(0, 0, 0, 40))
        p.drawEllipse(QRectF(x, r.top() + 4, d, d))
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QRectF(x, r.top() + 3, d, d))


# --------------------------------------------------------------------------- #
# Avanzamento a pallini
# --------------------------------------------------------------------------- #

class IndicatoreAvanzamento(QWidget):
    """Un pallino per domanda: grigio, corrente, verde (giusta) o rosso (sbagliata)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stati: list[str] = []
        self.setFixedHeight(22)

    def imposta(self, stati: list[str]) -> None:
        self._stati = list(stati)
        self.updateGeometry()
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(max(1, len(self._stati)) * 24, 22)

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = tema()
        n = len(self._stati)
        if not n:
            return
        passo = 24
        x0 = self.width() / 2 - (n - 1) * passo / 2
        cy = self.height() / 2
        for i, stato in enumerate(self._stati):
            c = QPointF(x0 + i * passo, cy)
            if stato == "giusta":
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(t.c("successo"))
                p.drawEllipse(c, 7, 7)
            elif stato == "sbagliata":
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(t.c("errore"))
                p.drawEllipse(c, 7, 7)
            elif stato == "corrente":
                p.setPen(QPen(t.c("primario"), 2.5))
                p.setBrush(t.c("primario_tenue"))
                p.drawEllipse(c, 7.5, 7.5)
            else:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(t.c("bordo_forte"))
                p.drawEllipse(c, 5, 5)


# --------------------------------------------------------------------------- #
# Anello della percentuale (riepilogo)
# --------------------------------------------------------------------------- #

class AnelloPercentuale(QWidget):
    """Grafico ad anello con la percentuale di risposte giuste."""

    def __init__(self, parent=None, lato: int = 170):
        super().__init__(parent)
        self._valore = 0.0
        self._mostrato = 0.0
        self.setFixedSize(lato, lato)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(900)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._muovi)

    def _muovi(self, v):
        self._mostrato = float(v)
        self.update()

    def imposta(self, percentuale: float, anima: bool = True) -> None:
        self._valore = percentuale
        self._anim.stop()
        if anima:
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(float(percentuale))
            self._anim.start()
        else:
            self._mostrato = percentuale
            self.update()

    def colore(self) -> QColor:
        if self._valore >= 70:
            return tema().c("successo")
        if self._valore >= 40:
            return tema().c("oro")
        return tema().c("errore")

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        spessore = 14
        r = QRectF(self.rect()).adjusted(spessore / 2 + 2, spessore / 2 + 2, -spessore / 2 - 2, -spessore / 2 - 2)
        p.setPen(QPen(tema().c("superficie_alt") if not tema().scuro else tema().c("bordo"), spessore))
        p.drawEllipse(r)
        if self._mostrato > 0:
            p.setPen(QPen(self.colore(), spessore, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawArc(r, 90 * 16, -int(self._mostrato / 100 * 360 * 16))
        p.setPen(tema().c("testo"))
        p.setFont(font(40, SEMIBOLD))
        p.drawText(QRectF(self.rect()), Qt.AlignmentFlag.AlignCenter, f"{round(self._mostrato)}%")


# --------------------------------------------------------------------------- #
# Stack con dissolvenza
# --------------------------------------------------------------------------- #

class StackDissolvenza(QStackedWidget):
    """QStackedWidget che passa da una schermata all'altra con una dissolvenza."""

    def __init__(self, parent=None, durata: int = 260):
        super().__init__(parent)
        self.durata = durata
        self._velo: QLabel | None = None

    def mostra(self, widget: QWidget, anima: bool = True) -> None:
        if self.currentWidget() is widget:
            return
        if not anima or not self.isVisible() or self.currentWidget() is None:
            self.setCurrentWidget(widget)
            return
        istantanea = self.currentWidget().grab()
        self._rimuovi_velo()
        velo = QLabel(self)
        velo.setPixmap(istantanea)
        velo.setGeometry(self.rect())
        self.setCurrentWidget(widget)
        velo.show()
        velo.raise_()
        effetto = QGraphicsOpacityEffect(velo)
        velo.setGraphicsEffect(effetto)
        anim = QPropertyAnimation(effetto, b"opacity", velo)
        anim.setDuration(self.durata)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.finished.connect(velo.deleteLater)
        anim.start()
        self._velo = velo
        velo.destroyed.connect(lambda *_: setattr(self, "_velo", None))

    def _rimuovi_velo(self):
        if self._velo is not None:
            try:
                self._velo.deleteLater()
            except RuntimeError:
                pass
            self._velo = None


def dissolvi(widget: QWidget, durata: int = 160) -> None:
    """Dissolvenza breve di un widget già visibile (es. cambio domanda)."""
    if not widget.isVisible():
        return
    istantanea = widget.grab()
    velo = QLabel(widget)
    velo.setPixmap(istantanea)
    velo.setGeometry(widget.rect())
    velo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    velo.show()
    velo.raise_()
    effetto = QGraphicsOpacityEffect(velo)
    velo.setGraphicsEffect(effetto)
    anim = QPropertyAnimation(effetto, b"opacity", velo)
    anim.setDuration(durata)
    anim.setStartValue(1.0)
    anim.setEndValue(0.0)
    anim.finished.connect(velo.deleteLater)
    anim.start()


# --------------------------------------------------------------------------- #
# Finestra di conferma sovrapposta
# --------------------------------------------------------------------------- #

class Conferma(QWidget):
    """Finestra di conferma modale disegnata sopra la finestra principale."""

    risposta = Signal(bool)

    def __init__(self, ospite: QWidget, titolo: str, testo: str, testo_si: str, testo_no: str,
                 pericolo: bool = True):
        super().__init__(ospite)
        self._ospite = ospite
        self.setGeometry(ospite.rect())
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        ospite.installEventFilter(self)

        self.card = Card(self, raggio=20, padding=26, ombra=2.0)
        self.card.setFixedWidth(480)
        lay = self.card.lay
        lay.setSpacing(10)
        lay.addWidget(etichetta(titolo, "titolo_medio", a_capo=True))
        lay.addWidget(etichetta(testo, "secondario", a_capo=True))
        lay.addSpacing(12)
        riga = QHBoxLayout()
        riga.addStretch(1)
        self.no = pulsante(testo_no)
        self.si = pulsante(testo_si, "pericolo_pieno" if pericolo else "primario")
        self.no.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.si.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        riga.addWidget(self.no)
        riga.addWidget(self.si)
        lay.addLayout(riga)
        self.no.clicked.connect(lambda: self._chiudi(False))
        self.si.clicked.connect(lambda: self._chiudi(True))
        self._riposiziona()

    def eventFilter(self, oggetto, evento):
        if oggetto is self._ospite and evento.type() == QEvent.Type.Resize:
            self.setGeometry(self._ospite.rect())
            self._riposiziona()
        return False

    def _riposiziona(self):
        self.card.adjustSize()
        self.card.move((self.width() - self.card.width()) // 2, (self.height() - self.card.height()) // 2 - 20)

    def apri(self) -> None:
        self.show()
        self.raise_()
        self.no.setFocus()
        effetto = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effetto)
        anim = QPropertyAnimation(effetto, b"opacity", self)
        anim.setDuration(150)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.finished.connect(lambda: self.setGraphicsEffect(None))
        anim.start()

    def _chiudi(self, esito: bool) -> None:
        self._ospite.removeEventFilter(self)
        self.hide()
        self.deleteLater()
        self.risposta.emit(esito)

    def keyPressEvent(self, evento):
        if evento.key() == Qt.Key.Key_Escape:
            self._chiudi(False)
        elif evento.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._chiudi(self.focusWidget() is self.si)
        else:
            evento.accept()

    def mousePressEvent(self, evento):
        evento.accept()  # i clic fuori dalla card non passano sotto

    def paintEvent(self, evento):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(8, 12, 22, 120 if not tema().scuro else 160))


def chiedi_conferma(ospite: QWidget, titolo: str, testo: str, testo_si: str, testo_no: str,
                    su_risposta: Callable[[bool], None], pericolo: bool = True) -> Conferma:
    """Mostra una conferma sopra ``ospite`` e chiama ``su_risposta(bool)``."""
    dialogo = Conferma(ospite, titolo, testo, testo_si, testo_no, pericolo)
    dialogo.risposta.connect(su_risposta)
    dialogo.apri()
    return dialogo


def contenitore_centrato(contenuto: QWidget, larghezza_max: int) -> QWidget:
    """Centra orizzontalmente ``contenuto`` limitandone la larghezza."""
    esterno = QWidget()
    lay = QHBoxLayout(esterno)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.addStretch(1)
    contenuto.setMaximumWidth(larghezza_max)
    lay.addWidget(contenuto, 100)
    lay.addStretch(1)
    return esterno


__all__ = [
    "AnelloPercentuale", "Card", "CardBandiera", "CardModalita", "Conferma", "EtichettaElisa",
    "IndicatoreAvanzamento",
    "Interruttore", "PulsanteRisposta", "Segmenti", "StackDissolvenza", "VistaBandiera",
    "chiedi_conferma", "contenitore_centrato", "disegna_bandiera", "dissolvi", "etichetta",
    "imposta_ruolo", "mescola", "pulsante", "separatore",
]
