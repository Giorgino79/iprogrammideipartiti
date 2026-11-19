from django.core.management.base import BaseCommand, CommandError

from analisi import sondaggi
from analisi.models import Partito


class Command(BaseCommand):
    help = ('Aggiorna le intenzioni di voto dei partiti (Supermedia YouTrend/Agi, letta dalla tabella degli '
            'aggregatori di Wikipedia). Pensato per Heroku Scheduler, due volte al giorno.')

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='mostra i dati senza scriverli')

    def handle(self, *args, **opts):
        try:
            data, valori = sondaggi.leggi_supermedia(sondaggi.scarica_wikitext())
            sondaggi.controlla(valori)
        except (sondaggi.ErroreSondaggi, OSError, ValueError, KeyError) as e:
            raise CommandError('Sondaggi NON aggiornati: %s' % e)

        gia = Partito.objects.exclude(sondaggio_data=None).order_by('-sondaggio_data').values_list(
            'sondaggio_data', flat=True).first()
        if gia and data < gia:
            raise CommandError('Sondaggi NON aggiornati: la fonte (%s) è più vecchia di quella salvata (%s)' % (data, gia))

        fonte = 'Supermedia YouTrend/Agi, %s (letta da Wikipedia)' % data.strftime('%d/%m/%Y')
        self.stdout.write('Supermedia del %s: %s' % (data, ', '.join('%s %.1f' % kv for kv in sorted(
            valori.items(), key=lambda kv: kv[1]))))
        if opts['dry_run']:
            self.stdout.write('Dry run: nessuna modifica.')
            return

        aggiornati = 0
        for slug, valore in valori.items():
            aggiornati += Partito.objects.filter(slug=slug).update(
                sondaggio=valore, sondaggio_data=data, sondaggio_fonte=fonte, sondaggio_url=sondaggi.URL_FONTE)
        self.stdout.write(self.style.SUCCESS('Sondaggi aggiornati: %d partiti, dati del %s.' % (aggiornati, data)))
