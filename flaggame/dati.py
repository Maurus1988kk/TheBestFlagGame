"""Caricamento delle bandiere: scansione delle cartelle, nomi, continenti, gruppi.

Questo modulo legge soltanto: non rinomina, sposta o modifica mai i file
delle cartelle delle bandiere. Le informazioni aggiuntive (nomi italiani,
continenti, livelli) arrivano dai file JSON della cartella ``dati``.

Struttura attesa della radice delle bandiere (vedi STRUTTURA_DATI.md)::

    flags/
        easy/            bandiere del livello Facile (file sciolti)
        intermediate/    livello Intermedio
        difficult/0..26  livello Difficile, una sottocartella per gruppo di similarità
        nerd/0..34       livello Nerd, una sottocartella per gruppo di similarità
        theworld/<continente>/   usata solo per ricavare il continente
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

AREA_MONDO = "mondo"

ESTENSIONI_IMMAGINE = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}
FILE_DI_SISTEMA = {"thumbs.db", "desktop.ini", ".ds_store"}

CONTINENTI_PREDEFINITI = ("europa", "asia", "africa", "america_nord", "america_sud", "oceania")

LIVELLI_PREDEFINITI = (
    {"id": "facile", "nome": "Facile", "cartella": "easy", "distrattori": "area", "punti": 100},
    {"id": "intermedio", "nome": "Intermedio", "cartella": "intermediate", "distrattori": "area", "punti": 150},
    {"id": "difficile", "nome": "Difficile", "cartella": "difficult", "distrattori": "area", "punti": 200},
    {"id": "nerd", "nome": "Nerd", "cartella": "nerd", "distrattori": "gruppo", "punti": 300},
)
PUNTI_PREDEFINITI = 100  # punti per risposta giusta di un livello senza "punti" in livelli.json


# --------------------------------------------------------------------------- #
# Strutture dati
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class ConfigLivello:
    """Definizione di un livello letta da livelli.json."""

    id: str
    nome: str
    cartella: str
    distrattori: str = "area"  # "area" oppure "gruppo"
    punti: int = PUNTI_PREDEFINITI  # punti per risposta giusta (classifica)


@dataclass(frozen=True)
class Bandiera:
    """Una bandiera (stato, territorio, regione...) indipendente dal livello."""

    id: str
    nome: str
    continente: str | None
    iso: str | None = None
    tipo: str | None = None
    ritaglia_sfondo: bool = False   # immagine con sfondo uniforme intorno (es. Nepal)


@dataclass
class Livello:
    """Le bandiere di un livello, con gli eventuali gruppi di similarità."""

    config: ConfigLivello
    percorsi: dict[str, Path] = field(default_factory=dict)
    gruppi: dict[str, frozenset[str]] = field(default_factory=dict)
    gruppi_di: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.config.id

    @property
    def ha_gruppi(self) -> bool:
        return bool(self.gruppi)


@dataclass(frozen=True)
class Anomalia:
    """Un problema trovato durante la scansione (file illeggibile, duplicato...)."""

    percorso: str
    tipo: str
    dettaglio: str


@dataclass
class Configurazione:
    """Contenuto dei file JSON della cartella ``dati``."""

    livelli: list[ConfigLivello]
    cartella_continenti: str = "theworld"
    continenti: tuple[str, ...] = CONTINENTI_PREDEFINITI
    cartelle_theworld: dict[str, str] = field(default_factory=dict)
    mappa_continenti: dict[str, str | None] = field(default_factory=dict)
    nomi: dict[str, dict] = field(default_factory=dict)
    alias: dict[str, str] = field(default_factory=dict)
    alias_esatti: dict[str, str] = field(default_factory=dict)


class ErroreDati(Exception):
    """Errore grave nei dati (es. radice delle bandiere non valida)."""


# --------------------------------------------------------------------------- #
# Funzioni di supporto
# --------------------------------------------------------------------------- #

def normalizza(testo: str) -> str:
    """Minuscolo, accenti in forma composta (NFC) e spazi singoli."""
    testo = unicodedata.normalize("NFC", testo).strip().lower()
    return " ".join(testo.split())


def chiave_naturale(nome: str) -> list:
    """Chiave di ordinamento che mette "2" prima di "10"."""
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", nome)]


def nome_da_file(stem: str) -> str:
    """Nome leggibile ricavato dal nome del file, se manca in nomi.json."""
    pulito = " ".join(unicodedata.normalize("NFC", stem).replace("_", " ").split())
    return " ".join(p[:1].upper() + p[1:] for p in pulito.split(" "))


def formato_immagine(percorso: Path) -> str | None:
    """Riconosce il formato dal contenuto (non dall'estensione).

    Restituisce "png", "jpeg", "gif", "bmp", "webp", "svg" oppure ``None`` se
    il file è vuoto, illeggibile o non è un'immagine.
    """
    try:
        with open(percorso, "rb") as f:
            testa = f.read(512)
    except OSError:
        return None
    if testa.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if testa.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if testa[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if testa.startswith(b"BM"):
        return "bmp"
    if testa[:4] == b"RIFF" and testa[8:12] == b"WEBP":
        return "webp"
    if b"<svg" in testa.lower():
        return "svg"
    return None


_FORMATO_ESTENSIONE = {
    ".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg", ".gif": "gif",
    ".bmp": "bmp", ".webp": "webp", ".svg": "svg",
}


def _leggi_json(percorso: Path) -> dict:
    try:
        with open(percorso, encoding="utf-8") as f:
            dati = json.load(f)
        return dati if isinstance(dati, dict) else {}
    except (OSError, ValueError):
        return {}


def _punti_validi(valore) -> int:
    """Punti per risposta letti da livelli.json (numero intero positivo)."""
    if isinstance(valore, (int, float)) and not isinstance(valore, bool) and valore > 0:
        return int(valore)
    return PUNTI_PREDEFINITI


def carica_configurazione(cartella_dati: Path) -> Configurazione:
    """Legge livelli.json, nomi.json e continenti.json (con valori predefiniti)."""
    livelli_json = _leggi_json(cartella_dati / "livelli.json")
    nomi_json = _leggi_json(cartella_dati / "nomi.json")
    cont_json = _leggi_json(cartella_dati / "continenti.json")

    livelli = []
    for voce in livelli_json.get("livelli") or LIVELLI_PREDEFINITI:
        try:
            livelli.append(ConfigLivello(
                id=str(voce["id"]),
                nome=str(voce.get("nome", voce["id"])),
                cartella=str(voce["cartella"]),
                distrattori="gruppo" if voce.get("distrattori") == "gruppo" else "area",
                punti=_punti_validi(voce.get("punti")),
            ))
        except (KeyError, TypeError):
            continue

    return Configurazione(
        livelli=livelli,
        cartella_continenti=str(livelli_json.get("cartella_continenti", "theworld")),
        continenti=tuple(cont_json.get("continenti") or CONTINENTI_PREDEFINITI),
        cartelle_theworld={normalizza(k): v for k, v in (cont_json.get("cartelle_theworld") or {
            "africa": "africa", "asia": "asia", "europe": "europa",
            "northamerica": "america_nord", "southamerica": "america_sud", "oceania": "oceania",
        }).items()},
        mappa_continenti={normalizza(k): v for k, v in (cont_json.get("mappa") or {}).items()},
        nomi={normalizza(k): v for k, v in (nomi_json.get("bandiere") or {}).items() if isinstance(v, dict)},
        alias={normalizza(k): normalizza(v) for k, v in (nomi_json.get("alias") or {}).items()},
        alias_esatti={k.strip(): normalizza(v) for k, v in (nomi_json.get("alias_esatti") or {}).items()},
    )


def riconosci_radice(percorso: Path | str | None, config: Configurazione) -> Path | None:
    """Restituisce la radice delle bandiere se ``percorso`` (o la sua
    sottocartella ``flags``) contiene almeno una cartella di livello."""
    if not percorso:
        return None
    percorso = Path(percorso)
    for candidato in (percorso, percorso / "flags"):
        try:
            if candidato.is_dir() and any((candidato / l.cartella).is_dir() for l in config.livelli):
                return candidato
        except OSError:
            continue
    return None


def trova_radice(preferita: str | None, candidati: list[Path], config: Configurazione) -> Path | None:
    """Cerca la radice: prima quella scelta dall'utente, poi i candidati."""
    for percorso in ([preferita] if preferita else []) + list(candidati):
        radice = riconosci_radice(percorso, config)
        if radice is not None:
            return radice.resolve()
    return None


# --------------------------------------------------------------------------- #
# Catalogo
# --------------------------------------------------------------------------- #

@dataclass
class Catalogo:
    """Tutte le bandiere disponibili, organizzate per livello."""

    radice: Path
    bandiere: dict[str, Bandiera]
    livelli: dict[str, Livello]
    continenti: tuple[str, ...]
    anomalie: list[Anomalia]
    _cache_pool: dict = field(default_factory=dict, repr=False)

    def pool(self, livello: str, area: str = AREA_MONDO) -> list[str]:
        """Id delle bandiere giocabili per livello e area (ordinati)."""
        chiave = (livello, area)
        if chiave not in self._cache_pool:
            liv = self.livelli.get(livello)
            ids = [] if liv is None else [
                i for i in liv.percorsi
                if area == AREA_MONDO or self.bandiere[i].continente == area
            ]
            self._cache_pool[chiave] = sorted(ids)
        return list(self._cache_pool[chiave])

    def percorso(self, id_bandiera: str, livello: str | None = None) -> Path:
        """File immagine della bandiera, preferendo quello del livello indicato."""
        if livello in self.livelli and id_bandiera in self.livelli[livello].percorsi:
            return self.livelli[livello].percorsi[id_bandiera]
        for liv in self.livelli.values():
            if id_bandiera in liv.percorsi:
                return liv.percorsi[id_bandiera]
        raise KeyError(id_bandiera)

    def nome(self, id_bandiera: str) -> str:
        return self.bandiere[id_bandiera].nome

    def percorsi_da_ritagliare(self) -> set[str]:
        """File delle bandiere marcate con ``ritaglia_sfondo`` in nomi.json."""
        return {str(p) for liv in self.livelli.values() for i, p in liv.percorsi.items()
                if self.bandiere[i].ritaglia_sfondo}

    def totale_bandiere(self) -> int:
        """Numero di bandiere diverse giocabili in almeno un livello."""
        return len({i for liv in self.livelli.values() for i in liv.percorsi})


class _Identificatore:
    """Ricava l'id di una bandiera dal nome del file, applicando gli alias."""

    def __init__(self, config: Configurazione):
        self.alias = config.alias
        self.alias_esatti = config.alias_esatti

    def id_da_file(self, percorso: Path) -> str:
        stem = unicodedata.normalize("NFC", percorso.stem).strip()
        if stem in self.alias_esatti:
            return self.alias_esatti[stem]
        n = normalizza(stem)
        return self.alias.get(n, n)

    @staticmethod
    def canonico(percorso: Path, id_bandiera: str) -> bool:
        """Vero se il nome del file coincide con l'id (non è un alias)."""
        return normalizza(percorso.stem) == id_bandiera


def _file_immagine(cartella: Path, radice: Path, anomalie: list[Anomalia]) -> list[Path]:
    """File di una cartella (non ricorsivo) che hanno estensione da immagine."""
    risultato = []
    try:
        voci = sorted(cartella.iterdir(), key=lambda p: chiave_naturale(p.name))
    except OSError as e:
        anomalie.append(Anomalia(_rel(cartella, radice), "cartella_illeggibile", str(e)))
        return risultato
    for voce in voci:
        if voce.is_dir():
            continue
        if voce.name.lower() in FILE_DI_SISTEMA:
            continue
        if voce.suffix.lower() not in ESTENSIONI_IMMAGINE:
            anomalie.append(Anomalia(_rel(voce, radice), "non_immagine",
                                     "file ignorato: non è un'immagine"))
            continue
        risultato.append(voce)
    return risultato


def _rel(percorso: Path, radice: Path) -> str:
    try:
        return percorso.relative_to(radice).as_posix()
    except ValueError:
        return percorso.as_posix()


def nome_bandiera(info: dict, lingua: str) -> str | None:
    """Nome di una bandiera da nomi.json nella lingua richiesta: ``nome`` è
    l'italiano, ``nome_<codice>`` le altre lingue. ``None`` se manca."""
    return info.get("nome") if lingua == "it" else info.get(f"nome_{lingua}")


def carica_catalogo(radice: Path | str, config: Configurazione, lingua: str = "it") -> Catalogo:
    """Scansiona la radice delle bandiere e costruisce il catalogo, con i nomi
    delle bandiere nella ``lingua`` indicata ("it", "en"...)."""
    radice = Path(radice)
    if not radice.is_dir():
        raise ErroreDati(f"Cartella non trovata: {radice}")

    ident = _Identificatore(config)
    anomalie: list[Anomalia] = []
    stem_di: dict[str, str] = {}          # id -> nome file originale (per il nome di riserva)
    validi: dict[str, Path] = {}          # id -> un file valido qualsiasi (per sostituzioni)
    illeggibili: list[tuple[str, str, Path]] = []  # (livello, id, file)
    livelli: dict[str, Livello] = {}

    def esamina(file: Path) -> tuple[str, bool]:
        """Restituisce (id, valido) e registra le anomalie del file."""
        id_b = ident.id_da_file(file)
        stem_di.setdefault(id_b, file.stem)
        formato = formato_immagine(file)
        if formato is None:
            anomalie.append(Anomalia(_rel(file, radice), "illeggibile",
                                     "file vuoto o danneggiato"))
            return id_b, False
        atteso = _FORMATO_ESTENSIONE.get(file.suffix.lower())
        if atteso and atteso != formato:
            anomalie.append(Anomalia(_rel(file, radice), "estensione_errata",
                                     f"estensione {file.suffix} ma contenuto {formato.upper()} "
                                     "(viene letto comunque)"))
        if id_b not in validi or (ident.canonico(file, id_b) and not ident.canonico(validi[id_b], id_b)):
            validi[id_b] = file
        return id_b, True

    for cfg in config.livelli:
        livello = Livello(cfg)
        livelli[cfg.id] = livello
        cartella = radice / cfg.cartella
        if not cartella.is_dir():
            anomalie.append(Anomalia(cfg.cartella, "cartella_mancante",
                                     f"manca la cartella del livello {cfg.nome}"))
            continue

        membri: dict[str, set[str]] = {}

        def aggiungi(file: Path, gruppo: str | None) -> None:
            id_b, ok = esamina(file)
            insieme = membri.setdefault(gruppo, set()) if gruppo is not None else None
            gia = livello.percorsi.get(id_b)
            if insieme is not None and id_b in insieme or (gruppo is None and gia is not None):
                anomalie.append(Anomalia(_rel(file, radice), "duplicato",
                                         f"stessa bandiera di un altro file nella stessa cartella ({id_b})"))
                if ok and gia is not None and ident.canonico(file, id_b) and not ident.canonico(gia, id_b):
                    livello.percorsi[id_b] = file
                return
            if insieme is not None:
                insieme.add(id_b)
            if ok:
                if gia is None:
                    livello.percorsi[id_b] = file
            else:
                illeggibili.append((cfg.id, id_b, file))

        for file in _file_immagine(cartella, radice, anomalie):
            aggiungi(file, None)
        try:
            sottocartelle = sorted((d for d in cartella.iterdir() if d.is_dir()),
                                   key=lambda d: chiave_naturale(d.name))
        except OSError:
            sottocartelle = []
        for sotto in sottocartelle:
            for file in _file_immagine(sotto, radice, anomalie):
                aggiungi(file, sotto.name)
            if any(d.is_dir() for d in sotto.iterdir()):
                anomalie.append(Anomalia(_rel(sotto, radice), "sottocartelle_ignorate",
                                         "le sottocartelle di un gruppo non vengono lette"))

        livello.gruppi = {g: frozenset(m) for g, m in membri.items() if m}

    # Continenti ricavati da flags/theworld (e file di riserva per le sostituzioni).
    continente_cartella: dict[str, str] = {}
    cartella_mondo = radice / config.cartella_continenti
    if cartella_mondo.is_dir():
        for sotto in sorted(cartella_mondo.iterdir(), key=lambda d: chiave_naturale(d.name)):
            if not sotto.is_dir():
                continue
            cont = config.cartelle_theworld.get(normalizza(sotto.name))
            if cont is None:
                anomalie.append(Anomalia(_rel(sotto, radice), "continente_sconosciuto",
                                         "sottocartella di theworld non associata a un continente"))
                continue
            for file in _file_immagine(sotto, radice, anomalie):
                id_b, _ = esamina(file)
                continente_cartella.setdefault(id_b, cont)

    # File illeggibili: si usa la stessa bandiera presa da un'altra cartella.
    for id_liv, id_b, file in illeggibili:
        livello = livelli[id_liv]
        if id_b in livello.percorsi:
            continue
        sostituto = validi.get(id_b)
        if sostituto is not None:
            livello.percorsi[id_b] = sostituto
            anomalie.append(Anomalia(_rel(file, radice), "sostituito",
                                     f"al suo posto si usa {_rel(sostituto, radice)}"))
        else:
            anomalie.append(Anomalia(_rel(file, radice), "escluso",
                                     "nessuna copia valida: bandiera esclusa dal livello"))

    # Gruppi definitivi: solo bandiere con un'immagine valida.
    for livello in livelli.values():
        livello.gruppi = {g: frozenset(m & livello.percorsi.keys())
                          for g, m in livello.gruppi.items()}
        livello.gruppi = {g: m for g, m in livello.gruppi.items() if m}
        gruppi_di: dict[str, list[str]] = {}
        for g in sorted(livello.gruppi, key=chiave_naturale):
            for id_b in livello.gruppi[g]:
                gruppi_di.setdefault(id_b, []).append(g)
        livello.gruppi_di = {k: tuple(v) for k, v in gruppi_di.items()}

    # Bandiere: nome e continente.
    usati = {i for liv in livelli.values() for i in liv.percorsi}
    bandiere: dict[str, Bandiera] = {}
    for id_b in sorted(usati):
        info = config.nomi.get(id_b, {})
        # senza traduzione si usa il nome del file (i file hanno quasi tutti nomi inglesi)
        nome = nome_bandiera(info, lingua) or nome_da_file(stem_di.get(id_b, id_b))
        if not info:
            anomalie.append(Anomalia(id_b, "senza_nome",
                                     f"manca in nomi.json: uso il nome \"{nome}\""))
        if id_b in config.mappa_continenti:
            cont = config.mappa_continenti[id_b]
        else:
            cont = continente_cartella.get(id_b)
            if cont is None:
                anomalie.append(Anomalia(id_b, "senza_continente",
                                         "continente sconosciuto: esclusa dal filtro per area"))
        if cont is not None and cont not in config.continenti:
            anomalie.append(Anomalia(id_b, "continente_sconosciuto", f"continente \"{cont}\" non valido"))
            cont = None
        bandiere[id_b] = Bandiera(id_b, nome, cont, info.get("iso"), info.get("tipo"),
                                  bool(info.get("ritaglia_sfondo", False)))

    return Catalogo(radice=radice, bandiere=bandiere, livelli=livelli,
                    continenti=tuple(config.continenti), anomalie=anomalie)
