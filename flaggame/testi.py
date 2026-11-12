"""Tutti i testi dell'interfaccia, in un unico posto per poterli tradurre.

Per tradurre il gioco basta copiare questo file e cambiare le stringhe a
destra del segno "=". I nomi delle modalità restano in inglese per scelta.
"""

TITOLO_APP = "The Best Flag Game"
SOTTOTITOLO_APP = "Quanto conosci le bandiere del mondo?"

# --- Modalità ----------------------------------------------------------------
MODALITA = {
    "flag": "Guess the Flag",
    "country": "Guess the Country",
}
DESCRIZIONE_MODALITA = {
    "flag": "Guarda la bandiera e scegli il nome giusto tra quattro.",
    "country": "Leggi il nome dello stato e trova la sua bandiera tra quattro.",
}

# --- Livelli -----------------------------------------------------------------
LIVELLI = {
    "facile": "Facile",
    "intermedio": "Intermedio",
    "difficile": "Difficile",
    "nerd": "Nerd",
}
DESCRIZIONE_LIVELLI = {
    "facile": "Gli stati più conosciuti del mondo.",
    "intermedio": "Tutti gli stati, più isole e territori.",
    "difficile": "Bandiere che si somigliano, stati USA e regioni russe.",
    "nerd": "Solo bandiere quasi identiche tra loro. Buona fortuna!",
}

# --- Aree --------------------------------------------------------------------
AREA_MONDO = "Tutto il mondo"
CONTINENTI = {
    "europa": "Europa",
    "asia": "Asia",
    "africa": "Africa",
    "america_nord": "America del Nord",
    "america_sud": "America del Sud",
    "oceania": "Oceania",
}

# --- Home --------------------------------------------------------------------
HOME_SEZIONE_MODALITA = "Modalità"
HOME_SEZIONE_LIVELLO = "Livello"
HOME_SEZIONE_AREA = "Area"
HOME_GIOCA = "Gioca"
HOME_CLASSIFICA = "Classifica"
HOME_IMPOSTAZIONI = "Impostazioni"
HOME_INFO_DISPONIBILI = "{n} bandiere disponibili · {d} domande"
HOME_AVVISO_POCHE = "Solo {n} bandiere disponibili: la partita avrà {n} domande"
HOME_AVVISO_UNA = "Solo 1 bandiera disponibile: la partita avrà 1 domanda"
HOME_NON_GIOCABILE = "Nessuna bandiera disponibile per questa combinazione"
HOME_SUGGERIMENTO_TASTI = "Durante la partita: tasti 1–4 per rispondere, Esc per uscire"
HOME_AREA_NON_DISPONIBILE = "{area} (nessuna bandiera)"

# --- Partita -----------------------------------------------------------------
GIOCO_ABBANDONA = "Abbandona"
GIOCO_DOMANDA = "Domanda {n} / {tot}"
GIOCO_DOMANDA_FLAG = "A chi appartiene questa bandiera?"
GIOCO_DOMANDA_COUNTRY = "Qual è la bandiera di"
GIOCO_GIUSTO = "Esatto!"
GIOCO_SBAGLIATO = "Sbagliato: era {nome}"
GIOCO_AVANTI = "Avanti"
GIOCO_RISULTATI = "Vedi risultati"
GIOCO_SUGGERIMENTO_AVANTI = "Premi Invio o fai clic per continuare"
GIOCO_IN_PAUSA = "Timer in pausa"
GIOCO_CONFERMA_TITOLO = "Abbandonare la partita?"
GIOCO_CONFERMA_TESTO = "La partita in corso andrà persa e non verrà salvata in classifica."
GIOCO_CONFERMA_SI = "Abbandona"
GIOCO_CONFERMA_NO = "Continua a giocare"

# --- Riepilogo ---------------------------------------------------------------
RIEPILOGO_TITOLO = "Partita completata"
RIEPILOGO_GIUSTE = "{g} risposte giuste su {t}"
RIEPILOGO_GIUSTE_UNA = "{g} risposta giusta su {t}"
RIEPILOGO_TEMPO = "Tempo totale"
RIEPILOGO_TEMPO_MEDIO = "Tempo medio"
RIEPILOGO_SECONDI = "{s:.1f} s"
RIEPILOGO_LE_TUE_RISPOSTE = "Le tue risposte"
RIEPILOGO_RISPOSTA_GIUSTA = "Risposta giusta"
RIEPILOGO_TUA_RISPOSTA = "La tua risposta: {nome}"
RIEPILOGO_NOME = "Il tuo nome"
RIEPILOGO_NOME_SEGNAPOSTO = "Scrivi il tuo nome"
RIEPILOGO_SALVA = "Salva in classifica"
RIEPILOGO_SALVATO = "Salvato in classifica"
RIEPILOGO_GIOCA_ANCORA = "Gioca ancora"
RIEPILOGO_MENU = "Menu principale"
RIEPILOGO_GIUDIZI = [
    (100, "Perfetto!"),
    (80, "Ottimo lavoro!"),
    (60, "Bel risultato!"),
    (40, "Puoi fare di meglio"),
    (0, "Non arrenderti!"),
]

# --- Classifica --------------------------------------------------------------
CLASSIFICA_TITOLO = "Classifica"
CLASSIFICA_SOTTOTITOLO = "I 10 migliori risultati per modalità, livello e area"
CLASSIFICA_TUTTE_MODALITA = "Tutte"
CLASSIFICA_TUTTI_LIVELLI = "Tutti i livelli"
CLASSIFICA_TUTTE_AREE = "Tutte le aree"
CLASSIFICA_COLONNE = {
    "pos": "#",
    "nome": "Nome",
    "percentuale": "Risultato",
    "tempo": "Tempo",
    "data": "Data",
    "modalita": "Modalità",
    "livello": "Livello",
    "area": "Area",
}
CLASSIFICA_VUOTA = "Ancora nessun risultato per questa combinazione."
CLASSIFICA_VUOTA_SUGGERIMENTO = "Gioca una partita e salva il tuo punteggio per entrare in classifica."
CLASSIFICA_FORMATO_DATA = "%d/%m/%Y %H:%M"
CLASSIFICA_TUO_RISULTATO = "Il tuo risultato è in posizione {pos}"

# --- Impostazioni ------------------------------------------------------------
IMPOSTAZIONI_TITOLO = "Impostazioni"
IMP_ASPETTO = "Aspetto"
IMP_TEMA = "Tema"
IMP_TEMA_DESCR = "Colori chiari o scuri per tutta l'applicazione."
IMP_TEMA_CHIARO = "Chiaro"
IMP_TEMA_SCURO = "Scuro"
IMP_GIOCO = "Partita"
IMP_SUONI = "Effetti sonori"
IMP_SUONI_DESCR = "Suoni per risposta giusta, sbagliata e fine partita."
IMP_AUTO = "Avanzamento automatico"
IMP_AUTO_DESCR = "Dopo il feedback passa da solo alla domanda successiva. Se disattivato, si prosegue con un clic."
IMP_DATI = "Dati"
IMP_CARTELLA = "Cartella delle bandiere"
IMP_CARTELLA_SCEGLI = "Scegli cartella…"
IMP_CARTELLA_PREDEFINITA = "Usa predefinita"
IMP_CARTELLA_INFO = "{n} bandiere caricate"
IMP_CARTELLA_ANOMALIE = "{n} bandiere caricate · {a} avvisi sui file (passa il mouse per i dettagli)"
IMP_SALVATAGGI = "Classifica e impostazioni"
IMP_APRI_CARTELLA = "Apri cartella"
IMP_STORICO = "Storico delle domande"
IMP_AZZERA_STORICO = "Azzera storico"
IMP_AZZERA_STORICO_DESCR = "Il gioco ricorda le ultime bandiere uscite per non ripeterle: qui puoi dimenticarle."
IMP_STORICO_AZZERATO = "Storico azzerato"
IMP_SVUOTA_CLASSIFICA = "Cancella classifica"
IMP_SVUOTA_TITOLO = "Cancellare tutta la classifica?"
IMP_SVUOTA_TESTO = "Tutti i risultati salvati verranno eliminati. L'operazione non si può annullare."
IMP_SVUOTA_SI = "Cancella"
IMP_ANNULLA = "Annulla"
IMP_INFO_VERSIONE = "{app} · versione {v}"

# --- Cartella non trovata ----------------------------------------------------
CARTELLA_TITOLO = "Cartella delle bandiere non trovata"
CARTELLA_TESTO = ("Il gioco cerca una cartella che contenga le sottocartelle dei livelli "
                  "({cartelle}). Di solito si chiama «flags» e sta accanto al programma.")
CARTELLA_CERCATO_IN = "Cercata in: {percorso}"
CARTELLA_SCEGLI = "Scegli cartella…"
CARTELLA_RIPROVA = "Riprova"
CARTELLA_NON_VALIDA = "La cartella scelta non contiene le sottocartelle dei livelli."
CARTELLA_DIALOGO = "Scegli la cartella delle bandiere"

# --- Generali ----------------------------------------------------------------
INDIETRO = "Indietro"
ERRORE_TITOLO = "Si è verificato un errore"
