from .models import Partito


def partiti_header(request):
    """Simboli dei partiti dal più basso al più alto nei sondaggi (crescente verso destra); le coalizioni restano fuori."""
    partiti = list(Partito.objects.filter(coalizione=False))
    partiti.sort(key=lambda p: (p.sondaggio is None, p.sondaggio or 0, p.nome))
    # chi non ha percentuale va per primo, a sinistra
    senza = [p for p in partiti if p.sondaggio is None]
    con = [p for p in partiti if p.sondaggio is not None]
    ordinati = senza + con
    fonte = next((p for p in con), None)
    return {
        'partiti_header': ordinati,
        'sondaggio_fonte': fonte.sondaggio_fonte if fonte else '',
        'sondaggio_url': fonte.sondaggio_url if fonte else '',
        'coalizioni': Partito.objects.filter(coalizione=True),
    }
