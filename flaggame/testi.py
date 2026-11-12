"""Testi dell'interfaccia nella lingua scelta.

I testi veri stanno in flaggame/lingue/<codice>.py (it.py, en.py), tutti con
gli stessi nomi. Questo modulo espone quelli della lingua corrente: il codice
scrive sempre ``testi.NOME`` (mai ``from testi import NOME``), così dopo
``imposta_lingua`` legge già i testi nuovi. Non dipende da Qt.

Per aggiungere una lingua: crea flaggame/lingue/<codice>.py copiando it.py,
importalo qui sotto e aggiungilo a ``LINGUE`` e ``_MODULI``. I nomi delle
bandiere stanno in dati/nomi.json (``nome`` in italiano, ``nome_<codice>``
per le altre lingue).
"""

from .lingue import en, it

# Nome di ogni lingua scritto nella lingua stessa (per il menu delle impostazioni).
LINGUE = {"it": "Italiano", "en": "English"}
LINGUA_PREDEFINITA = "it"
_MODULI = {"it": it, "en": en}   # import espliciti: PyInstaller li include nell'eseguibile

lingua = LINGUA_PREDEFINITA


def testi_di(codice: str) -> dict:
    """Tutti i testi (nomi in MAIUSCOLO) di una lingua."""
    modulo = _MODULI[codice]
    return {nome: valore for nome, valore in vars(modulo).items() if nome.isupper()}


def imposta_lingua(codice: str) -> str:
    """Cambia la lingua dei testi; un codice sconosciuto diventa quello predefinito."""
    global lingua
    if codice not in _MODULI:
        codice = LINGUA_PREDEFINITA
    globals().update(testi_di(codice))
    lingua = codice
    return codice


def lingua_di_sistema(codice_locale: str) -> str:
    """Lingua da usare al primo avvio, dal codice della lingua di Windows ("it_IT", "en_GB"...):
    italiano per chi ha Windows in italiano, inglese per tutti gli altri."""
    return "it" if codice_locale.lower().startswith("it") else "en"


imposta_lingua(LINGUA_PREDEFINITA)
