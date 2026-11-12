"""Percorsi dell'applicazione: cartella del programma, risorse, dati utente.

Funziona sia avviando ``main.py`` con Python sia dall'eseguibile creato con
PyInstaller (in quel caso ``sys.frozen`` è vero).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

NOME_CARTELLA_UTENTE = "FlagGame"
NOME_CARTELLA_BANDIERE = "flags"


def eseguibile_congelato() -> bool:
    """Vero se il programma gira come eseguibile PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def cartella_app() -> Path:
    """Cartella che contiene l'eseguibile (o ``main.py`` in sviluppo)."""
    if eseguibile_congelato():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def cartella_risorse() -> Path:
    """Cartella delle risorse incluse nel programma (dati/, assets/)."""
    if eseguibile_congelato():
        return Path(getattr(sys, "_MEIPASS", cartella_app()))
    return cartella_app()


def cartella_dati_app() -> Path:
    """Cartella con nomi.json, continenti.json e livelli.json.

    Se accanto all'eseguibile esiste una cartella ``dati`` modificabile viene
    usata quella, altrimenti la copia inclusa nel programma.
    """
    esterna = cartella_app() / "dati"
    if (esterna / "livelli.json").is_file():
        return esterna
    return cartella_risorse() / "dati"


def cartella_assets() -> Path:
    """Cartella con icona e altre risorse grafiche."""
    return cartella_risorse() / "assets"


def cartella_utente() -> Path:
    """Cartella dei dati dell'utente: %APPDATA%\\FlagGame su Windows.

    La variabile d'ambiente ``FLAGGAME_DATI_UTENTE`` permette di cambiarla
    (la usano i test per non toccare i dati veri).
    """
    forzata = os.environ.get("FLAGGAME_DATI_UTENTE")
    if forzata:
        cartella = Path(forzata)
    else:
        base = os.environ.get("APPDATA")
        cartella = Path(base) / NOME_CARTELLA_UTENTE if base else Path.home() / ".flaggame"
    cartella.mkdir(parents=True, exist_ok=True)
    return cartella


def candidati_radice_bandiere() -> list[Path]:
    """Posizioni in cui cercare la cartella delle bandiere, in ordine.

    Prima accanto al programma, poi risalendo fino a tre cartelle (comodo
    quando l'eseguibile sta in ``dist\\FlagGame`` dentro la cartella del progetto).
    """
    base = cartella_app()
    candidati: list[Path] = []
    cartella = base
    for _ in range(4):
        candidati.append(cartella / NOME_CARTELLA_BANDIERE)
        candidati.append(cartella)
        if cartella.parent == cartella:
            break
        cartella = cartella.parent
    return candidati
