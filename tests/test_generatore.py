"""Test del generatore di domande sulle bandiere vere."""

from __future__ import annotations

import random
from collections import Counter

import pytest

from flaggame.dati import AREA_MONDO
from flaggame.generatore import (DOMANDE_PER_PARTITA, MODALITA, OPZIONI_PER_DOMANDA, Generatore,
                                 chiave_storico)
from flaggame.persistenza import Storico

LIVELLI = ("facile", "intermedio", "difficile", "nerd")
AREE = (AREA_MONDO, "europa", "asia", "africa", "america_nord", "america_sud", "oceania")
PARTITE = 1000


def stesso_gruppo(catalogo, livello, a, b) -> bool:
    gruppi = catalogo.livelli[livello].gruppi_di
    return bool(set(gruppi.get(a, ())) & set(gruppi.get(b, ())))


def membri_gruppi(catalogo, livello, id_b) -> set[str]:
    liv = catalogo.livelli[livello]
    membri = set()
    for g in liv.gruppi_di.get(id_b, ()):
        membri |= liv.gruppi[g]
    return membri


@pytest.mark.parametrize("area", AREE)
@pytest.mark.parametrize("livello", LIVELLI)
@pytest.mark.parametrize("modalita", MODALITA)
def test_mille_partite(catalogo, modalita, livello, area):
    """1000 partite per combinazione: domande giuste, nessuna ripetizione."""
    storico = Storico(None)
    gen = Generatore(catalogo, storico, rng=random.Random(f"{modalita}|{livello}|{area}"))
    info = gen.info(livello, area)
    pool = set(catalogo.pool(livello, area))
    assert info.disponibili == len(pool)
    if not info.giocabile:
        pytest.skip("combinazione non giocabile")
    attese = min(DOMANDE_PER_PARTITA, len(pool))
    for _ in range(PARTITE):
        domande = gen.genera(modalita, livello, area)
        assert len(domande) == attese == info.domande
        giuste = [d.risposta.id for d in domande]
        assert len(set(giuste)) == len(giuste), "risposta giusta ripetuta nella partita"
        assert set(giuste) <= pool
        for d in domande:
            ids = [o.id for o in d.opzioni]
            nomi = [o.nome.casefold() for o in d.opzioni]
            assert len(ids) == OPZIONI_PER_DOMANDA
            assert len(set(ids)) == OPZIONI_PER_DOMANDA, "opzione duplicata"
            assert len(set(nomi)) == OPZIONI_PER_DOMANDA, "due opzioni con lo stesso nome"
            assert d.risposta.id in ids
            assert d.opzioni[d.indice_giusto].id == d.risposta.id
            assert all(o.immagine.is_file() for o in d.opzioni)
        gen.registra_uscite(modalita, livello, area, giuste)


@pytest.mark.parametrize("modalita", MODALITA)
def test_nerd_distrattori_dallo_stesso_gruppo(catalogo, modalita):
    """Nerd: almeno il 90% dei distrattori dallo stesso gruppo,
    il 100% quando il gruppo della risposta ha almeno 4 bandiere."""
    gen = Generatore(catalogo, rng=random.Random(7))
    totale = stesso = 0
    for area in AREE:
        if not gen.info("nerd", area).giocabile:
            continue
        for _ in range(300):
            for d in gen.genera(modalita, "nerd", area):
                gruppo_grande = len(membri_gruppi(catalogo, "nerd", d.risposta.id)) >= 4
                for o in d.opzioni:
                    if o.id == d.risposta.id:
                        continue
                    totale += 1
                    ok = stesso_gruppo(catalogo, "nerd", d.risposta.id, o.id)
                    stesso += ok
                    if gruppo_grande:
                        assert ok, f"{o.id} non è nel gruppo di {d.risposta.id} ({area})"
    assert totale > 0
    assert stesso / totale >= 0.90


def test_nerd_country_mostra_bandiere_simili(catalogo):
    """In Guess the Country nerd le 4 bandiere sono dello stesso gruppo."""
    gen = Generatore(catalogo, rng=random.Random(3))
    for _ in range(200):
        for d in gen.genera("country", "nerd", AREA_MONDO):
            for o in d.opzioni:
                assert o.id == d.risposta.id or stesso_gruppo(catalogo, "nerd", d.risposta.id, o.id)


def test_difficile_usa_i_gruppi_nel_mondo(catalogo):
    """Difficile (Tutto il mondo): i distrattori vengono dal gruppo della risposta."""
    gen = Generatore(catalogo, rng=random.Random(11))
    for _ in range(200):
        for d in gen.genera("flag", "difficile", AREA_MONDO):
            if len(membri_gruppi(catalogo, "difficile", d.risposta.id)) >= 4:
                for o in d.opzioni:
                    assert o.id == d.risposta.id or stesso_gruppo(catalogo, "difficile", d.risposta.id, o.id)


@pytest.mark.parametrize("livello", ("facile", "intermedio", "difficile"))
@pytest.mark.parametrize("area", AREE[1:])
def test_distrattori_stesso_continente(catalogo, livello, area):
    """Con un filtro continente, i distrattori sono dello stesso continente."""
    gen = Generatore(catalogo, rng=random.Random(5))
    if not gen.info(livello, area).giocabile:
        pytest.skip("combinazione non giocabile")
    for _ in range(100):
        for d in gen.genera("flag", livello, area):
            for o in d.opzioni:
                assert catalogo.bandiere[o.id].continente == area


def test_facile_distrattori_dallo_stesso_livello(catalogo):
    gen = Generatore(catalogo, rng=random.Random(2))
    facili = set(catalogo.livelli["facile"].percorsi)
    for _ in range(200):
        for d in gen.genera("flag", "facile", AREA_MONDO):
            assert {o.id for o in d.opzioni} <= facili


def test_risposta_giusta_in_posizione_casuale(catalogo):
    gen = Generatore(catalogo, rng=random.Random(1))
    posizioni = Counter()
    for _ in range(500):
        for d in gen.genera("flag", "intermedio", AREA_MONDO):
            posizioni[d.indice_giusto] += 1
    totale = sum(posizioni.values())
    for i in range(OPZIONI_PER_DOMANDA):
        assert 0.20 < posizioni[i] / totale < 0.30


def test_due_generazioni_consecutive_diverse(catalogo):
    """Generatore predefinito (random.SystemRandom): partite sempre diverse."""
    gen1, gen2 = Generatore(catalogo), Generatore(catalogo)
    assert isinstance(gen1.rng, random.SystemRandom)
    for livello in LIVELLI:
        a = [(d.risposta.id, tuple(o.id for o in d.opzioni)) for d in gen1.genera("flag", livello)]
        b = [(d.risposta.id, tuple(o.id for o in d.opzioni)) for d in gen2.genera("flag", livello)]
        c = [(d.risposta.id, tuple(o.id for o in d.opzioni)) for d in gen1.genera("flag", livello)]
        assert a != b
        assert a != c


def _sovrapposizioni(catalogo, livello, area, con_storico: bool, partite: int = 40) -> int:
    storico = Storico(None) if con_storico else None
    gen = Generatore(catalogo, storico, rng=random.Random(99))
    precedente: set[str] = set()
    ripetute = 0
    for _ in range(partite):
        ids = [d.risposta.id for d in gen.genera("flag", livello, area)]
        ripetute += len(precedente & set(ids))
        precedente = set(ids)
        gen.registra_uscite("flag", livello, area, ids)
    return ripetute


def test_storico_riduce_ripetizioni(catalogo):
    senza = _sovrapposizioni(catalogo, "facile", AREA_MONDO, con_storico=False)
    con = _sovrapposizioni(catalogo, "facile", AREA_MONDO, con_storico=True)
    assert senza > 0
    assert con == 0
    # pool grande: nessuna bandiera torna prima di 60 uscite
    storico = Storico(None)
    gen = Generatore(catalogo, storico, rng=random.Random(4))
    uscite: list[str] = []
    for _ in range(6):
        ids = [d.risposta.id for d in gen.genera("country", "intermedio", AREA_MONDO)]
        gen.registra_uscite("country", "intermedio", AREA_MONDO, ids)
        uscite += ids
    assert len(set(uscite)) == len(uscite) == 60


def test_storico_pool_piccolo_sceglie_le_meno_recenti(catalogo):
    """Pool piccolo (Facile + America del Sud, 12 bandiere): ammette ripetizioni
    ma sceglie sempre prima le mai uscite e poi le meno recenti."""
    livello, area = "facile", "america_sud"
    pool = catalogo.pool(livello, area)
    assert DOMANDE_PER_PARTITA < len(pool) < DOMANDE_PER_PARTITA * 2
    storico = Storico(None)
    gen = Generatore(catalogo, storico, rng=random.Random(8))
    chiave = chiave_storico("flag", livello, area)
    viste: Counter = Counter()
    for _ in range(3 * len(pool)):
        recenti = storico.recenti(chiave)
        mai_uscite = [i for i in pool if i not in recenti]
        meno_recenti = [i for i in recenti if i in pool]
        ids = [d.risposta.id for d in gen.genera("flag", livello, area)]
        if len(mai_uscite) >= DOMANDE_PER_PARTITA:
            assert set(ids) <= set(mai_uscite)          # scelta casuale tra le mai uscite
        else:
            assert set(ids) == set((mai_uscite + meno_recenti)[:DOMANDE_PER_PARTITA])
        gen.registra_uscite("flag", livello, area, ids)
        viste.update(ids)
    assert set(viste) == set(pool)
    con = _sovrapposizioni(catalogo, livello, area, con_storico=True)
    senza = _sovrapposizioni(catalogo, livello, area, con_storico=False)
    assert con <= senza


def test_info_combinazioni_ridotte(catalogo):
    gen = Generatore(catalogo)
    info = gen.info("nerd", "america_sud")
    assert info.giocabile and info.ridotta
    assert info.domande == info.disponibili < DOMANDE_PER_PARTITA
    assert len(gen.genera("flag", "nerd", "america_sud")) == info.domande
    info = gen.info("facile", AREA_MONDO)
    assert info.giocabile and not info.ridotta and info.domande == DOMANDE_PER_PARTITA
    vuoto = gen.info("inesistente", AREA_MONDO)
    assert not vuoto.giocabile and vuoto.domande == 0


def test_chiave_storico():
    assert chiave_storico("flag", "nerd", "europa") == "flag|nerd|europa"
