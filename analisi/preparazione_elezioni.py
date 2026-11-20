"""Prepara i risultati elettorali: somma i dati per comune/sezione del Ministero dell'Interno in provincia.

Fonte: Ministero dell'Interno, Eligendo - Archivio storico, sezione Open data
(https://elezionistorico.interno.gov.it/eligendo/opendata.php). I file grezzi sono molto grandi e non stanno nel
progetto: da questi si ricavano due piccoli CSV per elezione, in analisi/dati_elezioni/.
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

USCITA = Path(__file__).resolve().parent / 'dati_elezioni'

REGIONI = {
    'ABRUZZI': 'ABRUZZO', "VALLE D'AOSTA": "VALLE D'AOSTA", "VALLE D'AOSTA/VALLEE D'AOSTE": "VALLE D'AOSTA",
    'FRIULI-VENEZIA GIULIA': 'FRIULI-VENEZIA GIULIA', 'FRIULI VENEZIA GIULIA': 'FRIULI-VENEZIA GIULIA',
    'TRENTINO-ALTO ADIGE': 'TRENTINO-ALTO ADIGE', 'TRENTINO ALTO ADIGE': 'TRENTINO-ALTO ADIGE',
    "TRENTINO-ALTO ADIGE/SUDTIROL": 'TRENTINO-ALTO ADIGE',
}


def pulisci(testo):
    return re.sub(r'\s+', ' ', (testo or '').strip())


def regione(r):
    r = pulisci(r).upper()
    return REGIONI.get(r, r)


GRAFIE_PROVINCE = {  # stessa provincia scritta in modo diverso negli anni
    'FORLÌ-CESENA': "FORLI'-CESENA", "REGGIO NELL' EMILIA": "REGGIO NELL'EMILIA", 'REGGIO EMILIA': "REGGIO NELL'EMILIA",
}


def provincia(p):
    p = pulisci(p).upper().replace("’", "'")
    return GRAFIE_PROVINCE.get(p, p)


def intero(v):
    v = pulisci(str(v)).replace('.', '')
    return int(v) if v else 0


# nomi delle colonne nei file per comune di ogni elezione
COLONNE_VECCHIE = dict(regione='REGIONE', provincia='PROVINCIA', comune='COMUNE', elettori='ELETTORI',
                       votanti='VOTANTI', lista='LISTA', voti=('VOTI_LISTA', 'VOTILISTA'),
                       bianche=('SCHEDE_BIANCHE', 'SCHEDEBIANCHE'))
COLONNE_2024 = dict(regione='DESCREGIONE', provincia='DESCPROVINCIA', comune='DESCCOMUNE', elettori='ELETTORI',
                    votanti='VOTANTI', lista='DESCLISTA', voti=('NUMVOTI',), bianche=('NUMSCHEDEBIANCHE',))


def _colonna(riga, nomi):
    nomi = (nomi,) if isinstance(nomi, str) else nomi
    for n in nomi:
        if riga.get(n) not in (None, ''):
            return riga[n]
    return ''


def _legge_comuni(percorso, col, codifica='latin-1'):
    """Una riga per comune e lista: somma i voti per provincia e conta elettori e votanti una volta per comune."""
    voti = defaultdict(int)
    affluenza = {}
    visti = set()
    with open(percorso, encoding=codifica, errors='replace', newline='') as f:
        for riga in csv.DictReader(f, delimiter=';'):
            reg, prov = regione(riga[col['regione']]), provincia(riga[col['provincia']])
            com = pulisci(riga[col['comune']])
            voti[(reg, prov, pulisci(riga[col['lista']]))] += intero(_colonna(riga, col['voti']))
            if (reg, prov, com) not in visti:  # elettori e votanti si ripetono su ogni lista del comune
                visti.add((reg, prov, com))
                a = affluenza.setdefault((reg, prov), [0, 0, 0])
                a[0] += intero(riga[col['elettori']])
                a[1] += intero(riga[col['votanti']])
                a[2] += intero(_colonna(riga, col['bianche']))
    return voti, affluenza


def scrivi(nome, voti, affluenza):
    USCITA.mkdir(exist_ok=True)
    with open(USCITA / f'{nome}_liste.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['regione', 'provincia', 'lista', 'voti'])
        for (reg, prov, lista), n in sorted(voti.items()):
            if n:
                w.writerow([reg, prov, lista, n])
    with open(USCITA / f'{nome}_affluenza.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['regione', 'provincia', 'elettori', 'votanti', 'bianche'])
        for (reg, prov), (e, v, b) in sorted(affluenza.items()):
            w.writerow([reg, prov, e, v, '' if b is None else b])


def prepara_europee(cartella):
    """cartella: contiene europee-2004*.txt ... e la cartella Europee-20240609/ (file estratti dagli archivi ZIP)."""
    cartella = Path(cartella)
    risultati = {}
    for anno, nome in [(2004, 'europee-20040612.txt'), (2009, 'europee-20090607.txt'),
                       (2014, 'europee-20140525.txt'), (2019, 'europee-20190526.txt')]:
        risultati[anno] = _legge_comuni(cartella / nome, COLONNE_VECCHIE)
    risultati[2024] = _legge_comuni(cartella / 'Europee-20240609' / 'EUROPEE_SCRUTINI&LISTE_ITALIA_LivComune.csv',
                                    COLONNE_2024, codifica='cp1252')
    for anno, (voti, affluenza) in risultati.items():
        scrivi(f'europee_{anno}', voti, affluenza)
    return risultati
