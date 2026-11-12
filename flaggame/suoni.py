"""Effetti sonori generati al volo con il modulo ``wave`` (nessun file audio esterno).

I file .wav vengono creati la prima volta nella cartella dei dati utente e
riprodotti con ``winsound`` (solo Windows, nessuna dipendenza). Su altri
sistemi i suoni sono semplicemente disattivati.
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

FREQUENZA = 44100

# nome -> lista di (frequenza Hz, durata s, volume 0-1); frequenza 0 = pausa
MELODIE = {
    "giusto": [(659.25, 0.09, 0.5), (987.77, 0.16, 0.5)],
    "sbagliato": [(220.0, 0.12, 0.45), (174.61, 0.22, 0.45)],
    "fine": [(523.25, 0.11, 0.45), (659.25, 0.11, 0.45), (783.99, 0.11, 0.45), (1046.5, 0.30, 0.45)],
}


def campioni_nota(frequenza: float, durata: float, volume: float, morbida: bool) -> list[int]:
    """Campioni a 16 bit di una nota con attacco e rilascio dolci."""
    n = int(FREQUENZA * durata)
    attacco = int(FREQUENZA * 0.008)
    rilascio = int(FREQUENZA * min(0.08, durata * 0.6))
    valori = []
    for i in range(n):
        if frequenza <= 0:
            valori.append(0)
            continue
        t = i / FREQUENZA
        if morbida:
            onda = math.sin(2 * math.pi * frequenza * t) + 0.25 * math.sin(4 * math.pi * frequenza * t)
            onda /= 1.25
        else:  # suono più "ruvido" per l'errore (onda triangolare)
            fase = (frequenza * t) % 1.0
            onda = 4 * abs(fase - 0.5) - 1
        inviluppo = 1.0
        if i < attacco:
            inviluppo = i / attacco
        elif i > n - rilascio:
            inviluppo = max(0.0, (n - i) / rilascio)
        valori.append(int(32767 * volume * inviluppo * onda))
    return valori


def genera_wav(percorso: Path, nome: str) -> None:
    """Scrive il file .wav dell'effetto ``nome``."""
    campioni: list[int] = []
    for frequenza, durata, volume in MELODIE[nome]:
        campioni += campioni_nota(frequenza, durata, volume, morbida=(nome != "sbagliato"))
    percorso.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(percorso), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(FREQUENZA)
        f.writeframes(struct.pack(f"<{len(campioni)}h", *campioni))


class Suoni:
    """Riproduce gli effetti sonori, se abilitati."""

    def __init__(self, cartella: Path, abilitati: bool = True):
        self.cartella = Path(cartella)
        self.abilitati = abilitati
        try:
            import winsound  # noqa: F401  (solo Windows)
            self._winsound = winsound
        except ImportError:
            self._winsound = None

    def _file(self, nome: str) -> Path | None:
        percorso = self.cartella / f"{nome}.wav"
        if not percorso.exists():
            try:
                genera_wav(percorso, nome)
            except OSError:
                return None
        return percorso

    def suona(self, nome: str) -> None:
        """Riproduce l'effetto in modo asincrono (non blocca l'interfaccia)."""
        if not self.abilitati or self._winsound is None or nome not in MELODIE:
            return
        percorso = self._file(nome)
        if percorso is None:
            return
        ws = self._winsound
        try:
            ws.PlaySound(str(percorso), ws.SND_FILENAME | ws.SND_ASYNC | ws.SND_NODEFAULT)
        except RuntimeError:
            pass
