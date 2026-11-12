"""Classifica dei risultati, salvata in %APPDATA%\\FlagGame\\classifica.json.

Ordinamento per **punti**, poi percentuale, tempo e data. I punti rendono
confrontabili partite di livelli e lunghezze diverse (le viste «Tutte»):

* ogni risposta giusta vale i ``punti`` del livello (livelli.json:
  Facile 100, Intermedio 150, Difficile 200, Nerd 300);
* la velocità dà un bonus fino al 10%: pieno con una media di
  ``SECONDI_VELOCE`` secondi a domanda o meno, nullo da ``SECONDI_LENTO`` in su.

Il bonus è volutamente piccolo: con al massimo 10 domande una risposta giusta
in più vale sempre più di qualunque bonus (9 giuste x 1,10 < 10 giuste). Così,
dentro la stessa combinazione modalità/livello/area, l'ordine è lo stesso di
"percentuale, poi tempo"; una partita breve (es. 3 domande) non supera più
una partita da 10 solo perché ha la stessa percentuale.

Ogni risultato salvato conserva anche le singole risposte (``risposte``), usate
dalle statistiche personali. I risultati salvati prima di questa versione non
le hanno: contano nelle statistiche generali ma non in quelle per bandiera.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from . import testi
from .persistenza import leggi_json, scrivi_json_atomico

TUTTE = None  # valore dei filtri per "tutte le modalità/livelli/aree"
LUNGHEZZA_MAX_NOME = 24

PUNTI_PREDEFINITI = 100          # punti per risposta giusta di un livello sconosciuto
BONUS_VELOCITA_MAX = 0.10        # +10% al massimo
SECONDI_VELOCE = 2.0             # media per domanda con bonus pieno
SECONDI_LENTO = 12.0             # media per domanda senza bonus


def calcola_punti(giuste: int, totale: int, tempo: float, punti_risposta: int) -> int:
    """Punti di una partita: risposte giuste x punti del livello, più il bonus velocità."""
    if giuste <= 0 or totale <= 0:
        return 0
    medio = max(0.0, tempo) / totale
    quota = (SECONDI_LENTO - medio) / (SECONDI_LENTO - SECONDI_VELOCE)
    quota = max(0.0, min(1.0, quota))
    return round(giuste * punti_risposta * (1 + BONUS_VELOCITA_MAX * quota))


@dataclass(frozen=True)
class RispostaSalvata:
    """Una risposta di una partita salvata: bandiera giusta, scelta, secondi."""

    id: str        # id della bandiera giusta
    scelta: str    # id della bandiera (o del nome) scelto
    tempo: float

    @property
    def giusta(self) -> bool:
        return self.id == self.scelta

    @classmethod
    def da_dict(cls, d: dict) -> "RispostaSalvata":
        return cls(id=str(d["id"]), scelta=str(d["scelta"]), tempo=float(d.get("tempo", 0.0)))


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
    risposte: tuple[RispostaSalvata, ...] = ()

    @property
    def percentuale(self) -> float:
        return 100.0 * self.giuste / self.totale if self.totale else 0.0

    @classmethod
    def da_dict(cls, d: dict) -> "Risultato":
        risposte = []
        for r in d.get("risposte") or ():
            try:
                risposte.append(RispostaSalvata.da_dict(r))
            except (KeyError, TypeError, ValueError):
                continue  # risposta non valida: ignorata, il risultato resta
        return cls(
            nome=str(d["nome"]), giuste=int(d["giuste"]), totale=int(d["totale"]),
            tempo=float(d["tempo"]), modalita=str(d["modalita"]), livello=str(d["livello"]),
            area=str(d["area"]), data=str(d.get("data", "")), id=str(d.get("id") or uuid.uuid4().hex),
            risposte=tuple(risposte),
        )


def pulisci_nome(nome: str) -> str:
    """Nome senza spazi superflui e di lunghezza ragionevole."""
    return " ".join(nome.split())[:LUNGHEZZA_MAX_NOME]


class Classifica:
    """Elenco dei risultati con filtri, punti e salvataggio atomico.

    ``punti_livello`` associa a ogni livello i punti per risposta giusta
    (di solito da livelli.json); i livelli mancanti valgono ``PUNTI_PREDEFINITI``.
    """

    def __init__(self, percorso: Path | str | None = None,
                 punti_livello: dict[str, int] | None = None):
        self.percorso = Path(percorso) if percorso else None
        self.punti_livello: dict[str, int] = dict(punti_livello or {})
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
                "versione": 2,
                "risultati": [asdict(r) for r in self._risultati],
            })

    def aggiungi(self, risultato: Risultato) -> Risultato:
        """Aggiunge un risultato e salva subito."""
        risultato = Risultato(**{**risultato.__dict__, "nome": pulisci_nome(risultato.nome) or testi.NOME_ANONIMO})
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

    # ---------------------------------------------------------------- punti

    def punti_risposta(self, livello: str) -> int:
        """Punti di una risposta giusta nel livello indicato."""
        return self.punti_livello.get(livello, PUNTI_PREDEFINITI)

    def punti(self, risultato: Risultato) -> int:
        return calcola_punti(risultato.giuste, risultato.totale, risultato.tempo,
                             self.punti_risposta(risultato.livello))

    def chiave_ordinamento(self, r: Risultato):
        """Punti decrescenti, poi percentuale decrescente, tempo e data crescenti."""
        return (-self.punti(r), -round(r.percentuale, 6), r.tempo, r.data)

    # --------------------------------------------------------------- filtri

    def filtra(self, modalita: str | None = TUTTE, livello: str | None = TUTTE,
               area: str | None = TUTTE) -> list[Risultato]:
        """Risultati della combinazione richiesta, già ordinati.
        ``None`` in un filtro significa "tutte"."""
        righe = [r for r in self._risultati
                 if (modalita is None or r.modalita == modalita)
                 and (livello is None or r.livello == livello)
                 and (area is None or r.area == area)]
        return sorted(righe, key=self.chiave_ordinamento)

    def top(self, n: int = 10, **filtri) -> list[Risultato]:
        return self.filtra(**filtri)[:n]

    def posizione(self, id_risultato: str, **filtri) -> int | None:
        """Posizione (1-based) di un risultato nella vista filtrata."""
        for i, r in enumerate(self.filtra(**filtri), start=1):
            if r.id == id_risultato:
                return i
        return None
