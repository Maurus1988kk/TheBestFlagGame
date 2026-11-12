"""Test della classifica e della persistenza su disco."""

from __future__ import annotations

import json
import os

import pytest

from flaggame import persistenza
from flaggame.classifica import Classifica, Risultato, pulisci_nome
from flaggame.persistenza import Impostazioni, Storico, leggi_json, scrivi_json_atomico


def ris(nome, giuste, tempo, data="2026-01-01T10:00:00", modalita="flag", livello="facile",
        area="mondo", totale=10):
    return Risultato(nome=nome, giuste=giuste, totale=totale, tempo=tempo, modalita=modalita,
                     livello=livello, area=area, data=data)


def test_ordinamento_percentuale_poi_tempo(tmp_path):
    c = Classifica(tmp_path / "classifica.json")
    c.aggiungi(ris("Lento", 9, 50.0))
    c.aggiungi(ris("Veloce", 9, 20.0))
    c.aggiungi(ris("Perfetto", 10, 90.0))
    c.aggiungi(ris("Scarso", 3, 5.0))
    c.aggiungi(ris("Pari", 9, 20.0, data="2026-01-02T10:00:00"))
    assert [r.nome for r in c.filtra()] == ["Perfetto", "Veloce", "Pari", "Lento", "Scarso"]


def test_percentuale_con_partite_brevi(tmp_path):
    c = Classifica(tmp_path / "c.json")
    c.aggiungi(ris("Breve", 3, 10.0, totale=3))     # 100%
    c.aggiungi(ris("Lunga", 9, 5.0))               # 90%
    assert [r.nome for r in c.filtra()] == ["Breve", "Lunga"]
    assert c.filtra()[0].percentuale == 100


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
