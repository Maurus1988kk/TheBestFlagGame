"""Finestra principale: collega schermate, dati, classifica, storico e suoni."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QMainWindow, QVBoxLayout, QWidget

from .. import NOME_APP, percorsi, testi
from ..classifica import Classifica, Risultato
from ..dati import (AREA_MONDO, Catalogo, ErroreDati, carica_catalogo, carica_configurazione,
                    riconosci_radice, trova_radice)
from ..generatore import Generatore
from ..partita import Partita
from ..persistenza import Impostazioni, Storico
from ..suoni import Suoni
from .componenti import StackDissolvenza, chiedi_conferma
from .grafica import aggiorna_icone, icona_app
from .immagini import CacheImmagini
from .schermata_cartella import SchermataCartella
from .schermata_classifica import SchermataClassifica
from .schermata_gioco import SchermataGioco
from .schermata_home import SchermataHome
from .schermata_impostazioni import SchermataImpostazioni
from .schermata_riepilogo import SchermataRiepilogo
from .tema import applica_tema

DURATA_DISSOLVENZA = 260


class FinestraPrincipale(QMainWindow):
    """Contiene lo stack delle schermate e lo stato dell'applicazione."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(NOME_APP)
        self.setWindowIcon(icona_app())
        self.setMinimumSize(1000, 700)

        cartella = percorsi.cartella_utente()
        self.cartella_utente = cartella
        self.impostazioni = Impostazioni.carica(cartella / "impostazioni.json")
        self.classifica = Classifica(cartella / "classifica.json")
        self.storico = Storico(cartella / "storico.json")
        self.suoni = Suoni(cartella / "suoni", self.impostazioni.suoni)
        self.cache = CacheImmagini()
        self.config = carica_configurazione(percorsi.cartella_dati_app())
        self.catalogo: Catalogo | None = None
        self.generatore: Generatore | None = None
        self.partita: Partita | None = None
        self._ritorno_classifica: QWidget | None = None

        applica_tema(self.impostazioni.tema, cartella / "cache")

        # schermate
        radice = QWidget()
        radice.setObjectName("radice")
        lay = QVBoxLayout(radice)
        lay.setContentsMargins(0, 0, 0, 0)
        self.stack = StackDissolvenza(durata=DURATA_DISSOLVENZA)
        lay.addWidget(self.stack)
        self.setCentralWidget(radice)

        self.home = SchermataHome()
        self.gioco = SchermataGioco(self.cache, lambda: self.impostazioni.avanzamento_automatico)
        self.riepilogo = SchermataRiepilogo(self.cache)
        self.schermata_classifica = SchermataClassifica(self.classifica)
        self.schermata_impostazioni = SchermataImpostazioni()
        self.schermata_cartella = SchermataCartella()
        for s in (self.home, self.gioco, self.riepilogo, self.schermata_classifica,
                  self.schermata_impostazioni, self.schermata_cartella):
            self.stack.addWidget(s)
        self._collega()

        if self.impostazioni.geometria:
            self.restoreGeometry(QByteArray.fromHex(self.impostazioni.geometria.encode()))
        else:
            self.resize(1240, 820)
        self.carica_bandiere(anima=False)

    # ------------------------------------------------------------ segnali

    def _collega(self):
        self.home.gioca.connect(self.avvia_partita)
        self.home.apri_classifica.connect(self._classifica_da_home)
        self.home.apri_impostazioni.connect(self.apri_impostazioni)
        self.home.selezione_cambiata.connect(self._ricorda_selezione)

        self.gioco.finita.connect(self._partita_finita)
        self.gioco.abbandonata.connect(self._partita_abbandonata)
        self.gioco.risposta_data.connect(lambda giusta: self.suoni.suona("giusto" if giusta else "sbagliato"))

        self.riepilogo.salva.connect(self._salva_risultato)
        self.riepilogo.gioca_ancora.connect(self._gioca_ancora)
        self.riepilogo.menu.connect(self.vai_home)

        self.schermata_classifica.indietro.connect(
            lambda: self.stack.mostra(self._ritorno_classifica or self.home))

        imp = self.schermata_impostazioni
        imp.indietro.connect(self.vai_home)
        imp.tema_cambiato.connect(self._cambia_tema)
        imp.suoni_cambiati.connect(self._cambia_suoni)
        imp.auto_cambiato.connect(self._cambia_auto)
        imp.scegli_cartella.connect(self.scegli_cartella)
        imp.cartella_predefinita.connect(self._cartella_predefinita)
        imp.apri_cartella_dati.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.cartella_utente))))
        imp.azzera_storico.connect(self._azzera_storico)
        imp.svuota_classifica.connect(self._chiedi_svuota_classifica)

        self.schermata_cartella.scegli.connect(self.scegli_cartella)
        self.schermata_cartella.riprova.connect(lambda: self.carica_bandiere())

    # -------------------------------------------------------------- dati

    def nomi_livelli(self) -> list[tuple[str, str]]:
        return [(c.id, testi.LIVELLI.get(c.id, c.nome)) for c in self.config.livelli]

    def nomi_aree(self) -> list[tuple[str, str]]:
        continenti = self.catalogo.continenti if self.catalogo else self.config.continenti
        return [(AREA_MONDO, testi.AREA_MONDO)] + [(c, testi.CONTINENTI.get(c, c)) for c in continenti]

    def nome_livello(self, id_livello: str) -> str:
        return dict(self.nomi_livelli()).get(id_livello, id_livello)

    def nome_area(self, area: str) -> str:
        return dict(self.nomi_aree()).get(area, area)

    def carica_bandiere(self, anima: bool = True, errore: str = "") -> bool:
        """Cerca la cartella delle bandiere e costruisce il catalogo."""
        candidati = percorsi.candidati_radice_bandiere()
        radice = trova_radice(self.impostazioni.cartella_bandiere or None, candidati, self.config)
        self.catalogo = None
        if radice is not None:
            try:
                catalogo = carica_catalogo(radice, self.config)
                if catalogo.totale_bandiere() > 0:
                    self.catalogo = catalogo
            except (ErroreDati, OSError) as e:
                errore = str(e)
        if self.catalogo is None:
            cercato = self.impostazioni.cartella_bandiere or str(candidati[0])
            self.schermata_cartella.mostra([c.cartella for c in self.config.livelli], cercato, errore)
            self.stack.mostra(self.schermata_cartella, anima)
            return False
        self.generatore = Generatore(self.catalogo, self.storico)
        self.cache.svuota()
        self.cache.da_ritagliare = self.catalogo.percorsi_da_ritagliare()
        imp = self.impostazioni
        self.home.configura(self.nomi_livelli(), self.nomi_aree(), self.generatore.info,
                            imp.ultima_modalita, imp.ultimo_livello, imp.ultima_area)
        self.schermata_classifica.configura(self.nomi_livelli(), self.nomi_aree())
        self.stack.mostra(self.home, anima)
        return True

    def scegli_cartella(self) -> None:
        iniziale = self.impostazioni.cartella_bandiere or str(percorsi.cartella_app())
        scelta = QFileDialog.getExistingDirectory(self, testi.CARTELLA_DIALOGO, iniziale)
        if not scelta:
            return
        radice = riconosci_radice(scelta, self.config)
        if radice is None:
            if self.stack.currentWidget() is self.schermata_cartella:
                self.schermata_cartella.mostra([c.cartella for c in self.config.livelli], scelta,
                                               testi.CARTELLA_NON_VALIDA)
            else:
                chiedi_conferma(self.centralWidget(), testi.CARTELLA_TITOLO, testi.CARTELLA_NON_VALIDA,
                                "OK", testi.IMP_ANNULLA, lambda _: None, pericolo=False)
            return
        self.impostazioni.cartella_bandiere = str(radice)
        self._salva_impostazioni()
        self.carica_bandiere()

    def _cartella_predefinita(self) -> None:
        self.impostazioni.cartella_bandiere = ""
        self._salva_impostazioni()
        self.carica_bandiere()

    # ------------------------------------------------------------ partita

    def avvia_partita(self, modalita: str, livello: str, area: str) -> None:
        if self.generatore is None:
            return
        domande = self.generatore.genera(modalita, livello, area)
        self.partita = Partita(modalita, livello, area, domande)
        self._ricorda_selezione(modalita, livello, area)
        self.gioco.avvia(self.partita, testi.MODALITA[modalita], self.nome_livello(livello),
                         self.nome_area(area))
        self.stack.mostra(self.gioco)
        # il cronometro parte quando la prima domanda è davvero visibile
        QTimer.singleShot(DURATA_DISSOLVENZA, self.gioco.mostra_prima_domanda)

    def _registra_storico(self, partita: Partita) -> None:
        if self.generatore is not None:
            self.generatore.registra_uscite(partita.modalita, partita.livello, partita.area,
                                            partita.ids_mostrati())

    def _partita_finita(self, partita: Partita) -> None:
        self._registra_storico(partita)
        self.suoni.suona("fine")
        self.riepilogo.mostra(partita, testi.MODALITA[partita.modalita], self.nome_livello(partita.livello),
                              self.nome_area(partita.area), self.impostazioni.ultimo_nome)
        self.stack.mostra(self.riepilogo)

    def _partita_abbandonata(self, partita: Partita) -> None:
        self._registra_storico(partita)
        self.partita = None
        self.vai_home()

    def _gioca_ancora(self) -> None:
        if self.partita is not None:
            p = self.partita
            self.avvia_partita(p.modalita, p.livello, p.area)

    def _salva_risultato(self, nome: str) -> None:
        p = self.partita
        if p is None:
            return
        risultato = self.classifica.aggiungi(Risultato(
            nome=nome, giuste=p.giuste, totale=p.totale, tempo=round(p.tempo(), 2),
            modalita=p.modalita, livello=p.livello, area=p.area))
        self.impostazioni.ultimo_nome = risultato.nome
        self._salva_impostazioni()
        self.riepilogo.segna_salvato()
        self.schermata_classifica.mostra(p.modalita, p.livello, p.area, evidenzia=risultato.id)
        self._ritorno_classifica = self.riepilogo
        self.stack.mostra(self.schermata_classifica)

    # -------------------------------------------------------- navigazione

    def vai_home(self) -> None:
        self.gioco.ferma()
        self.stack.mostra(self.home if self.catalogo else self.schermata_cartella)

    def _classifica_da_home(self) -> None:
        self.schermata_classifica.mostra(self.home.modalita(), self.home.livello(), self.home.area())
        self._ritorno_classifica = self.home
        self.stack.mostra(self.schermata_classifica)

    def apri_impostazioni(self) -> None:
        self._aggiorna_impostazioni()
        self.stack.mostra(self.schermata_impostazioni)

    def _aggiorna_impostazioni(self) -> None:
        if self.catalogo is not None:
            cartella = str(self.catalogo.radice)
            avvisi = [a for a in self.catalogo.anomalie if a.tipo not in ("senza_nome",)]
            n = self.catalogo.totale_bandiere()
            info = (testi.IMP_CARTELLA_ANOMALIE.format(n=n, a=len(avvisi)) if avvisi
                    else testi.IMP_CARTELLA_INFO.format(n=n))
            dettagli = "\n".join(f"• {a.percorso}: {a.dettaglio}" for a in avvisi[:40])
        else:
            cartella, info, dettagli = self.impostazioni.cartella_bandiere, "", ""
        self.schermata_impostazioni.mostra(self.impostazioni, cartella, info, dettagli,
                                           str(self.cartella_utente))

    # ------------------------------------------------------- impostazioni

    def _salva_impostazioni(self) -> None:
        try:
            self.impostazioni.salva(self.cartella_utente / "impostazioni.json")
        except OSError:
            pass

    def _ricorda_selezione(self, modalita: str, livello: str, area: str) -> None:
        imp = self.impostazioni
        if (imp.ultima_modalita, imp.ultimo_livello, imp.ultima_area) != (modalita, livello, area):
            imp.ultima_modalita, imp.ultimo_livello, imp.ultima_area = modalita, livello, area
            self._salva_impostazioni()

    def _cambia_tema(self, nome: str) -> None:
        self.impostazioni.tema = nome
        applica_tema(nome, self.cartella_utente / "cache")
        aggiorna_icone(self)
        self._salva_impostazioni()

    def _cambia_suoni(self, attivi: bool) -> None:
        self.impostazioni.suoni = attivi
        self.suoni.abilitati = attivi
        self._salva_impostazioni()
        if attivi:
            self.suoni.suona("giusto")

    def _cambia_auto(self, attivo: bool) -> None:
        self.impostazioni.avanzamento_automatico = attivo
        self._salva_impostazioni()

    def _azzera_storico(self) -> None:
        self.storico.azzera()
        self.schermata_impostazioni.segnala_storico_azzerato()

    def _chiedi_svuota_classifica(self) -> None:
        def esito(si: bool):
            if si:
                self.classifica.svuota()
        chiedi_conferma(self.centralWidget(), testi.IMP_SVUOTA_TITOLO, testi.IMP_SVUOTA_TESTO,
                        testi.IMP_SVUOTA_SI, testi.IMP_ANNULLA, esito)

    def closeEvent(self, evento):
        self.gioco.ferma()
        self.impostazioni.geometria = bytes(self.saveGeometry().toHex()).decode()
        self._salva_impostazioni()
        super().closeEvent(evento)
