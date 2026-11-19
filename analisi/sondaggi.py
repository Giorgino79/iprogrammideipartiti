"""Lettura delle intenzioni di voto dalla tabella degli aggregatori di Wikipedia.

La prima riga della tabella "Polling aggregator" della pagina inglese
"Opinion polling for the next Italian general election" riporta la Supermedia
YouTrend/Agi. La pagina si legge con l'API di MediaWiki (testo wiki), non con lo scraping dell'HTML.
"""
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime

PAGINA = 'Opinion polling for the next Italian general election'
API = 'https://en.wikipedia.org/w/api.php'
USER_AGENT = 'OsservatorioProgrammiPartiti/1.0 (aggiornamento sondaggi)'
AGGREGATORE = 'Youtrend'
URL_FONTE = 'https://www.youtrend.it/la-supermedia/'

# sigla nell'intestazione della tabella -> slug del partito
SIGLE = {
    'FdI': 'fdi', 'PD': 'pd', 'M5S': 'm5s', 'Lega': 'lega', 'FI': 'forza-italia', 'A': 'azione',
    'IV': 'italia-viva', 'AVS': 'avs', '+E': 'piu-europa', 'NM': 'noi-moderati', 'FN': 'futuro-nazionale',
}


class ErroreSondaggi(Exception):
    pass


def scarica_wikitext():
    url = API + '?' + urllib.parse.urlencode(
        dict(action='parse', page=PAGINA, prop='wikitext', format='json', formatversion=2))
    richiesta = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(richiesta, timeout=60) as r:
        return json.load(r)['parse']['wikitext']


def leggi_supermedia(wikitext):
    """Restituisce (data, {slug: percentuale}) dalla riga YouTrend della prima tabella."""
    inizio = wikitext.find('{|')
    fine = wikitext.find('\n|}', inizio)
    if inizio < 0 or fine < 0:
        raise ErroreSondaggi('tabella degli aggregatori non trovata')
    tabella = wikitext[inizio:fine]

    # colonne dei partiti, nell'ordine in cui compaiono nell'intestazione
    colonne = re.findall(r'^!\s*style="width:35px;"\s*\|\[\[[^\]|]*\|([^\]]+)\]\]', tabella, re.M)
    if len(colonne) < 8:
        raise ErroreSondaggi('intestazione della tabella non riconosciuta')

    riga = next((r for r in tabella.split('\n|-') if re.match(r'\s*\|\s*' + AGGREGATORE + r'\s*\n', r)), None)
    if riga is None:
        raise ErroreSondaggi('riga %s non trovata' % AGGREGATORE)

    riga = re.sub(r'<ref.*?</ref>', '', riga, flags=re.S)
    data = re.search(r'\n\|\s*(\d{1,2} \w{3} \d{4})\s*\n', riga)
    if not data:
        raise ErroreSondaggi('data della riga non trovata')
    data_testo = data.group(1)
    data = datetime.strptime(data_testo, '%d %b %Y').date()

    sud = re.search(r'(\d+\.\d)\s*[–-]\s*\[\[South calls North\]\]', riga)
    resto = riga[riga.find(data_testo):]
    resto = re.sub(r'\{\{Hidden\|.*?\}\}\s*(?=\n)', '', resto, flags=re.S)
    numeri = re.findall(r'(?<![\d.])(\d{1,2}\.\d)(?![\d.])', resto)
    if len(numeri) < len(colonne):
        raise ErroreSondaggi('numeri insufficienti nella riga (%d su %d)' % (len(numeri), len(colonne)))

    valori = {}
    for sigla, numero in zip(colonne, numeri):
        slug = SIGLE.get(sigla.strip())
        if slug:
            valori[slug] = float(numero)
    if sud:
        valori['sud-chiama-nord'] = float(sud.group(1))
    return data, valori


def controlla(valori):
    """Controlli di buon senso: meglio non aggiornare che scrivere dati sbagliati."""
    if len(valori) < 10:
        raise ErroreSondaggi('troppi pochi partiti letti (%d)' % len(valori))
    if any(not 0 < v < 60 for v in valori.values()):
        raise ErroreSondaggi('percentuale fuori dai limiti: %s' % valori)
    if sum(valori.values()) > 100:
        raise ErroreSondaggi('somma oltre il 100%%: %.1f' % sum(valori.values()))
