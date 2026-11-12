"""Test della classifica e della persistenza su disco."""

from __future__ import annotations

import json
import os
import random

import pytest

from flaggame import persistenza
from flaggame.classifica import (Classifica, RispostaSalvata, Risultato, calcola_punti,
                                 pulisci_nome)
from flaggame.persistenza import Impostazioni, Storico, leggi_json, scrivi_json_atomico


PUNTI = {"facile": 100, "intermedio": 150, "difficile": 200, "nerd": 300}


def ris(nome, giuste, tempo, data="2026-01-01T10:00:00", modalita="flag", livello="facile",
        area="mondo", totale=10, risposte=()):
    return Risultato(nome=nome, giuste=giuste, totale=totale, tempo=tempo, modalita=modalita,
                     livello=livello, area=area, data=data, risposte=tuple(risposte))


def test_ordinamento_percentuale_poi_tempo(tmp_path):
    c = Classifica(tmp_path / "classifica.json")
    c.aggiungi(ris("Lento", 9, 50.0))
    c.aggiungi(ris("Veloce", 9, 20.0))
    c.aggiungi(ris("Perfetto", 10, 90.0))
    c.aggiungi(ris("Scarso", 3, 5.0))
    c.aggiungi(ris("Pari", 9, 20.0, data="2026-01-02T10:00:00"))
    assert [r.nome for r in c.filtra()] == ["Perfetto", "Veloce", "Pari", "Lento", "Scarso"]


def test_partite_brevi_non_superano_quelle_lunghe(tmp_path):
    """Con i punti, 3 su 3 (100%) non vale più di 9 su 10 (90%)."""
    c = Classifica(tmp_path / "c.json", PUNTI)
    c.aggiungi(ris("Breve", 3, 10.0, totale=3))     # 100%, 300 punti + bonus
    c.aggiungi(ris("Lunga", 9, 50.0))              # 90%, 900 punti + bonus
    assert [r.nome for r in c.filtra()] == ["Lunga", "Breve"]
    assert c.filtra()[1].percentuale == 100


def test_calcolo_punti():
    assert calcola_punti(10, 10, 200.0, 100) == 1000      # 20 s a domanda: nessun bonus
    assert calcola_punti(10, 10, 120.0, 100) == 1000      # 12 s a domanda: ancora nessun bonus
    assert calcola_punti(10, 10, 20.0, 100) == 1100       # 2 s a domanda: bonus pieno (+10%)
    assert calcola_punti(10, 10, 5.0, 100) == 1100        # più veloce: il bonus non cresce
    assert calcola_punti(10, 10, 70.0, 100) == 1050       # 7 s a domanda: metà bonus
    assert calcola_punti(7, 10, 200.0, 300) == 2100
    assert calcola_punti(0, 10, 5.0, 300) == 0
    assert calcola_punti(3, 0, 5.0, 300) == 0


def test_una_risposta_giusta_in_piu_vale_piu_di_ogni_bonus():
    for punti in PUNTI.values():
        for giuste in range(10):
            velocissimo = calcola_punti(giuste, 10, 0.0, punti)
            lentissimo = calcola_punti(giuste + 1, 10, 10_000.0, punti)
            assert velocissimo < lentissimo


def test_livelli_diversi_nella_vista_tutte(tmp_path):
    c = Classifica(tmp_path / "c.json", PUNTI)
    c.aggiungi(ris("Facile perfetto", 10, 15.0, livello="facile"))   # 1100 punti
    c.aggiungi(ris("Nerd 70%", 7, 150.0, livello="nerd"))            # 2100 punti
    c.aggiungi(ris("Difficile 60%", 6, 150.0, livello="difficile"))  # 1200 punti
    assert [r.nome for r in c.filtra()] == ["Nerd 70%", "Difficile 60%", "Facile perfetto"]
    assert c.punti(c.filtra()[0]) == 2100


def test_livello_sconosciuto_vale_100_punti(tmp_path):
    c = Classifica(tmp_path / "c.json", PUNTI)
    assert c.punti_risposta("esperto") == 100
    assert c.punti(ris("X", 5, 500.0, livello="esperto")) == 500


def test_stessa_combinazione_ordine_come_percentuale_poi_tempo(tmp_path):
    """Dentro una combinazione l'ordine per punti coincide con quello vecchio."""
    rng = random.Random(7)
    for livello in PUNTI:
        c = Classifica(None, PUNTI)
        for i in range(300):
            c.aggiungi(ris(f"G{i}", rng.randint(0, 10), round(rng.uniform(5, 200), 2),
                           data=f"2026-01-01T10:{i // 60:02d}:{i % 60:02d}", livello=livello))
        vecchio = sorted(c.tutti(), key=lambda r: (-r.percentuale, r.tempo, r.data))
        assert [r.id for r in c.filtra()] == [r.id for r in vecchio]


def test_risposte_salvate_e_ricaricate(tmp_path):
    percorso = tmp_path / "c.json"
    risposte = [RispostaSalvata("italy", "italy", 2.5), RispostaSalvata("chad", "romania", 7.25)]
    salvato = Classifica(percorso, PUNTI).aggiungi(ris("Mauro", 1, 9.75, totale=2, risposte=risposte))
    ricaricato = Classifica(percorso, PUNTI).tutti()[0]
    assert ricaricato == salvato
    assert [r.giusta for r in ricaricato.risposte] == [True, False]
    assert json.loads(percorso.read_text(encoding="utf-8"))["risultati"][0]["risposte"][1] == {
        "id": "chad", "scelta": "romania", "tempo": 7.25}


def test_risultati_della_versione_precedente(tmp_path):
    """I risultati senza "risposte" (salvati prima dei punti) si leggono e hanno i punti."""
    percorso = tmp_path / "c.json"
    scrivi_json_atomico(percorso, {"versione": 1, "risultati": [
        {"nome": "Vecchio", "giuste": 8, "totale": 10, "tempo": 60.0, "modalita": "flag",
         "livello": "nerd", "area": "mondo", "data": "2025-11-09T21:00:00", "id": "abc"},
        {"nome": "Rotte", "giuste": 1, "totale": 1, "tempo": 3.0, "modalita": "flag",
         "livello": "facile", "area": "mondo", "id": "def", "risposte": [{"id": "x"}, {"id": "y", "scelta": "y"}]},
    ]})
    c = Classifica(percorso, PUNTI)
    vecchio = c.tutti()[0]
    assert vecchio.risposte == ()
    assert c.punti(vecchio) == calcola_punti(8, 10, 60.0, 300)
    assert [r.id for r in c.tutti()[1].risposte] == ["y"]          # risposta non valida ignorata


def test_filtri_e_top(tmp_path):
    c = Classifica(tmp_path / "c.json")
    for i in range(15):
        c.aggiungi(ris(f"G{i}", i % 11, 30 - i))
    c.aggiungi(ris("Country", 10, 1, modalita="country"))
    c.aggiungi(ris("Nerd", 10, 1, livello="nerd"))
    c.aggiungi(ris("Europa", 10, 1, area="europa"))
    assert len(c.top(modalita="flag", livello="facile", area="mondo")) == 10
    assert [r.nome for r in c.filtra(modalita="country")] == ["Country"]
    assert [r.nome for r in c.filtra(livello="nerd")] == ["Nerd"]
    assert [r.nome for r in c.filtra(area="europa")] == ["Europa"]
    assert len(c.filtra()) == 18
    tutti = c.filtra(modalita="flag", livello="facile", area="mondo")
    ultimo = tutti[-1]
    assert c.posizione(ultimo.id, modalita="flag", livello="facile", area="mondo") == 15


def test_salvataggio_e_ricaricamento_senza_perdite(tmp_path):
    percorso = tmp_path / "classifica.json"
    c = Classifica(percorso)
    originali = [c.aggiungi(ris(f"Nome {i} àèé", i % 11, 10.5 + i, modalita=("flag", "country")[i % 2]))
                 for i in range(30)]
    ricaricata = Classifica(percorso)
    assert len(ricaricata) == 30
    assert sorted(ricaricata.tutti(), key=lambda r: r.id) == sorted(originali, key=lambda r: r.id)
    assert [r.id for r in ricaricata.filtra()] == [r.id for r in c.filtra()]


def test_nome_ripulito(tmp_path):
    c = Classifica(tmp_path / "c.json")
    r = c.aggiungi(ris("   Mario    Rossi   ", 5, 10))
    assert r.nome == "Mario Rossi"
    assert c.aggiungi(ris("   ", 5, 10)).nome == "Anonimo"
    assert len(pulisci_nome("x" * 100)) == 24


def test_scrittura_atomica_non_corrompe(tmp_path, monkeypatch):
    percorso = tmp_path / "classifica.json"
    c = Classifica(percorso)
    c.aggiungi(ris("Primo", 10, 10))
    contenuto = percorso.read_text(encoding="utf-8")

    def guasto(*args, **kwargs):
        raise OSError("crash simulato durante la rinomina")
    monkeypatch.setattr(persistenza.os, "replace", guasto)
    with pytest.raises(OSError):
        c.aggiungi(ris("Secondo", 9, 10))
    monkeypatch.undo()
    assert percorso.read_text(encoding="utf-8") == contenuto      # file vecchio intatto
    assert [p.name for p in tmp_path.iterdir()] == ["classifica.json"]  # nessun temporaneo rimasto
    assert [r.nome for r in Classifica(percorso).filtra()] == ["Primo"]


def test_file_danneggiato_viene_messo_da_parte(tmp_path):
    percorso = tmp_path / "classifica.json"
    percorso.write_text("{ non è json", encoding="utf-8")
    c = Classifica(percorso)
    assert len(c) == 0
    copie = [p for p in tmp_path.iterdir() if ".danneggiato-" in p.name]
    assert len(copie) == 1


def test_righe_non_valide_ignorate(tmp_path):
    percorso = tmp_path / "c.json"
    scrivi_json_atomico(percorso, {"risultati": [
        {"nome": "Ok", "giuste": 5, "totale": 10, "tempo": 3, "modalita": "flag",
         "livello": "facile", "area": "mondo", "data": "2026-01-01T00:00:00", "id": "a"},
        {"nome": "Rotta"},
    ]})
    assert [r.nome for r in Classifica(percorso).tutti()] == ["Ok"]


def test_impostazioni(tmp_path):
    percorso = tmp_path / "impostazioni.json"
    imp = Impostazioni.carica(percorso)
    assert imp.tema == "chiaro" and imp.suoni and imp.avanzamento_automatico
    imp.tema = "scuro"
    imp.ultimo_nome = "Mauro"
    imp.salva(percorso)
    di_nuovo = Impostazioni.carica(percorso)
    assert di_nuovo.tema == "scuro" and di_nuovo.ultimo_nome == "Mauro"
    percorso.write_text(json.dumps({"tema": "viola", "suoni": "si"}), encoding="utf-8")
    strane = Impostazioni.carica(percorso)
    assert strane.tema == "chiaro" and strane.suoni is True


def test_storico_persistente_e_limitato(tmp_path):
    percorso = tmp_path / "storico.json"
    s = Storico(percorso, massimo=60)
    s.registra("k", [f"b{i}" for i in range(50)])
    s.registra("k", [f"b{i}" for i in range(40, 70)])
    recenti = Storico(percorso).recenti("k")
    assert len(recenti) == 60
    assert recenti[-1] == "b69"
    assert len(set(recenti)) == 60
    s.azzera()
    assert Storico(percorso).recenti("k") == []


def test_leggi_json_mancante(tmp_path):
    assert leggi_json(tmp_path / "manca.json", {"x": 1}) == {"x": 1}
    assert not os.path.exists(tmp_path / "manca.json")
