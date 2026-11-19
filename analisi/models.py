from django.core.validators import MaxValueValidator, MinValueValidator
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


class Tema(models.Model):
    nome = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    ordine = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordine', 'nome']
        verbose_name_plural = 'temi'

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse('confronto_tema', args=[self.slug])


def _voto(descrizione):
    return models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)], help_text=descrizione)


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
    fattibilita = models.CharField(max_length=1, choices=FATTIBILITA, blank=True,
                                   help_text='Vecchio giudizio a tre livelli: non più mostrato')
    tema = models.ForeignKey('Tema', null=True, blank=True, on_delete=models.SET_NULL, related_name='commenti')
    voto_fattibilita = _voto('1-5: 1 = serve l\'unanimità UE o una riforma costituzionale; 5 = già realizzata o realizzabile subito')
    voto_copertura = _voto('1-5: 1 = nessuna copertura e costo molto alto; 5 = coperta in modo credibile o senza costo')
    voto_esiti = _voto('1-5: 1 = tentativi simili falliti o con effetti negativi; 5 = esiti positivi')
    voto_chiarezza = _voto('1-5: 1 = proposta generica; 5 = misura precisa, con numeri e tempi')
    voto_rischi = _voto('1-5: 1 = rischi alti; 5 = rischi bassi')
    costo = models.CharField('Costo approssimativo', max_length=200, blank=True)
    motivazione = models.CharField('Motivazione del giudizio', max_length=300, blank=True)

    class Meta:
        ordering = ['ordine', 'pagina']
        verbose_name_plural = 'commenti'

    def __str__(self):
        return self.titolo

    VOTI = [('voto_fattibilita', 'Fattibilità'), ('voto_copertura', 'Copertura'), ('voto_esiti', 'Esiti storici'),
            ('voto_chiarezza', 'Chiarezza'), ('voto_rischi', 'Rischi (5 = bassi)')]

    @property
    def voti(self):
        return [(nome, getattr(self, campo)) for campo, nome in self.VOTI]

    @property
    def media(self):
        v = [getattr(self, c) for c, _ in self.VOTI if getattr(self, c)]
        return round(sum(v) / len(v), 1) if v else None

    @property
    def da_verificare(self):
        return '[verificare]' in ' '.join([self.precedenti, self.fondi, self.rischi_benefici, self.motivazione, self.promessa])
