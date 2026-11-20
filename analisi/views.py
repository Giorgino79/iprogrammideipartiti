from django.db.models import Count, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import (Affluenza, Commento, Elezione, Partito, Programma, Quesito, RisultatoCandidato, RisultatoLista,
                     RisultatoQuesito, Tema, Territorio)


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
    'politiche': ((Elezione.POLITICHE_CAMERA, Elezione.POLITICHE_SENATO), 'Elezioni politiche'),
    'regionali': (Elezione.REGIONALI, 'Elezioni regionali'),
    'referendum': (Elezione.REFERENDUM, 'Referendum'),
}


def _siglie(sigla):
    return sigla if isinstance(sigla, tuple) else (sigla,)


def _slug_tipo(tipo):
    return next(slug for slug, (sigla, _) in TIPI_RISULTATI.items() if tipo in _siglie(sigla))


def risultati(request):
    presenti = set(Elezione.objects.values_list('tipo', flat=True).distinct())
    tipi = [(slug, nome, bool(set(_siglie(sigla)) & presenti)) for slug, (sigla, nome) in TIPI_RISULTATI.items()]
    return render(request, 'analisi/risultati.html', {'tipi': tipi})


def risultati_tipo(request, slug):
    if slug not in TIPI_RISULTATI:
        raise Http404
    sigla, nome = TIPI_RISULTATI[slug]
    elezioni = Elezione.objects.filter(tipo__in=_siglie(sigla)).order_by('-data', 'tipo')
    regioni = scelta = None
    if sigla == Elezione.REGIONALI:  # molte elezioni: prima si sceglie la Regione
        regioni = list(elezioni.order_by('ambito').values_list('ambito', flat=True).distinct())
        scelta = request.GET.get('regione') if request.GET.get('regione') in regioni else None
        elezioni = elezioni.filter(ambito=scelta) if scelta else elezioni.none()
    return render(request, 'analisi/risultati_tipo.html', {
        'nome': nome, 'elezioni': elezioni, 'regioni': regioni, 'scelta': scelta,
    })


def _candidati(qs):
    righe = [(r['candidato'], None, r['tot'])
             for r in qs.values('candidato').annotate(tot=Sum('voti')).order_by('-tot')]
    return _tabella(righe)[0]


def _tabella(righe):
    """righe: [(nome lista, partito o None, voti)] -> con la percentuale sui voti di lista validi."""
    totale = sum(v for _, _, v in righe) or 1
    return [dict(lista=n, partito=p, voti=v, percento=round(100 * v / totale, 2)) for n, p, v in righe], totale


def _righe_quesiti(qs):
    righe = {}
    for r in qs.values('quesito__numero', 'quesito__titolo', 'quesito__tipo').annotate(
            e=Sum('elettori'), v=Sum('votanti'), b=Sum('bianche'), si=Sum('si'), no=Sum('no')).order_by('quesito__numero'):
        validi = (r['si'] or 0) + (r['no'] or 0)
        righe[r['quesito__numero']] = dict(
            numero=r['quesito__numero'], titolo=r['quesito__titolo'], tipo=r['quesito__tipo'],
            elettori=r['e'], votanti=r['v'], bianche=r['b'], si=r['si'], no=r['no'],
            affluenza=round(100 * r['v'] / r['e'], 2) if r['e'] else None,
            si_pct=round(100 * r['si'] / validi, 2) if validi else None,
            no_pct=round(100 * r['no'] / validi, 2) if validi else None)
    return righe


def _referendum(request, elezione):
    base = RisultatoQuesito.objects.filter(quesito__elezione=elezione)
    nazionale = _righe_quesiti(base)
    territori = Territorio.objects.filter(risultati_quesiti__quesito__elezione=elezione).distinct()
    try:
        scelto = territori.filter(pk=int(request.GET.get('provincia', ''))).first()
    except ValueError:
        scelto = None
    locale = _righe_quesiti(base.filter(territorio=scelto)) if scelto else None
    if locale:
        for n, r in locale.items():
            ita = nazionale.get(n, {})
            r['diff_si'] = round(r['si_pct'] - ita['si_pct'], 2) if r['si_pct'] is not None and ita.get('si_pct') is not None else None
    return render(request, 'analisi/risultato_referendum.html', {
        'elezione': elezione, 'tipo_slug': 'referendum', 'tipo_nome': 'Referendum',
        'nazionale': list(nazionale.values()), 'territori': territori, 'scelto': scelto,
        'locale': list(locale.values()) if locale else None,
    })


def risultati_elezione(request, pk):
    elezione = get_object_or_404(Elezione, pk=pk)
    if elezione.tipo == Elezione.REFERENDUM:
        return _referendum(request, elezione)
    base = RisultatoLista.objects.filter(elezione=elezione)

    def righe(qs):
        return [(r['lista__nome'], r['lista__partito__nome'], r['tot'])
                for r in qs.values('lista__nome', 'lista__partito__nome').annotate(tot=Sum('voti')).order_by('-tot')]

    nazionale, tot_nazionale = _tabella(righe(base))
    aff = Affluenza.objects.filter(elezione=elezione)
    aff_naz = aff.aggregate(e=Sum('elettori'), v=Sum('votanti'), b=Sum('bianche'))
    territori = Territorio.objects.filter(affluenze__elezione=elezione).exclude(provincia='COMUNE NON ABBINATO')
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
    cand_naz = _candidati(RisultatoCandidato.objects.filter(elezione=elezione))
    cand_loc = _candidati(RisultatoCandidato.objects.filter(elezione=elezione, territorio=scelto)) if scelto else None
    return render(request, 'analisi/risultato_elezione.html', {
        'cand_naz': cand_naz, 'cand_loc': cand_loc, 'elezione': elezione, 'tipo_slug': _slug_tipo(elezione.tipo), 'tipo_nome': TIPI_RISULTATI[_slug_tipo(elezione.tipo)][1],
        'nazionale': nazionale, 'aff_naz': aff_naz, 'territori': territori,
        'scelto': scelto, 'locale': locale, 'aff_loc': aff_loc,
        'affl_naz_pct': round(100 * aff_naz['v'] / aff_naz['e'], 2) if aff_naz['e'] else None,
        'affl_loc_pct': round(100 * aff_loc.votanti / aff_loc.elettori, 2) if aff_loc and aff_loc.elettori else None,
    })
