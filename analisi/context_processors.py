from .models import Partito


def partiti_header(request):
    partiti = list(Partito.objects.all())
    return {
        'partiti_header': partiti,
        'partiti_sx': [p for p in partiti if p.schieramento == Partito.SINISTRA],
        'partiti_ce': [p for p in partiti if p.schieramento == Partito.CENTRO],
        'partiti_dx': [p for p in partiti if p.schieramento == Partito.DESTRA],
    }
