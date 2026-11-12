"""Classifica dei risultati, salvata in %APPDATA%\\FlagGame\\classifica.json.

Ordinamento: percentuale decrescente, poi tempo crescente (a parità di
entrambi vince chi ha ottenuto il risultato per primo).
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from .persistenza import leggi_json, scrivi_json_atomico

TUTTE = None  # valore dei filtri per "tutte le modalità/livelli/aree"
LUNGHEZZA_MAX_NOME = 24


@dataclass(frozen=True)
class Risultato:
    """Una riga della classifica."""

    nome: str
    giuste: int
    totale: int
    tempo: float          # secondi
    modalita: str
    livello: str
    area: str
    data: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    @property
    def percentuale(self) -> float:
        return 100.0 * self.giuste / self.totale if self.totale else 0.0

    @classmethod
    def da_dict(cls, d: dict) -> "Risultato":
        return cls(
            nome=str(d["nome"]), giuste=int(d["giuste"]), totale=int(d["totale"]),
            tempo=float(d["tempo"]), modalita=str(d["modalita"]), livello=str(d["livello"]),
            area=str(d["area"]), data=str(d.get("data", "")), id=str(d.get("id") or uuid.uuid4().hex),
        )


def chiave_ordinamento(r: Risultato):
    """Percentuale decrescente, tempo crescente, data crescente."""
    return (-round(r.percentuale, 6), r.tempo, r.data)


def pulisci_nome(nome: str) -> str:
    """Nome senza spazi superflui e di lunghezza ragionevole."""
    return " ".join(nome.split())[:LUNGHEZZA_MAX_NOME]


class Classifica:
    """Elenco dei risultati con filtri e salvataggio atomico."""

    def __init__(self, percorso: Path | str | None = None):
        self.percorso = Path(percorso) if percorso else None
        self._risultati: list[Risultato] = []
        if self.percorso is not None:
            self.carica()

    def carica(self) -> None:
        dati = leggi_json(self.percorso, {})
        righe = dati.get("risultati", []) if isinstance(dati, dict) else []
        self._risultati = []
        for riga in righe:
            try:
                self._risultati.append(Risultato.da_dict(riga))
            except (KeyError, TypeError, ValueError):
                continue  # riga non valida: ignorata

    def salva(self) -> None:
        if self.percorso is not None:
            scrivi_json_atomico(self.percorso, {
                "versione": 1,
                "risultati": [asdict(r) for r in self._risultati],
            })

    def aggiungi(self, risultato: Risultato) -> Risultato:
        """Aggiunge un risultato e salva subito."""
        risultato = Risultato(**{**asdict(risultato), "nome": pulisci_nome(risultato.nome) or "Anonimo"})
        self._risultati.append(risultato)
        self.salva()
        return risultato

    def svuota(self) -> None:
        self._risultati.clear()
        self.salva()

    def __len__(self) -> int:
        return len(self._risultati)

    def tutti(self) -> list[Risultato]:
        return list(self._risultati)

    def filtra(self, modalita: str | None = TUTTE, livello: str | None = TUTTE,
               area: str | None = TUTTE) -> list[Risultato]:
        """Risultati della combinazione richiesta, già ordinati.
        ``None`` in un filtro significa "tutte"."""
        righe = [r for r in self._risultati
                 if (modalita is None or r.modalita == modalita)
                 and (livello is None or r.livello == livello)
                 and (area is None or r.area == area)]
        return sorted(righe, key=chiave_ordinamento)

    def top(self, n: int = 10, **filtri) -> list[Risultato]:
        return self.filtra(**filtri)[:n]

    def posizione(self, id_risultato: str, **filtri) -> int | None:
        """Posizione (1-based) di un risultato nella vista filtrata."""
        for i, r in enumerate(self.filtra(**filtri), start=1):
            if r.id == id_risultato:
                return i
        return None
