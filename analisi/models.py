from django.db import models
from django.urls import reverse


class Partito(models.Model):
    SINISTRA, CENTRO, DESTRA = 'SX', 'CE', 'DX'
    SCHIERAMENTI = [(SINISTRA, 'Sinistra'), (CENTRO, 'Centro'), (DESTRA, 'Destra')]

    nome = models.CharField(max_length=120)
    sigla = models.CharField(max_length=20)
    slug = models.SlugField(unique=True)
    schieramento = models.CharField(max_length=2, choices=SCHIERAMENTI)
    logo = models.ImageField(upload_to='loghi/', blank=True)
    ordine = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordine', 'nome']
        verbose_name_plural = 'partiti'

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse('partito', args=[self.slug])


class Programma(models.Model):
    ITALIANO, EUROPEO = 'IT', 'EU'
    AMBITI = [(ITALIANO, 'Italiano'), (EUROPEO, 'Europeo')]

    partito = models.ForeignKey(Partito, on_delete=models.CASCADE, related_name='programmi')
    titolo = models.CharField(max_length=200)
    anno = models.PositiveSmallIntegerField()
    ambito = models.CharField(max_length=2, choices=AMBITI, default=ITALIANO)
    documento = models.FileField(upload_to='programmi/', blank=True, help_text='PDF del programma originale')

    class Meta:
        ordering = ['-anno', 'titolo']
        verbose_name_plural = 'programmi'

    def __str__(self):
        return f'{self.titolo} ({self.anno})'

    def get_absolute_url(self):
        return reverse('programma', args=[self.pk])


class Commento(models.Model):
    BASSA, MEDIA, ALTA = 'B', 'M', 'A'
    FATTIBILITA = [(BASSA, 'Bassa'), (MEDIA, 'Media'), (ALTA, 'Alta')]

    programma = models.ForeignKey(Programma, on_delete=models.CASCADE, related_name='commenti')
    ordine = models.PositiveSmallIntegerField(default=0)
    titolo = models.CharField(max_length=200)
    pagina = models.PositiveSmallIntegerField(null=True, blank=True, help_text='Pagina del PDF dove si trova il punto')
    promessa = models.TextField('Cosa promette')
    precedenti = models.TextField('Precedenti storici', blank=True)
    fondi = models.TextField('Fondi: credibilità e stabilità', blank=True)
    rischi_benefici = models.TextField('Rischi e benefici', blank=True)
    fattibilita = models.CharField(max_length=1, choices=FATTIBILITA)
    motivazione = models.CharField('Motivazione del giudizio', max_length=300, blank=True)

    class Meta:
        ordering = ['ordine', 'pagina']
        verbose_name_plural = 'commenti'

    def __str__(self):
        return self.titolo
