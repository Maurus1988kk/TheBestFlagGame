"""Statistiche personali, calcolate dai risultati salvati in classifica.

Non c'è un file a parte: ogni risultato della classifica conserva le sue
risposte (``Risultato.risposte``), quindi cancellare la classifica azzera
anche le statistiche e le due cose non possono mai divergere.

* Riepilogo, livelli e andamento usano tutti i risultati del giocatore.
* Continenti e "bandiere da ripassare" servono le singole risposte, che ci
  sono solo nei risultati salvati da questa versione in poi.

I nomi dei giocatori si confrontano senza badare a maiuscole e spazi
("mauro" e "Mauro " sono la stessa persona); si mostra la grafia più recente.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from .classifica import Classifica, Risultato

PARTITE_ANDAMENTO = 20       # partite mostrate nel grafico dell'andamento
BANDIERE_DA_RIPASSARE = 8


def chiave_giocatore(nome: str) -> str:
    return " ".join(nome.split()).casefold()


def giocatori(risultati: Iterable[Risultato]) -> list[str]:
    """Nomi dei giocatori, da chi ha giocato più di recente."""
    ultimo: dict[str, tuple[str, str]] = {}   # chiave -> (data, nome)
    for r in risultati:
        k = chiave_giocatore(r.nome)
        if k not in ultimo or r.data >= ultimo[k][0]:
            ultimo[k] = (r.data, r.nome)
    return [nome for _, nome in sorted(ultimo.values(), key=lambda v: v[0], reverse=True)]


@dataclass(frozen=True)
class Quota:
    """Risposte giuste su risposte date in una categoria (un livello, un continente)."""

    chiave: str
    giuste: int
    totale: int

    @property
    def percentuale(self) -> float:
        return 100.0 * self.giuste / self.totale if self.totale else 0.0


@dataclass(frozen=True)
class PuntoAndamento:
    """Una partita nel grafico dell'andamento."""

    risultato: Risultato
    punti: int

    @property
    def percentuale(self) -> float:
        return self.risultato.percentuale


@dataclass(frozen=True)
class BandieraDaRipassare:
    """Una bandiera sbagliata spesso, con la risposta scelta più spesso al suo posto."""

    id: str
    sbagliate: int
    viste: int
    confusa_con: str | None

    @property
    def errore(self) -> float:
        return self.sbagliate / self.viste if self.viste else 0.0


@dataclass(frozen=True)
class Statistiche:
    giocatore: str
    partite: int
    risposte: int
    giuste: int
    tempo_medio: float                    # secondi per risposta
    migliore: PuntoAndamento | None       # risultato con più punti
    per_livello: list[Quota]
    per_continente: list[Quota]
    andamento: list[PuntoAndamento]       # ultime partite, dalla più vecchia
    da_ripassare: list[BandieraDaRipassare]
    partite_con_dettaglio: int            # partite che hanno le singole risposte

    @property
    def percentuale(self) -> float:
        return 100.0 * self.giuste / self.risposte if self.risposte else 0.0

    @property
    def vuota(self) -> bool:
        return self.partite == 0


def _quote(conteggi: dict[str, list[int]], ordine: Sequence[str]) -> list[Quota]:
    """Una quota per ogni chiave di ``ordine`` (anche se mai giocata), poi le altre."""
    chiavi = list(ordine) + sorted(k for k in conteggi if k not in ordine)
    return [Quota(k, *conteggi.get(k, (0, 0))) for k in chiavi]


def calcola(classifica: Classifica, giocatore: str,
            continente_di: Callable[[str], str | None] = lambda _id: None,
            ordine_livelli: Sequence[str] = (), ordine_continenti: Sequence[str] = ()) -> Statistiche:
    """Statistiche di ``giocatore`` a partire dai risultati della classifica."""
    chiave = chiave_giocatore(giocatore)
    mie = sorted((r for r in classifica.tutti() if chiave_giocatore(r.nome) == chiave),
                 key=lambda r: r.data)

    per_livello: dict[str, list[int]] = {}
    per_continente: dict[str, list[int]] = {}
    viste: Counter[str] = Counter()
    sbagliate: Counter[str] = Counter()
    confusioni: dict[str, Counter[str]] = defaultdict(Counter)
    con_dettaglio = 0
    for r in mie:
        quota = per_livello.setdefault(r.livello, [0, 0])
        quota[0] += r.giuste
        quota[1] += r.totale
        if r.risposte:
            con_dettaglio += 1
        for risposta in r.risposte:
            viste[risposta.id] += 1
            if not risposta.giusta:
                sbagliate[risposta.id] += 1
                confusioni[risposta.id][risposta.scelta] += 1
            continente = continente_di(risposta.id)
            if continente:
                quota = per_continente.setdefault(continente, [0, 0])
                quota[0] += risposta.giusta
                quota[1] += 1

    punti = [PuntoAndamento(r, classifica.punti(r)) for r in mie]
    migliore = (min(punti, key=lambda p: classifica.chiave_ordinamento(p.risultato))
                if punti else None)
    da_ripassare = sorted(
        (BandieraDaRipassare(i, n, viste[i], confusioni[i].most_common(1)[0][0])
         for i, n in sbagliate.items()),
        key=lambda b: (-b.sbagliate, -b.errore, b.id),
    )[:BANDIERE_DA_RIPASSARE]

    risposte = sum(r.totale for r in mie)
    return Statistiche(
        giocatore=mie[-1].nome if mie else giocatore,
        partite=len(mie),
        risposte=risposte,
        giuste=sum(r.giuste for r in mie),
        tempo_medio=sum(r.tempo for r in mie) / risposte if risposte else 0.0,
        migliore=migliore,
        per_livello=_quote(per_livello, ordine_livelli),
        per_continente=_quote(per_continente, ordine_continenti),
        andamento=punti[-PARTITE_ANDAMENTO:],
        da_ripassare=da_ripassare,
        partite_con_dettaglio=con_dettaglio,
    )
