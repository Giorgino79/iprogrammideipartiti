from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from analisi.dati_esempio import ESEMPI
from analisi.dati_voti import TEMI, VOTI
from analisi.models import Commento, Partito, Programma, Tema


class Command(BaseCommand):
    help = 'Carica partiti, programmi e commenti di esempio (non tocca quello che esiste già)'

    def handle(self, *args, **opts):
        temi = {}
        for i, (slug, nome) in enumerate(TEMI, 1):
            temi[slug], _ = Tema.objects.get_or_create(slug=slug, defaults=dict(nome=nome, ordine=i))
        for e in ESEMPI:
            dati = dict(e['partito'])
            logo = dati.pop('logo', '')
            partito, _ = Partito.objects.get_or_create(slug=dati.pop('slug'), defaults=dati)
            if logo and not partito.logo and (Path(settings.MEDIA_ROOT) / 'loghi' / logo).exists():
                partito.logo = f'loghi/{logo}'
                partito.save()
            for p in e['programmi']:
                pdf = Path(settings.MEDIA_ROOT) / 'programmi' / p['pdf']
                documento = f"programmi/{p['pdf']}" if pdf.exists() else ''
                programma = Programma.objects.filter(partito=partito, documento=documento).first() if documento else None
                if programma is None:
                    programma, _ = Programma.objects.get_or_create(
                        partito=partito, titolo=p['titolo'], anno=p['anno'],
                        defaults=dict(ambito=p['ambito'], documento=documento))
                elif programma.titolo != p['titolo']:
                    programma.titolo = p['titolo']
                    programma.save()
                if not programma.commenti.exists():
                    for c in p['commenti']:
                        Commento.objects.create(programma=programma, **c)
                for commento in programma.commenti.filter(voto_fattibilita__isnull=True):
                    dati = VOTI.get((p['pdf'], commento.ordine))
                    if dati:
                        tema, f, co, s, ch, ri, costo = dati
                        commento.tema = temi[tema]
                        commento.voto_fattibilita, commento.voto_copertura, commento.voto_esiti = f, co, s
                        commento.voto_chiarezza, commento.voto_rischi, commento.costo = ch, ri, costo
                        commento.save()
        self.stdout.write(self.style.SUCCESS('Esempi caricati.'))
