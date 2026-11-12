"""Temi chiaro e scuro: palette dei colori e foglio di stile QSS.

I widget disegnati a mano (bandiere, pulsanti di risposta, card...) leggono i
colori da ``tema()`` al momento del disegno; i widget standard vengono
stilizzati dal foglio QSS generato qui.
"""

from __future__ import annotations

from pathlib import Path
from string import Template

from PySide6.QtCore import QObject, QPointF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QApplication

FONT = "Segoe UI"
SEMIBOLD = QFont.Weight.DemiBold
GRASSETTO = QFont.Weight.Bold

PALETTE = {
    "chiaro": {
        "sfondo": "#F2F4F9",
        "superficie": "#FFFFFF",
        "superficie_alt": "#F4F6FB",
        "superficie_hover": "#F3F6FF",
        "bordo": "#E2E7F0",
        "bordo_forte": "#CBD3E1",
        "testo": "#141B2D",
        "testo_secondario": "#5A6579",
        "testo_terziario": "#8B95A8",
        "primario": "#2F6BFF",
        "primario_hover": "#2160F0",
        "primario_premuto": "#1A4FCC",
        "primario_tenue": "#E7EEFF",
        "su_primario": "#FFFFFF",
        "successo": "#15A150",
        "successo_tenue": "#E2F6EA",
        "errore": "#E1444A",
        "errore_tenue": "#FDE9EA",
        "avviso": "#A15C07",
        "avviso_tenue": "#FDF1D8",
        "bordo_bandiera": "#C3CAD7",
        "ombra": "#101828",
        "oro": "#E9A700",
        "argento": "#9AA5B8",
        "bronzo": "#C27A3A",
    },
    "scuro": {
        "sfondo": "#0D121C",
        "superficie": "#151C2A",
        "superficie_alt": "#1B2333",
        "superficie_hover": "#1E2840",
        "bordo": "#263047",
        "bordo_forte": "#35415B",
        "testo": "#E9EEF7",
        "testo_secondario": "#A2ADC1",
        "testo_terziario": "#717D95",
        "primario": "#5B8CFF",
        "primario_hover": "#729DFF",
        "primario_premuto": "#4674EC",
        "primario_tenue": "#1C2A4D",
        "su_primario": "#FFFFFF",
        "successo": "#2FC56A",
        "successo_tenue": "#11301F",
        "errore": "#F2666C",
        "errore_tenue": "#3A191D",
        "avviso": "#F5B83D",
        "avviso_tenue": "#33280F",
        "bordo_bandiera": "#55627C",
        "ombra": "#000000",
        "oro": "#F2B91C",
        "argento": "#AEB8CA",
        "bronzo": "#D08B4F",
    },
}

# Intensità delle ombre disegnate a mano (alfa massimo del bordo).
INTENSITA_OMBRA = {"chiaro": 26, "scuro": 70}


class Tema(QObject):
    """Tema corrente; emette ``cambiato`` quando l'utente lo cambia."""

    cambiato = Signal(str)

    def __init__(self):
        super().__init__()
        self.nome = "chiaro"

    def c(self, chiave: str, alfa: int | None = None) -> QColor:
        """Colore della palette corrente (con trasparenza opzionale 0-255)."""
        colore = QColor(PALETTE[self.nome][chiave])
        if alfa is not None:
            colore.setAlpha(alfa)
        return colore

    @property
    def scuro(self) -> bool:
        return self.nome == "scuro"

    @property
    def ombra(self) -> int:
        return INTENSITA_OMBRA[self.nome]


_tema = Tema()


def tema() -> Tema:
    return _tema


def font(pixel: int, peso: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Font dell'interfaccia di ``pixel`` pixel logici."""
    f = QFont(FONT)
    f.setPixelSize(pixel)
    f.setWeight(peso)
    f.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    return f


def _freccia(colore: str, percorso: Path) -> str:
    """Disegna la freccina dei menu a tendina e restituisce il percorso per il QSS."""
    pix = QPixmap(24, 24)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    penna = QPen(QColor(colore), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                 Qt.PenJoinStyle.RoundJoin)
    p.setPen(penna)
    linea = QPainterPath(QPointF(7, 10))
    linea.lineTo(12, 15)
    linea.lineTo(17, 10)
    p.drawPath(linea)
    p.end()
    pix.save(str(percorso), "PNG")
    return percorso.as_posix()


QSS = Template(r"""
* { font-family: "$font"; }
QWidget { color: $testo; font-size: 14px; }
QMainWindow, #radice { background: $sfondo; }
QWidget#schermata { background: $sfondo; }
QToolTip { background: $superficie; color: $testo; border: 1px solid $bordo_forte;
           border-radius: 6px; padding: 6px 8px; }

QLabel { background: transparent; }
QLabel[ruolo="titolo"] { font-size: 28px; font-weight: 700; }
QLabel[ruolo="titolo_medio"] { font-size: 22px; font-weight: 700; }
QLabel[ruolo="sottotitolo"] { font-size: 15px; color: $testo_secondario; }
QLabel[ruolo="sezione"] { font-size: 12px; font-weight: 700; color: $testo_terziario; }
QLabel[ruolo="secondario"] { color: $testo_secondario; }
QLabel[ruolo="terziario"] { color: $testo_terziario; font-size: 13px; }
QLabel[ruolo="forte"] { font-weight: 600; font-size: 15px; }
QLabel[ruolo="info"] { color: $testo_secondario; font-size: 13px; padding: 8px 12px;
                       background: $superficie_alt; border-radius: 10px; }
QLabel[ruolo="avviso"] { color: $avviso; font-size: 13px; font-weight: 600; padding: 8px 12px;
                         background: $avviso_tenue; border-radius: 10px; }
QLabel[ruolo="errore"] { color: $errore; font-size: 13px; font-weight: 600; padding: 8px 12px;
                         background: $errore_tenue; border-radius: 10px; }
QLabel[ruolo="chip"] { color: $testo_secondario; font-size: 12px; font-weight: 600;
                       background: $superficie_alt; border: 1px solid $bordo;
                       border-radius: 11px; padding: 3px 10px; }
QLabel[ruolo="timer"] { font-size: 26px; font-weight: 600; color: $testo; }
QLabel[ruolo="timer_pausa"] { font-size: 26px; font-weight: 600; color: $testo_terziario; }
QLabel[ruolo="contatore"] { font-size: 14px; font-weight: 600; color: $testo_secondario; }
QLabel[ruolo="domanda"] { font-size: 17px; color: $testo_secondario; }
QLabel[ruolo="stato_nome"] { font-size: 40px; font-weight: 700; color: $testo; }
QLabel[ruolo="esito_giusto"] { font-size: 16px; font-weight: 700; color: $successo; }
QLabel[ruolo="esito_sbagliato"] { font-size: 16px; font-weight: 700; color: $errore; }

QPushButton { border-radius: 10px; padding: 9px 18px; font-size: 14px; font-weight: 600;
              border: 1px solid $bordo; background: $superficie; color: $testo; }
QPushButton:hover { background: $superficie_hover; border-color: $bordo_forte; }
QPushButton:pressed { background: $superficie_alt; }
QPushButton:disabled { color: $testo_terziario; background: $superficie_alt; border-color: $bordo; }
QPushButton:focus { outline: none; }
QPushButton[variante="primario"] { background: $primario; color: $su_primario; border: 1px solid $primario; }
QPushButton[variante="primario"]:hover { background: $primario_hover; border-color: $primario_hover; }
QPushButton[variante="primario"]:pressed { background: $primario_premuto; border-color: $primario_premuto; }
QPushButton[variante="primario"]:disabled { background: $bordo; border-color: $bordo; color: $testo_terziario; }
QPushButton[variante="grande"] { background: $primario; color: $su_primario; border: 1px solid $primario;
                                 font-size: 17px; font-weight: 700; padding: 13px 34px; border-radius: 14px; }
QPushButton[variante="grande"]:hover { background: $primario_hover; border-color: $primario_hover; }
QPushButton[variante="grande"]:pressed { background: $primario_premuto; border-color: $primario_premuto; }
QPushButton[variante="grande"]:disabled { background: $bordo; border-color: $bordo; color: $testo_terziario; }
QPushButton[variante="fantasma"] { background: transparent; border: 1px solid transparent; color: $testo_secondario; }
QPushButton[variante="fantasma"]:hover { background: $superficie_alt; color: $testo; }
QPushButton[variante="fantasma"]:pressed { background: $bordo; }
QPushButton[variante="pericolo"] { background: $superficie; color: $errore; border: 1px solid $bordo; }
QPushButton[variante="pericolo"]:hover { background: $errore_tenue; border-color: $errore; }
QPushButton[variante="pericolo_pieno"] { background: $errore; color: #FFFFFF; border: 1px solid $errore; }
QPushButton[variante="pericolo_pieno"]:hover { background: $errore; border-color: $testo; }

QLineEdit { background: $superficie; border: 1px solid $bordo_forte; border-radius: 10px;
            padding: 9px 12px; font-size: 15px; selection-background-color: $primario;
            selection-color: #FFFFFF; }
QLineEdit:focus { border: 2px solid $primario; padding: 8px 11px; }
QLineEdit:disabled { color: $testo_secondario; background: $superficie_alt; }

QComboBox { background: $superficie; border: 1px solid $bordo_forte; border-radius: 10px;
            padding: 8px 12px; padding-right: 34px; font-size: 14px; min-height: 22px; }
QComboBox:hover { border-color: $primario; }
QComboBox:focus { border-color: $primario; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: center right;
                       width: 30px; border: none; }
QComboBox::down-arrow { image: url("$freccia"); width: 16px; height: 16px; }
QComboBox QAbstractItemView { background: $superficie; border: 1px solid $bordo_forte;
                              padding: 4px; outline: none; selection-background-color: $primario_tenue;
                              selection-color: $testo; }
QComboBox QAbstractItemView::item { min-height: 32px; padding: 0 10px; border-radius: 6px; color: $testo; }
QComboBox QAbstractItemView::item:hover { background: $superficie_hover; }
QComboBox QAbstractItemView::item:selected { background: $primario_tenue; color: $testo; }
QComboBox QAbstractItemView::item:disabled { color: $testo_terziario; }

QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: $bordo_forte; border-radius: 3px; min-height: 36px; }
QScrollBar::handle:vertical:hover { background: $testo_terziario; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: $bordo_forte; border-radius: 3px; min-width: 36px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QTableWidget { background: transparent; border: none; gridline-color: transparent;
               font-size: 14px; outline: none; }
QHeaderView { background: transparent; }
QHeaderView::section { background: transparent; color: $testo_terziario; font-size: 12px;
                       font-weight: 700; border: none; border-bottom: 1px solid $bordo_forte;
                       padding: 10px 10px; }
QTableCornerButton::section { background: transparent; border: none; }

QFrame[ruolo="separatore"] { background: $bordo; max-height: 1px; min-height: 1px; border: none; }
""")


def applica_tema(nome: str, cartella_cache: Path) -> None:
    """Imposta il tema su tutta l'applicazione e avvisa i widget."""
    if nome not in PALETTE:
        nome = "chiaro"
    _tema.nome = nome
    app = QApplication.instance()
    cartella_cache.mkdir(parents=True, exist_ok=True)
    colori = dict(PALETTE[nome])
    colori["font"] = FONT
    colori["freccia"] = _freccia(colori["testo_secondario"], cartella_cache / f"freccia_{nome}.png")
    app.setStyleSheet(QSS.substitute(colori))
    for w in app.allWidgets():
        w.update()
    _tema.cambiato.emit(nome)


def ripolish(widget) -> None:
    """Riapplica lo stile dopo aver cambiato una proprietà usata nel QSS."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
