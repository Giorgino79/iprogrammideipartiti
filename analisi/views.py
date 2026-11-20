from django.db.models import Count, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import Affluenza, Commento, Elezione, Partito, Programma, RisultatoLista, Tema, Territorio


def home(request):
    return render(request, 'analisi/home.html')


def partito(request, slug):
    partito = get_object_or_404(Partito, slug=slug)
    return render(request, 'analisi/partito.html', {
        'partito': partito,
        'programmi': partito.programmi.all(),
    })


def programma(request, pk):
    programma = get_object_or_404(Programma.objects.select_related('partito'), pk=pk)
    return render(request, 'analisi/programma.html', {
        'programma': programma,
        'partito': programma.partito,
        'commenti': programma.commenti.all(),
    })


def metodo(request):
    return render(request, 'analisi/metodo.html', {'voti': Commento.VOTI})


def confronto(request):
    temi = Tema.objects.annotate(partiti=Count('commenti__programma__partito', distinct=True)).order_by('ordine', 'nome')
    return render(request, 'analisi/confronto.html', {
        'pronti': [t for t in temi if t.partiti >= 2],
        'uno_solo': [t for t in temi if t.partiti == 1],
        'in_preparazione': [t for t in temi if t.partiti == 0],
    })


def confronto_tema(request, slug):
    tema = get_object_or_404(Tema, slug=slug)
    ambito = request.GET.get('ambito', '')
    commenti = (tema.commenti.select_related('programma', 'programma__partito')
                .order_by('programma__partito__ordine', 'programma__anno', 'ordine'))
    if ambito in (Programma.ITALIANO, Programma.EUROPEO):
        commenti = commenti.filter(programma__ambito=ambito)
    commenti = list(commenti)
    partiti = {c.programma.partito_id for c in commenti}
    return render(request, 'analisi/confronto_tema.html', {
        'tema': tema, 'commenti': commenti, 'ambito': ambito, 'voti': Commento.VOTI,
        'n_partiti': len(partiti),
    })


TIPI_RISULTATI = {
    'europee': (Elezione.EUROPEE, 'Elezioni europee'),
    'politiche': (Elezione.POLITICHE_CAMERA, 'Elezioni politiche'),
    'regionali': (Elezione.REGIONALI, 'Elezioni regionali'),
    'referendum': (Elezione.REFERENDUM, 'Referendum'),
}


def risultati(request):
    presenti = set(Elezione.objects.values_list('tipo', flat=True).distinct())
    tipi = [(slug, nome, sigla in presenti) for slug, (sigla, nome) in TIPI_RISULTATI.items()]
    return render(request, 'analisi/risultati.html', {'tipi': tipi})


def risultati_tipo(request, slug):
    if slug not in TIPI_RISULTATI:
        raise Http404
    sigla, nome = TIPI_RISULTATI[slug]
    return render(request, 'analisi/risultati_tipo.html', {
        'nome': nome, 'elezioni': Elezione.objects.filter(tipo=sigla),
    })


def _tabella(righe):
    """righe: [(nome lista, partito o None, voti)] -> con la percentuale sui voti di lista validi."""
    totale = sum(v for _, _, v in righe) or 1
    return [dict(lista=n, partito=p, voti=v, percento=round(100 * v / totale, 2)) for n, p, v in righe], totale


def risultati_elezione(request, pk):
    elezione = get_object_or_404(Elezione, pk=pk)
    base = RisultatoLista.objects.filter(elezione=elezione)

    def righe(qs):
        return [(r['lista__nome'], r['lista__partito__nome'], r['tot'])
                for r in qs.values('lista__nome', 'lista__partito__nome').annotate(tot=Sum('voti')).order_by('-tot')]

    nazionale, tot_nazionale = _tabella(righe(base))
    aff = Affluenza.objects.filter(elezione=elezione)
    aff_naz = aff.aggregate(e=Sum('elettori'), v=Sum('votanti'), b=Sum('bianche'))
    territori = Territorio.objects.filter(affluenze__elezione=elezione)
    scelto = None
    locale = None
    aff_loc = None
    try:
        scelto = territori.filter(pk=int(request.GET.get('provincia', ''))).first()
    except ValueError:
        scelto = None
    if scelto:
        locale, _ = _tabella(righe(base.filter(territorio=scelto)))
        confronto = {r['lista']: r['percento'] for r in nazionale}
        for r in locale:
            r['differenza'] = round(r['percento'] - confronto.get(r['lista'], 0), 2)
        aff_loc = aff.filter(territorio=scelto).first()
    return render(request, 'analisi/risultato_elezione.html', {
        'elezione': elezione, 'nazionale': nazionale, 'aff_naz': aff_naz, 'territori': territori,
        'scelto': scelto, 'locale': locale, 'aff_loc': aff_loc,
        'affl_naz_pct': round(100 * aff_naz['v'] / aff_naz['e'], 2) if aff_naz['e'] else None,
        'affl_loc_pct': round(100 * aff_loc.votanti / aff_loc.elettori, 2) if aff_loc and aff_loc.elettori else None,
    })
