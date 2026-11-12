"""Controlli sulla struttura del codice e sui moduli senza interfaccia."""

from __future__ import annotations

import string
import subprocess
import sys
import wave

from flaggame.suoni import MELODIE, Suoni, genera_wav

from .conftest import RADICE_PROGETTO

MODULI_LOGICA = ["flaggame.dati", "flaggame.generatore", "flaggame.partita", "flaggame.classifica",
                 "flaggame.persistenza", "flaggame.suoni", "flaggame.percorsi", "flaggame.testi",
                 "flaggame.statistiche"]


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


def _segnaposto(valore) -> set:
    """Segnaposto {n}, {nome}... contenuti in un testo (anche dentro liste e dizionari)."""
    if isinstance(valore, str):
        return {campo for _, campo, _, _ in string.Formatter().parse(valore) if campo is not None}
    if isinstance(valore, dict):
        return {(k, s) for k, v in valore.items() for s in _segnaposto(v)}
    if isinstance(valore, (list, tuple)):
        return {(i, s) for i, v in enumerate(valore) for s in _segnaposto(v)}
    return set()


def test_testi_completi():
    from flaggame import testi
    for codice in testi.LINGUE:
        testi.imposta_lingua(codice)
        assert set(testi.LIVELLI) == {"facile", "intermedio", "difficile", "nerd"}
        assert set(testi.CONTINENTI) == {"europa", "asia", "africa", "america_nord", "america_sud", "oceania"}
        assert testi.MODALITA == {"flag": "Guess the Flag", "country": "Guess the Country"}
    testi.imposta_lingua("it")


def test_tutte_le_lingue_hanno_gli_stessi_testi():
    """Stessi nomi, stesse chiavi e stessi segnaposto ({n}, {nome}...) in ogni lingua."""
    from flaggame import testi
    italiano = testi.testi_di("it")
    for codice in testi.LINGUE:
        altra = testi.testi_di(codice)
        assert set(altra) == set(italiano), codice
        for nome, valore in italiano.items():
            assert type(altra[nome]) is type(valore), (codice, nome)
            if isinstance(valore, dict):
                assert set(altra[nome]) == set(valore), (codice, nome)
            if isinstance(valore, list):
                assert [x[0] for x in altra[nome]] == [x[0] for x in valore], (codice, nome)
            assert _segnaposto(altra[nome]) == _segnaposto(valore), (codice, nome)


def test_cambio_lingua_e_lingua_di_sistema():
    from flaggame import testi
    assert testi.imposta_lingua("en") == "en" and testi.HOME_GIOCA == "Play"
    assert testi.imposta_lingua("xx") == "it" and testi.HOME_GIOCA == "Gioca"
    assert testi.lingua_di_sistema("it_IT") == "it"
    assert testi.lingua_di_sistema("it_CH") == "it"
    assert testi.lingua_di_sistema("en_GB") == "en"
    assert testi.lingua_di_sistema("de_DE") == "en"


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
