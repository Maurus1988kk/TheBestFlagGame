"""Creazione delle domande di una partita.

Regole principali:

* le risposte giuste di una partita sono tutte diverse;
* le 4 opzioni di una domanda sono tutte diverse (anche nel nome) e in ordine casuale;
* tra una partita e l'altra si privilegiano le bandiere non uscite di recente
  (storico delle ultime risposte giuste per modalità/livello/area);
* le opzioni sbagliate ("distrattori") vengono scelte per fasce di priorità:
  si pesca a caso dalla prima fascia e si passa alla successiva solo se non basta.

Fasce per i livelli con ``distrattori = "area"`` (Facile, Intermedio, Difficile)::

    1. stesso gruppo di similarità e stessa area      (solo se il livello ha gruppi)
    2. gruppi vicini (che condividono bandiere) e stessa area
    3. stesso livello e stessa area
    4. altri livelli, stessa area
    5. stesso gruppo, gruppi vicini, stesso livello, poi tutto il resto

Fasce per i livelli con ``distrattori = "gruppo"`` (Nerd)::

    1. stesso gruppo e stessa area
    2. stesso gruppo (qualsiasi area)
    3. gruppi vicini e stessa area
    4. gruppi vicini
    5. stesso livello e stessa area, altri livelli e stessa area, poi tutto il resto

Con "Tutto il mondo" la condizione sull'area è sempre vera.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

from .dati import AREA_MONDO, Catalogo

MODALITA_BANDIERA = "flag"      # Guess the Flag: si vede la bandiera, si sceglie il nome
MODALITA_STATO = "country"      # Guess the Country: si legge il nome, si sceglie la bandiera
MODALITA = (MODALITA_BANDIERA, MODALITA_STATO)

DOMANDE_PER_PARTITA = 10
OPZIONI_PER_DOMANDA = 4


@dataclass(frozen=True)
class Opzione:
    """Una delle 4 risposte possibili."""

    id: str
    nome: str
    immagine: Path


@dataclass(frozen=True)
class Domanda:
    """Una domanda: la risposta giusta e le 4 opzioni (giusta compresa)."""

    numero: int
    risposta: Opzione
    opzioni: tuple[Opzione, ...]

    @property
    def indice_giusto(self) -> int:
        return next(i for i, o in enumerate(self.opzioni) if o.id == self.risposta.id)


@dataclass(frozen=True)
class InfoCombinazione:
    """Quante domande si possono fare con un livello e un'area."""

    disponibili: int   # bandiere diverse che possono essere risposta giusta
    domande: int       # domande della partita (al massimo DOMANDE_PER_PARTITA)
    giocabile: bool

    @property
    def ridotta(self) -> bool:
        """Vero se la partita avrà meno di 10 domande."""
        return self.giocabile and self.domande < DOMANDE_PER_PARTITA


def chiave_storico(modalita: str, livello: str, area: str) -> str:
    """Chiave dello storico anti-ripetizione per una combinazione."""
    return f"{modalita}|{livello}|{area}"


class Generatore:
    """Genera le domande delle partite a partire dal catalogo.

    ``storico`` è un oggetto con i metodi ``recenti(chiave) -> list[str]``
    (dal meno al più recente) e ``registra(chiave, ids)``; può mancare.
    ``rng`` permette di passare un generatore casuale nei test; di norma si
    usa ``random.SystemRandom``, quindi ogni avvio produce partite diverse.
    """

    def __init__(self, catalogo: Catalogo, storico=None, rng: random.Random | None = None,
                 domande_per_partita: int = DOMANDE_PER_PARTITA):
        self.catalogo = catalogo
        self.storico = storico
        self.rng = rng if rng is not None else random.SystemRandom()
        self.domande_per_partita = domande_per_partita
        self._cache_fasce: dict[tuple[str, str, str], list[list[str]]] = {}
        self._tutti = sorted({i for liv in catalogo.livelli.values() for i in liv.percorsi})
        self._nomi_distinti = len({catalogo.nome(i).casefold() for i in self._tutti})

    # ------------------------------------------------------------------ info

    def info(self, livello: str, area: str = AREA_MONDO) -> InfoCombinazione:
        """Calcola in anticipo quante domande uniche sono possibili."""
        disponibili = len(self.catalogo.pool(livello, area))
        giocabile = disponibili > 0 and self._nomi_distinti >= OPZIONI_PER_DOMANDA
        domande = min(disponibili, self.domande_per_partita) if giocabile else 0
        return InfoCombinazione(disponibili, domande, giocabile)

    # -------------------------------------------------------------- partita

    def genera(self, modalita: str, livello: str, area: str = AREA_MONDO) -> list[Domanda]:
        """Crea le domande di una nuova partita."""
        if modalita not in MODALITA:
            raise ValueError(f"Modalità sconosciuta: {modalita}")
        info = self.info(livello, area)
        if not info.giocabile:
            raise ValueError(f"Combinazione non giocabile: {livello} / {area}")
        risposte = self._scegli_risposte(modalita, livello, area, info.domande)
        domande = []
        for numero, id_giusto in enumerate(risposte, start=1):
            ids = [id_giusto] + self._scegli_distrattori(id_giusto, livello, area)
            self.rng.shuffle(ids)
            domande.append(Domanda(
                numero=numero,
                risposta=self._opzione(id_giusto, livello),
                opzioni=tuple(self._opzione(i, livello) for i in ids),
            ))
        return domande

    def registra_uscite(self, modalita: str, livello: str, area: str, ids: list[str]) -> None:
        """Aggiunge allo storico le risposte giuste effettivamente mostrate."""
        if self.storico is not None and ids:
            self.storico.registra(chiave_storico(modalita, livello, area), list(ids))

    # ------------------------------------------------------------- risposte

    def _scegli_risposte(self, modalita: str, livello: str, area: str, n: int) -> list[str]:
        """Sceglie n risposte giuste diverse, evitando quelle uscite di recente."""
        pool = self.catalogo.pool(livello, area)
        recenti = []
        if self.storico is not None:
            recenti = self.storico.recenti(chiave_storico(modalita, livello, area))
        # posizione nello storico: più è alta, più l'uscita è recente
        eta = {id_b: pos for pos, id_b in enumerate(recenti)}
        freschi = [i for i in pool if i not in eta]
        if len(freschi) >= n:
            scelte = self.rng.sample(freschi, n)
        else:
            # pool piccolo: tutte le fresche più le meno recenti
            vecchie = sorted((i for i in pool if i in eta), key=lambda i: eta[i])
            scelte = freschi + vecchie[: n - len(freschi)]
        self.rng.shuffle(scelte)
        return scelte

    # ---------------------------------------------------------- distrattori

    def _scegli_distrattori(self, id_giusto: str, livello: str, area: str) -> list[str]:
        """Sceglie 3 opzioni sbagliate seguendo le fasce di priorità."""
        servono = OPZIONI_PER_DOMANDA - 1
        scelti: list[str] = []
        nomi = {self.catalogo.nome(id_giusto).casefold()}
        for fascia in self._fasce(id_giusto, livello, area):
            for candidato in self._in_ordine_casuale(fascia, servono - len(scelti)):
                nome = self.catalogo.nome(candidato).casefold()
                if nome in nomi:
                    continue
                scelti.append(candidato)
                nomi.add(nome)
                if len(scelti) == servono:
                    return scelti
        return scelti

    def _in_ordine_casuale(self, fascia: list[str], servono: int):
        """Scorre la fascia in ordine casuale senza mescolarla tutta se è grande."""
        if len(fascia) <= 4 * servono + 8:
            copia = list(fascia)
            self.rng.shuffle(copia)
            yield from copia
            return
        visti: set[int] = set()
        for _ in range(4 * servono + 8):
            i = self.rng.randrange(len(fascia))
            if i not in visti:
                visti.add(i)
                yield fascia[i]
        resto = [x for i, x in enumerate(fascia) if i not in visti]
        self.rng.shuffle(resto)
        yield from resto

    def _fasce(self, id_giusto: str, livello: str, area: str) -> list[list[str]]:
        chiave = (livello, area, id_giusto)
        if chiave not in self._cache_fasce:
            self._cache_fasce[chiave] = self._calcola_fasce(id_giusto, livello, area)
        return self._cache_fasce[chiave]

    def _calcola_fasce(self, id_giusto: str, livello: str, area: str) -> list[list[str]]:
        cat = self.catalogo
        liv = cat.livelli[livello]

        def in_area(insieme) -> set[str]:
            if area == AREA_MONDO:
                return set(insieme)
            return {i for i in insieme if cat.bandiere[i].continente == area}

        gruppi = liv.gruppi_di.get(id_giusto, ())
        stesso_gruppo: set[str] = set()
        for g in gruppi:
            stesso_gruppo |= liv.gruppi[g]
        vicini = self.gruppi_vicini(livello, id_giusto)
        stesso_livello = set(liv.percorsi)
        tutti = set(self._tutti)

        if liv.config.distrattori == "gruppo":
            ordine = [in_area(stesso_gruppo), stesso_gruppo, in_area(vicini), vicini,
                      in_area(stesso_livello), in_area(tutti), stesso_livello, tutti]
        else:
            ordine = [in_area(stesso_gruppo), in_area(vicini), in_area(stesso_livello),
                      in_area(tutti), stesso_gruppo, vicini, stesso_livello, tutti]

        fasce, usati = [], {id_giusto}
        for insieme in ordine:
            nuovi = sorted(insieme - usati)
            if nuovi:
                fasce.append(nuovi)
                usati |= insieme
        return fasce

    def gruppi_vicini(self, livello: str, id_bandiera: str) -> set[str]:
        """Bandiere dei gruppi che condividono almeno una bandiera con i gruppi
        di ``id_bandiera`` (escluse quelle dei suoi gruppi)."""
        liv = self.catalogo.livelli[livello]
        propri = liv.gruppi_di.get(id_bandiera, ())
        if not propri:
            return set()
        membri: set[str] = set()
        for g in propri:
            membri |= liv.gruppi[g]
        vicini: set[str] = set()
        for nome, gruppo in liv.gruppi.items():
            if nome not in propri and gruppo & membri:
                vicini |= gruppo
        return vicini - membri

    def _opzione(self, id_bandiera: str, livello: str) -> Opzione:
        return Opzione(id_bandiera, self.catalogo.nome(id_bandiera),
                       self.catalogo.percorso(id_bandiera, livello))
