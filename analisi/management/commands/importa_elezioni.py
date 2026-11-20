import csv
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from analisi.models import (Affluenza, Elezione, Lista, Partito, Quesito, RisultatoLista, RisultatoQuesito,
                            Territorio)

DATI = Path(__file__).resolve().parents[2] / 'dati_elezioni'
FONTE = 'Ministero dell\'Interno, Eligendo - Archivio storico (open data)'
FONTE_URL = 'https://elezionistorico.interno.gov.it/eligendo/opendata.php'
NOTA_EUROPEE = ('Risultati in Italia, sommati per provincia dai dati per comune del Ministero dell\'Interno. '
                'Non comprendono gli elettori all\'estero, quindi l\'affluenza può differire dai dati nazionali '
                'ufficiali. Le percentuali sono sui voti di lista validi. Il Ministero precisa che i dati per '
                'comune in parte sono ufficiosi e possono differire dai riepiloghi ufficiali.')

NOTA_REFERENDUM = ('Risultati in Italia, sommati per provincia dai dati del Ministero dell\'Interno; non comprendono gli '
                   'elettori all\'estero. Per i referendum abrogativi la consultazione è valida se partecipa più della '
                   'metà degli aventi diritto (compresi quelli all\'estero); per i costituzionali non c\'è quorum. '
                   'Le percentuali di sì e no sono sui voti validi. Il Ministero precisa che i dati per comune in parte '
                   'sono ufficiosi e possono differire dai riepiloghi ufficiali. Per il 2022 i titoli dei quesiti sono '
                   'sintetici.')
MESI = ['', 'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre',
        'novembre', 'dicembre']

# file -> (tipo, data)
NOTA_POLITICHE = ('Voti di lista in Italia, sommati per provincia dai dati per comune del Ministero dell\'Interno. '
                  'Non comprendono la circoscrizione Estero. Le percentuali sono sui voti di lista validi. Per il Senato '
                  'del 2001 le \"liste\" sono le coalizioni dei candidati nei collegi uninominali. I comuni che non si '
                  'riesce ad abbinare a una provincia (meno dell\'1% dei voti) sono conteggiati solo nel totale '
                  'nazionale. Il Ministero precisa che i dati per comune in parte sono ufficiosi e possono differire '
                  'dai riepiloghi ufficiali.')
DATE_POLITICHE = {2001: date(2001, 5, 13), 2006: date(2006, 4, 9), 2008: date(2008, 4, 13), 2013: date(2013, 2, 24),
                  2018: date(2018, 3, 4), 2022: date(2022, 9, 25)}
ELEZIONI = {
    'europee_2004': (Elezione.EUROPEE, date(2004, 6, 12)),
    'europee_2009': (Elezione.EUROPEE, date(2009, 6, 7)),
    'europee_2014': (Elezione.EUROPEE, date(2014, 5, 25)),
    'europee_2019': (Elezione.EUROPEE, date(2019, 5, 26)),
    'europee_2024': (Elezione.EUROPEE, date(2024, 6, 9)),
}
for _anno, _data in DATE_POLITICHE.items():
    ELEZIONI[f'politiche_camera_{_anno}'] = (Elezione.POLITICHE_CAMERA, _data)
    ELEZIONI[f'politiche_senato_{_anno}'] = (Elezione.POLITICHE_SENATO, _data)

NOMI = {Elezione.EUROPEE: 'Elezioni europee {anno}',
        Elezione.POLITICHE_CAMERA: 'Elezioni politiche {anno} - Camera dei Deputati',
        Elezione.POLITICHE_SENATO: 'Elezioni politiche {anno} - Senato della Repubblica'}
NOTE = {Elezione.EUROPEE: NOTA_EUROPEE, Elezione.POLITICHE_CAMERA: NOTA_POLITICHE, Elezione.POLITICHE_SENATO: NOTA_POLITICHE}

# Collegamento alle liste con i partiti di oggi, solo dove la continuità è chiara (testo contenuto nel nome della lista)
COLLEGAMENTI = [
    ("FRATELLI D'ITALIA", 'fdi'), ('PARTITO DEMOCRATICO', 'pd'), ('MOVIMENTO 5 STELLE', 'm5s'),
    ('FORZA ITALIA', 'forza-italia'), ('LEGA NORD', 'lega'), ('LEGA SALVINI PREMIER', 'lega'), ('LEGA PER SALVINI', 'lega'),
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
                defaults=dict(nome=NOMI[tipo].format(anno=data.year), fonte=FONTE, fonte_url=FONTE_URL, nota=NOTE[tipo]))
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
        for percorso in sorted(DATI.glob('referendum_*.csv')):
            d = percorso.stem.split('_')[1]
            data = date(int(d[:4]), int(d[4:6]), int(d[6:]))
            elezione, _ = Elezione.objects.get_or_create(
                tipo=Elezione.REFERENDUM, data=data, ambito='',
                defaults=dict(nome=f'Referendum del {data.day} {MESI[data.month]} {data.year}', fonte=FONTE,
                              fonte_url=FONTE_URL, nota=NOTA_REFERENDUM))
            elezione.quesiti.all().delete()  # cancella anche i risultati collegati
            territori, quesiti, risultati = {}, {}, []
            with open(percorso, encoding='utf-8', newline='') as f:
                for r in csv.DictReader(f):
                    k = (r['regione'], r['provincia'])
                    if k not in territori:
                        territori[k], _ = Territorio.objects.get_or_create(regione=k[0], provincia=k[1])
                    num = int(r['num'])
                    if num not in quesiti:
                        quesiti[num] = Quesito.objects.create(elezione=elezione, numero=num, titolo=r['quesito'], tipo=r['tipo'])
                    risultati.append(RisultatoQuesito(
                        quesito=quesiti[num], territorio=territori[k], elettori=int(r['elettori']),
                        votanti=int(r['votanti']), bianche=int(r['bianche']), si=int(r['si']), no=int(r['no'])))
            RisultatoQuesito.objects.bulk_create(risultati)
            self.stdout.write(f'{elezione}: {len(quesiti)} quesiti, {len(risultati)} risultati')
        self.stdout.write(self.style.SUCCESS('Elezioni importate.'))
