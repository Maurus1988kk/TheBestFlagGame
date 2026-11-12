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
def dati_utente_temporanei(tmp_path_factory, monkeypatch):
    """Nessun test scrive nella vera cartella %APPDATA%\\FlagGame.

    La cartella sta fuori da ``tmp_path``, che resta vuota per i test. La
    lingua è fissata all'italiano (al primo avvio il gioco seguirebbe la
    lingua di Windows) e viene ripristinata dopo ogni test."""
    from flaggame import testi
    cartella = tmp_path_factory.mktemp("utente")
    (cartella / "impostazioni.json").write_text('{"lingua": "it"}', encoding="utf-8")
    monkeypatch.setenv("FLAGGAME_DATI_UTENTE", str(cartella))
    yield
    testi.imposta_lingua("it")
