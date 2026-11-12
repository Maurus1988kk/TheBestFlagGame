"""Test dello stato della partita e del cronometro (orologio finto)."""

from __future__ import annotations

from pathlib import Path

import pytest

from flaggame.generatore import Domanda, Opzione
from flaggame.partita import Cronometro, Partita, StatoPartita, formatta_tempo


class OrologioFinto:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t

    def avanza(self, secondi):
        self.t += secondi


def domanda(n: int) -> Domanda:
    opzioni = tuple(Opzione(f"id{n}_{i}", f"Nome {n}-{i}", Path("x.png")) for i in range(4))
    return Domanda(n, opzioni[n % 4], opzioni)


def test_formatta_tempo():
    assert formatta_tempo(0) == "00:00.0"
    assert formatta_tempo(5.49) == "00:05.4"
    assert formatta_tempo(65.96) == "01:05.9"
    assert formatta_tempo(3599.99) == "59:59.9"
    assert formatta_tempo(-3) == "00:00.0"


def test_cronometro_pausa():
    o = OrologioFinto()
    c = Cronometro(o)
    assert c.trascorso() == 0
    c.avvia()
    o.avanza(2)
    c.pausa()
    o.avanza(10)
    assert c.trascorso() == pytest.approx(2)
    c.riprendi()
    o.avanza(1.5)
    assert c.trascorso() == pytest.approx(3.5)


def test_partita_completa_e_timer_in_pausa_durante_feedback():
    o = OrologioFinto()
    domande = [domanda(n) for n in range(1, 4)]
    p = Partita("flag", "facile", "mondo", domande, orologio=o)
    assert p.stato == StatoPartita.PRONTA
    o.avanza(5)                      # prima che compaia la domanda: non conta
    assert p.tempo() == 0
    p.avvia()
    o.avanza(2)
    r = p.rispondi(domande[0].indice_giusto)
    assert r.giusta and r.tempo == pytest.approx(2)
    assert p.stato == StatoPartita.FEEDBACK
    o.avanza(1.2)                    # feedback: timer fermo
    assert p.tempo() == pytest.approx(2)
    p.avanti()
    o.avanza(3)
    r = p.rispondi((domande[1].indice_giusto + 1) % 4)
    assert not r.giusta and r.tempo == pytest.approx(3)
    p.avanti()
    o.avanza(1)
    p.rispondi(domande[2].indice_giusto)
    assert p.avanti() is None
    assert p.stato == StatoPartita.FINITA
    assert p.giuste == 2 and p.totale == 3
    assert p.percentuale == pytest.approx(200 / 3)
    assert p.tempo() == pytest.approx(6)
    assert p.ids_mostrati() == [d.risposta.id for d in domande]


def test_non_si_risponde_due_volte():
    p = Partita("flag", "facile", "mondo", [domanda(1), domanda(2)], orologio=OrologioFinto())
    with pytest.raises(RuntimeError):
        p.rispondi(0)                # partita non iniziata
    p.avvia()
    p.rispondi(0)
    with pytest.raises(RuntimeError):
        p.rispondi(1)
    with pytest.raises(RuntimeError):
        p.avvia()


def test_abbandono_e_sospensione():
    o = OrologioFinto()
    domande = [domanda(n) for n in range(1, 6)]
    p = Partita("country", "nerd", "europa", domande, orologio=o)
    p.avvia()
    o.avanza(1)
    p.sospendi()                     # finestra di conferma aperta
    o.avanza(30)
    p.riprendi()
    assert p.tempo() == pytest.approx(1)
    p.rispondi(0)
    p.avanti()
    p.abbandona()
    assert p.stato == StatoPartita.ABBANDONATA
    assert p.domanda_corrente is None
    assert p.ids_mostrati() == [d.risposta.id for d in domande[:2]]


def test_partita_vuota_non_ammessa():
    with pytest.raises(ValueError):
        Partita("flag", "facile", "mondo", [])
