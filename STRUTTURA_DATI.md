# Struttura dei dati delle bandiere

Risultato dell'esplorazione della cartella del progetto (fase 0), fatta prima di
scrivere il codice. Il gioco non rinomina, sposta o modifica mai i file delle bandiere:
tutte le informazioni aggiuntive stanno nei file JSON della cartella `dati/` (un test
automatico, `test_la_scansione_non_modifica_i_file`, controlla che la scansione non tocchi i file).

**Pulizia del 12/11/2026** (fatta a mano, non dal gioco): eliminata la copia
`intermediate/jamaica (1).PNG`; i due file pieni di zeri `difficult/10/canada.png` e
`difficult/5/marshall islands.gif` sostituiti con le copie buone di `easy/` e `intermediate/`;
eliminati dalla radice i file del vecchio programma C# (`GAME.exe`, `gui.png`, `c1.PNG`,
`c2.png`, `c3.PNG`, `italy.png`, `New Text Document.txt`). I numeri qui sotto sono aggiornati.

## 1. Cartelle e sottocartelle

```
THEBESTFLAGGAME/
├── flags/                       radice delle bandiere
│   ├── easy/                    187 file, nessuna sottocartella        → livello Facile
│   ├── intermediate/            243 file, nessuna sottocartella        → livello Intermedio
│   ├── difficult/0 … 26/        27 sottocartelle, 329 file in tutto    → livello Difficile
│   ├── nerd/0 … 34/             35 sottocartelle, 220 file in tutto    → livello Nerd
│   └── theworld/                bandiere divise per continente (228 file)
│       ├── africa/        55
│       ├── asia/          47
│       ├── europe/        57
│       ├── northamerica/  34
│       ├── oceania/       21
│       └── southamerica/  14
```

Le sottocartelle di `difficult` e di `nerd` hanno nomi numerici (`0`, `1`, … `26` / `34`)
e sono **gruppi di similarità**: ogni gruppo contiene bandiere che si somigliano.
Anche `difficult` è divisa in gruppi, non solo `nerd`: il gioco li usa in entrambi i livelli
(vedi sotto). `theworld` non è un livello: il vecchio programma la usava per giocare per
continente; ora serve a ricavare il continente di ogni bandiera.

## 2. Formati e dimensioni delle immagini

| Estensione | File | Contenuto reale |
|---|---|---|
| `.png` / `.PNG` (maiuscole e minuscole mescolate) | 735 + 249 | 981 PNG, 3 JPEG |
| `.gif` | 195 | 195 GIF |
| `.jpg` | 28 | 28 JPEG |
| `.svg` | 0 | — (il gioco li supporterebbe comunque, tramite QtSvg) |

* Dimensioni molto varie: da 204×102 a 2560×1707 pixel. Le più comuni sono 275×183 (153 file),
  432×216 (76), 318×159 (60), 2000×1333 (47), 324×216 (36), 2560×1707 (34), 1600×800 (29).
  Mediana: circa 432×240.
* Rapporto larghezza/altezza da 0,82 (Nepal, dopo aver tolto lo sfondo, vedi sotto) a 2,03
  (Isola di Natale), passando per 1,00 di Svizzera e Vaticano. Il gioco mostra **sempre** le
  bandiere con le proporzioni originali, centrate in un riquadro fisso con un bordo grigio sottile.
* Modalità colore: 536 a tavolozza, 431 RGBA (con trasparenza), 239 RGB.
* Il formato viene riconosciuto dal contenuto del file, non dall'estensione.

## 3. Convenzione dei nomi dei file

Il nome del file (senza estensione) è il nome dello stato. Non ci sono codici ISO né underscore.

* Quasi sempre **inglese minuscolo con spazi**: `united arab emirates.png`, `south korea.PNG`.
* Alcuni nomi **in italiano**: `cile`, `etiopia`, `libia`, `antigua e barbuda`, `capo verde`,
  `papua nuova guinea`, `antille olandesi`, `martinica`, `polinesia`, `sao tomè e principe`.
* Alcuni **errori di ortografia**: `cambodgia`, `philippinas`, `swatziland`, `new zeland`,
  `hawai`, `catalunia`, `antartica`, `aaland island`, `island of man`.
* Stati USA e soggetti federali russi in **inglese con l'iniziale maiuscola**:
  `New York.png`, `Kabardino-Balkaria.PNG`, `Sakha Yakutia.gif`.
* Casi particolari: `Birmania - Burma - Myanmar.png` (tre nomi), `sao tomè e principe.gif`
  (lettera accentata).

**Identificativo usato dal gioco**: nome del file in minuscolo, senza estensione, con gli spazi
normalizzati (es. `united arab emirates`). Il **nome visualizzato in italiano** sta in
`dati/nomi.json` (333 voci, con codice ISO quando esiste e tipo: stato, territorio, stato USA,
soggetto federale russo, regione, nazione costitutiva…).

Alias definiti in `dati/nomi.json`:

| File | Diventa | Motivo |
|---|---|---|
| `jamaica (1).PNG` | `jamaica` | copia identica (file eliminato, l'alias resta nel caso ricompaia) |
| `south georgia.gif` (nerd) | `south georgia and south sandwich islands` | stessa immagine con nome diverso |
| `Georgia.png` (con la **G maiuscola**) | `georgia (usa)` → «Georgia (USA)» | è lo stato USA; `georgia.PNG` minuscolo è lo stato del Caucaso |

## 4. Informazione sul continente

È **già presente** nella cartella `flags/theworld/<continente>` per 228 bandiere.
Il file `dati/continenti.json` contiene comunque la mappa completa bandiera → continente
(codici `europa`, `asia`, `africa`, `america_nord`, `america_sud`, `oceania`), ottenuta da
`theworld` più una tabella compilata a mano per le 105 bandiere che lì mancano. Se in futuro si
aggiunge una bandiera non presente in `continenti.json`, il gioco usa la cartella di `theworld`
in cui si trova.

**Correzioni rispetto a `theworld`** (i file non sono stati spostati, la correzione è nel JSON):

| Bandiera | In `theworld` | In `continenti.json` |
|---|---|---|
| Afghanistan | europe | Asia |
| Groenlandia | europe | America del Nord |
| Guam | asia | Oceania |

Scelte convenzionali mantenute: Armenia, Azerbaigian, Georgia, Cipro, Turchia e Russia in Europa;
Kazakistan in Asia; Isola di Natale e Isole Cocos in Oceania; «America del Nord» comprende
America centrale e Caraibi (nel vecchio programma: «Central and North America»).

**Bandiere aggiunte a mano** (non presenti in `theworld`):

* 50 stati USA → America del Nord (anche le Hawaii, per coerenza politica);
* 34 soggetti federali russi → Europa o Asia secondo la posizione rispetto agli Urali
  (es. Tatarstan, Cecenia, Carelia in Europa; Jacuzia, Kamčatka, Novosibirsk in Asia);
* territori e regioni: Isole Åland, Fær Øer, Guernsey, Jersey, Isola di Man, Paesi Baschi,
  Catalogna, Corsica, Sardegna, Transnistria → Europa; Sant'Elena, Ascensione, Tristan da Cunha,
  Somaliland → Africa; Falkland → America del Sud; Sint Maarten → America del Nord;
  Nuova Caledonia, Niue, Norfolk, Tokelau → Oceania.

**Bandiere senza continente** (escluse dal filtro per area, giocabili in «Tutto il mondo»):

* `antartica` (Antartide) — non appartiene a nessuno dei sei continenti del gioco.

## 5. Quante bandiere per livello e per area

Bandiere **diverse** (i duplicati contano una volta):

| Livello | Tutto il mondo | Europa | Asia | Africa | Am. Nord | Am. Sud | Oceania |
|---|---|---|---|---|---|---|---|
| Facile (`easy`) | 187 | 51 | 44 | 52 | 20 | 12 | **8** |
| Intermedio (`intermediate`) | 243 | 60 | 47 | 58 | 36 | 15 | 26 |
| Difficile (`difficult`) | 309 | 68 | 64 | 55 | 85 | 14 | 22 |
| Nerd (`nerd`) | 158 | 39 | 32 | 24 | 41 | **3** | 19 |

In tutto: **333 bandiere diverse**. Le combinazioni con meno di 10 bandiere sono
Facile + Oceania (8) e Nerd + America del Sud (3): il menu mostra l'avviso
«Solo N bandiere disponibili: la partita avrà N domande». Nessuna combinazione è
disattivata, perché le 4 opzioni si completano sempre con bandiere di altri livelli.

Relazioni tra livelli: tutte le bandiere di Facile sono anche in Intermedio;
Difficile aggiunge 84 bandiere non presenti in Intermedio (stati USA, regioni russe, …);
Nerd ha 20 bandiere che non sono in Difficile (dipendenze britanniche, regioni europee,
Somaliland, Transnistria…).

**Gruppi di similarità**

| Livello | Gruppi | Bandiere per gruppo | Bandiere in più gruppi |
|---|---|---|---|
| Difficile | 27 (`0`–`26`) | da 4 a 53 | 20 |
| Nerd | 35 (`0`–`34`) | da 4 a 20 | 51 |

Tutti i gruppi hanno almeno 4 bandiere, quindi in Nerd le 4 opzioni vengono **sempre** dallo
stesso gruppo (in «Tutto il mondo»). Esempi: Nerd `18` = Andorra, Ciad, Moldavia, Romania;
Nerd `22` = Indonesia, Monaco, Polonia, Singapore; Difficile `25` = 34 soggetti federali russi;
Difficile `26` = 50 stati USA.

## 6. Duplicati e anomalie

**Duplicati voluti** (stessa bandiera in più cartelle): sono la normalità, perché ogni livello ha
la sua copia. Il gioco li riconosce tramite l'identificativo e non li ripete mai nella stessa
domanda né come risposta giusta nella stessa partita.

**Duplicati e anomalie da segnalare** (gestiti dal programma):

| File | Problema | Come lo gestisce il gioco |
|---|---|---|
| `intermediate/equatorial guinea.png`, `difficult/15/…`, `theworld/africa/…` | estensione `.png` ma contenuto JPEG | letto comunque (formato riconosciuto dal contenuto) |
| `nerd/2/south georgia.gif`, `nerd/12/south georgia.gif` | stessa immagine di `south georgia and south sandwich islands.gif` | alias in `nomi.json` |
| `Georgia.png` (stato USA) e `georgia.PNG` (stato) | stesso nome, cambia solo la maiuscola | alias esatto in `nomi.json` |
| `difficult/0` e `difficult/12` | gruppi con le stesse 11 bandiere | nessun problema (unione dei gruppi) |
| `niger.png` | due immagini diverse: 600×600 con bande **trasparenti** sopra e sotto (easy, intermediate, theworld) e 600×357 (difficult, nerd) | ogni livello usa la sua; i bordi trasparenti vengono tolti automaticamente al caricamento |
| `nepal.gif` (easy, intermediate, difficult/17) | bandiera disegnata su una **tela bianca** 2400×1524: la bandiera vera occupa solo la parte sinistra, quindi sembrerebbe un rettangolo | `"ritaglia_sfondo": true` in `nomi.json`: il gioco toglie lo sfondo in memoria e mostra la vera forma verticale |

Non ci sono file non-immagine né file illeggibili dentro `flags/`. Se un file vuoto o
danneggiato ricomparisse, il gioco lo sostituirebbe con la stessa bandiera presa da un'altra
cartella (lo verifica il test `test_file_danneggiato_sostituito_da_altra_cartella`).

Il ritaglio automatico per colore **non** viene fatto su tutte le bandiere: molte hanno un bordo
uniforme che fa parte del disegno (Giappone, Russia, Polonia, gli stati USA con lo stemma al
centro…). Per questo è attivo solo dove indicato in `nomi.json`; quello dei bordi trasparenti
invece è sempre sicuro.

Il programma ripete questi controlli a ogni avvio: nella schermata **Impostazioni** compare il
numero di avvisi e, passando il mouse, l'elenco dei file problematici.

## 7. File aggiuntivi in `dati/`

| File | Contenuto |
|---|---|
| `livelli.json` | livelli in ordine, cartella di ciascuno, strategia dei distrattori (`area` o `gruppo`) |
| `nomi.json` | nome italiano, codice ISO e tipo di ogni bandiera; alias; `ritaglia_sfondo` per il Nepal |
| `continenti.json` | elenco dei continenti, corrispondenza con le sottocartelle di `theworld`, mappa bandiera → continente |
