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


# ---------------------------------------------------------------- referendum
COSTITUZIONALI = {'20011007', '20060625', '20161204', '20200920', '20260322'}
TITOLI_2022 = {  # titoli sintetici: i file del 2022 non riportano il testo dei quesiti
    '1': "Abrogazione delle norme sull'incandidabilità e decadenza dalle cariche dopo una condanna (decreto Severino)",
    '2': 'Limitazione delle misure cautelari: abrogazione parziale',
    '3': 'Separazione delle funzioni dei magistrati giudicanti e requirenti',
    '4': 'Valutazione dei magistrati: partecipazione dei membri laici ai consigli giudiziari',
    '5': 'Elezione dei componenti togati del CSM: abolizione delle liste di presentatori',
}
TITOLO_2026 = 'Referendum costituzionale: ordinamento giurisdizionale e istituzione della Corte disciplinare'


def titolo(t):
    t = pulisci(t).replace(' ? ', ' - ').replace('?A', "'A").replace("L?", "L'")
    return t.capitalize() if t.isupper() else t


def _riga_ref(dati, reg, prov, num, quesito, elettori, votanti, bianche, si, no):
    d = dati.setdefault((reg, prov, num), dict(quesito=quesito, elettori=0, votanti=0, bianche=0, si=0, no=0))
    d['elettori'] += elettori
    d['votanti'] += votanti
    d['bianche'] += bianche
    d['si'] += si
    d['no'] += no


def _ref_vecchi(percorso):
    """Referendum 2000-2020: sì e no per quesito, per provincia (2000-2006) o per comune (dal 2009)."""
    dati = {}
    with open(percorso, encoding='latin-1', newline='') as f:
        for r in csv.DictReader(f, delimiter=';'):
            _riga_ref(dati, regione(r['REGIONE']), provincia(r['PROVINCIA']), pulisci(r['NUM_REFERENDUM']),
                      titolo(r['QUESITO']), intero(r['ELETTORI']), intero(r['VOTANTI']),
                      intero(_colonna(r, ('SKBIANCHE', 'SCHEDE_BIANCHE'))), intero(r['NUMVOTISI']), intero(r['NUMVOTINO']))
    return dati


def _ref_2022(cartella):
    dati = {}
    for q in '12345':
        percorso = next(Path(cartella).glob(f'*Scrutini_quesito{q}.csv'))
        with open(percorso, encoding='cp1252', errors='replace', newline='') as f:
            for r in csv.DictReader(f, delimiter=';'):
                _riga_ref(dati, regione(r['REGIONE']), provincia(r['PROVINCIA']), q, TITOLI_2022[q],
                          intero(r['ELETTORI']), intero(r['VOTANTI']), intero(r['SCHEDE_BIANCHE']),
                          intero(r['VOTI_SI']), intero(r['VOTI_NO']))
    return dati


def _ref_2025(percorso):
    dati = {}
    with open(percorso, encoding='utf-8-sig', errors='replace', newline='') as f:
        for r in csv.DictReader(f, delimiter=';'):
            validi, si = intero(r['VOTIVALIDI']), intero(r['VOTIVALIDI_SI'])
            _riga_ref(dati, regione(r['REGIONE']), provincia(r['PROVINCIA']), pulisci(r['NUMQUESITO']),
                      titolo(r['QUESITOREFERENDUM']), intero(r['ELETTORITOT']), intero(r['VOTANTITOT']),
                      intero(r['SKBIANCHE']), si, validi - si)
    return dati


def _ref_2026(percorso):
    dati = {}
    with open(percorso, encoding='utf-8-sig', errors='replace', newline='') as f:
        f.readline()  # la prima riga contiene solo il titolo del quesito
        for r in csv.DictReader(f, delimiter=';'):
            validi, si = intero(r['VOTIVALIDI']), intero(r['VOTISI'])
            _riga_ref(dati, regione(r['REG']), provincia(r['PROV']), '1', TITOLO_2026, intero(r['ELETTORITOTALI']),
                      intero(r['NUMVOTANTITOTALI']), intero(r['SKBIANCHE']), si, validi - si)
    return dati


def scrivi_referendum(data, dati, costituzionale):
    USCITA.mkdir(exist_ok=True)
    with open(USCITA / f'referendum_{data}.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['regione', 'provincia', 'num', 'quesito', 'tipo', 'elettori', 'votanti', 'bianche', 'si', 'no'])
        for (reg, prov, num), d in sorted(dati.items(), key=lambda kv: (kv[0][2].zfill(3), kv[0][0], kv[0][1])):
            w.writerow([reg, prov, num, d['quesito'], 'C' if costituzionale else 'A',
                        d['elettori'], d['votanti'], d['bianche'], d['si'], d['no']])


def prepara_referendum(cartella):
    """cartella: contiene le cartelle 20000521, ..., 20260322 con i file estratti dagli archivi ZIP."""
    cartella = Path(cartella)
    risultati = {}
    for data in ['20000521', '20011007', '20030615', '20050612', '20060625', '20090621', '20110612',
                 '20160417', '20161204', '20200920']:
        risultati[data] = _ref_vecchi(cartella / data / f'referendum-{data}.txt')
    risultati['20220612'] = _ref_2022(cartella / '20220612')
    risultati['20250608'] = _ref_2025(cartella / '20250608' / 'referendum-20250608' / 'Referendum_LivComune.csv')
    risultati['20260322'] = _ref_2026(cartella / '20260322' / 'referendum-20260322' / 'Referendum2026_OpenData_LivComune.csv')
    for data, dati in risultati.items():
        scrivi_referendum(data, dati, data in COSTITUZIONALI)
    return risultati
