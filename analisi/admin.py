from django.contrib import admin

from .models import Commento, Partito, Programma


@admin.register(Partito)
class PartitoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'sigla', 'schieramento', 'ordine']
    prepopulated_fields = {'slug': ('sigla',)}


class CommentoInline(admin.StackedInline):
    model = Commento
    extra = 0


@admin.register(Programma)
class ProgrammaAdmin(admin.ModelAdmin):
    list_display = ['titolo', 'partito', 'anno', 'ambito']
    list_filter = ['partito', 'ambito']
    inlines = [CommentoInline]
