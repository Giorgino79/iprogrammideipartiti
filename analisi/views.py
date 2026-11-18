from django.shortcuts import get_object_or_404, render

from .models import Partito, Programma


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
