"""Stato di una partita in corso e cronometro.

Il cronometro parte quando compare la prima domanda e resta in pausa durante
il feedback dopo ogni risposta, così il tempo misura solo il ragionamento.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .generatore import Domanda


class Cronometro:
    """Cronometro con pausa. ``orologio`` restituisce secondi (iniettabile nei test)."""

    def __init__(self, orologio: Callable[[], float] = time.perf_counter):
        self._orologio = orologio
        self._accumulato = 0.0
        self._inizio: float | None = None

    @property
    def in_corso(self) -> bool:
        return self._inizio is not None

    def avvia(self) -> None:
        """Avvia (o riprende) il conteggio."""
        if self._inizio is None:
            self._inizio = self._orologio()

    riprendi = avvia

    def pausa(self) -> None:
        """Mette in pausa conservando il tempo già trascorso."""
        if self._inizio is not None:
            self._accumulato += self._orologio() - self._inizio
            self._inizio = None

    def trascorso(self) -> float:
        """Secondi trascorsi, esclusi i periodi di pausa."""
        if self._inizio is None:
            return self._accumulato
        return self._accumulato + (self._orologio() - self._inizio)


def formatta_tempo(secondi: float) -> str:
    """Formato mm:ss.d (decimi troncati, così il display non "salta avanti")."""
    decimi = int(max(0.0, secondi) * 10)
    minuti, resto = divmod(decimi, 600)
    return f"{minuti:02d}:{resto // 10:02d}.{resto % 10}"


class StatoPartita(Enum):
    PRONTA = "pronta"          # creata, timer fermo
    DOMANDA = "domanda"        # in attesa di risposta, timer in corso
    FEEDBACK = "feedback"      # risposta data, timer in pausa
    FINITA = "finita"
    ABBANDONATA = "abbandonata"


@dataclass(frozen=True)
class RispostaData:
    """Esito di una domanda."""

    domanda: Domanda
    scelta: int        # indice dell'opzione scelta (0-3)
    giusta: bool
    tempo: float       # secondi spesi su questa domanda

    @property
    def opzione_scelta(self):
        return self.domanda.opzioni[self.scelta]


class Partita:
    """Svolgimento di una partita: domande, risposte, tempo."""

    def __init__(self, modalita: str, livello: str, area: str, domande: list[Domanda],
                 orologio: Callable[[], float] = time.perf_counter):
        if not domande:
            raise ValueError("Una partita deve avere almeno una domanda")
        self.modalita = modalita
        self.livello = livello
        self.area = area
        self.domande = list(domande)
        self.risposte: list[RispostaData] = []
        self.stato = StatoPartita.PRONTA
        self._indice = 0
        self._crono = Cronometro(orologio)
        self._inizio_domanda = 0.0

    # ---------------------------------------------------------------- stato

    @property
    def totale(self) -> int:
        return len(self.domande)

    @property
    def indice(self) -> int:
        """Indice (0-based) della domanda corrente."""
        return self._indice

    @property
    def domanda_corrente(self) -> Domanda | None:
        if self.stato in (StatoPartita.FINITA, StatoPartita.ABBANDONATA):
            return None
        return self.domande[self._indice]

    @property
    def giuste(self) -> int:
        return sum(1 for r in self.risposte if r.giusta)

    @property
    def percentuale(self) -> float:
        return 100.0 * self.giuste / self.totale

    @property
    def ultima_domanda(self) -> bool:
        return self._indice >= self.totale - 1

    def tempo(self) -> float:
        """Tempo di gioco trascorso finora (pause escluse)."""
        return self._crono.trascorso()

    @property
    def timer_in_corso(self) -> bool:
        return self._crono.in_corso

    def ids_mostrati(self) -> list[str]:
        """Risposte giuste delle domande già comparse (per lo storico)."""
        if self.stato == StatoPartita.PRONTA:
            return []
        fino = min(self._indice + 1, self.totale)
        return [d.risposta.id for d in self.domande[:fino]]

    # -------------------------------------------------------------- comandi

    def avvia(self) -> Domanda:
        """Mostra la prima domanda e fa partire il cronometro."""
        if self.stato != StatoPartita.PRONTA:
            raise RuntimeError("La partita è già iniziata")
        self.stato = StatoPartita.DOMANDA
        self._crono.avvia()
        self._inizio_domanda = self._crono.trascorso()
        return self.domande[0]

    def rispondi(self, scelta: int) -> RispostaData:
        """Registra la risposta e mette in pausa il cronometro."""
        if self.stato != StatoPartita.DOMANDA:
            raise RuntimeError("Nessuna domanda in attesa di risposta")
        domanda = self.domande[self._indice]
        if not 0 <= scelta < len(domanda.opzioni):
            raise ValueError("Opzione inesistente")
        self._crono.pausa()
        risposta = RispostaData(domanda, scelta, scelta == domanda.indice_giusto,
                                self._crono.trascorso() - self._inizio_domanda)
        self.risposte.append(risposta)
        self.stato = StatoPartita.FEEDBACK
        return risposta

    def avanti(self) -> Domanda | None:
        """Passa alla domanda successiva (riprende il cronometro) o chiude la partita."""
        if self.stato != StatoPartita.FEEDBACK:
            raise RuntimeError("Prima bisogna rispondere")
        if self.ultima_domanda:
            self.stato = StatoPartita.FINITA
            return None
        self._indice += 1
        self.stato = StatoPartita.DOMANDA
        self._inizio_domanda = self._crono.trascorso()
        self._crono.riprendi()
        return self.domande[self._indice]

    def sospendi(self) -> None:
        """Pausa temporanea (es. finestra di conferma aperta)."""
        if self.stato == StatoPartita.DOMANDA:
            self._crono.pausa()

    def riprendi(self) -> None:
        if self.stato == StatoPartita.DOMANDA:
            self._crono.riprendi()

    def abbandona(self) -> None:
        """Interrompe la partita: non andrà in classifica."""
        self._crono.pausa()
        self.stato = StatoPartita.ABBANDONATA
