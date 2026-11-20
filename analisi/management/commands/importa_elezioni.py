import csv
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from analisi.models import Affluenza, Elezione, Lista, Partito, RisultatoLista, Territorio

DATI = Path(__file__).resolve().parents[2] / 'dati_elezioni'
FONTE = 'Ministero dell\'Interno, Eligendo - Archivio storico (open data)'
FONTE_URL = 'https://elezionistorico.interno.gov.it/eligendo/opendata.php'
NOTA_EUROPEE = ('Risultati in Italia, sommati per provincia dai dati per comune del Ministero dell\'Interno. '
                'Non comprendono gli elettori all\'estero, quindi l\'affluenza può differire dai dati nazionali '
                'ufficiali. Le percentuali sono sui voti di lista validi. Il Ministero precisa che i dati per '
                'comune in parte sono ufficiosi e possono differire dai riepiloghi ufficiali.')

# file -> (tipo, data)
ELEZIONI = {
    'europee_2004': (Elezione.EUROPEE, date(2004, 6, 12)),
    'europee_2009': (Elezione.EUROPEE, date(2009, 6, 7)),
    'europee_2014': (Elezione.EUROPEE, date(2014, 5, 25)),
    'europee_2019': (Elezione.EUROPEE, date(2019, 5, 26)),
    'europee_2024': (Elezione.EUROPEE, date(2024, 6, 9)),
}

# Collegamento alle liste con i partiti di oggi, solo dove la continuità è chiara (testo contenuto nel nome della lista)
COLLEGAMENTI = [
    ("FRATELLI D'ITALIA", 'fdi'), ('PARTITO DEMOCRATICO', 'pd'), ('MOVIMENTO 5 STELLE', 'm5s'),
    ('FORZA ITALIA', 'forza-italia'), ('LEGA NORD', 'lega'), ('LEGA SALVINI PREMIER', 'lega'),
    ('ALLEANZA VERDI E SINISTRA', 'avs'), ('AZIONE - SIAMO EUROPEI', 'azione'),
    ('+EUROPA', 'piu-europa'), ('NOI MODERATI', 'noi-moderati'),
]


def partito_di(nome, partiti):
    n = nome.upper()
    for testo, slug in COLLEGAMENTI:
        if testo in n and not n.startswith('UNITI NELL'):
            return partiti.get(slug)
    return None


class Command(BaseCommand):
    help = 'Importa i risultati elettorali (già sommati per provincia) da analisi/dati_elezioni/'

    @transaction.atomic
    def handle(self, *args, **opts):
        partiti = {p.slug: p for p in Partito.objects.all()}
        for nome_file, (tipo, data) in ELEZIONI.items():
            liste_csv, aff_csv = DATI / f'{nome_file}_liste.csv', DATI / f'{nome_file}_affluenza.csv'
            if not liste_csv.exists():
                continue
            elezione, _ = Elezione.objects.get_or_create(
                tipo=tipo, data=data, ambito='',
                defaults=dict(nome=f'Elezioni europee {data.year}', fonte=FONTE, fonte_url=FONTE_URL, nota=NOTA_EUROPEE))
            elezione.risultati.all().delete()
            elezione.affluenze.all().delete()
            territori = {}

            def territorio(reg, prov):
                if (reg, prov) not in territori:
                    territori[(reg, prov)], _ = Territorio.objects.get_or_create(regione=reg, provincia=prov)
                return territori[(reg, prov)]

            liste, risultati = {}, []
            with open(liste_csv, encoding='utf-8', newline='') as f:
                for r in csv.DictReader(f):
                    if r['lista'] not in liste:
                        liste[r['lista']], _ = Lista.objects.get_or_create(
                            elezione=elezione, nome=r['lista'], defaults=dict(partito=partito_di(r['lista'], partiti)))
                    risultati.append(RisultatoLista(elezione=elezione, territorio=territorio(r['regione'], r['provincia']),
                                                    lista=liste[r['lista']], voti=int(r['voti'])))
            RisultatoLista.objects.bulk_create(risultati)
            with open(aff_csv, encoding='utf-8', newline='') as f:
                Affluenza.objects.bulk_create([
                    Affluenza(elezione=elezione, territorio=territorio(r['regione'], r['provincia']),
                              elettori=int(r['elettori']), votanti=int(r['votanti']),
                              bianche=int(r['bianche']) if r['bianche'] != '' else None)
                    for r in csv.DictReader(f)])
            self.stdout.write(f'{elezione}: {len(liste)} liste, {len(risultati)} risultati')
        self.stdout.write(self.style.SUCCESS('Elezioni importate.'))
