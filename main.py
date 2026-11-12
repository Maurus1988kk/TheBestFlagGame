"""Avvia The Best Flag Game.

    python main.py              avvia il gioco
    python main.py --verifica   avvio di prova senza finestre (codice di uscita 0 = tutto ok)
"""

import sys

from flaggame.ui.app import avvia, verifica

if __name__ == "__main__":
    sys.exit(verifica() if "--verifica" in sys.argv else avvia())
