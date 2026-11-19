"""Temi, punteggi (1-5) e costo approssimativo di ogni commento.

Criteri, uguali per tutti (vedi la pagina "Come giudichiamo"):
  F  fattibilità: 1 = serve l'unanimità UE o una riforma costituzionale; 5 = già realizzata o realizzabile subito
  C  copertura:   1 = nessuna copertura e costo molto alto; 5 = coperta in modo credibile o senza costo
  S  esiti storici: 1 = tentativi simili falliti o con effetti negativi; 5 = esiti positivi
  Ch chiarezza:   1 = proposta generica; 5 = misura precisa, con numeri e tempi
  Ri rischi:      1 = rischi alti; 5 = rischi bassi
I punteggi sono giudizi dell'analisi, non misure: vanno letti con le motivazioni e le fonti.
"""

TEMI = [
    ('pensioni', 'Pensioni'),
    ('fisco', 'Fisco e imposte'),
    ('lavoro', 'Lavoro e salari'),
    ('poverta', 'Povertà e sussidi'),
    ('giovani', 'Giovani e famiglia'),
    ('casa-infrastrutture', 'Casa e infrastrutture'),
    ('istituzioni', 'Istituzioni italiane'),
    ('ue-trattati', 'Unione europea: Trattati e veto'),
    ('debito-bce', 'Bilancio, debito e BCE'),
    ('difesa', 'Difesa'),
    ('energia-clima', 'Energia e clima'),
    ('immigrazione', 'Immigrazione'),
]

# (file PDF, ordine del commento) -> (tema, F, C, S, Ch, Ri, costo)
VOTI = {
    # PD 2022
    ('pd-2022.pdf', 1): ('lavoro', 3, 5, 3, 3, 3, 'Basso per lo Stato; a carico di imprese e appalti'),
    ('pd-2022.pdf', 2): ('giovani', 3, 1, 2, 4, 2, 'Fino a circa 5 miliardi l\'anno (stima su ~550.000 diciottenni)'),
    ('pd-2022.pdf', 3): ('casa-infrastrutture', 2, 1, 2, 4, 2, '75-100 miliardi in 10 anni (stima)'),
    ('pd-2022.pdf', 4): ('istituzioni', 1, 5, 1, 4, 3, 'Nessuno'),
    # Centrodestra 2022 e Forza Italia 2022 (stesso programma)
    ('cdx-2022.pdf', 1): ('casa-infrastrutture', 3, 2, 2, 4, 2, 'Circa 13,5 miliardi (stima ufficiale) [verificare]'),
    ('cdx-2022.pdf', 2): ('fisco', 4, 2, 3, 4, 3, 'Non indicato: meno gettito'),
    ('cdx-2022.pdf', 3): ('istituzioni', 1, 5, 1, 2, 2, 'Nessuno'),
    ('cdx-2022.pdf', 4): ('poverta', 5, 3, 3, 2, 3, 'RdC 8-9 miliardi l\'anno; costo del sostituto non indicato'),
    ('fi-2022.pdf', 1): ('casa-infrastrutture', 3, 2, 2, 4, 2, 'Circa 13,5 miliardi (stima ufficiale) [verificare]'),
    ('fi-2022.pdf', 2): ('fisco', 4, 2, 3, 4, 3, 'Non indicato: meno gettito'),
    ('fi-2022.pdf', 3): ('istituzioni', 1, 5, 1, 2, 2, 'Nessuno'),
    ('fi-2022.pdf', 4): ('poverta', 5, 3, 3, 2, 3, 'RdC 8-9 miliardi l\'anno; costo del sostituto non indicato'),
    # FdI Europee 2024
    ('fdi-europee-2024.pdf', 1): ('energia-clima', 3, 5, 3, 4, 3, 'Nessun costo diretto'),
    ('fdi-europee-2024.pdf', 2): ('debito-bce', 1, 4, 2, 4, 2, 'Non indicato: più deficit nazionale'),
    ('fdi-europee-2024.pdf', 3): ('debito-bce', 1, 5, 2, 2, 3, 'Nessuno'),
    # FdI brochure bilancio 2024
    ('fdi-bilancio-2024.pdf', 1): ('fisco', 5, 3, 4, 5, 3, 'Circa 10 miliardi l\'anno'),
    ('fdi-bilancio-2024.pdf', 2): ('pensioni', 5, 3, 2, 4, 3, 'Non indicato'),
    # Futuro Nazionale
    ('fn-2026.pdf', 1): ('ue-trattati', 1, 5, 1, 3, 1, 'Nessun costo diretto; rischio sui fondi UE'),
    ('fn-2026.pdf', 2): ('debito-bce', 1, 3, 1, 2, 1, 'Non indicato'),
    ('fn-2026.pdf', 3): ('pensioni', 3, 1, 2, 3, 2, 'Alcuni miliardi l\'anno, in crescita (stima)'),
    ('fn-2026.pdf', 4): ('immigrazione', 1, 1, 2, 2, 1, 'Non quantificato'),
    # Lega 2022
    ('lega-2022.pdf', 1): ('fisco', 4, 2, 3, 4, 3, 'Entrata una tantum non stimata'),
    ('lega-2022.pdf', 2): ('fisco', 3, 1, 3, 4, 2, 'Decine di miliardi per la fase 2 (stima)'),
    ('lega-2022.pdf', 3): ('pensioni', 3, 1, 2, 5, 2, 'Alcuni miliardi l\'anno (stima)'),
    ('lega-2022.pdf', 4): ('istituzioni', 3, 2, 3, 3, 2, 'Livelli essenziali: decine di miliardi (stima)'),
    # M5S 2022
    ('m5s-2022.pdf', 1): ('lavoro', 3, 5, 3, 4, 3, 'Basso per lo Stato; a carico di imprese e appalti'),
    ('m5s-2022.pdf', 2): ('fisco', 2, 1, 1, 3, 1, 'Non stimato (crediti edilizi oltre 100 miliardi) [verificare]'),
    ('m5s-2022.pdf', 3): ('poverta', 5, 3, 3, 3, 3, 'Circa 8-9 miliardi l\'anno'),
    ('m5s-2022.pdf', 4): ('fisco', 2, 1, 2, 4, 2, 'Decine di miliardi l\'anno [verificare]'),
    # Forza Italia Europee 2024
    ('fi-eu-2024.pdf', 1): ('debito-bce', 1, 2, 3, 2, 2, 'Non indicato'),
    ('fi-eu-2024.pdf', 2): ('ue-trattati', 1, 5, 1, 3, 2, 'Nessuno'),
    ('fi-eu-2024.pdf', 3): ('difesa', 3, 3, 2, 3, 4, 'Non indicato'),
    ('fi-eu-2024.pdf', 4): ('energia-clima', 2, 2, 2, 3, 2, 'Decine di miliardi per ogni centrale [verificare]'),
    # Lega Europee 2024
    ('lega-eu-2024.pdf', 1): ('ue-trattati', 5, 5, 3, 4, 2, 'Nessuno'),
    ('lega-eu-2024.pdf', 2): ('energia-clima', 3, 4, 2, 2, 2, 'Nessun costo diretto'),
    ('lega-eu-2024.pdf', 3): ('debito-bce', 2, 2, 2, 2, 2, 'Non indicato'),
    ('lega-eu-2024.pdf', 4): ('debito-bce', 1, 5, 3, 3, 2, 'Nessuno'),
    # M5S Europee 2024
    ('m5s-eu-2024.pdf', 1): ('ue-trattati', 1, 4, 1, 4, 2, 'Non indicato'),
    ('m5s-eu-2024.pdf', 2): ('poverta', 1, 1, 2, 3, 3, 'Non indicato (molto superiore al RdC italiano)'),
    ('m5s-eu-2024.pdf', 3): ('debito-bce', 2, 3, 2, 4, 3, 'Non indicato: più deficit nazionale'),
    ('m5s-eu-2024.pdf', 4): ('lavoro', 2, 2, 3, 3, 3, 'Non stimato'),
    # Azione Europee 2024
    ('azione-eu-2024.pdf', 1): ('difesa', 2, 2, 2, 4, 3, 'Non indicato'),
    ('azione-eu-2024.pdf', 2): ('energia-clima', 3, 5, 3, 4, 2, 'Nessun costo diretto'),
    ('azione-eu-2024.pdf', 3): ('immigrazione', 2, 2, 2, 3, 3, 'Non indicato'),
    ('azione-eu-2024.pdf', 4): ('fisco', 2, 5, 2, 3, 3, 'Nessuno'),
    # Stati Uniti d'Europa (Italia Viva) Europee 2024
    ('sue-eu-2024.pdf', 1): ('ue-trattati', 1, 5, 1, 4, 2, 'Nessun costo diretto'),
    ('sue-eu-2024.pdf', 2): ('difesa', 1, 2, 2, 3, 2, 'Asset russi congelati 190-210 miliardi [verificare]'),
    ('sue-eu-2024.pdf', 3): ('debito-bce', 1, 1, 1, 4, 2, '800-900 miliardi l\'anno in più (stima)'),
    ('sue-eu-2024.pdf', 4): ('giovani', 4, 3, 3, 3, 4, '2-2,5 miliardi l\'anno (stima)'),
    # AVS Europee 2024
    ('avs-eu-2024.pdf', 1): ('debito-bce', 1, 1, 1, 3, 1, 'Oltre 1.500 miliardi di debito italiano coinvolto (stima)'),
    ('avs-eu-2024.pdf', 2): ('fisco', 1, 3, 1, 3, 3, 'Gettito non stimato'),
    ('avs-eu-2024.pdf', 3): ('energia-clima', 2, 1, 2, 4, 2, '2.000 miliardi, orizzonte non indicato'),
    ('avs-eu-2024.pdf', 4): ('lavoro', 2, 2, 3, 3, 3, 'Non stimato'),
}
