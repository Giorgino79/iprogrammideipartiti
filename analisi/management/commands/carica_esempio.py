import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from analisi.models import Commento, Partito, Programma

PDF = Path.home() / 'Scrivania' / 'AGGIORNAMENTO-PROGRAMMA_INSIEMEPERUNITALIADEMOCRATICAEPROGRESSISTA_250822-1.pdf'

COMMENTI = [
    dict(ordine=1, pagina=19, titolo='Salario minimo contrattuale', fattibilita='M',
         motivazione='Un minimo legale è realizzabile; estendere i contratti a tutti ha un record storico di fallimento.',
         promessa='Una legge che estende a tutti i lavoratori il trattamento economico dei contratti firmati dai sindacati più rappresentativi, più un salario minimo "modello tedesco" con soglia proposta dalle parti sociali (circa 9 € lordi l\'ora).',
         precedenti='L\'efficacia generale dei contratti (art. 39 Cost.) non è mai stata attuata dal 1948, con governi di ogni colore.\nIl Jobs Act del 2014 prevedeva nella delega un "compenso orario minimo", mai attuato.\nIn Germania il minimo legale è stato introdotto nel 2015 (8,50 €): la maggior parte degli studi non trova perdite di posti di lavoro rilevanti [verificare].',
         fondi='Costo diretto per lo Stato basso; il costo ricade su imprese e appalti pubblici.',
         rischi_benefici='Beneficio: salari più alti dove ci sono contratti "pirata", meno lavoro povero.\nRischio: nei settori e nelle aree a bassa produttività, soprattutto al Sud, parte dei rapporti può scivolare nel nero invece di salire di paga.\nRischio: con la soglia affidata alle parti sociali, tutto dipende dall\'accordo tra sindacati e associazioni datoriali.'),
    dict(ordine=2, pagina=34, titolo='Dotazione di 10.000 € ai 18enni', fattibilita='B',
         motivazione='La misura è attuabile, ma la copertura indicata non regge.',
         promessa='10.000 € a 18 anni in base all\'ISEE, per casa, studio e lavoro, coperti "prevalentemente" da un aumento dell\'imposta di successione sopra i 5 milioni (lo 0,2% di eredità e donazioni).',
         precedenti='Il Bonus cultura 18app (500 €) è durato anni, ma costava circa 0,3 miliardi l\'anno [verificare].\nIl Child Trust Fund britannico (2005-2011), un conto di risparmio per ogni neonato, è stato chiuso per ragioni di costo.',
         fondi='I diciottenni sono circa 550.000 l\'anno. Anche con l\'ISEE che riduce la platea, la spesa sarebbe di alcuni miliardi l\'anno (stima).\nL\'intera imposta di successione italiana rende circa 1 miliardo l\'anno [verificare]: una quota minima di essa non può coprire "prevalentemente" questa spesa.\nIl gettito sulle grandi eredità è piccolo, variabile e aggirabile. Una spesa fissa annuale su un\'entrata così incerta è instabile.',
         rischi_benefici='Beneficio: più pari opportunità all\'ingresso nella vita adulta.\nRischio: se i soldi mancano, o si taglia l\'importo o si pesca altrove nel bilancio.\nRischio: l\'uso dei soldi è difficile da controllare.'),
    dict(ordine=3, pagina=27, titolo='500.000 alloggi popolari in 10 anni', fattibilita='B',
         motivazione='Bassa su numero e tempi, media sulla direzione: una parte del piano è sensata se ha un finanziamento certo.',
         promessa='500.000 alloggi popolari in 10 anni, con rigenerazione urbana e meno consumo di suolo.',
         precedenti='Il Piano INA-Casa (1949-63) costruì circa 350.000 alloggi in 14 anni, con un prelievo dedicato sui salari [verificare].\nIl successore, la Gescal, fu chiuso nel 1998 e le competenze passarono alle Regioni [verificare].\nDa allora nessun programma statale paragonabile; i Piani casa del 2009 e del 2014 furono molto più piccoli.',
         fondi='Il testo non indica la fonte. Stima: a 150-200 mila € ad alloggio servirebbero 75-100 miliardi in 10 anni.\nIl PNRR ne copre solo una piccola parte. Serve un fondo stabile per un decennio, quindi oltre una legislatura.\nSi aggiungono manutenzione e gestione, che oggi lasciano molti alloggi pubblici inutilizzabili [verificare].',
         rischi_benefici='Beneficio: l\'edilizia sociale italiana è molto sotto la media dei Paesi europei comparabili [verificare].\nRischio: tempi lunghi dei cantieri pubblici e lentezza di Comuni e Regioni.\nRischio: i costi si sommano negli anni e vincolano i bilanci futuri.'),
    dict(ordine=4, pagina=13, titolo='Sfiducia costruttiva', fattibilita='B',
         motivazione='Dipende dalla politica e da un referendum, non da soldi o tecnica.',
         promessa='Introdurre la sfiducia costruttiva per limitare le crisi di governo. Richiede una revisione costituzionale (art. 94).',
         precedenti='La Bicamerale del 1997 fallì. La riforma Berlusconi fu bocciata dal referendum del 2006 e la riforma Renzi-Boschi da quello del 2016.\nPassata solo la riforma del Titolo V (2001), di centrosinistra, con maggioranza risicata.\nIn Germania la sfiducia costruttiva funziona, ma con un sistema di partiti e una legge elettorale diversi.',
         fondi='Costo zero: nessun problema di copertura.',
         rischi_benefici='Beneficio: governi più stabili.\nRischio: da sola non cura la frammentazione dei partiti, che è la vera causa delle crisi.\nRischio: può tenere in vita governi deboli invece di renderli forti.'),
]


class Command(BaseCommand):
    help = 'Carica il PD 2022 con i 4 commenti di esempio'

    def add_arguments(self, parser):
        parser.add_argument('--solo-se-vuoto', action='store_true',
                            help='non fa nulla se esiste già almeno un partito')

    def handle(self, *args, **opts):
        if opts['solo_se_vuoto'] and Partito.objects.exists():
            return
        pd, _ = Partito.objects.get_or_create(
            slug='pd', defaults=dict(nome='Partito Democratico', sigla='PD', schieramento=Partito.SINISTRA, ordine=1))
        pr, creato = Programma.objects.get_or_create(
            partito=pd, anno=2022, defaults=dict(titolo='Insieme per un\'Italia democratica e progressista'))
        dest = Path(settings.MEDIA_ROOT) / 'programmi' / 'pd-2022.pdf'
        if not dest.exists() and PDF.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(PDF, dest)
        if not pr.documento and dest.exists():
            pr.documento = 'programmi/pd-2022.pdf'
            pr.save()
        if not pr.commenti.exists():
            for c in COMMENTI:
                Commento.objects.create(programma=pr, **c)
        self.stdout.write(self.style.SUCCESS('Esempio caricato.'))
