from .models import Partito


def partiti_header(request):
    """Simboli dei partiti dal più alto al più basso nei sondaggi (il più votato a sinistra); le coalizioni restano fuori."""
    partiti = list(Partito.objects.filter(coalizione=False))
    con = sorted((p for p in partiti if p.sondaggio is not None), key=lambda p: (-p.sondaggio, p.nome))
    senza = sorted((p for p in partiti if p.sondaggio is None), key=lambda p: p.nome)
    ordinati = con + senza  # chi non ha percentuale va in fondo, a destra
    fonte = con[0] if con else None
    return {
        'partiti_header': ordinati,
        'sondaggio_fonte': fonte.sondaggio_fonte if fonte else '',
        'sondaggio_url': fonte.sondaggio_url if fonte else '',
        'coalizioni': Partito.objects.filter(coalizione=True),
    }
