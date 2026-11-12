"""Configurazione comune dei test."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RADICE_PROGETTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE_PROGETTO))

from flaggame.dati import carica_catalogo, carica_configurazione  # noqa: E402

CARTELLA_BANDIERE = RADICE_PROGETTO / "flags"


@pytest.fixture(scope="session")
def config():
    return carica_configurazione(RADICE_PROGETTO / "dati")


@pytest.fixture(scope="session")
def catalogo(config):
    if not CARTELLA_BANDIERE.is_dir():
        pytest.skip("cartella flags non presente")
    return carica_catalogo(CARTELLA_BANDIERE, config)


@pytest.fixture(autouse=True)
def dati_utente_temporanei(tmp_path, monkeypatch):
    """Nessun test scrive nella vera cartella %APPDATA%\\FlagGame."""
    monkeypatch.setenv("FLAGGAME_DATI_UTENTE", str(tmp_path / "utente"))
