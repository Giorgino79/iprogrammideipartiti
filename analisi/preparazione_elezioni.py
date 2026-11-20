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
    if r.startswith('TRENTINO'):
        return 'TRENTINO-ALTO ADIGE'
    if r.startswith("VALLE D'AOSTA"):
        return "VALLE D'AOSTA"
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


# ------------------------------------------------------------------ politiche
import unicodedata  # noqa: E402


def norma_comune(nome):
    n = unicodedata.normalize('NFKD', nome or '')
    n = ''.join(c for c in n if not unicodedata.combining(c)).upper()
    return re.sub(r'\s+', ' ', re.sub(r"[’'`\-./]", ' ', n)).strip()


def regione_da_circoscrizione(c):
    """'LOMBARDIA 1' -> 'LOMBARDIA'"""
    return regione(re.sub(r'\s*\d+\s*$', '', pulisci(c)))


def mappe_comuni(cartella_europee):
    """(anno europee) -> {(regione, comune normalizzato): provincia, oppure None se il nome è ambiguo}."""
    c = Path(cartella_europee)
    sorgenti = {2004: (c / 'europee-20040612.txt', COLONNE_VECCHIE, 'latin-1'),
                2009: (c / 'europee-20090607.txt', COLONNE_VECCHIE, 'latin-1'),
                2014: (c / 'europee-20140525.txt', COLONNE_VECCHIE, 'latin-1'),
                2019: (c / 'europee-20190526.txt', COLONNE_VECCHIE, 'latin-1'),
                2024: (c / 'Europee-20240609' / 'EUROPEE_SCRUTINI&LISTE_ITALIA_LivComune.csv', COLONNE_2024, 'cp1252')}
    mappe = {}
    for anno, (percorso, col, cod) in sorgenti.items():
        visti = {}
        with open(percorso, encoding=cod, errors='replace', newline='') as f:
            for r in csv.DictReader(f, delimiter=';'):
                k = (regione(r[col['regione']]), norma_comune(r[col['comune']]))
                p = provincia(r[col['provincia']])
                visti[k] = p if visti.get(k, p) == p else None
        mappe[anno] = visti
    return mappe


def _num(v):
    v = pulisci(str(v)).replace(' ', '')
    if not v:
        return 0
    if ',' in v:
        v = v.split(',')[0]
    return int(v.replace('.', ''))


def _righe_politiche(percorso, tipo, codifica='latin-1'):
    """Restituisce tuple (regione, provincia o None, comune, chiave comune, elettori, votanti, bianche, lista, voti)."""
    with open(percorso, encoding=codifica, errors='replace', newline='') as f:
        for r in csv.DictReader(f, delimiter=';'):
            if tipo in ('it_prov', 'taa_2013'):  # 2006-2013: Camera e Senato, di solito con la provincia
                reg = regione_da_circoscrizione(r.get('CIRCOSCRIZIONE') or r.get('REGIONE'))
                prov = provincia(r['PROVINCIA']) if r.get('PROVINCIA') else None
                comune = pulisci(r['COMUNE'])
                yield (reg, prov, comune, (r.get('COLLEGIO') if prov is None else prov, comune),
                       _num(r.get('ELETTORI') or r.get('ELETTORI_TOTALI')),
                       _num(r.get('VOTANTI') or r.get('VOTANTI_TOTALI')), _num(r['SCHEDE_BIANCHE']), pulisci(r['LISTA']),
                       _num(r.get('VOTILISTA') or r.get('VOTI_LISTA')))
            elif tipo == 'camera_2001':
                yield (regione_da_circoscrizione(r['CIRCOSCRIZIONE']), None, pulisci(r['COMUNE']),
                       (pulisci(r['COLLEGIO']), pulisci(r['COMUNE'])), _num(r['ELETTORI']), _num(r['VOTANTI']),
                       _num(r['SCHEDE_BIANCHE']), pulisci(r['LISTA']), _num(r['VOTI_LISTA']))
            elif tipo == 'senato_2001':
                yield (regione(r['REGIONE']), None, pulisci(r['COMUNE']), (pulisci(r['COLLEGIO']), pulisci(r['COMUNE'])),
                       _num(r['ELETTORI']), _num(r['VOTANTI']), _num(r['SCHEDE_BIANCHE']), pulisci(r['LISTA']),
                       _num(r['VOTI_LISTA']))
            elif tipo == 'camera_2018':
                yield (regione_da_circoscrizione(r['CIRCOSCRIZIONE']), None, pulisci(r['COMUNE']),
                       (pulisci(r['COLLEGIOUNINOMINALE']), pulisci(r['COMUNE'])), _num(r['ELETTORI']),
                       _num(r['VOTANTI']), _num(r['SCHEDE_BIANCHE']), pulisci(r['LISTA']), _num(r['VOTI_LISTA']))
            elif tipo == 'senato_2018':
                yield (regione(r['REGIONE']), None, pulisci(r['COMUNE']),
                       (pulisci(r['COLLEGIOUNINOMINALE']), pulisci(r['COMUNE'])), _num(r['ELETTORI']),
                       _num(r['VOTANTI']), _num(r['SCHEDE_BIANCHE']), pulisci(r['LISTA']), _num(r['VOTI_LISTA']))
            elif tipo == '2022':
                yield (regione_da_circoscrizione(r['CIRC-REG']), None, pulisci(r['COMUNE']),
                       (pulisci(r['COLLUNINOM']), pulisci(r['COMUNE'])), _num(r['ELETTORITOT']),
                       _num(r['VOTANTITOT']), _num(r['SKBIANCHE']), pulisci(r['DESCRLISTA']), _num(r['VOTILISTA']))


# camera/senato, anno -> [(file, tipo, codifica)], anni delle europee da cui ricavare le province
SORGENTI_POLITICHE = {
    ('camera', 2001): ([('camera-20010513/camera-20010513_Proporzionale.txt', 'camera_2001', 'latin-1')], [2004, 2009]),
    ('camera', 2006): ([('camera-20060409/camera_italia-20060409.txt', 'it_prov', 'latin-1')], []),
    ('camera', 2008): ([('camera-20080413/camera_italia-20080413.txt', 'it_prov', 'latin-1')], []),
    ('camera', 2013): ([('camera-20130224/camera_italia-20130224.txt', 'it_prov', 'latin-1')], []),
    ('camera', 2018): ([('camera-20180304/Camera2018_livComune.txt', 'camera_2018', 'latin-1')], [2019, 2014, 2024]),
    ('camera', 2022): ([('camera-20220925/camera2022_Italia_LivComune.csv', '2022', 'latin-1')], [2024, 2019]),
    ('senato', 2001): ([('senato-20010513/senato-20010513.txt', 'senato_2001', 'latin-1')], [2004, 2009]),
    ('senato', 2006): ([('senato-20060409/senato_italia-20060409.txt', 'it_prov', 'latin-1'),
                        ('senato-20060409/senato_vaosta_trentino-20060409.txt', 'taa_2013', 'latin-1')], [2009, 2004]),
    ('senato', 2008): ([('senato-20080413/senato_italia-20080413.txt', 'it_prov', 'latin-1'),
                        ('senato-20080413/senato_vaosta_trentino_20080413.txt', 'taa_2013', 'latin-1')], []),
    ('senato', 2013): ([('senato-20130224/senato_italia-20130224.txt', 'it_prov', 'latin-1'),
                        ('senato-20130224/senato_vaosta_trentino-20130224.txt', 'taa_2013', 'latin-1')], []),
    ('senato', 2018): ([('senato-20180304/Senato2018_livComune.txt', 'senato_2018', 'latin-1')], [2019, 2014, 2024]),
    ('senato', 2022): ([('senato-20220925/Senato_Italia_LivComune.csv', '2022', 'latin-1')], [2024, 2019]),
}
NON_ASSEGNATA = 'COMUNE NON ABBINATO'


def _compatte(mappa):
    """Stessa mappa, ma con i nomi senza spazi (SAN REMO = SANREMO)."""
    out = {}
    for (reg, nome), prov in mappa.items():
        k = (reg, nome.replace(' ', ''))
        out[k] = prov if out.get(k, prov) == prov else None
    return out


def trova_provincia(reg, comune, anni, mappe, compatte):
    """Cerca la provincia di un comune; le zone di una città ('Roma - Trieste', 'Milano 1') cercano il nome della città."""
    nome = norma_comune(comune)
    nome = re.sub(r'^PARTE DI COMUNE ', '', nome)
    nome = re.sub(r'\s+\d+$', '', nome)
    parole = nome.split()
    candidati = [' '.join(parole[:i]) for i in range(len(parole), 0, -1)]
    for a in anni:
        for c in candidati:
            p = mappe[a].get((reg, c)) or compatte[a].get((reg, c.replace(' ', '')))
            if p:
                return p
    return None


def prepara_politiche(cartella, cartella_europee):
    cartella = Path(cartella)
    mappe = mappe_comuni(cartella_europee)
    compatte = {a: _compatte(m) for a, m in mappe.items()}
    esito = {}
    for (camera_senato, anno), (file_tipo, anni_mappa) in SORGENTI_POLITICHE.items():
        voti = defaultdict(int)
        affluenza = {}
        liste_viste = set()
        aff_viste = set()
        non_abbinati = 0
        totale = 0
        for rel, tipo, cod in file_tipo:
            for reg, prov, comune, chiave, el, vo, bi, lista, n in _righe_politiche(cartella / rel, tipo, cod):
                if prov is None:
                    prov = trova_provincia(reg, comune, anni_mappa, mappe, compatte) or NON_ASSEGNATA
                if (chiave, lista) not in liste_viste:  # lo stesso comune compare su più righe (candidati)
                    liste_viste.add((chiave, lista))
                    voti[(reg, prov, lista)] += n
                    totale += n
                    if prov == NON_ASSEGNATA:
                        non_abbinati += n
                if chiave not in aff_viste:
                    aff_viste.add(chiave)
                    a = affluenza.setdefault((reg, prov), [0, 0, 0])
                    a[0] += el
                    a[1] += vo
                    a[2] += bi
        scrivi(f'politiche_{camera_senato}_{anno}', voti, affluenza)
        esito[(camera_senato, anno)] = (voti, affluenza, non_abbinati, totale)
    return esito


# ------------------------------------------------------------------ lettura di file Excel (xlsx)
def righe_xlsx(percorso, foglio=1):
    """Legge un foglio xlsx senza librerie esterne: restituisce le righe come liste di testi."""
    import xml.etree.ElementTree as ET
    import zipfile
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(percorso) as z:
        condivise = []
        if 'xl/sharedStrings.xml' in z.namelist():
            for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', ns):
                condivise.append(''.join(t.text or '' for t in si.iter('{%s}t' % ns['m'])))
        radice = ET.fromstring(z.read(f'xl/worksheets/sheet{foglio}.xml'))
        for riga in radice.iter('{%s}row' % ns['m']):
            valori = {}
            for c in riga.findall('m:c', ns):
                col = re.match(r'[A-Z]+', c.get('r')).group(0)
                v = c.find('m:v', ns)
                if v is None:
                    is_ = c.find('m:is', ns)
                    valori[col] = ''.join(t.text or '' for t in is_.iter('{%s}t' % ns['m'])) if is_ is not None else ''
                else:
                    valori[col] = condivise[int(v.text)] if c.get('t') == 's' else v.text
            if valori:
                n = max(len(k) * 26 + (ord(k[-1]) - 64) for k in valori)  # indice massimo di colonna
                yield valori


# ------------------------------------------------------------------ regionali
FORMATI_REGIONALI = {
    # nome: colonne (alias separati da |)
    'legacy': dict(reg='REGIONE', prov='PROVINCIA|provincia', comune='COMUNE', elettori='ELETTORI', votanti='VOTANTI',
                   bianche='SCHEDE_BIANCHE', cogn='COGNOME', nome='NOME', vc='VOTI_CANDIDATO|VOTICANDIDLEADER',
                   lista='LISTA', vl='VOTI_LISTA|VOTILISTA'),
    'csvreg': dict(reg='REG', prov='PROV', comune='COMUNE', elettori='ELETTORITOT', votanti='VOTANTITOT',
                   bianche='SKBIANCHE', cogn='COGNOME', nome='NOME', vc='VOTICANDIDATO', lista='DESCRLISTA', vl='VOTILISTA'),
    'nuovo2023': dict(reg='REGIONE', prov='PROVINCIA', comune='COMUNE', elettori='ELETTORITOT', votanti='VOTANTITOT',
                      bianche='SKBIANCHE', cogn='COGNOME', nome='NOME', vc='VOTICAND', lista='DESCRLISTA', vl='VOTILISTA'),
    'xlsx': dict(reg='REGIONE|REG', prov='PROVINCIA|PROV', comune='COMUNE', elettori='ELETTORI_TOT|ELETTORITOT',
                 votanti='VOTANTI_TOT|VOTANTITOT', bianche='SKBIANCHE', cogn='COGNOME', nome='NOME',
                 vc='VOTICAND|VOTICANDLEADER', lista='DESCRLISTA', vl='VOTILISTA'),
    'sezioni': dict(reg='REGIONE', prov='', comune='COMUNE', sezione='SEZIONE', elettori='ELETTORI_TOTALI',
                    votanti='VOTANTI_TOTALI', bianche='SCHEDE_BIANCHE', cogn='COGNOME_CANDIDATO', nome='NOME_CANDIDATO',
                    vc='VOTI_CANDIDATO', lista='LISTA', vl='VOTI_LISTA'),
    'comuni2025': dict(reg='REGIONE', prov='', comune='COMUNE', elettori='ELETTORI', votanti='VOTANTI',
                       bianche='SCHEDE_BIANCHE', cogn='COGNOME', nome='NOME', vc='VOTI_CANDIDATO', lista='LISTA',
                       vl='VOTI_LISTA'),
    'listecand': dict(reg='REGIONE', prov='PROVINCIA', comune='COMUNE', cogn='COGNOME', nome='NOME', vc='VOTICANDIDATO',
                      lista='DESCRLISTA', vl='VOTILISTA'),
    'scrutini2024': dict(reg='REGIONE', prov='PROVINCIA', comune='COMUNE', elettori='NUMELETTORI', votanti='VOTANTI',
                         bianche='SKBIANCHE'),
}

# data -> [(file, formato, codifica)]
FILE_REGIONALI = {
    '20000416': [('regionali-20000416/regionali-20000416.txt', 'legacy', 'latin-1')],
    '20010624': [('regionali-20010624/regionali-20010624.csv', 'csvreg', 'cp1252')],
    '20011111': [('regionali-20011111/regionali-20011111.txt', 'legacy', 'latin-1')],
    '20050403': [('regionali-20050403/regionali-20050403.txt', 'legacy', 'latin-1')],
    '20050417': [('regionali-20050417/regionali-20050417.txt', 'legacy', 'latin-1')],
    '20061105': [('regionali-20061105/regionali-20061105.txt', 'legacy', 'latin-1')],
    '20081214': [('regionali-20081214/regionali-20081214.txt', 'legacy', 'latin-1')],
    '20100328': [('regionali-20100328/regionali-20100328.txt', 'legacy', 'latin-1')],
    '20111016': [('regionali-20111016/regionali-20111016.xlsx', 'xlsx', None)],
    '20130224': [('regionali-20130224/regionali-20130224.txt', 'legacy', 'latin-1')],
    '20131117': [('regionali-20131117/regionali-20131117.txt', 'legacy', 'latin-1')],
    '20140525': [('regionali-20140525/regionali-20140525.txt', 'legacy', 'latin-1')],
    '20141123': [('regionali-20141123/regionali-20141123.txt', 'legacy', 'latin-1')],
    '20150531': [('regionali-20150531/regionali-20150531.txt', 'legacy', 'latin-1')],
    '20180304': [('regionali-20180304/regionali-20180304.txt', 'legacy', 'latin-1')],
    '20190210': [('regionali-20190210/regionali-20190210.txt', 'legacy', 'latin-1')],
    '20190324': [('regionali-20190324/regionali-20190324.txt', 'legacy', 'latin-1')],
    '20190526': [('regionali-20190526/regionali-20190526.txt', 'legacy', 'latin-1')],
    '20191027': [('regionali-20191027/regionali-20191027.txt', 'legacy', 'latin-1')],
    '20200126': [('regionali-20200126/regionali-20200126.txt', 'legacy', 'latin-1')],
    '20200920': [('regionali-20200920/Regionali_AltreRegioni_Scrutini.xlsx', 'xlsx', None),
                 ('regionali-20200920/RegionaliToscana_Scrutini.xlsx', 'xlsx', None)],
    '20211003': [('regionali-20211003/scrutini-20211003.txt', 'legacy', 'latin-1')],
    '20230212': [('regionali-20230212/regionali-20230212.csv', 'nuovo2023', 'cp1252')],
    '20240310': [('regionali-20240310/Liste&Candidati_10032024.txt|regionali-20240310/Scrutini_10032024.txt', 'duefile', 'cp1252')],
    '20240421': [('regionali-20240421/Liste&Candidati_21042024.txt|regionali-20240421/Scrutini_21042024.txt', 'duefile', 'cp1252')],
    '20240609': [('regionali-20240609/regionali-20240609.csv', 'csvreg', 'cp1252')],
    '20241027': [('regionali-20241027/Regionali_Liguria_2024_Scrutini.csv', 'sezioni', 'cp1252')],
    '20241117': [('regionali-20241117/Regionali_Umbria_ 2024_Scrutini.csv', 'sezioni', 'cp1252'),
                 ('regionali-20241117/Regionali_EmiliaRomagna_2024_Scrutini.csv', 'sezioni', 'cp1252')],
    '20251005': [('regionali-20251005/20251005_REGIONALI_CALABRIA_SCRUTINI.csv', 'comuni2025', 'cp1252')],
    '20251012': [('regionali-20251012/20251012_REGIONALI_TOSCANA_SCRUTINI.csv', 'comuni2025', 'cp1252')],
    '20251123': [('regionali-20251123/20251123_REGIONALI_SCRUTINI.csv', 'comuni2025', 'cp1252')],
}


def _alias(riga, nomi):
    for n in (nomi or '').split('|'):
        if n and riga.get(n) not in (None, ''):
            return riga[n]
    return ''


def _righe_dict(percorso, codifica):
    if str(percorso).endswith('.xlsx'):
        it = righe_xlsx(percorso)
        intestazione = None
        for valori in it:
            if intestazione is None:
                intestazione = {col: pulisci(v).upper() for col, v in valori.items()}
                continue
            yield {intestazione[col]: v for col, v in valori.items() if col in intestazione}
        return
    with open(percorso, encoding=codifica, errors='replace', newline='') as f:
        r = csv.DictReader(f, delimiter=';')
        r.fieldnames = [n.strip().upper() for n in r.fieldnames]
        yield from r


def _righe_regionali(cartella, spec, formato, codifica):
    col = FORMATI_REGIONALI.get(formato)
    if formato == 'duefile':
        liste, scrutini = spec.split('|')
        aff = {}
        for r in _righe_dict(cartella / scrutini, codifica):
            aff[(regione(r['REGIONE']), provincia(r['PROVINCIA']), pulisci(r['COMUNE']))] = (
                _num(r['NUMELETTORI']), _num(r['VOTANTI']), _num(r['SKBIANCHE']))
        for r in _righe_dict(cartella / liste, codifica):
            reg, prov, com = regione(r['REGIONE']), provincia(r['PROVINCIA']), pulisci(r['COMUNE'])
            el, vo, bi = aff.get((reg, prov, com), (0, 0, 0))
            yield (reg, prov, com, (reg, prov, com), el, vo, bi, pulisci(r['DESCRLISTA']), _num(r['VOTILISTA']),
                   pulisci(r['COGNOME']), pulisci(r['NOME']), _num(r['VOTICANDIDATO']))
        return
    for r in _righe_dict(cartella / spec, codifica):
        reg = regione(_alias(r, col['reg']))
        prov = provincia(_alias(r, col['prov'])) if col.get('prov') else None
        com = pulisci(_alias(r, col['comune']))
        unita = (reg, prov, com, pulisci(r.get(col.get('sezione', ''), '')) if col.get('sezione') else '')
        yield (reg, prov or None, com, unita, _num(_alias(r, col['elettori'])), _num(_alias(r, col['votanti'])),
               _num(_alias(r, col['bianche'])), pulisci(_alias(r, col['lista'])), _num(_alias(r, col['vl'])),
               pulisci(_alias(r, col['cogn'])), pulisci(_alias(r, col['nome'])), _num(_alias(r, col['vc'])))


def prepara_regionali(cartella, cartella_europee, solo=None):
    cartella = Path(cartella)
    mappe = mappe_comuni(cartella_europee)
    compatte = {a: _compatte(m) for a, m in mappe.items()}
    esito = {}
    for data, specifiche in FILE_REGIONALI.items():
        if solo and data not in solo:
            continue
        liste, candidati, affluenza = defaultdict(int), defaultdict(int), {}
        viste_l, viste_c, viste_u = set(), set(), set()
        non_abbinati = totale = 0
        for spec, formato, codifica in specifiche:
            for reg, prov, com, unita, el, vo, bi, lista, vl, cogn, nome, vc in _righe_regionali(cartella, spec, formato, codifica):
                if not prov:
                    prov = trova_provincia(reg, com, [2024, 2019, 2014], mappe, compatte) or NON_ASSEGNATA
                if lista and (unita, cogn, nome, lista) not in viste_l:
                    viste_l.add((unita, cogn, nome, lista))
                    liste[(reg, prov, lista)] += vl
                    totale += vl
                    if prov == NON_ASSEGNATA:
                        non_abbinati += vl
                if cogn and (unita, cogn, nome) not in viste_c:
                    viste_c.add((unita, cogn, nome))
                    candidati[(reg, prov, f'{cogn} {nome}'.strip())] += vc
                if unita not in viste_u:
                    viste_u.add(unita)
                    a = affluenza.setdefault((reg, prov), [0, 0, 0])
                    a[0] += el
                    a[1] += vo
                    a[2] += bi
        scrivi(f'regionali_{data}', liste, affluenza)
        with open(USCITA / f'regionali_{data}_candidati.csv', 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(['regione', 'provincia', 'candidato', 'voti'])
            for (reg, prov, cand), n in sorted(candidati.items()):
                if n:
                    w.writerow([reg, prov, cand, n])
        esito[data] = (liste, candidati, affluenza, non_abbinati, totale)
    return esito


# ------------------------------------------------------------------ comunali (grandi città)
CITTA = ['ROMA', 'MILANO', 'TORINO', 'BOLOGNA', 'NAPOLI']
DATE_COMUNALI = ['20010513', '20040612', '20060528', '20080413', '20090607', '20110515', '20130526', '20160605', '20211003']


def prepara_comunali(cartella):
    """Una riga per elezione e città: sindaco e liste per turno. Scrive comunali_<città>_<data>.csv."""
    cartella = Path(cartella)
    risultati = {}
    for data in DATE_COMUNALI:
        percorso = cartella / data / f'comunali-{data}.txt'
        dati = {c: dict(cand={}, liste=defaultdict(int), aff={}, righe=set(), regione='') for c in CITTA}
        with open(percorso, encoding='latin-1', errors='replace', newline='') as f:
            r = csv.DictReader(f, delimiter=';')
            r.fieldnames = [n.strip().upper() for n in r.fieldnames]
            for riga in r:
                com = pulisci(riga['COMUNE']).upper()
                if com not in dati or pulisci(riga['PROVINCIA']).upper() != com:
                    continue
                d = dati[com]
                d['regione'] = regione(riga['REGIONE'])
                turno = pulisci(riga['TURNO']) or '1'
                cogn, nome = pulisci(riga['COGNOME']), pulisci(riga['NOME'])
                voti_c = _num(_alias(riga, 'VOTI_CANDIDATO|VOTICANDIDSINDACO'))
                lista = pulisci(_alias(riga, 'LISTA|DESCRLISTA'))
                voti_l = _num(_alias(riga, 'VOTI_LISTA|VOTILISTA'))
                d['cand'].setdefault((turno, f'{cogn} {nome}'.strip()), voti_c)
                if turno == '1' and lista and (cogn, nome, lista) not in d['righe']:
                    d['righe'].add((cogn, nome, lista))
                    d['liste'][lista] += voti_l
                if turno not in d['aff']:
                    d['aff'][turno] = (_num(_alias(riga, 'ELETTORI|ELETTORITOT')), _num(_alias(riga, 'VOTANTI|VOTANTITOT')),
                                       _num(_alias(riga, 'SCHEDE_BIANCHE|SKBIANCHE')))
        for com, d in dati.items():
            if not d['cand']:
                continue
            USCITA.mkdir(exist_ok=True)
            with open(USCITA / f'comunali_{com.lower()}_{data}.csv', 'w', encoding='utf-8', newline='') as f:
                w = csv.writer(f)
                w.writerow(['tipo', 'turno', 'nome', 'voti', 'elettori', 'votanti', 'bianche', 'regione'])
                for turno, (e, v, b) in sorted(d['aff'].items()):
                    w.writerow(['A', turno, '', '', e, v, b, d['regione']])
                for (turno, nome), n in sorted(d['cand'].items()):
                    w.writerow(['C', turno, nome, n, '', '', '', d['regione']])
                for lista, n in sorted(d['liste'].items()):
                    if n:
                        w.writerow(['L', '1', lista, n, '', '', '', d['regione']])
            risultati[(com, data)] = d
    return risultati
