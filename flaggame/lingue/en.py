"""User interface texts in English.

Same names as flaggame/lingue/it.py (a test checks that names and
placeholders such as {n} match). The mode names stay in English everywhere.
"""

TITOLO_APP = "The Best Flag Game"
SOTTOTITOLO_APP = "How well do you know the flags of the world?"

# --- Modes -------------------------------------------------------------------
MODALITA = {
    "flag": "Guess the Flag",
    "country": "Guess the Country",
}
DESCRIZIONE_MODALITA = {
    "flag": "Look at the flag and pick the right name out of four.",
    "country": "Read the name of the country and find its flag out of four.",
}

# --- Levels ------------------------------------------------------------------
LIVELLI = {
    "facile": "Easy",
    "intermedio": "Intermediate",
    "difficile": "Hard",
    "nerd": "Nerd",
}
DESCRIZIONE_LIVELLI = {
    "facile": "The best-known countries in the world.",
    "intermedio": "Every country, plus islands and territories.",
    "difficile": "Look-alike flags, US states and Russian regions.",
    "nerd": "Only nearly identical flags. Good luck!",
}

# --- Areas -------------------------------------------------------------------
AREA_MONDO = "Whole world"
CONTINENTI = {
    "europa": "Europe",
    "asia": "Asia",
    "africa": "Africa",
    "america_nord": "North America",
    "america_sud": "South America",
    "oceania": "Oceania",
}

# --- Home --------------------------------------------------------------------
HOME_SEZIONE_MODALITA = "Mode"
HOME_SEZIONE_LIVELLO = "Level"
HOME_SEZIONE_AREA = "Area"
HOME_GIOCA = "Play"
HOME_CLASSIFICA = "Leaderboard"
HOME_IMPOSTAZIONI = "Settings"
HOME_STATISTICHE = "Statistics"
HOME_INFO_DISPONIBILI = "{n} flags available · {d} questions"
HOME_AVVISO_POCHE = "Only {n} flags available: the game will have {n} questions"
HOME_AVVISO_UNA = "Only 1 flag available: the game will have 1 question"
HOME_NON_GIOCABILE = "No flags available for this combination"
HOME_SUGGERIMENTO_TASTI = "During the game: keys 1–4 to answer, Esc to quit"
HOME_AREA_NON_DISPONIBILE = "{area} (no flags)"

# --- Game --------------------------------------------------------------------
GIOCO_ABBANDONA = "Quit"
GIOCO_DOMANDA = "Question {n} / {tot}"
GIOCO_DOMANDA_FLAG = "Whose flag is this?"
GIOCO_DOMANDA_COUNTRY = "Which one is the flag of"
GIOCO_GIUSTO = "Correct!"
GIOCO_SBAGLIATO = "Wrong: it was {nome}"
GIOCO_AVANTI = "Next"
GIOCO_RISULTATI = "See results"
GIOCO_SUGGERIMENTO_AVANTI = "Press Enter or click to continue"
GIOCO_IN_PAUSA = "Timer paused"
GIOCO_CONFERMA_TITOLO = "Quit the game?"
GIOCO_CONFERMA_TESTO = "The current game will be lost and won't be saved to the leaderboard."
GIOCO_CONFERMA_SI = "Quit"
GIOCO_CONFERMA_NO = "Keep playing"

# --- Summary -----------------------------------------------------------------
RIEPILOGO_TITOLO = "Game complete"
RIEPILOGO_GIUSTE = "{g} correct answers out of {t}"
RIEPILOGO_GIUSTE_UNA = "{g} correct answer out of {t}"
RIEPILOGO_TEMPO = "Total time"
RIEPILOGO_TEMPO_MEDIO = "Average time"
RIEPILOGO_PUNTI = "Points"
RIEPILOGO_SECONDI = "{s:.1f} s"
RIEPILOGO_LE_TUE_RISPOSTE = "Your answers"
RIEPILOGO_RISPOSTA_GIUSTA = "Correct answer"
RIEPILOGO_TUA_RISPOSTA = "Your answer: {nome}"
RIEPILOGO_NOME = "Your name"
RIEPILOGO_NOME_SEGNAPOSTO = "Type your name"
RIEPILOGO_SALVA = "Save to leaderboard"
RIEPILOGO_SALVATO = "Saved to leaderboard"
RIEPILOGO_GIOCA_ANCORA = "Play again"
RIEPILOGO_MENU = "Main menu"
RIEPILOGO_GIUDIZI = [
    (100, "Perfect!"),
    (80, "Great job!"),
    (60, "Nice result!"),
    (40, "You can do better"),
    (0, "Don't give up!"),
]

# --- Leaderboard -------------------------------------------------------------
CLASSIFICA_TITOLO = "Leaderboard"
CLASSIFICA_SOTTOTITOLO = "Top 10 scores by mode, level and area"
CLASSIFICA_TUTTE_MODALITA = "All"
CLASSIFICA_TUTTI_LIVELLI = "All levels"
CLASSIFICA_TUTTE_AREE = "All areas"
CLASSIFICA_COLONNE = {
    "pos": "#",
    "nome": "Name",
    "punti": "Points",
    "percentuale": "Result",
    "tempo": "Time",
    "data": "Date",
    "modalita": "Mode",
    "livello": "Level",
    "area": "Area",
}
CLASSIFICA_VUOTA = "No results for this combination yet."
CLASSIFICA_VUOTA_SUGGERIMENTO = "Play a game and save your score to get on the leaderboard."
CLASSIFICA_FORMATO_DATA = "%d %b %Y %H:%M"
CLASSIFICA_TUO_RISULTATO = "Your result is in position {pos}"
CLASSIFICA_SPIEGAZIONE_PUNTI = ("Points for each correct answer: {livelli}, "
                                "plus up to 10% for answering quickly.")
CLASSIFICA_PUNTI_LIVELLO = "{punti} in {livello}"

# --- Statistics --------------------------------------------------------------
STAT_TITOLO = "Statistics"
STAT_SOTTOTITOLO = "Your progress, game after game"
STAT_GIOCATORE = "Player"
STAT_PARTITE = "Games played"
STAT_PARTITE_SOTTO = "saved to the leaderboard"
STAT_GIUSTE = "Correct answers"
STAT_GIUSTE_SOTTO = "{g} out of {t}"
STAT_TEMPO = "Average time"
STAT_TEMPO_SOTTO = "per answer"
STAT_TEMPO_VALORE = "{s:.1f} s"
STAT_MIGLIORE = "Best score"
STAT_MIGLIORE_SOTTO = "{livello} · {modalita}"
STAT_PER_LIVELLO = "By level"
STAT_PER_CONTINENTE = "By continent"
STAT_ANDAMENTO = "Progress"
STAT_ANDAMENTO_SOTTO = "Correct answers in the last {n} games"
STAT_ANDAMENTO_UNA = "Correct answers in your first game: play again to see your progress"
STAT_DA_RIPASSARE = "Flags to review"
STAT_SBAGLIATA = "Missed {n} times out of {v}"
STAT_SBAGLIATA_UNA = "Missed once out of {v}"
STAT_CONFUSA = "Mistaken for: {nome}"
STAT_NON_GIOCATO = "not played"
STAT_QUOTA_TOOLTIP = "{nome}: {g} correct answers out of {t} ({p}%)"
STAT_QUOTA_TOOLTIP_VUOTA = "{nome}: no games"
STAT_PUNTO_TOOLTIP = "{data}\n{modalita} · {livello} · {area}\n{g} correct out of {t} ({p}%) · {punti} points"
STAT_SENZA_DETTAGLIO = ("Will show up from your next games: individual answers "
                        "are saved from this version on.")
STAT_NESSUN_ERRORE = "No mistakes so far: well done!"
STAT_VUOTA = "No statistics yet."
STAT_VUOTA_SUGGERIMENTO = "Play a game and save it with your name: your progress will show up here."

# --- Settings ----------------------------------------------------------------
IMPOSTAZIONI_TITOLO = "Settings"
IMP_ASPETTO = "Appearance"
IMP_TEMA = "Theme"
IMP_TEMA_DESCR = "Light or dark colors for the whole app."
IMP_TEMA_CHIARO = "Light"
IMP_TEMA_SCURO = "Dark"
IMP_GIOCO = "Game"
IMP_SUONI = "Sound effects"
IMP_SUONI_DESCR = "Sounds for right and wrong answers and at the end of the game."
IMP_AUTO = "Auto-advance"
IMP_AUTO_DESCR = "After the feedback, moves on to the next question by itself. When off, continue with a click."
IMP_DATI = "Data"
IMP_CARTELLA = "Flags folder"
IMP_CARTELLA_SCEGLI = "Choose folder…"
IMP_CARTELLA_PREDEFINITA = "Use default"
IMP_CARTELLA_INFO = "{n} flags loaded"
IMP_CARTELLA_ANOMALIE = "{n} flags loaded · {a} file warnings (hover for details)"
IMP_SALVATAGGI = "Leaderboard and settings"
IMP_APRI_CARTELLA = "Open folder"
IMP_STORICO = "Question history"
IMP_AZZERA_STORICO = "Reset history"
IMP_AZZERA_STORICO_DESCR = ("The game remembers the latest flags it showed so it doesn't repeat them: "
                            "you can make it forget them here.")
IMP_STORICO_AZZERATO = "History reset"
IMP_SVUOTA_CLASSIFICA = "Clear leaderboard and statistics"
IMP_SVUOTA_TITOLO = "Clear leaderboard and statistics?"
IMP_SVUOTA_TESTO = ("All saved results, and the statistics with them, will be deleted. "
                    "This can't be undone.")
IMP_SVUOTA_SI = "Delete"
IMP_ANNULLA = "Cancel"
IMP_INFO_VERSIONE = "{app} · version {v}"
IMP_LINGUA = "Language"
IMP_LINGUA_DESCR = "Language of the interface and of the flag names."

# --- Folder not found --------------------------------------------------------
CARTELLA_TITOLO = "Flags folder not found"
CARTELLA_TESTO = ("The game looks for a folder that contains the level subfolders "
                  "({cartelle}). It's usually called “flags” and sits next to the program.")
CARTELLA_CERCATO_IN = "Looked in: {percorso}"
CARTELLA_SCEGLI = "Choose folder…"
CARTELLA_RIPROVA = "Try again"
CARTELLA_NON_VALIDA = "The selected folder doesn't contain the level subfolders."
CARTELLA_DIALOGO = "Choose the flags folder"

# --- General -----------------------------------------------------------------
INDIETRO = "Back"
ERRORE_TITOLO = "An error occurred"
NOME_ANONIMO = "Anonymous"
