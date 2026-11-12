"""Sostituisce le bandiere di flags/ con le versioni ufficiali di Wikimedia Commons.

Le immagini originali erano screenshot fatti a mano: formati, colori e
proporzioni diversi, alcune bandiere superate. Questo script prende per ogni
bandiera il disegno di riferimento su Commons (quasi sempre un SVG di pubblico
dominio), lo fa rendere in PNG dal server di Wikimedia e lo porta alla stessa
altezza per tutte (``altezza`` in fonti_bandiere.json), con le proporzioni
ufficiali.

Uso, dalla cartella del progetto e con il Python di build (serve Pillow):

    python tools/aggiorna_bandiere.py info       controlla i file su Commons, aggiunge licenze e pagine
    python tools/aggiorna_bandiere.py scarica    scarica e prepara i PNG (nella cartella di cache)
    python tools/aggiorna_bandiere.py confronto  crea confronto.html: ultimo commit (o quello indicato) / nuove
    python tools/aggiorna_bandiere.py applica    sostituisce i file in flags/ (stessi nomi e cartelle)

La corrispondenza bandiera -> file di Commons sta in tools/fonti_bandiere.json.
La cache è in %LOCALAPPDATA%\\FlagGame-build\\commons (fuori da OneDrive);
si può cambiare con la variabile FLAGGAME_COMMONS. "applica" non tocca le
bandiere che non hanno un PNG pronto. Il progetto è sotto git: per tornare
indietro basta ``git checkout -- flags``.
"""

from __future__ import annotations

import base64
import html
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))

from flaggame.dati import (ESTENSIONI_IMMAGINE, FILE_DI_SISTEMA, _Identificatore,  # noqa: E402
                           carica_configurazione)

FONTI = RADICE / "tools" / "fonti_bandiere.json"
CARTELLA_BANDIERE = RADICE / "flags"
API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia chiede un User-Agent che identifichi lo strumento.
USER_AGENT = "FlagGameUpdater/1.0 (personal non-commercial flag quiz; python-urllib)"
LARGHEZZE_STANDARD = (960, 1280, 1920, 2560, 3840)   # le uniche servite dal server delle miniature
PAUSA = 4.0                                           # secondi tra un download e l'altro (limiti di Wikimedia)


def cartella_cache() -> Path:
    base = os.environ.get("FLAGGAME_COMMONS") or os.path.join(
        os.environ.get("LOCALAPPDATA", str(Path.home())), "FlagGame-build", "commons")
    return Path(base)


def leggi_fonti() -> dict:
    return json.loads(FONTI.read_text(encoding="utf-8"))


def scrivi_fonti(dati: dict) -> None:
    FONTI.write_bytes(json.dumps(dati, ensure_ascii=False, indent=1).encode("utf-8") + b"\n")


def scarica_url(url: str, tentativi: int = 8) -> bytes:
    """Scarica rispettando i limiti di Wikimedia: con 429 aspetta quanto chiede
    il server (Retry-After) prima di riprovare."""
    for tentativo in range(tentativi):
        richiesta = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(richiesta, timeout=60) as risposta:
                return risposta.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and tentativo < tentativi - 1:
                try:
                    attesa = int(e.headers.get("Retry-After", "0"))
                except ValueError:
                    attesa = 0
                time.sleep(max(attesa, 10) + 5 * tentativo)
                continue
            raise
        except urllib.error.URLError:
            if tentativo < tentativi - 1:
                time.sleep(3 * (tentativo + 1))
                continue
            raise
    raise RuntimeError("non raggiungibile")


# --------------------------------------------------------------------------- #
# info: esistenza dei file, redirect, dimensioni, licenze
# --------------------------------------------------------------------------- #

def comando_info() -> int:
    dati = leggi_fonti()
    voci = dati["bandiere"]
    per_titolo: dict[str, list[str]] = {}
    for id_b, v in voci.items():
        per_titolo.setdefault("File:" + v["commons"], []).append(id_b)
    titoli = list(per_titolo)
    mancanti = []
    for inizio in range(0, len(titoli), 40):
        blocco = titoli[inizio:inizio + 40]
        parametri = {
            "action": "query", "format": "json", "formatversion": "2", "redirects": "1",
            "titles": "|".join(blocco), "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata", "iiextmetadatafilter": "LicenseShortName",
        }
        risposta = json.loads(scarica_url(API + "?" + urllib.parse.urlencode(parametri)))
        q = risposta.get("query", {})
        rinomina = {}
        for passo in q.get("normalized", []) + q.get("redirects", []):
            rinomina[passo["from"]] = passo["to"]
        pagine = {p["title"]: p for p in q.get("pages", [])}
        for titolo in blocco:
            finale = titolo
            while finale in rinomina:
                finale = rinomina[finale]
            pagina = pagine.get(finale)
            for id_b in per_titolo[titolo]:
                v = voci[id_b]
                if not pagina or pagina.get("missing") or not pagina.get("imageinfo"):
                    v.pop("licenza", None)
                    v["mancante"] = True
                    mancanti.append((id_b, titolo))
                    continue
                info = pagina["imageinfo"][0]
                v.pop("mancante", None)
                v["file"] = finale.removeprefix("File:")
                v["pagina"] = info["descriptionurl"].split("?")[0]
                v["url"] = info["url"].split("?")[0]
                v["mime"] = info.get("mime", "")
                v["larghezza"], v["altezza"] = info.get("width", 0), info.get("height", 0)
                meta = info.get("extmetadata", {})
                v["licenza"] = meta.get("LicenseShortName", {}).get("value", "")
        time.sleep(PAUSA)
    scrivi_fonti(dati)
    print(f"{len(voci)} bandiere, {len(mancanti)} file non trovati su Commons")
    for id_b, titolo in mancanti:
        print(f"  MANCA  {id_b:40s} {titolo}")
    licenze: dict[str, int] = {}
    for v in voci.values():
        if v.get("licenza"):
            licenze[v["licenza"]] = licenze.get(v["licenza"], 0) + 1
    print("licenze:", ", ".join(f"{k}: {n}" for k, n in sorted(licenze.items(), key=lambda x: -x[1])))
    return 1 if mancanti else 0


# --------------------------------------------------------------------------- #
# scarica: miniatura PNG del server -> altezza uniforme
# --------------------------------------------------------------------------- #

def url_miniatura(url_originale: str, larghezza: int) -> str:
    """URL della resa PNG di un file di Commons a una delle larghezze standard."""
    parti = urllib.parse.urlsplit(url_originale)
    cartelle, nome = parti.path.rsplit("/", 1)
    percorso = cartelle.replace("/wikipedia/commons/", "/wikipedia/commons/thumb/", 1)
    estensione = ".png" if nome.lower().endswith(".svg") else ""
    return f"{parti.scheme}://{parti.netloc}{percorso}/{nome}/{larghezza}px-{nome}{estensione}"


def prepara_png(contenuto: bytes, altezza: int) -> bytes:
    from PIL import Image
    im = Image.open(io.BytesIO(contenuto))
    im.load()
    im = im.convert("RGBA")
    larghezza = max(1, round(im.width * altezza / im.height))
    im = im.resize((larghezza, altezza), Image.Resampling.LANCZOS)
    if im.getchannel("A").getextrema()[0] == 255:   # nessuna trasparenza: basta RGB
        im = im.convert("RGB")
    uscita = io.BytesIO()
    im.save(uscita, "PNG", optimize=True)
    return uscita.getvalue()


def comando_scarica(solo: list[str]) -> int:
    dati = leggi_fonti()
    altezza = int(dati.get("altezza", 600))
    pronte = cartella_cache() / "pronte"
    pronte.mkdir(parents=True, exist_ok=True)
    errori = []
    voci = {k: v for k, v in dati["bandiere"].items() if not solo or k in solo}
    for n, (id_b, v) in enumerate(sorted(voci.items()), start=1):
        destinazione = pronte / f"{id_b}.png"
        firma = f"{v.get('url')}|{altezza}"
        firma_file = pronte / f"{id_b}.fonte"
        if destinazione.exists() and firma_file.exists() and firma_file.read_text(encoding="utf-8") == firma:
            continue   # già scaricata con la stessa fonte
        if v.get("mancante") or not v.get("url"):
            errori.append((id_b, "nessun file su Commons (lancia prima 'info')"))
            continue
        try:
            if v.get("mime") == "image/svg+xml" or v["url"].lower().endswith(".svg"):
                rapporto = v["larghezza"] / v["altezza"] if v.get("altezza") else 1.5
                serve = altezza * rapporto * 1.25   # un po' di margine per la riduzione
                larghezza = next((l for l in LARGHEZZE_STANDARD if l >= serve), LARGHEZZE_STANDARD[-1])
                contenuto = scarica_url(url_miniatura(v["url"], larghezza))
            else:
                contenuto = scarica_url(v["url"])   # immagine bitmap: si usa l'originale
            destinazione.write_bytes(prepara_png(contenuto, altezza))
            firma_file.write_text(firma, encoding="utf-8")
            print(f"[{n}/{len(voci)}] {id_b}", flush=True)
        except Exception as e:  # noqa: BLE001 - si segnala e si prosegue
            errori.append((id_b, str(e)))
            print(f"[{n}/{len(voci)}] ERRORE {id_b}: {e}")
        time.sleep(PAUSA)
    print(f"Fatto. Cartella: {pronte}. Errori: {len(errori)}")
    for id_b, e in errori:
        print(f"  {id_b}: {e}")
    return 1 if errori else 0


# --------------------------------------------------------------------------- #
# file delle bandiere nel progetto
# --------------------------------------------------------------------------- #

def file_bandiere() -> list[tuple[Path, str]]:
    """(file, id) per ogni immagine in flags/, comprese le copie e theworld."""
    ident = _Identificatore(carica_configurazione(RADICE / "dati"))
    risultato = []
    for f in sorted(CARTELLA_BANDIERE.rglob("*")):
        if f.is_file() and f.suffix.lower() in ESTENSIONI_IMMAGINE and f.name.lower() not in FILE_DI_SISTEMA:
            risultato.append((f, ident.id_da_file(f)))
    return risultato


# --------------------------------------------------------------------------- #
# confronto: pagina HTML prima/dopo
# --------------------------------------------------------------------------- #

def _miniatura_base64(contenuto: bytes, altezza: int = 90) -> str:
    from PIL import Image
    im = Image.open(io.BytesIO(contenuto))
    im.load()
    im = im.convert("RGBA")
    im.thumbnail((int(altezza * 3), altezza), Image.Resampling.LANCZOS)
    uscita = io.BytesIO()
    im.save(uscita, "PNG", optimize=True)
    return base64.b64encode(uscita.getvalue()).decode()


def immagini_di_un_commit(commit: str) -> dict[str, bytes]:
    """Prima immagine di ogni bandiera com'era in ``commit`` (vuoto se non c'è git)."""
    import subprocess
    ident = _Identificatore(carica_configurazione(RADICE / "dati"))
    try:
        elenco = subprocess.run(["git", "ls-tree", "-r", "--name-only", commit, "--", "flags"],
                                cwd=RADICE, capture_output=True, text=True, encoding="utf-8", check=True)
    except (OSError, subprocess.CalledProcessError):
        return {}
    risultato: dict[str, bytes] = {}
    for riga in sorted(elenco.stdout.splitlines()):
        percorso = Path(riga)
        if percorso.suffix.lower() not in ESTENSIONI_IMMAGINE:
            continue
        id_b = ident.id_da_file(percorso)
        if id_b not in risultato:
            contenuto = subprocess.run(["git", "show", f"{commit}:{riga}"], cwd=RADICE, capture_output=True)
            if contenuto.returncode == 0:
                risultato[id_b] = contenuto.stdout
    return risultato


def comando_confronto(commit: str = "HEAD") -> int:
    """Pagina HTML: a sinistra le bandiere dell'ultimo commit (o di ``commit``),
    a destra quelle pronte nella cache."""
    dati = leggi_fonti()
    nomi = json.loads((RADICE / "dati" / "nomi.json").read_text(encoding="utf-8"))["bandiere"]
    pronte = cartella_cache() / "pronte"
    prima = immagini_di_un_commit(commit)
    if not prima:   # niente git: si usano i file attuali
        for f, id_b in file_bandiere():
            prima.setdefault(id_b, f.read_bytes())
    righe = []
    for id_b in sorted(dati["bandiere"], key=lambda i: nomi.get(i, {}).get("nome", i).casefold()):
        v = dati["bandiere"][id_b]
        vecchio = prima.get(id_b)
        nuovo = pronte / f"{id_b}.png"
        try:
            img_vecchio = (f'<img src="data:image/png;base64,{_miniatura_base64(vecchio)}">'
                           if vecchio else "—")
        except Exception:  # noqa: BLE001
            img_vecchio = "illeggibile"
        img_nuovo = (f'<img src="data:image/png;base64,{_miniatura_base64(nuovo.read_bytes())}">'
                     if nuovo.exists() else '<b class="manca">non trovata</b>')
        nota = f'<div class="nota">{html.escape(v["nota"])}</div>' if v.get("nota") else ""
        pagina = v.get("pagina", "")
        fonte = (f'<a href="{html.escape(pagina)}">{html.escape(v.get("file", v["commons"]))}</a>'
                 if pagina else html.escape(v["commons"]))
        righe.append(f"<tr><td><b>{html.escape(nomi.get(id_b, {}).get('nome', id_b))}</b>"
                     f"<div class='id'>{html.escape(id_b)}</div>{nota}</td>"
                     f"<td>{img_vecchio}</td><td>{img_nuovo}</td>"
                     f"<td class='fonte'>{fonte}<div>{html.escape(v.get('licenza', ''))}</div></td></tr>")
    pagina_html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
<title>Bandiere: prima e dopo</title><style>
body {{ font-family: "Segoe UI", sans-serif; background: #F2F4F9; color: #141B2D; margin: 24px; }}
table {{ border-collapse: collapse; background: #fff; border-radius: 12px; }}
td, th {{ padding: 8px 14px; border-bottom: 1px solid #E2E7F0; vertical-align: middle; text-align: left; }}
img {{ height: 90px; border: 1px solid #C3CAD7; }}
.id {{ color: #8B95A8; font-size: 12px; }} .fonte {{ font-size: 12px; color: #5A6579; max-width: 260px; }}
.nota {{ color: #A15C07; font-size: 12px; max-width: 260px; }} .manca {{ color: #E1444A; }}
</style></head><body><h1>Bandiere: prima e dopo</h1>
<p>{len(righe)} bandiere. A sinistra com'erano nel commit {html.escape(commit)}, a destra la versione di Wikimedia Commons.</p>
<table><tr><th>Bandiera</th><th>Prima</th><th>Dopo</th><th>Fonte</th></tr>{''.join(righe)}</table>
</body></html>"""
    destinazione = cartella_cache() / "confronto.html"
    destinazione.write_text(pagina_html, encoding="utf-8")
    print(destinazione)
    return 0


# --------------------------------------------------------------------------- #
# applica: sostituzione dei file in flags/
# --------------------------------------------------------------------------- #

def comando_applica() -> int:
    pronte = cartella_cache() / "pronte"
    sostituiti, rinominati, saltati = 0, 0, []
    for f, id_b in file_bandiere():
        nuovo = pronte / f"{id_b}.png"
        if not nuovo.exists():
            saltati.append(f.relative_to(RADICE).as_posix())
            continue
        contenuto = nuovo.read_bytes()
        if f.suffix.lower() == ".png":
            # stesso file (anche se l'estensione è .PNG): si riscrive al suo posto
            f.write_bytes(contenuto)
        else:
            destinazione = f.with_suffix(".png")
            if destinazione.exists():
                raise SystemExit(f"Esiste già {destinazione}: controlla a mano prima di continuare")
            destinazione.write_bytes(contenuto)
            f.unlink()
            rinominati += 1
        sostituiti += 1
    print(f"File sostituiti: {sostituiti} (di cui {rinominati} diventati .png). Senza versione nuova: {len(saltati)}")
    for s in saltati:
        print("  invariato:", s)
    return 0


def main(argv: list[str]) -> int:
    comandi = {"info": lambda: comando_info(), "scarica": lambda: comando_scarica(argv[2:]),
               "confronto": lambda: comando_confronto(argv[2] if len(argv) > 2 else "HEAD"),
               "applica": comando_applica}
    if len(argv) < 2 or argv[1] not in comandi:
        print(__doc__)
        return 2
    return comandi[argv[1]]()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
