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

**Bandiere ufficiali dal 12/11/2026**: le immagini originali erano screenshot fatti a mano
(formati, colori e proporzioni diversi, alcune bandiere superate). Sono state tutte sostituite con
le versioni di **Wikimedia Commons**, con lo script `tools/aggiorna_bandiere.py` (vedi il
paragrafo 8). Nomi dei file, cartelle, livelli e gruppi sono rimasti gli stessi; le 223 immagini
`.gif`/`.jpg` sono diventate `.png` con lo stesso nome.

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

Tutti i 1207 file sono **PNG** (958 con estensione `.png`, 249 con `.PNG`: le maiuscole dei nomi
originali sono rimaste), resi dal server di Wikimedia a partire dai disegni vettoriali ufficiali.

* **Altezza uguale per tutti: 600 pixel**; la larghezza segue le **proporzioni ufficiali**, da
  492 px (Nepal, 0,82) a 1526 px (Qatar, 28:11 = 2,54), passando per 1:1 di Svizzera e Vaticano,
  5:4 di Monaco, 3:2 dell'Indonesia, 2:1 del Regno Unito. Prima Monaco e Indonesia avevano le
  stesse proporzioni (3:2) e in Nerd erano di fatto due immagini identiche.
* 553 immagini RGB e 654 RGBA (il Nepal, che non è rettangolare, ha lo sfondo trasparente).
* Il gioco mostra **sempre** le bandiere con le proporzioni originali, centrate in un riquadro
  fisso con un bordo grigio sottile. Il formato viene comunque riconosciuto dal contenuto del
  file, non dall'estensione: si possono aggiungere anche JPG, GIF, BMP, WEBP o SVG.

## 3. Convenzione dei nomi dei file

Il nome del file (senza estensione) è il nome dello stato. Non ci sono codici ISO né underscore.

* Quasi sempre **inglese minuscolo con spazi**: `united arab emirates.png`, `south korea.PNG`.
* Alcuni nomi **in italiano**: `cile`, `etiopia`, `libia`, `antigua e barbuda`, `capo verde`,
  `papua nuova guinea`, `antille olandesi`, `martinica`, `polinesia`, `sao tomè e principe`.
* Alcuni **errori di ortografia**: `cambodgia`, `philippinas`, `swatziland`, `new zeland`,
  `hawai`, `catalunia`, `antartica`, `aaland island`, `island of man`.
* Stati USA e soggetti federali russi in **inglese con l'iniziale maiuscola**:
  `New York.png`, `Kabardino-Balkaria.PNG`, `Sakha Yakutia.png`.
* Casi particolari: `Birmania - Burma - Myanmar.png` (tre nomi), `sao tomè e principe.png`
  (lettera accentata).

**Identificativo usato dal gioco**: nome del file in minuscolo, senza estensione, con gli spazi
normalizzati (es. `united arab emirates`). Il **nome visualizzato in italiano** sta in
`dati/nomi.json` (333 voci, con codice ISO quando esiste e tipo: stato, territorio, stato USA,
soggetto federale russo, regione, nazione costitutiva…).

Alias definiti in `dati/nomi.json`:

| File | Diventa | Motivo |
|---|---|---|
| `jamaica (1).PNG` | `jamaica` | copia identica (file eliminato, l'alias resta nel caso ricompaia) |
| `south georgia.png` (nerd) | `south georgia and south sandwich islands` | stessa bandiera con nome diverso |
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
| `nerd/2/south georgia.png`, `nerd/12/south georgia.png` | stessa bandiera di `south georgia and south sandwich islands.png` | alias in `nomi.json` |
| `Georgia.png` (stato USA) e `georgia.PNG` (stato) | stesso nome, cambia solo la maiuscola | alias esatto in `nomi.json` |
| `difficult/0` e `difficult/12` | gruppi con le stesse 11 bandiere | nessun problema (unione dei gruppi) |

Risolte con le bandiere di Commons: tre file JPEG con estensione `.png` (Guinea Equatoriale), due
immagini diverse del Niger (una con bande trasparenti), il Nepal disegnato su una tela bianca
(ora ha lo sfondo trasparente e la sua forma vera).

Non ci sono file non-immagine né file illeggibili dentro `flags/`. Se un file vuoto o
danneggiato ricomparisse, il gioco lo sostituirebbe con la stessa bandiera presa da un'altra
cartella (lo verifica il test `test_file_danneggiato_sostituito_da_altra_cartella`).

Il ritaglio automatico per colore **non** viene fatto su tutte le bandiere: molte hanno un bordo
uniforme che fa parte del disegno (Giappone, Russia, Polonia, gli stati USA con lo stemma al
centro…). Per questo è attivo solo dove indicato in `nomi.json` (`"ritaglia_sfondo": true`,
oggi non serve a nessuna bandiera); quello dei bordi trasparenti invece è sempre sicuro.

Il programma ripete questi controlli a ogni avvio: nella schermata **Impostazioni** compare il
numero di avvisi e, passando il mouse, l'elenco dei file problematici.

## 7. File aggiuntivi in `dati/`

| File | Contenuto |
|---|---|
| `livelli.json` | livelli in ordine, cartella di ciascuno, strategia dei distrattori (`area` o `gruppo`), punti per risposta giusta |
| `nomi.json` | nome italiano, codice ISO e tipo di ogni bandiera; alias; `ritaglia_sfondo` (facoltativo) |
| `continenti.json` | elenco dei continenti, corrispondenza con le sottocartelle di `theworld`, mappa bandiera → continente |

## 8. Fonti delle immagini

Ogni bandiera viene da **Wikimedia Commons**. La corrispondenza bandiera → file di Commons, con
licenza e pagina di ciascun file, sta in `tools/fonti_bandiere.json`; lo script
`tools/aggiorna_bandiere.py` (comandi `info`, `scarica`, `confronto`, `applica`) la usa per
riscaricare tutto, per esempio quando una bandiera cambia. Licenze: 319 pubblico dominio, 7 CC0,
5 CC BY-SA (Antartide, Paesi Baschi, Čukotka, Chakassia, Sardegna: chi le ridistribuisce deve
citare gli autori indicati nella pagina di Commons), Mississippi «copyrighted free use», Oman OGL.

**Casi senza una bandiera ufficiale unica** (scelta spiegata nel campo `nota` del JSON):

| Bandiera | Scelta |
|---|---|
| Afghanistan | tricolore 2013–2021, ancora riconosciuto dall'ONU; dal 2021 i talebani usano una bandiera bianca con la shahada |
| Antartide | nessuna bandiera ufficiale: si usa quella del Trattato Antartico |
| Irlanda del Nord | nessuna bandiera ufficiale dal 1972 (vale l'Union Jack): si usa la Ulster Banner |
| Isole Cocos | la bandiera ufficiale è quella australiana (sarebbe identica all'Australia): si usa quella locale |
| Nuova Caledonia | due bandiere ufficiali usate insieme: si usa solo quella kanak, come nell'originale |
| Tibet | bandiera del governo in esilio |
| Sahara Occidentale | bandiera della Repubblica Sahrawi; territorio conteso |
| Antille Olandesi | territorio sciolto nel 2010: bandiera storica 1986–2010 |
| Bolivia, Costa Rica, Perù | versione di stato con lo stemma, come negli screenshot originali |

**Bandiere cambiate rispetto agli screenshot**: Mississippi (2021), Minnesota e Utah (2024),
Kirghizistan (2023), Mauritania (2017), Siria (2025), Martinica (2023, prima c'era la bandiera
coloniale con i serpenti), Tomsk (bianca con lo stemma, senza la fascia verde); Novosibirsk e Perm'
ora hanno la bandiera della **regione** (prima c'era quella della città).
