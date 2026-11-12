"""Controlli sulla struttura del codice e sui moduli senza interfaccia."""

from __future__ import annotations

import subprocess
import sys
import wave

from flaggame.suoni import MELODIE, Suoni, genera_wav

from .conftest import RADICE_PROGETTO

MODULI_LOGICA = ["flaggame.dati", "flaggame.generatore", "flaggame.partita", "flaggame.classifica",
                 "flaggame.persistenza", "flaggame.suoni", "flaggame.percorsi", "flaggame.testi"]


def test_la_logica_non_importa_qt():
    """Generatore, partita, classifica & co. si usano senza PySide6."""
    codice = (
        "import sys\n"
        f"for m in {MODULI_LOGICA!r}:\n"
        "    __import__(m)\n"
        "qt = sorted(m for m in sys.modules if m.startswith(('PySide6', 'shiboken')))\n"
        "print(qt)\n"
        "sys.exit(1 if qt else 0)\n"
    )
    esito = subprocess.run([sys.executable, "-c", codice], cwd=RADICE_PROGETTO,
                           capture_output=True, text=True)
    assert esito.returncode == 0, esito.stdout + esito.stderr


def test_testi_completi():
    from flaggame import testi
    assert set(testi.LIVELLI) == {"facile", "intermedio", "difficile", "nerd"}
    assert set(testi.CONTINENTI) == {"europa", "asia", "africa", "america_nord", "america_sud", "oceania"}
    assert testi.MODALITA == {"flag": "Guess the Flag", "country": "Guess the Country"}


def test_suoni_generati(tmp_path):
    for nome in MELODIE:
        percorso = tmp_path / f"{nome}.wav"
        genera_wav(percorso, nome)
        with wave.open(str(percorso)) as f:
            assert f.getnchannels() == 1 and f.getsampwidth() == 2
            durata = f.getnframes() / f.getframerate()
            assert 0.1 < durata < 1.5
    spenti = Suoni(tmp_path / "suoni", abilitati=False)
    spenti.suona("giusto")                     # disattivati: non fa nulla
    assert not (tmp_path / "suoni").exists()
