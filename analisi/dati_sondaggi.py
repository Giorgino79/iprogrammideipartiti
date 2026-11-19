"""Intenzioni di voto: Supermedia YouTrend/Agi del 19 novembre 2026.

Media ponderata di nove sondaggi di sei istituti, rilevati dal 5 al 18 novembre 2026.
Dati letti dall'articolo di Lettera43 che riporta la Supermedia (la pagina di Youtrend non è stata aperta
direttamente) e confrontati con l'ultimo sondaggio SWG per La7 del 16 novembre. Da aggiornare a ogni nuova Supermedia.
"""
from datetime import date

DATA = date(2026, 11, 19)
FONTE = 'Supermedia YouTrend/Agi, 19 novembre 2026 (sondaggi dal 5 al 18 novembre)'
URL = 'https://www.lettera43.it/sondaggi-politici-supermedia-19-novembre-campo-largo-avanti-due-punti-centrodestra/'

VALORI = {
    'fdi': '27.8',
    'pd': '20.5',
    'm5s': '12.8',
    'forza-italia': '7.1',
    'futuro-nazionale': '6.5',
    'avs': '6.2',
    'lega': '5.6',
    'azione': '3.2',
    'italia-viva': '2.4',
    'piu-europa': '1.2',
    'noi-moderati': '1.0',
    'sud-chiama-nord': '1.0',
}

# Partiti presenti nei sondaggi e non ancora considerati (programmi da cercare)
NUOVI_PARTITI = [
    dict(nome='Noi Moderati', sigla='NM', slug='noi-moderati', logo='nm.png', schieramento='DX', ordine=11),
    dict(nome='+Europa', sigla='+E', slug='piu-europa', logo='pe.png', schieramento='CE', ordine=12),
    dict(nome='Sud chiama Nord', sigla='SCN', slug='sud-chiama-nord', logo='scn.png', schieramento='CE', ordine=13),
]

# Coalizioni: non hanno una percentuale propria e non compaiono nell'header dei partiti
COALIZIONI = ['centrodestra']
