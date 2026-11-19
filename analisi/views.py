from django.db.models import Count
from django.shortcuts import get_object_or_404, render

from .models import Commento, Partito, Programma, Tema


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
