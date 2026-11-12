"""Caricamento e cache delle immagini delle bandiere (PNG, JPG, GIF, SVG...).

Il formato viene riconosciuto dal contenuto del file, quindi funziona anche
con file dall'estensione sbagliata (es. un JPEG salvato come .png).
"""

from __future__ import annotations

import os
from collections import OrderedDict
from pathlib import Path

from PySide6.QtCore import QRect, QRectF, QSize, Qt
from PySide6.QtGui import QBitmap, QImage, QImageReader, QPainter, QPixmap, QRegion
from PySide6.QtSvg import QSvgRenderer

LATO_MASSIMO_SORGENTE = 1400  # le immagini enormi vengono ridotte già in lettura


def percorso_normale(percorso) -> str:
    """Percorso assoluto e senza differenze di maiuscole (per i confronti)."""
    return os.path.normcase(os.path.abspath(str(percorso)))


def _riquadro_contenuto(maschera: QImage, sfondo: tuple[int, int]) -> QRect:
    """Rettangolo che racchiude il contenuto (non lo sfondo) di una maschera
    monocromatica. ``sfondo`` è un pixel che sicuramente è sfondo.

    La convenzione dei bit (1 = sfondo o 1 = contenuto) cambia tra le funzioni
    di Qt, quindi si provano la maschera e la sua inversa e si tiene il
    rettangolo che esclude il pixel di sfondo."""
    for tentativo in range(2):
        if tentativo:
            maschera = maschera.copy()
            maschera.invertPixels()
        r = QRegion(QBitmap.fromImage(maschera)).boundingRect()
        if r.isValid() and not r.contains(*sfondo):
            return r
    return QRect(0, 0, maschera.width(), maschera.height())


def ritaglia_bordi(immagine: QImage, sfondo_uniforme: bool = False) -> QImage:
    """Toglie i bordi trasparenti (sempre) e, se richiesto, lo sfondo uniforme
    del colore dell'angolo in alto a destra. Il file su disco non viene toccato."""
    immagine = immagine.convertToFormat(QImage.Format.Format_ARGB32)
    w, h = immagine.width(), immagine.height()
    rettangolo = immagine.rect()
    angoli = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    trasparenti = [a for a in angoli if immagine.hasAlphaChannel() and immagine.pixelColor(*a).alpha() == 0]
    if trasparenti:
        rettangolo = _riquadro_contenuto(immagine.createAlphaMask(), trasparenti[0])
    if sfondo_uniforme:
        maschera = immagine.createMaskFromColor(immagine.pixel(w - 1, 0), Qt.MaskMode.MaskInColor)
        rettangolo = rettangolo.intersected(_riquadro_contenuto(maschera, (w - 1, 0)))
    if rettangolo.isValid() and not rettangolo.isEmpty() and rettangolo != immagine.rect():
        immagine = immagine.copy(rettangolo)
    return immagine


class CacheImmagini:
    """Tiene in memoria le ultime immagini usate e le loro versioni scalate."""

    def __init__(self, max_sorgenti: int = 120, max_scalate: int = 240):
        self._sorgenti: OrderedDict[str, QImage | QSvgRenderer | None] = OrderedDict()
        self._scalate: OrderedDict[tuple, QPixmap] = OrderedDict()
        self.max_sorgenti = max_sorgenti
        self.max_scalate = max_scalate
        self._da_ritagliare: set[str] = set()   # file con sfondo uniforme da togliere

    @property
    def da_ritagliare(self) -> set[str]:
        return set(self._da_ritagliare)

    @da_ritagliare.setter
    def da_ritagliare(self, percorsi) -> None:
        self._da_ritagliare = {percorso_normale(p) for p in percorsi}

    def svuota(self) -> None:
        self._sorgenti.clear()
        self._scalate.clear()

    # ------------------------------------------------------------ sorgenti

    def _carica(self, percorso: str):
        if percorso.lower().endswith(".svg"):
            renderer = QSvgRenderer(percorso)
            return renderer if renderer.isValid() else None
        lettore = QImageReader(percorso)
        lettore.setDecideFormatFromContent(True)
        lettore.setAutoTransform(True)
        dimensione = lettore.size()
        if dimensione.isValid() and max(dimensione.width(), dimensione.height()) > LATO_MASSIMO_SORGENTE:
            lettore.setScaledSize(dimensione.scaled(LATO_MASSIMO_SORGENTE, LATO_MASSIMO_SORGENTE,
                                                    Qt.AspectRatioMode.KeepAspectRatio))
        immagine = lettore.read()
        if immagine.isNull():
            # ultimo tentativo: SVG con estensione diversa
            renderer = QSvgRenderer(percorso)
            return renderer if renderer.isValid() else None
        immagine = ritaglia_bordi(immagine, percorso_normale(percorso) in self._da_ritagliare)
        return immagine.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)

    def _sorgente(self, percorso: Path | str):
        chiave = str(percorso)
        if chiave in self._sorgenti:
            self._sorgenti.move_to_end(chiave)
            return self._sorgenti[chiave]
        sorgente = self._carica(chiave)
        self._sorgenti[chiave] = sorgente
        while len(self._sorgenti) > self.max_sorgenti:
            self._sorgenti.popitem(last=False)
        return sorgente

    def dimensione(self, percorso: Path | str | None) -> QSize:
        """Dimensione originale (serve per il rapporto larghezza/altezza)."""
        if not percorso:
            return QSize()
        s = self._sorgente(percorso)
        if s is None:
            return QSize()
        if isinstance(s, QSvgRenderer):
            return s.defaultSize()
        return s.size()

    def precarica(self, percorsi) -> None:
        for percorso in percorsi:
            self._sorgente(percorso)

    # ------------------------------------------------------------- scalate

    def pixmap(self, percorso: Path | str, larghezza: int, altezza: int, dpr: float = 1.0) -> QPixmap | None:
        """Immagine adattata a ``larghezza`` x ``altezza`` (pixel logici),
        mantenendo le proporzioni originali."""
        if larghezza <= 0 or altezza <= 0:
            return None
        chiave = (str(percorso), larghezza, altezza, round(dpr, 2))
        if chiave in self._scalate:
            self._scalate.move_to_end(chiave)
            return self._scalate[chiave]
        sorgente = self._sorgente(percorso)
        if sorgente is None:
            return None
        lw, lh = max(1, round(larghezza * dpr)), max(1, round(altezza * dpr))
        if isinstance(sorgente, QSvgRenderer):
            destinazione = sorgente.defaultSize().scaled(lw, lh, Qt.AspectRatioMode.KeepAspectRatio)
            immagine = QImage(destinazione, QImage.Format.Format_ARGB32_Premultiplied)
            immagine.fill(Qt.GlobalColor.transparent)
            p = QPainter(immagine)
            sorgente.render(p, QRectF(0, 0, destinazione.width(), destinazione.height()))
            p.end()
        else:
            immagine = sorgente.scaled(lw, lh, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
        pix = QPixmap.fromImage(immagine)
        pix.setDevicePixelRatio(dpr)
        self._scalate[chiave] = pix
        while len(self._scalate) > self.max_scalate:
            self._scalate.popitem(last=False)
        return pix
