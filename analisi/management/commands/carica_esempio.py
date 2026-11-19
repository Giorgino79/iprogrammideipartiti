from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from analisi.dati_esempio import ESEMPI
from analisi.models import Commento, Partito, Programma


class Command(BaseCommand):
    help = 'Carica partiti, programmi e commenti di esempio (non tocca quello che esiste già)'

    def handle(self, *args, **opts):
        for e in ESEMPI:
            dati = dict(e['partito'])
            partito, _ = Partito.objects.get_or_create(slug=dati.pop('slug'), defaults=dati)
            for p in e['programmi']:
                pdf = Path(settings.MEDIA_ROOT) / 'programmi' / p['pdf']
                programma, _ = Programma.objects.get_or_create(
                    partito=partito, titolo=p['titolo'], anno=p['anno'],
                    defaults=dict(ambito=p['ambito'], documento=f"programmi/{p['pdf']}" if pdf.exists() else ''))
                if not programma.commenti.exists():
                    for c in p['commenti']:
                        Commento.objects.create(programma=programma, **c)
        self.stdout.write(self.style.SUCCESS('Esempi caricati.'))
