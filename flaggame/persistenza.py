"""Salvataggio su disco: scrittura JSON atomica, impostazioni, storico.

Tutti i file stanno in %APPDATA%\\FlagGame\\ (vedi ``percorsi.cartella_utente``).
La scrittura avviene su un file temporaneo nella stessa cartella, poi con
``os.replace`` il temporaneo prende il posto del file vero: se il programma
si chiude a metà scrittura, il file precedente resta intatto.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from pathlib import Path


def scrivi_json_atomico(percorso: Path | str, dati) -> None:
    """Scrive ``dati`` in JSON sostituendo il file in un'unica operazione."""
    percorso = Path(percorso)
    percorso.parent.mkdir(parents=True, exist_ok=True)
    fd, temporaneo = tempfile.mkstemp(prefix=percorso.name + ".", suffix=".tmp",
                                      dir=str(percorso.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(dati, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        # Su Windows un antivirus può tenere aperto il file per un attimo: riprova.
        for tentativo in range(5):
            try:
                os.replace(temporaneo, percorso)
                break
            except PermissionError:
                if tentativo == 4:
                    raise
                time.sleep(0.05 * (tentativo + 1))
    except BaseException:
        try:
            os.unlink(temporaneo)
        except OSError:
            pass
        raise


def leggi_json(percorso: Path | str, predefinito):
    """Legge un JSON. Se manca restituisce ``predefinito``; se è danneggiato
    lo rinomina in ``*.danneggiato-<data>`` (per non perderlo) e restituisce
    ``predefinito``."""
    percorso = Path(percorso)
    if not percorso.exists():
        return predefinito
    try:
        with open(percorso, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        copia = percorso.with_name(f"{percorso.name}.danneggiato-{datetime.now():%Y%m%d-%H%M%S}")
        try:
            os.replace(percorso, copia)
        except OSError:
            pass
        return predefinito


# --------------------------------------------------------------------------- #

@dataclass
class Impostazioni:
    """Preferenze dell'utente (impostazioni.json)."""

    tema: str = "chiaro"                 # "chiaro" o "scuro"
    suoni: bool = True
    avanzamento_automatico: bool = True  # passa da solo alla domanda successiva
    ultimo_nome: str = ""
    cartella_bandiere: str = ""          # vuoto = cerca accanto al programma
    ultima_modalita: str = "flag"
    ultimo_livello: str = "facile"
    ultima_area: str = "mondo"
    geometria: str = ""                  # posizione/dimensione finestra (esadecimale)

    @classmethod
    def carica(cls, percorso: Path) -> "Impostazioni":
        dati = leggi_json(percorso, {})
        imp = cls()
        if isinstance(dati, dict):
            for campo in fields(cls):
                if campo.name in dati and isinstance(dati[campo.name], type(getattr(imp, campo.name))):
                    setattr(imp, campo.name, dati[campo.name])
        if imp.tema not in ("chiaro", "scuro"):
            imp.tema = "chiaro"
        return imp

    def salva(self, percorso: Path) -> None:
        scrivi_json_atomico(percorso, asdict(self))


class Storico:
    """Ultime risposte giuste uscite, per combinazione modalità/livello/area.

    Serve a evitare che le stesse bandiere tornino nelle partite successive.
    """

    def __init__(self, percorso: Path | None = None, massimo: int = 60):
        self.percorso = Path(percorso) if percorso else None
        self.massimo = massimo
        self._dati: dict[str, list[str]] = {}
        if self.percorso is not None:
            dati = leggi_json(self.percorso, {})
            voci = dati.get("recenti", {}) if isinstance(dati, dict) else {}
            self._dati = {str(k): [str(x) for x in v][-massimo:]
                          for k, v in voci.items() if isinstance(v, list)}

    def recenti(self, chiave: str) -> list[str]:
        """Id usciti di recente, dal meno al più recente."""
        return list(self._dati.get(chiave, []))

    def registra(self, chiave: str, ids: list[str]) -> None:
        """Aggiunge le uscite in coda (una bandiera già presente torna "recente")."""
        lista = [x for x in self._dati.get(chiave, []) if x not in set(ids)]
        lista.extend(ids)
        self._dati[chiave] = lista[-self.massimo:]
        self.salva()

    def azzera(self) -> None:
        self._dati.clear()
        self.salva()

    def salva(self) -> None:
        if self.percorso is not None:
            scrivi_json_atomico(self.percorso, {"versione": 1, "recenti": self._dati})
