"""Crea lo zip da condividere: dist/FlagGame-<versione>.zip.

Dentro c'è la cartella ``FlagGame`` pronta da usare: l'eseguibile creato da
build.bat, la cartella ``flags`` accanto a FlagGame.exe (dove il gioco la cerca
per prima) e un LEGGIMI.txt. Chi lo riceve lo estrae e fa doppio clic su
FlagGame.exe: non serve installare niente. I dati dell'utente (classifica,
impostazioni) stanno in %APPDATA% e non finiscono mai nello zip.

Uso (di solito lo lancia ``build.bat --zip``, dopo aver creato l'eseguibile):

    python tools/crea_zip.py                 crea lo zip e lo verifica
    python tools/crea_zip.py --senza-verifica

La verifica estrae lo zip in una cartella temporanea fuori dal progetto e
avvia ``FlagGame.exe --verifica``: così si controlla che il gioco trovi le
bandiere contenute nello zip e non quelle del progetto.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))

from flaggame import NOME_APP, VERSIONE  # noqa: E402

CARTELLA_EXE = RADICE / "dist" / "FlagGame"
CARTELLA_BANDIERE = RADICE / "flags"
DA_ESCLUDERE = {"thumbs.db", "desktop.ini", ".ds_store"}
GIA_COMPRESSI = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip", ".ico"}

LEGGIMI = f"""{NOME_APP} {VERSIONE}
{'=' * (len(NOME_APP) + len(VERSIONE) + 1)}

Gioco a quiz sulle bandiere del mondo: Guess the Flag e Guess the Country,
quattro livelli (Facile, Intermedio, Difficile, Nerd), classifica e statistiche.

COME SI AVVIA
1. Estrai tutto lo zip (tasto destro > "Estrai tutto..."): il gioco non parte
   dall'interno dello zip.
2. Apri la cartella FlagGame e fai doppio clic su FlagGame.exe.
   Non serve installare niente. Serve Windows 10 o 11 a 64 bit.

"WINDOWS HA PROTETTO IL PC"
Il programma non e' firmato digitalmente, quindi al primo avvio Windows puo'
mostrare questo avviso: clicca "Ulteriori informazioni" e poi "Esegui comunque".
Se l'antivirus lo blocca, aggiungi un'eccezione per la cartella FlagGame.

NON SEPARARE I FILE
La cartella "flags" deve restare accanto a FlagGame.exe, insieme a "_internal"
e "dati". Puoi spostare l'intera cartella FlagGame dove vuoi.

DOVE FINISCONO CLASSIFICA E IMPOSTAZIONI
In %APPDATA%\\FlagGame (pulsante "Apri cartella" nelle Impostazioni del gioco).
Per disinstallare basta cancellare la cartella FlagGame e quella in %APPDATA%.

TASTI RAPIDI
1-4 per rispondere, Invio o Spazio per andare avanti, Esc per abbandonare.

Le immagini delle bandiere vengono da Wikimedia Commons (quasi tutte di pubblico
dominio; licenze e autori nel progetto, file tools/fonti_bandiere.json).
"""


def _aggiungi_cartella(zf: zipfile.ZipFile, cartella: Path, prefisso: str) -> int:
    n = 0
    for f in sorted(cartella.rglob("*")):
        if not f.is_file() or f.name.lower() in DA_ESCLUDERE:
            continue
        nome = f"{prefisso}/{f.relative_to(cartella).as_posix()}"
        compressione = zipfile.ZIP_STORED if f.suffix.lower() in GIA_COMPRESSI else zipfile.ZIP_DEFLATED
        zf.write(f, nome, compress_type=compressione)
        n += 1
    return n


def crea_zip() -> Path:
    if not (CARTELLA_EXE / "FlagGame.exe").is_file():
        raise SystemExit(f"Manca {CARTELLA_EXE / 'FlagGame.exe'}: lancia prima build.bat")
    if not (CARTELLA_BANDIERE / "easy").is_dir():
        raise SystemExit(f"Manca la cartella delle bandiere: {CARTELLA_BANDIERE}")
    if (CARTELLA_EXE / "flags").exists():
        raise SystemExit(f"{CARTELLA_EXE / 'flags'} esiste già: toglila, le bandiere si prendono da {CARTELLA_BANDIERE}")
    destinazione = RADICE / "dist" / f"FlagGame-{VERSIONE}.zip"
    temporaneo = destinazione.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporaneo, "w", compresslevel=9) as zf:
        n = _aggiungi_cartella(zf, CARTELLA_EXE, "FlagGame")
        n += _aggiungi_cartella(zf, CARTELLA_BANDIERE, "FlagGame/flags")
        zf.writestr("FlagGame/LEGGIMI.txt", LEGGIMI.replace("\n", "\r\n").encode("utf-8"),
                    compress_type=zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(temporaneo) as zf:
        rotto = zf.testzip()
        if rotto:
            raise SystemExit(f"Zip danneggiato: {rotto}")
    os.replace(temporaneo, destinazione)
    print(f"Creato {destinazione} ({n + 1} file, {destinazione.stat().st_size / 1e6:.0f} MB)")
    return destinazione


def verifica_zip(percorso: Path) -> bool:
    """Estrae lo zip fuori dal progetto e avvia il gioco in modalità di verifica."""
    with tempfile.TemporaryDirectory(prefix="flaggame-zip-") as cartella:
        with zipfile.ZipFile(percorso) as zf:
            zf.extractall(cartella)
        exe = Path(cartella) / "FlagGame" / "FlagGame.exe"
        esito = subprocess.run([str(exe), "--verifica"], cwd=cartella, timeout=180)
        if esito.returncode == 0:
            print("Verifica riuscita: il gioco estratto dallo zip parte e trova le sue bandiere.")
            return True
        motivo = "bandiere non trovate" if esito.returncode == 2 else f"codice di uscita {esito.returncode}"
        print(f"Verifica NON riuscita ({motivo}).")
        return False


def main(argv: list[str]) -> int:
    percorso = crea_zip()
    if "--senza-verifica" in argv:
        return 0
    return 0 if verifica_zip(percorso) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
