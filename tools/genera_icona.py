"""Rigenera assets/icona.ico e assets/icona.png dal logo disegnato con Qt.

    python tools/genera_icona.py

Serve solo se si cambia il logo (flaggame/ui/grafica.py): l'icona è già
inclusa nel progetto. Richiede Pillow per scrivere un .ico multi-risoluzione.
"""

from __future__ import annotations

import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))

from PIL import Image  # noqa: E402
from PySide6.QtCore import QBuffer, QIODevice  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

from flaggame.ui.grafica import pixmap_logo  # noqa: E402

LATI = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def pil_da_pixmap(pix) -> Image.Image:
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    pix.save(buffer, "PNG")
    import io
    return Image.open(io.BytesIO(bytes(buffer.data()))).convert("RGBA")


def main() -> None:
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    cartella = RADICE / "assets"
    cartella.mkdir(exist_ok=True)
    immagini = [pil_da_pixmap(pixmap_logo(lato)) for lato in LATI]
    immagini[-1].save(cartella / "icona.png")
    immagini[-1].save(cartella / "icona.ico", format="ICO", sizes=[(l, l) for l in LATI],
                      append_images=immagini[:-1])
    print("Creati:", cartella / "icona.ico", cartella / "icona.png")
    app.quit()


if __name__ == "__main__":
    main()
