"""Bestandsbilanz mit explizitem Neubau und Abriss (AP4).

Nur Bilanzierung: T_B = T_A − D + N. Kein zweiter Szenariorechenkern – Zustände entstehen ausschließlich
in gebaeudesektor.py; dieses Modul liest Bruttovorgaben (data/eingaben/bestandsentwicklung/Bestandsentwicklung.xlsx),
rechnet Raten in Periodenflächen um, prüft sie gegen die Gesamtflächen der festen Zustände A und B und stellt
die Freigaben (welche Typen abgerissen bzw. neu gebaut werden dürfen) für die Rekonstruktion bereit.

Eingabearten je Größe (Neubau, Abriss):
- Rate_pct_pro_Jahr:   Periodenfläche = Rate / 100 · NGF_A · (Jahr_B − Jahr_A)   (lineare mittlere Periodenrate)
- Periodenflaeche_m2:  Bruttofläche im gesamten Zeitraum
- Bilanzrest:          Größe = Rest aus der Bilanz (ausdrücklich gewählte Identifikationsannahme; höchstens eine Größe)
Ohne Bruttoangaben ist nur N − D = T_B − T_A bekannt (Status NUR_NETTO); Neubau und Abriss werden dann nicht behauptet.
"""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
from distribution_to_json import DOMAENEN

SCHEMA = '1.0'
MERKMALE = ['geometry', 'quality', 'energy', 'pv', 'flex', 'weather', 'mass']
DOM = {'geometry': DOMAENEN['geometrie'], 'quality': DOMAENEN['qualitaet'], 'energy': DOMAENEN['versorgung'],
       'pv': DOMAENEN['pv'], 'flex': DOMAENEN['flex'], 'weather': ['Wien', 'Innsbruck'], 'mass': DOMAENEN['masse']}
GROESSEN = ['Neubau', 'Abriss']
EINGABEARTEN = ['Rate_pct_pro_Jahr', 'Periodenflaeche_m2', 'Bilanzrest']

BILANZ_OK = 'BILANZ_OK'
NUR_NETTO = 'NUR_NETTO'
WIDERSPRUCH = 'WIDERSPRUCH'
UNVOLLSTAENDIG = 'UNVOLLSTAENDIG'
BILANZSTATUS = {
    BILANZ_OK: 'Neubau und Abriss vorgegeben; T_A − D + N = T_B innerhalb der Bilanztoleranz.',
    NUR_NETTO: 'Keine Bruttoangaben: nur N − D = T_B − T_A bekannt. Neubau und Abriss sind nicht getrennt bestimmbar.',
    WIDERSPRUCH: 'Bruttovorgaben widersprechen der Flächenbilanz der Zustände A und B (oder Bilanzrest negativ).',
    UNVOLLSTAENDIG: 'Nur eine Größe vorgegeben oder ungültige Kombination; die zweite Größe fehlt (ggf. Eingabeart Bilanzrest).'}


def _sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def _datei(projekt):
    return Path(projekt['konfiguration']['bestandsentwicklung'])


def lade_bestandsentwicklung(projekt):
    """Liest und prüft Bestandsentwicklung.xlsx (Blätter Parameter, Verbindungen, Freigaben). Rechnet nichts."""
    path = _datei(projekt)
    if not path.is_file():
        raise FileNotFoundError(f'Bestandsentwicklung fehlt: {path.name}')
    blaetter = pd.read_excel(path, sheet_name=None)
    for name in ['Parameter', 'Verbindungen', 'Freigaben']:
        if name not in blaetter:
            raise ValueError(f'Bestandsentwicklung.xlsx: Blatt {name} fehlt.')
    par = blaetter['Parameter'].dropna(subset=['Parameter']).set_index('Parameter')['Wert'].to_dict()
    sv = par.get('schema_version')
    try:
        sv_ok = str(sv).strip() == SCHEMA or float(sv) == float(SCHEMA)   # Excel speichert '1.0' u. U. als Zahl
    except (TypeError, ValueError):
        sv_ok = False
    if not sv_ok:
        raise ValueError('Bestandsentwicklung.xlsx: unbekannte schema_version.')
    tol = pd.to_numeric(pd.Series([par.get('bilanztoleranz_m2')]), errors='coerce').iloc[0]
    if not np.isfinite(tol) or tol <= 0 or tol > 1e4:
        raise ValueError('bilanztoleranz_m2 muss > 0 und ≤ 10 000 m² sein.')
    v = blaetter['Verbindungen'].dropna(how='all').copy()
    need = {'Verbindung_ID', 'Groesse', 'Eingabeart', 'Wert'}
    if not need <= set(v):
        raise ValueError(f'Blatt Verbindungen: Spalten {sorted(need - set(v))} fehlen.')
    v['Verbindung_ID'] = v.Verbindung_ID.astype(str).str.strip()
    v['Groesse'] = v.Groesse.astype(str).str.strip()
    v['Eingabeart'] = v.Eingabeart.astype(str).str.strip()
    if not set(v.Groesse) <= set(GROESSEN):
        raise ValueError(f'Groesse nur {GROESSEN}.')
    if not set(v.Eingabeart) <= set(EINGABEARTEN):
        raise ValueError(f'Eingabeart nur {EINGABEARTEN}.')
    if v.duplicated(['Verbindung_ID', 'Groesse']).any():
        raise ValueError('Je Verbindung und Größe genau eine Zeile.')
    wert = pd.to_numeric(v.Wert, errors='coerce')
    feste = v.Eingabeart.ne('Bilanzrest')
    if (feste & (~np.isfinite(wert) | (wert < 0))).any():
        raise ValueError('Wert muss endlich und ≥ 0 sein (außer bei Bilanzrest).')
    v['Wert'] = wert.where(feste)
    f = blaetter['Freigaben'].dropna(how='all').copy()
    if not {'Art', 'Merkmal', 'Kategorie', 'Freigegeben'} <= set(f):
        raise ValueError('Blatt Freigaben: Spalten Art, Merkmal, Kategorie, Freigegeben erforderlich.')
    for c in ['Art', 'Merkmal', 'Kategorie']:
        f[c] = f[c].astype(str).str.strip()
    frei = pd.to_numeric(f.Freigegeben, errors='coerce')
    if not frei.isin([0, 1]).all():
        raise ValueError('Freigegeben nur 0 oder 1.')
    f['Freigegeben'] = frei.astype(int)
    if not set(f.Art) <= set(GROESSEN):
        raise ValueError('Freigaben: Art nur Neubau oder Abriss.')
    if f.duplicated(['Art', 'Merkmal', 'Kategorie']).any():
        raise ValueError('Freigaben: doppelte Zeile.')
    for art in GROESSEN:
        for m in MERKMALE:
            t = f[(f.Art == art) & (f.Merkmal == m)]
            if set(t.Kategorie) != set(DOM[m]):
                raise ValueError(f'Freigaben {art}/{m}: jede Kategorie genau einmal angeben ({", ".join(DOM[m])}).')
            if not t.Freigegeben.any():
                raise ValueError(f'Freigaben {art}/{m}: mindestens eine Kategorie freigeben.')
    root = Path(projekt['root'])
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        rel = path.name
    return {'datei': rel, 'sha256': _sha(path), 'bilanztoleranz_m2': float(tol), 'verbindungen': v.reset_index(drop=True),
            'freigaben': f.reset_index(drop=True)}


def freigaben(be, art):
    """{Merkmal: [freigegebene Kategorien]} für Neubau oder Abriss."""
    f = be['freigaben']
    f = f[(f.Art == art) & (f.Freigegeben == 1)]
    return {m: sorted(f.loc[f.Merkmal == m, 'Kategorie'], key=DOM[m].index) for m in MERKMALE}


def freigabetabelle(be):
    """Übersicht der Freigaben: je Art und Merkmal die freigegebenen Kategorien."""
    rows = []
    for art in GROESSEN:
        fr = freigaben(be, art)
        for m in MERKMALE:
            rows.append({'Art': art, 'Merkmal': m, 'Freigegeben': ', '.join(fr[m]),
                         'Alle': len(fr[m]) == len(DOM[m])})
    return pd.DataFrame(rows)


def maske(df, freigabe):
    """Boolesche Maske: Typ erfüllt die Freigabe in allen Merkmalen (energy auf Planebene, FW_* = DH)."""
    m = pd.Series(True, index=df.index)
    for d, cats in freigabe.items():
        werte = df[d].astype(str).str.strip()
        if d == 'energy':
            werte = werte.replace({'FW_Wien': 'DH', 'FW_erneu': 'DH'})
        m &= werte.isin(cats)
    return m


def periodenflaeche(eingabeart, wert, ngf_a, jahre):
    """Rate (% der Ausgangs-NGF pro Jahr) oder Periodenfläche → Periodenfläche in m²."""
    if eingabeart == 'Rate_pct_pro_Jahr':
        return float(wert) / 100.0 * float(ngf_a) * float(jahre)
    if eingabeart == 'Periodenflaeche_m2':
        return float(wert)
    raise ValueError('Bilanzrest hat keinen eigenen Wert.')


def bilanz(zeilen, ngf_a, ngf_b, jahr_a, jahr_b, toleranz_m2):
    """Bestandsbilanz einer Verbindung A → B.

    zeilen: DataFrame mit Groesse/Eingabeart/Wert (0–2 Zeilen). Gibt Status, Meldung, Periodenflächen und Tabelle zurück.
    Es wird nichts ausgeglichen: Widersprüche werden ausgewiesen, nicht korrigiert."""
    jahre = int(jahr_b) - int(jahr_a)
    if jahre <= 0:
        raise ValueError('Zeitreihenfolge: Zieljahr muss nach dem Ausgangsjahr liegen.')
    netto = float(ngf_b) - float(ngf_a)
    z = {r.Groesse: r for r in zeilen.itertuples()} if len(zeilen) else {}
    n = d = None
    status = BILANZ_OK
    meldung = BILANZSTATUS[BILANZ_OK]
    if not z:
        status, meldung = NUR_NETTO, BILANZSTATUS[NUR_NETTO]
    elif len(z) == 1:
        status, meldung = UNVOLLSTAENDIG, f'Nur {next(iter(z))} vorgegeben. ' + BILANZSTATUS[UNVOLLSTAENDIG]
    else:
        rest = [k for k, r in z.items() if r.Eingabeart == 'Bilanzrest']
        if len(rest) == 2:
            status, meldung = UNVOLLSTAENDIG, 'Neubau und Abriss als Bilanzrest: nicht bestimmbar.'
        else:
            werte = {k: periodenflaeche(r.Eingabeart, r.Wert, ngf_a, jahre) for k, r in z.items() if r.Eingabeart != 'Bilanzrest'}
            if rest == ['Neubau']:
                werte['Neubau'] = netto + werte['Abriss']
            elif rest == ['Abriss']:
                werte['Abriss'] = werte['Neubau'] - netto
            n, d = werte['Neubau'], werte['Abriss']
            abw = float(ngf_a) - d + n - float(ngf_b)
            if min(n, d) < 0:
                status, meldung = WIDERSPRUCH, f'Bilanzrest negativ (Neubau {n:,.0f} m², Abriss {d:,.0f} m²).'
            elif d > float(ngf_a):
                status, meldung = WIDERSPRUCH, 'Abriss übersteigt die Ausgangs-NGF.'
            elif abs(abw) > toleranz_m2:
                status, meldung = WIDERSPRUCH, (f'T_A − D + N weicht um {abw:,.2f} m² von T_B ab (Toleranz {toleranz_m2:g} m²). '
                                                'Vorgaben anpassen oder eine Größe als Bilanzrest angeben.')
    def zeile(name, wert, art='', vorgabe=np.nan):
        return {'Groesse': name, 'NGF_m2': wert, 'Anteil_Ausgangs_NGF_pct': 100 * wert / ngf_a if wert is not None else np.nan,
                'pct_Ausgangs_NGF_pro_Jahr': 100 * wert / ngf_a / jahre if wert is not None else np.nan,
                'Eingabeart': art, 'Vorgabe': vorgabe}
    art = {k: r.Eingabeart for k, r in z.items()}
    vorg = {k: r.Wert for k, r in z.items()}
    rows = [zeile('Ausgangsbestand T_A', float(ngf_a)),
            zeile('Abriss D', d, art.get('Abriss', ''), vorg.get('Abriss', np.nan)),
            zeile('Verbleibender Bestand T_A − D', None if d is None else float(ngf_a) - d),
            zeile('Neubau N', n, art.get('Neubau', ''), vorg.get('Neubau', np.nan)),
            zeile('Zielbestand Soll T_A − D + N', None if n is None or d is None else float(ngf_a) - d + n),
            zeile('Zielbestand Ist T_B', float(ngf_b)),
            zeile('Nettoänderung N − D = T_B − T_A', netto)]
    tab = pd.DataFrame(rows)
    tab.loc[tab.NGF_m2.isna(), ['Anteil_Ausgangs_NGF_pct', 'pct_Ausgangs_NGF_pro_Jahr']] = np.nan
    tab.loc[~tab.Groesse.isin(['Abriss D', 'Neubau N', 'Nettoänderung N − D = T_B − T_A']), 'pct_Ausgangs_NGF_pro_Jahr'] = np.nan
    return {'status': status, 'statusbedeutung': BILANZSTATUS[status], 'meldung': meldung, 'neubau_m2': n, 'abriss_m2': d,
            'netto_m2': netto, 'jahre': jahre, 'ngf_a': float(ngf_a), 'ngf_b': float(ngf_b), 'toleranz_m2': float(toleranz_m2),
            'tabelle': tab}


def zeilen_fuer(be, verbindung_id):
    v = be['verbindungen']
    return v[v.Verbindung_ID == verbindung_id]


def bilanz_fuer(verbindung_id, projekt, ngf_a, ngf_b, jahr_a, jahr_b):
    """Bilanz für eine registrierte Verbindung (Verbindung_ID = Rekonstruktions-ID) mit Freigaben und Herkunftsnachweis."""
    be = lade_bestandsentwicklung(projekt)
    r = bilanz(zeilen_fuer(be, verbindung_id), ngf_a, ngf_b, jahr_a, jahr_b, be['bilanztoleranz_m2'])
    r.update({'verbindung_id': verbindung_id, 'quelle': {'datei': be['datei'], 'sha256': be['sha256']},
              'freigabe_neubau': freigaben(be, 'Neubau'), 'freigabe_abriss': freigaben(be, 'Abriss')})
    return r


def extern_fuer(b):
    """Vorgaben für die Rekonstruktion mit externen Flüssen (nur bei BILANZ_OK), sonst None."""
    if b['status'] != BILANZ_OK:
        return None
    return {'neubau_m2': b['neubau_m2'], 'abriss_m2': b['abriss_m2'], 'bilanztoleranz_m2': b['toleranz_m2'],
            'freigabe_neubau': b['freigabe_neubau'], 'freigabe_abriss': b['freigabe_abriss'], 'quelle': b['quelle'],
            'jahre': b['jahre']}


def szenariobilanz(projekt, rekonstruktionen=None):
    """Bilanzübersicht aller registrierten Rekonstruktionspaare aus den gespeicherten Zuständen (nur lesen, keine Rekonstruktion)."""
    import json
    reg = json.loads(Path(projekt['konfiguration']['rekonstruktionen']).read_text(encoding='utf-8'))['rekonstruktionen']
    root = Path(projekt['ergebnisse']['szenarien'])
    be = lade_bestandsentwicklung(projekt)
    rows = []
    for rid, r in reg.items():
        if rekonstruktionen and rid not in rekonstruktionen:
            continue
        try:
            za = pd.read_csv(root / r['szenario_a'] / 'Verteilung.csv', sep=';', encoding='utf-8-sig')
            zb = pd.read_csv(root / r['szenario_b'] / 'Verteilung.csv', sep=';', encoding='utf-8-sig')
            b = bilanz(zeilen_fuer(be, rid), za.NGF_m2.sum(), zb.NGF_m2.sum(), za.Jahr.iloc[0], zb.Jahr.iloc[0], be['bilanztoleranz_m2'])
            rows.append({'Verbindung_ID': rid, 'A': r['szenario_a'], 'B': r['szenario_b'], 'Jahre': b['jahre'], 'NGF_A_m2': b['ngf_a'],
                         'NGF_B_m2': b['ngf_b'], 'Netto_m2': b['netto_m2'], 'Neubau_m2': b['neubau_m2'], 'Abriss_m2': b['abriss_m2'],
                         'Neubau_pct_pro_Jahr': np.nan if b['neubau_m2'] is None else 100 * b['neubau_m2'] / b['ngf_a'] / b['jahre'],
                         'Abriss_pct_pro_Jahr': np.nan if b['abriss_m2'] is None else 100 * b['abriss_m2'] / b['ngf_a'] / b['jahre'],
                         'Status': b['status'], 'Meldung': b['meldung']})
        except FileNotFoundError as e:
            rows.append({'Verbindung_ID': rid, 'A': r['szenario_a'], 'B': r['szenario_b'], 'Status': 'ZUSTAND_FEHLT', 'Meldung': f'nicht gespeichert: {Path(e.filename).parent.name}'})
    return pd.DataFrame(rows)
