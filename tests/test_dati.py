"""Test della scansione delle cartelle e dei file JSON."""

from __future__ import annotations

import json
import os
from pathlib import Path

from flaggame.dati import (AREA_MONDO, carica_catalogo, carica_configurazione, formato_immagine,
                           normalizza, riconosci_radice)

from .conftest import CARTELLA_BANDIERE, RADICE_PROGETTO

PNG_MINIMO = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000002000000010806000000f478d4fa"
    "0000001049444154789c63f8cfc0f01f0005fe02fef0c4e1bc0000000049454e44ae426082"
)


def test_catalogo_reale(catalogo):
    assert catalogo.totale_bandiere() == 333
    conteggi = {k: len(v.percorsi) for k, v in catalogo.livelli.items()}
    assert conteggi == {"facile": 187, "intermedio": 243, "difficile": 309, "nerd": 158}
    assert not catalogo.livelli["facile"].ha_gruppi
    assert len(catalogo.livelli["difficile"].gruppi) == 27
    assert len(catalogo.livelli["nerd"].gruppi) == 35


def test_tutti_i_nomi_sono_in_nomi_json(catalogo):
    senza_nome = [a for a in catalogo.anomalie if a.tipo == "senza_nome"]
    assert senza_nome == []
    assert catalogo.nome("italy") == "Italia"
    assert catalogo.nome("sao tomè e principe") == "São Tomé e Príncipe"


def test_georgia_stato_e_georgia_usa_sono_distinte(catalogo):
    assert catalogo.nome("georgia") == "Georgia"
    assert catalogo.nome("georgia (usa)") == "Georgia (USA)"
    assert catalogo.bandiere["georgia"].continente == "europa"
    assert catalogo.bandiere["georgia (usa)"].continente == "america_nord"
    assert "georgia (usa)" in catalogo.livelli["nerd"].percorsi
    assert "georgia" not in catalogo.livelli["nerd"].percorsi


def test_punti_dei_livelli(config, tmp_path):
    assert [(l.id, l.punti) for l in config.livelli] == [
        ("facile", 100), ("intermedio", 150), ("difficile", 200), ("nerd", 300)]
    (tmp_path / "livelli.json").write_text(json.dumps({"livelli": [
        {"id": "a", "cartella": "a"}, {"id": "b", "cartella": "b", "punti": -5},
        {"id": "c", "cartella": "c", "punti": "tanti"}, {"id": "d", "cartella": "d", "punti": 250}]}),
        encoding="utf-8")
    assert [l.punti for l in carica_configurazione(tmp_path).livelli] == [100, 100, 100, 250]


def test_file_reali_tutti_leggibili(catalogo):
    illeggibili = [a.percorso for a in catalogo.anomalie if a.tipo == "illeggibile"]
    assert illeggibili == []
    canada = catalogo.livelli["difficile"].percorsi["canada"]
    assert canada.parent.name == "10"
    assert formato_immagine(canada) == "png"


def test_file_danneggiato_sostituito_da_altra_cartella(config, tmp_path):
    radice = tmp_path / "flags"
    (radice / "easy").mkdir(parents=True)
    (radice / "difficult" / "10").mkdir(parents=True)
    (radice / "easy" / "canada.png").write_bytes(PNG_MINIMO)
    (radice / "difficult" / "10" / "canada.png").write_bytes(bytes(64))   # solo zeri
    cat = carica_catalogo(radice, config)
    tipi = {(a.tipo, a.percorso) for a in cat.anomalie}
    assert ("illeggibile", "difficult/10/canada.png") in tipi
    assert ("sostituito", "difficult/10/canada.png") in tipi
    assert cat.livelli["difficile"].percorsi["canada"].parent.name == "easy"
    assert "10" in cat.livelli["difficile"].gruppi_di["canada"]


def test_alias_e_duplicati(catalogo):
    assert "jamaica (1)" not in catalogo.bandiere
    assert catalogo.livelli["intermedio"].percorsi["jamaica"].name == "jamaica.PNG"
    assert "south georgia" not in catalogo.bandiere
    assert "south georgia and south sandwich islands" in catalogo.livelli["nerd"].percorsi


def test_continenti(catalogo):
    assert catalogo.bandiere["afghanistan"].continente == "asia"      # corretto rispetto a theworld
    assert catalogo.bandiere["guam"].continente == "oceania"
    assert catalogo.bandiere["greenland"].continente == "america_nord"
    assert catalogo.bandiere["antartica"].continente is None
    assert "antartica" in catalogo.pool("intermedio", AREA_MONDO)
    for area in catalogo.continenti:
        assert "antartica" not in catalogo.pool("intermedio", area)
    somma = sum(len(catalogo.pool("intermedio", a)) for a in catalogo.continenti)
    assert somma == len(catalogo.pool("intermedio", AREA_MONDO)) - 1


def test_json_coerenti(config):
    nomi = json.loads((RADICE_PROGETTO / "dati" / "nomi.json").read_text(encoding="utf-8"))
    cont = json.loads((RADICE_PROGETTO / "dati" / "continenti.json").read_text(encoding="utf-8"))
    assert set(nomi["bandiere"]) == set(cont["mappa"])
    validi = set(cont["continenti"]) | {None}
    assert all(v in validi for v in cont["mappa"].values())
    assert [l.cartella for l in config.livelli] == ["easy", "intermediate", "difficult", "nerd"]


def test_la_scansione_non_modifica_i_file(config):
    """Regola ferma: nessun file delle bandiere viene toccato."""
    def istantanea():
        return {p: (p.stat().st_size, p.stat().st_mtime_ns)
                for p in CARTELLA_BANDIERE.rglob("*") if p.is_file()}
    prima = istantanea()
    carica_catalogo(CARTELLA_BANDIERE, config)
    assert istantanea() == prima


def test_riconosci_radice(config, tmp_path):
    assert riconosci_radice(CARTELLA_BANDIERE, config) == CARTELLA_BANDIERE
    assert riconosci_radice(RADICE_PROGETTO, config) == CARTELLA_BANDIERE
    assert riconosci_radice(tmp_path, config) is None
    assert riconosci_radice(None, config) is None


def test_cartella_sintetica(config, tmp_path):
    """Livelli piatti e a gruppi, file non immagine, file vuoti, nomi nuovi."""
    radice = tmp_path / "flags"
    (radice / "easy").mkdir(parents=True)
    (radice / "nerd" / "1").mkdir(parents=True)
    (radice / "nerd" / "2").mkdir(parents=True)
    (radice / "theworld" / "europe").mkdir(parents=True)
    for nome in ("italy.png", "France.PNG", "nuova_bandiera.png"):
        (radice / "easy" / nome).write_bytes(PNG_MINIMO)
    (radice / "easy" / "leggimi.txt").write_text("ciao")
    (radice / "easy" / "Thumbs.db").write_bytes(b"x")
    (radice / "nerd" / "1" / "chad.png").write_bytes(PNG_MINIMO)
    (radice / "nerd" / "1" / "romania.png").write_bytes(b"")          # vuoto
    (radice / "nerd" / "2" / "romania.png").write_bytes(PNG_MINIMO)
    (radice / "theworld" / "europe" / "nuova_bandiera.png").write_bytes(PNG_MINIMO)
    (radice / "theworld" / "europe" / "romania.png").write_bytes(PNG_MINIMO)

    cat = carica_catalogo(radice, config)
    assert set(cat.livelli["facile"].percorsi) == {"italy", "france", "nuova_bandiera"}
    assert cat.nome("france") == "Francia"
    assert cat.nome("nuova_bandiera") == "Nuova Bandiera"          # nome ricavato dal file
    assert cat.bandiere["nuova_bandiera"].continente == "europa"    # da theworld
    tipi = {a.tipo for a in cat.anomalie}
    assert {"non_immagine", "illeggibile", "senza_nome", "cartella_mancante"} <= tipi
    nerd = cat.livelli["nerd"]
    assert nerd.gruppi == {"1": frozenset({"chad", "romania"}), "2": frozenset({"romania"})}
    assert nerd.percorsi["romania"].parent.name == "2"              # copia valida
    assert cat.livelli["intermedio"].percorsi == {}


def test_formato_immagine(tmp_path):
    f = tmp_path / "x.png"
    f.write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 20)
    assert formato_immagine(f) == "jpeg"
    f.write_bytes(b"<?xml version='1.0'?><svg xmlns='http://www.w3.org/2000/svg'></svg>")
    assert formato_immagine(f) == "svg"
    f.write_bytes(b"\0" * 64)
    assert formato_immagine(f) is None
    assert formato_immagine(tmp_path / "manca.png") is None


def test_normalizza():
    assert normalizza("  Sao  Tomè e Principe ") == "sao tomè e principe"
    assert normalizza("Birmania - Burma - Myanmar") == "birmania - burma - myanmar"


def test_configurazione_predefinita_senza_json(tmp_path):
    cfg = carica_configurazione(tmp_path)
    assert [l.id for l in cfg.livelli] == ["facile", "intermedio", "difficile", "nerd"]
    assert cfg.livelli[3].distrattori == "gruppo"
    assert os.path.isdir(tmp_path)
    assert Path(tmp_path).exists()
