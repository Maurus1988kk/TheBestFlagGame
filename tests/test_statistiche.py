"""Test delle statistiche personali."""

from __future__ import annotations

from flaggame.classifica import Classifica, RispostaSalvata, Risultato
from flaggame.statistiche import PARTITE_ANDAMENTO, calcola, giocatori

PUNTI = {"facile": 100, "intermedio": 150, "difficile": 200, "nerd": 300}
CONTINENTI = {"italy": "europa", "france": "europa", "chad": "africa", "romania": "europa",
              "japan": "asia", "monaco": "europa", "indonesia": "asia"}
LIVELLI = ["facile", "intermedio", "difficile", "nerd"]
ORDINE_CONTINENTI = ["europa", "asia", "africa", "america_nord", "america_sud", "oceania"]


def partita(nome, data, livello="facile", risposte=(), giuste=None, totale=None, tempo=30.0,
            modalita="flag"):
    risposte = tuple(RispostaSalvata(i, s, 3.0) for i, s in risposte)
    if giuste is None:
        giuste = sum(r.giusta for r in risposte)
        totale = len(risposte)
    return Risultato(nome=nome, giuste=giuste, totale=totale, tempo=tempo, modalita=modalita,
                     livello=livello, area="mondo", data=data, risposte=risposte)


def stat(c, nome):
    return calcola(c, nome, CONTINENTI.get, LIVELLI, ORDINE_CONTINENTI)


def test_giocatori_senza_doppioni_dal_piu_recente():
    c = Classifica(None, PUNTI)
    c.aggiungi(partita("mauro", "2026-01-01T10:00:00", giuste=5, totale=10))
    c.aggiungi(partita("Anna", "2026-01-02T10:00:00", giuste=5, totale=10))
    c.aggiungi(partita("  Mauro ", "2026-01-03T10:00:00", giuste=5, totale=10))
    assert giocatori(c.tutti()) == ["Mauro", "Anna"]


def test_statistiche_vuote():
    s = stat(Classifica(None, PUNTI), "Nessuno")
    assert s.vuota and s.percentuale == 0 and s.migliore is None and s.andamento == []
    assert [q.totale for q in s.per_livello] == [0, 0, 0, 0]


def test_riepilogo_livelli_e_migliore():
    c = Classifica(None, PUNTI)
    c.aggiungi(partita("Mauro", "2026-01-01T10:00:00", "facile", giuste=10, totale=10, tempo=50.0))
    c.aggiungi(partita("Mauro", "2026-01-02T10:00:00", "nerd", giuste=6, totale=10, tempo=200.0))
    c.aggiungi(partita("mauro", "2026-01-03T10:00:00", "nerd", giuste=2, totale=3, tempo=12.0))
    c.aggiungi(partita("Anna", "2026-01-04T10:00:00", "nerd", giuste=10, totale=10, tempo=10.0))
    s = stat(c, "MAURO")
    assert s.giocatore == "mauro"                     # grafia più recente
    assert (s.partite, s.giuste, s.risposte) == (3, 18, 23)
    assert round(s.tempo_medio, 3) == round(262 / 23, 3)
    assert [(q.chiave, q.giuste, q.totale) for q in s.per_livello] == [
        ("facile", 10, 10), ("intermedio", 0, 0), ("difficile", 0, 0), ("nerd", 8, 13)]
    assert s.migliore.risultato.livello == "nerd" and s.migliore.punti == 1800      # 20 s a domanda: nessun bonus
    assert [p.risultato.data[:10] for p in s.andamento] == ["2026-01-01", "2026-01-02", "2026-01-03"]
    assert s.partite_con_dettaglio == 0               # risultati senza le singole risposte


def test_continenti_e_bandiere_da_ripassare():
    c = Classifica(None, PUNTI)
    c.aggiungi(partita("Mauro", "2026-01-01T10:00:00", "nerd", [
        ("chad", "romania"), ("monaco", "indonesia"), ("italy", "italy"), ("japan", "japan")]))
    c.aggiungi(partita("Mauro", "2026-01-02T10:00:00", "nerd", [
        ("chad", "romania"), ("monaco", "monaco"), ("france", "italy"), ("chad", "andorra")]))
    s = stat(c, "Mauro")
    assert s.partite_con_dettaglio == 2
    cont = {q.chiave: (q.giuste, q.totale) for q in s.per_continente}
    assert cont["europa"] == (2, 4)        # italy, monaco x2, france
    assert cont["africa"] == (0, 3)
    assert cont["asia"] == (1, 1)
    assert cont["oceania"] == (0, 0)       # mai giocato, ma presente nel grafico
    assert [q.chiave for q in s.per_continente] == ORDINE_CONTINENTI
    ripasso = [(b.id, b.sbagliate, b.viste, b.confusa_con) for b in s.da_ripassare]
    assert ripasso == [("chad", 3, 3, "romania"), ("france", 1, 1, "italy"), ("monaco", 1, 2, "indonesia")]


def test_andamento_limitato_alle_ultime_partite():
    c = Classifica(None, PUNTI)
    for i in range(PARTITE_ANDAMENTO + 5):
        c.aggiungi(partita("Mauro", f"2026-01-01T10:{i:02d}:00", giuste=i % 11, totale=10))
    s = stat(c, "Mauro")
    assert len(s.andamento) == PARTITE_ANDAMENTO
    assert s.andamento[-1].risultato.data == f"2026-01-01T10:{PARTITE_ANDAMENTO + 4:02d}:00"
    assert s.partite == PARTITE_ANDAMENTO + 5
