"""Grafica disegnata con QPainter: logo, icone, illustrazioni, ombre.

Tutto è vettoriale e generato al volo, così resta nitido a ogni risoluzione
e si adatta ai colori del tema.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (QBrush, QColor, QIcon, QLinearGradient, QPainter, QPainterPath,
                           QPen, QPixmap)
from PySide6.QtWidgets import QApplication

from .tema import tema

# --------------------------------------------------------------------------- #
# Ombre
# --------------------------------------------------------------------------- #


def disegna_ombra(p: QPainter, r: QRectF, raggio: float, forza: float = 1.0,
                  estensione: int = 9, dy: float = 3.0) -> None:
    """Ombra morbida sotto un rettangolo arrotondato (strati semitrasparenti)."""
    base = tema().ombra * forza
    if base <= 0:
        return
    colore = tema().c("ombra")
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    for i in range(estensione, 0, -1):
        colore.setAlpha(max(1, int(base / estensione * 1.6 * (1 - i / (estensione + 1)))))
        p.setBrush(colore)
        rr = r.adjusted(-i * 0.7, -i * 0.5 + dy, i * 0.7, i * 0.9 + dy)
        p.drawRoundedRect(rr, raggio + i * 0.6, raggio + i * 0.6)
    p.restore()


# --------------------------------------------------------------------------- #
# Logo
# --------------------------------------------------------------------------- #

COLORI_LOGO = ("#FFC940", "#FFFFFF", "#FF5470")


def _onda(x0: float, larghezza: float, y: float, ampiezza: float, t: float) -> QPointF:
    """Punto di un bordo ondulato: l'onda cresce allontanandosi dall'asta."""
    return QPointF(x0 + t * larghezza, y + ampiezza * math.sin(2 * math.pi * t) * (0.35 + 0.65 * t))


def disegna_logo(p: QPainter, r: QRectF) -> None:
    """Logo del gioco: distintivo blu con asta e bandiera tricolore al vento."""
    s = min(r.width(), r.height())
    r = QRectF(r.center().x() - s / 2, r.center().y() - s / 2, s, s)
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    sfondo = QLinearGradient(r.topLeft(), r.bottomRight())
    sfondo.setColorAt(0.0, QColor("#3B82FF"))
    sfondo.setColorAt(1.0, QColor("#5B3DF5"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(sfondo))
    p.drawRoundedRect(r, s * 0.24, s * 0.24)

    # riflesso leggero in alto
    luce = QLinearGradient(r.topLeft(), QPointF(r.left(), r.center().y()))
    luce.setColorAt(0.0, QColor(255, 255, 255, 46))
    luce.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(QBrush(luce))
    p.drawRoundedRect(r, s * 0.24, s * 0.24)

    # asta e pomello
    asta_x = r.left() + s * 0.25
    p.setBrush(QColor("#FFFFFF"))
    p.drawRoundedRect(QRectF(asta_x, r.top() + s * 0.20, s * 0.06, s * 0.64), s * 0.03, s * 0.03)
    p.setBrush(QColor("#FFC940"))
    p.drawEllipse(QPointF(asta_x + s * 0.03, r.top() + s * 0.19), s * 0.05, s * 0.05)

    # bandiera ondulata a tre strisce
    x0 = asta_x + s * 0.06
    larghezza = s * 0.50
    y0 = r.top() + s * 0.24
    altezza = s * 0.36
    ampiezza = s * 0.035
    passi = 28
    for i, colore in enumerate(COLORI_LOGO):
        sopra = y0 + altezza * i / 3
        sotto = y0 + altezza * (i + 1) / 3
        striscia = QPainterPath(_onda(x0, larghezza, sopra, ampiezza, 0))
        for k in range(1, passi + 1):
            striscia.lineTo(_onda(x0, larghezza, sopra, ampiezza, k / passi))
        for k in range(passi, -1, -1):
            striscia.lineTo(_onda(x0, larghezza, sotto + (0.6 if i < 2 else 0), ampiezza, k / passi))
        striscia.closeSubpath()
        p.setBrush(QColor(colore))
        p.drawPath(striscia)
    p.restore()


def pixmap_logo(lato: int, dpr: float = 1.0) -> QPixmap:
    pix = QPixmap(int(lato * dpr), int(lato * dpr))
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    disegna_logo(p, QRectF(0, 0, lato * dpr, lato * dpr))
    p.end()
    pix.setDevicePixelRatio(dpr)
    return pix


def icona_app() -> QIcon:
    icona = QIcon()
    for lato in (16, 20, 24, 32, 40, 48, 64, 128, 256):
        icona.addPixmap(pixmap_logo(lato))
    return icona


# --------------------------------------------------------------------------- #
# Icone (griglia 24x24, tratto arrotondato)
# --------------------------------------------------------------------------- #

def _ingranaggio() -> QPainterPath:
    path = QPainterPath()
    denti, r_est, r_int = 8, 10.0, 7.6
    punti = []
    for k in range(denti):
        a = 2 * math.pi * k / denti
        for da, rr in ((-0.20, r_int), (-0.13, r_est), (0.13, r_est), (0.20, r_int)):
            punti.append(QPointF(12 + rr * math.cos(a + da), 12 + rr * math.sin(a + da)))
    path.moveTo(punti[0])
    for pt in punti[1:]:
        path.lineTo(pt)
    path.closeSubpath()
    path.addEllipse(QPointF(12, 12), 3.0, 3.0)
    return path


def _tracciato_icona(nome: str) -> tuple[QPainterPath, bool]:
    """Restituisce (tracciato, pieno)."""
    p = QPainterPath()
    pieno = False
    if nome == "gioca":
        p.moveTo(8, 5.5)
        p.lineTo(18.5, 12)
        p.lineTo(8, 18.5)
        p.closeSubpath()
        pieno = True
    elif nome == "trofeo":
        p.moveTo(7.5, 4)
        p.lineTo(16.5, 4)
        p.lineTo(16.5, 9)
        p.cubicTo(16.5, 12.5, 14.5, 14.5, 12, 14.5)
        p.cubicTo(9.5, 14.5, 7.5, 12.5, 7.5, 9)
        p.closeSubpath()
        p.moveTo(7.5, 6)
        p.cubicTo(4, 6, 4, 10.5, 7.8, 10.8)
        p.moveTo(16.5, 6)
        p.cubicTo(20, 6, 20, 10.5, 16.2, 10.8)
        p.moveTo(12, 14.5)
        p.lineTo(12, 17.5)
        p.moveTo(8.5, 20)
        p.lineTo(15.5, 20)
        p.moveTo(9.5, 17.5)
        p.lineTo(14.5, 17.5)
    elif nome == "ingranaggio":
        return _ingranaggio(), False
    elif nome == "indietro":
        p.moveTo(19, 12)
        p.lineTo(5.5, 12)
        p.moveTo(11, 6.5)
        p.lineTo(5.5, 12)
        p.lineTo(11, 17.5)
    elif nome == "avanti":
        p.moveTo(5, 12)
        p.lineTo(18.5, 12)
        p.moveTo(13, 6.5)
        p.lineTo(18.5, 12)
        p.lineTo(13, 17.5)
    elif nome == "cartella":
        p.moveTo(3.5, 7)
        p.lineTo(3.5, 18)
        p.cubicTo(3.5, 19, 4, 19.5, 5, 19.5)
        p.lineTo(19, 19.5)
        p.cubicTo(20, 19.5, 20.5, 19, 20.5, 18)
        p.lineTo(20.5, 9.5)
        p.cubicTo(20.5, 8.5, 20, 8, 19, 8)
        p.lineTo(12, 8)
        p.lineTo(10, 5.5)
        p.lineTo(5, 5.5)
        p.cubicTo(4, 5.5, 3.5, 6, 3.5, 7)
        p.closeSubpath()
    elif nome == "check":
        p.moveTo(5, 12.5)
        p.lineTo(10, 17.5)
        p.lineTo(19, 7)
    elif nome == "croce":
        p.moveTo(6.5, 6.5)
        p.lineTo(17.5, 17.5)
        p.moveTo(17.5, 6.5)
        p.lineTo(6.5, 17.5)
    elif nome == "orologio":
        p.addEllipse(QPointF(12, 12), 8.5, 8.5)
        p.moveTo(12, 7.5)
        p.lineTo(12, 12)
        p.lineTo(15, 14)
    elif nome == "casa":
        p.moveTo(4, 11)
        p.lineTo(12, 4.5)
        p.lineTo(20, 11)
        p.moveTo(6.5, 9.5)
        p.lineTo(6.5, 19.5)
        p.lineTo(17.5, 19.5)
        p.lineTo(17.5, 9.5)
    elif nome == "ricarica":
        rett = QRectF(4.5, 4.5, 15, 15)
        p.arcMoveTo(rett, 60)
        p.arcTo(rett, 60, 280)
        p.moveTo(17.5, 3.5)
        p.lineTo(17.2, 8.3)
        p.lineTo(12.6, 7.6)
    elif nome == "avviso":
        p.moveTo(12, 4)
        p.lineTo(21, 19.5)
        p.lineTo(3, 19.5)
        p.closeSubpath()
        p.moveTo(12, 9.5)
        p.lineTo(12, 13.5)
        p.moveTo(12, 16.6)
        p.lineTo(12, 16.7)
    elif nome == "info":
        p.addEllipse(QPointF(12, 12), 8.5, 8.5)
        p.moveTo(12, 11)
        p.lineTo(12, 16)
        p.moveTo(12, 8)
        p.lineTo(12, 8.1)
    elif nome == "grafico":
        p.moveTo(4, 20)
        p.lineTo(20, 20)
        for x, cima in ((7, 13), (12, 6), (17, 10)):
            p.moveTo(x, 17)
            p.lineTo(x, cima)
    elif nome == "bandiera":
        p.moveTo(6, 21)
        p.lineTo(6, 4)
        p.moveTo(6, 4.5)
        p.cubicTo(10, 2.5, 13, 7, 18.5, 5)
        p.lineTo(18.5, 13)
        p.cubicTo(13, 15, 10, 10.5, 6, 12.5)
    return p, pieno


def disegna_icona(p: QPainter, nome: str, r: QRectF, colore: QColor, spessore: float = 2.0) -> None:
    """Disegna l'icona ``nome`` nel rettangolo ``r``."""
    path, pieno = _tracciato_icona(nome)
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(r.topLeft())
    p.scale(r.width() / 24.0, r.height() / 24.0)
    if pieno:
        p.setPen(QPen(colore, spessore, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                      Qt.PenJoinStyle.RoundJoin))
        p.setBrush(colore)
    else:
        p.setPen(QPen(colore, spessore, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                      Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(path)
    p.restore()


def icona(nome: str, colore: QColor, lato: int = 20) -> QIcon:
    """QIcon nitida anche su schermi ad alta densità."""
    app = QApplication.instance()
    dpr = app.devicePixelRatio() if app else 1.0
    risultato = QIcon()
    for fattore in sorted({1.0, dpr, 2.0}):
        pix = QPixmap(int(lato * fattore), int(lato * fattore))
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        disegna_icona(p, nome, QRectF(0, 0, lato * fattore, lato * fattore), colore)
        p.end()
        pix.setDevicePixelRatio(fattore)
        risultato.addPixmap(pix)
    return risultato


def imposta_icona(pulsante, nome: str, chiave_colore: str = "testo_secondario", lato: int = 18) -> None:
    """Assegna un'icona a un pulsante e la ricorda per i cambi di tema."""
    pulsante.setProperty("icona_nome", nome)
    pulsante.setProperty("icona_colore", chiave_colore)
    pulsante.setIcon(icona(nome, tema().c(chiave_colore), lato))
    pulsante.setIconSize(QSize(lato, lato))


def aggiorna_icone(radice) -> None:
    """Ridisegna le icone dei pulsanti con i colori del tema corrente."""
    from PySide6.QtWidgets import QAbstractButton
    for pulsante in radice.findChildren(QAbstractButton):
        nome = pulsante.property("icona_nome")
        if nome:
            lato = pulsante.iconSize().width()
            pulsante.setIcon(icona(nome, tema().c(pulsante.property("icona_colore")), lato))


# --------------------------------------------------------------------------- #
# Illustrazioni delle card delle modalità
# --------------------------------------------------------------------------- #

def _mini_bandiera(p: QPainter, r: QRectF, colori: tuple[str, ...], verticale: bool = False,
                   bordo: QColor | None = None) -> None:
    p.save()
    clip = QPainterPath()
    clip.addRoundedRect(r, 3, 3)
    p.setClipPath(clip)
    n = len(colori)
    for i, c in enumerate(colori):
        if verticale:
            rr = QRectF(r.left() + r.width() * i / n, r.top(), r.width() / n + 0.5, r.height())
        else:
            rr = QRectF(r.left(), r.top() + r.height() * i / n, r.width(), r.height() / n + 0.5)
        p.fillRect(rr, QColor(c))
    p.restore()
    p.setPen(QPen(bordo or tema().c("bordo_bandiera"), 1))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), 3, 3)


def _badge(p: QPainter, centro: QPointF, raggio: float, colore: QColor, simbolo: str) -> None:
    p.setPen(QPen(tema().c("superficie"), 2.5))
    p.setBrush(colore)
    p.drawEllipse(centro, raggio, raggio)
    if simbolo == "?":
        f = p.font()
        f.setPixelSize(int(raggio * 1.3))
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("#FFFFFF"))
        p.drawText(QRectF(centro.x() - raggio, centro.y() - raggio, 2 * raggio, 2 * raggio),
                   Qt.AlignmentFlag.AlignCenter, "?")
    else:
        lato = raggio * 1.25
        disegna_icona(p, simbolo, QRectF(centro.x() - lato / 2, centro.y() - lato / 2, lato, lato),
                      QColor("#FFFFFF"), 3.0)


def illustrazione_flag(p: QPainter, r: QRectF) -> None:
    """Una bandiera grande con il punto di domanda e quattro risposte."""
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    h = r.height()
    fb = QRectF(r.left() + r.width() * 0.10, r.center().y() - h * 0.30, h * 0.90, h * 0.60)
    disegna_ombra(p, fb, 4, 0.6, 5, 2)
    _mini_bandiera(p, fb, ("#22B573", "#FFFFFF", "#FF5A5F"), verticale=True)
    _badge(p, QPointF(fb.right() - 2, fb.top() + 2), h * 0.12, tema().c("primario"), "?")
    x = fb.right() + r.width() * 0.10
    larghezza = r.right() - x - r.width() * 0.08
    altezza = h * 0.13
    passo = h * 0.19
    y = r.center().y() - (passo * 3 + altezza) / 2
    for i in range(4):
        rr = QRectF(x, y + i * passo, larghezza, altezza)
        giusta = i == 1
        p.setPen(QPen(tema().c("successo") if giusta else tema().c("bordo_forte"), 1.4))
        p.setBrush(tema().c("successo_tenue") if giusta else tema().c("superficie"))
        p.drawRoundedRect(rr, altezza / 2, altezza / 2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(tema().c("successo") if giusta else tema().c("bordo_forte"))
        p.drawRoundedRect(QRectF(rr.left() + altezza * 0.6, rr.center().y() - 2.5,
                                 larghezza * (0.45 if i % 2 else 0.6), 5), 2.5, 2.5)
    p.restore()


def illustrazione_country(p: QPainter, r: QRectF) -> None:
    """Un nome (barra di testo) e quattro bandiere in griglia 2x2."""
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    h = r.height()
    # "nome dello stato"
    nome = QRectF(r.left() + r.width() * 0.08, r.center().y() - h * 0.11, r.width() * 0.30, h * 0.22)
    p.setPen(QPen(tema().c("primario"), 1.4))
    p.setBrush(tema().c("superficie"))
    p.drawRoundedRect(nome, nome.height() / 2, nome.height() / 2)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(tema().c("primario"))
    p.drawRoundedRect(QRectF(nome.left() + nome.height() * 0.5, nome.center().y() - 3,
                             nome.width() - nome.height(), 6), 3, 3)
    # griglia di bandiere
    lb, hb, gap = h * 0.50, h * 0.33, h * 0.08
    x0 = r.right() - r.width() * 0.08 - 2 * lb - gap
    y0 = r.center().y() - hb - gap / 2
    disegni = [
        (("#0052B4", "#FFFFFF", "#D80027"), False),
        (("#FFDA44", "#D80027"), False),
        (("#009246", "#FFFFFF", "#CE2B37"), True),
        (("#000000", "#FFCE00", "#DD0000"), True),
    ]
    for i, (colori, vert) in enumerate(disegni):
        rr = QRectF(x0 + (i % 2) * (lb + gap), y0 + (i // 2) * (hb + gap), lb, hb)
        giusta = i == 2
        disegna_ombra(p, rr, 3, 0.5, 4, 1.5)
        _mini_bandiera(p, rr, colori, vert, tema().c("successo") if giusta else None)
        if giusta:
            p.setPen(QPen(tema().c("successo"), 2.4))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(rr.adjusted(-3, -3, 3, 3), 5, 5)
            _badge(p, QPointF(rr.right() + 1, rr.top() - 1), h * 0.085, tema().c("successo"), "check")
    # freccia tra nome e griglia
    p.setPen(QPen(tema().c("testo_terziario"), 1.6, Qt.PenStyle.DashLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(nome.right() + 8, nome.center().y()), QPointF(x0 - 10, nome.center().y()))
    p.restore()
