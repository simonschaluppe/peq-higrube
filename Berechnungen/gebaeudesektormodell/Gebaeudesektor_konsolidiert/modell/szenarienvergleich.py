"""Gebäudesektormodell – Mehrszenarienvergleich (AP2).

Liest ausschließlich gespeicherte Szenarioergebnisse (results/szenarien/<ID>/Kennwerte.csv,
Verteilung.csv, laufprotokoll.json). Keine Zustandsbildung, keine Energieberechnung,
keine Flussrekonstruktion. Drei Ansichten:

- Übersicht: alle ausgewählten Szenarien in einer gemeinsamen Kennwerttabelle;
- Referenzvergleich: alle Szenarien gegen eine gewählte Referenz;
- Paarvergleich: zwei Zustände im Detail (Merkmale, Typen, Flächen-/Struktureffekt).

Vergleichbarkeit je Kennwert: VERGLEICHBAR, BEDINGT_VERGLEICHBAR, NICHT_VERGLEICHBAR, KENNWERT_FEHLT.
Nicht vergleichbare Energiewerte sperren den Flächenvergleich nicht.
"""
from pathlib import Path
import json, html, platform
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import gebaeudesektor as gs

SCHEMA_VERSION = '1.0'
VERGLEICHBAR = 'VERGLEICHBAR'
BEDINGT = 'BEDINGT_VERGLEICHBAR'
NICHT = 'NICHT_VERGLEICHBAR'
FEHLT = 'KENNWERT_FEHLT'
STATUSFOLGE = [VERGLEICHBAR, BEDINGT, NICHT, FEHLT]
SCHLUESSEL = ['Bereich', 'Gruppe', 'Kennwert', 'Kategorie', 'Einheit']
ANTEILSEINHEIT = '% NGF'
STANDARD_MINDESTABDECKUNG_PCT = 95.0
LABELS = {'geometry': 'Geometrie', 'quality': 'Qualität', 'energy': 'Planversorgung', 'pv': 'PV', 'flex': 'Flexibilität', 'weather': 'Wetter', 'mass': 'Speichermasse'}
ORDERS = {'geometry': gs.GEOS, 'quality': gs.QUAL, 'energy': gs.ENERGY_PLAN, 'pv': gs.PVS, 'flex': gs.FLEX, 'weather': gs.WEATHER, 'mass': gs.MASS}
EXPORTDATEIEN = ['Kennwerte_Alle_Szenarien.csv', 'Vergleichbarkeit.csv', 'Referenzvergleich.csv', 'Paarvergleich.csv',
                 'Typenvergleich.csv', 'Vergleich.xlsx', 'Vergleich.html', 'vergleichsprotokoll.json']

# ---------------------------------------------------------------------------
# Register und Laden
# ---------------------------------------------------------------------------

def _projektfassung():
    import fassung
    return fassung.FASSUNG


def lade_vergleichsregister(projekt=None):
    projekt = gs.lade_projekt(projekt)
    cfg = json.loads(projekt['konfiguration']['vergleiche'].read_text(encoding='utf-8'))
    if cfg.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('Unbekanntes Schema in config/vergleiche.json.')
    for vid, v in cfg.get('vergleiche', {}).items():
        _pruefe_auswahl(vid, v.get('szenarien'), v.get('referenz'), v.get('paar'))
    return cfg

def _pruefe_auswahl(vid, szenarien, referenz, paar):
    if not gs.re.fullmatch(r'[A-Za-z0-9_-]+', str(vid)):
        raise ValueError(f'Vergleichs-ID {vid!r} ist kein sicherer Ordnername.')
    if not isinstance(szenarien, list) or len(szenarien) < 2 or len(set(szenarien)) != len(szenarien):
        raise ValueError(f'Vergleich {vid}: mindestens zwei verschiedene Szenarien angeben.')
    if referenz is not None and referenz not in szenarien:
        raise ValueError(f'Vergleich {vid}: Referenz {referenz} ist nicht unter den Szenarien.')
    if paar is not None:
        if not isinstance(paar, list) or len(paar) != 2 or paar[0] == paar[1] or not set(paar) <= set(szenarien):
            raise ValueError(f'Vergleich {vid}: Paar muss aus zwei verschiedenen ausgewählten Szenarien bestehen.')

def registrierte_vergleiche(projekt=None):
    cfg = lade_vergleichsregister(projekt)
    return pd.DataFrame([{'Vergleich_ID': k, 'Szenarien': ', '.join(v['szenarien']), 'Referenz': v.get('referenz'),
                          'Paar': ' → '.join(v['paar']) if v.get('paar') else '', 'Beschreibung': v.get('beschreibung', '')}
                         for k, v in cfg.get('vergleiche', {}).items()])

def vergleichsauswahl(vergleich_id, projekt=None):
    cfg = lade_vergleichsregister(projekt)
    if vergleich_id not in cfg['vergleiche']:
        raise KeyError(f'Vergleich {vergleich_id!r} ist nicht in config/vergleiche.json registriert.')
    v = cfg['vergleiche'][vergleich_id]
    return {'vergleich_id': vergleich_id, 'szenarien': list(v['szenarien']), 'referenz': v.get('referenz') or v['szenarien'][0],
            'paar': list(v['paar']) if v.get('paar') else None,
            'mindestabdeckung_pct': float(v.get('mindestabdeckung_pct', cfg.get('mindestabdeckung_pct', STANDARD_MINDESTABDECKUNG_PCT)))}

def _abdeckung_summen(k):
    """Summenzeilen (z. B. 'SUMME ohne Umgebungswärme') tragen in Kennwerte.csv keine eigene Abdeckung.
    Für den Vergleich gilt die kleinste Abdeckung der Einzelwerte derselben Gruppe und desselben Bereichs.
    Nur im Vergleich abgeleitet; Kennwerte.csv bleibt unverändert."""
    k = k.copy()
    summe = k.Kategorie.str.upper().str.startswith('SUMME') & k.Abdeckung_pct.isna()
    if summe.any():
        mins = k[~summe].groupby(['Bereich', 'Gruppe', 'Kennwert']).Abdeckung_pct.min()
        for i in k.index[summe]:
            key = (k.at[i, 'Bereich'], k.at[i, 'Gruppe'], k.at[i, 'Kennwert'])
            if key in mins.index:
                k.at[i, 'Abdeckung_pct'] = mins[key]
    return k

def lade_kennwerte(szenarien, projekt=None):
    """Lädt die gespeicherten Ergebnisse (mit Integritätsprüfung) und die gemeinsame Kennwerttabelle. Nur lesen."""
    projekt = gs.lade_projekt(projekt)
    teile, meta, zustaende = [], [], {}
    for sid in szenarien:
        z = gs.lade_gespeichertes_szenario(sid, projekt)
        if z['kennwerte'] is None:
            raise FileNotFoundError(f'{sid}: Kennwerte.csv fehlt (Ergebnis vor AP1). In 01_Szenario neu speichern.')
        k = z['kennwerte'].copy()
        fehlend = [c for c in gs.KENNWERTSPALTEN if c not in k]
        if fehlend:
            raise ValueError(f'{sid}: Kennwerte.csv ohne Spalten {fehlend}.')
        k['Kategorie'] = k['Kategorie'].fillna('').astype(str)
        k['Einheit'] = k['Einheit'].fillna('').astype(str)
        k['Bezugsflaeche'] = k['Bezugsflaeche'].fillna('').astype(str)
        if (k.Szenario_ID != sid).any() or (k.Zustand_ID != z['zustand_id']).any():
            raise ValueError(f'{sid}: Kennwerte gehören nicht zum gespeicherten Zustand.')
        if k.duplicated(SCHLUESSEL).any():
            raise ValueError(f'{sid}: doppelte Kennwerte.')
        k = _abdeckung_summen(k)
        teile.append(k[gs.KENNWERTSPALTEN])
        vb = z['protokoll'].get('vergleichsbasis', {})
        meta.append({'Szenario_ID': sid, 'Jahr': z['jahr'], 'Zustand_ID': z['zustand_id'], 'NGF_m2': float(z['df'].NGF_m2.sum()),
                     'Positive_Typen': int(z['df'].NGF_m2.gt(0).sum()), 'Energie': z['energiestatus'],
                     'Flaechenbasis': vb.get('flaeche'), 'Energiebasis': vb.get('energie'), 'Integritaet': z['integritaet'],
                     'Ordner': gs._relativ(projekt['root'], z['ordner'])})
        zustaende[sid] = z
    return {'kennwerte': pd.concat(teile, ignore_index=True), 'szenarien': pd.DataFrame(meta), 'zustaende': zustaende}

# ---------------------------------------------------------------------------
# Vergleichbarkeit
# ---------------------------------------------------------------------------

def _wert_vorhanden(r):
    return r is not None and pd.notna(r['Wert']) and np.isfinite(float(r['Wert'])) and r['Status'] not in ('NICHT_AUSGEFUEHRT', 'KENNWERT_FEHLT', 'KEINE_FLAECHE')

def status_paar(a, b, mindestabdeckung=STANDARD_MINDESTABDECKUNG_PCT):
    """Vergleichbarkeit eines Kennwerts zwischen zwei Szenarien. a/b: Zeilen (dict/Series) oder None. Gibt (Status, Grund) zurück."""
    if a is None or b is None:
        return FEHLT, 'Kennwert in einem Szenario nicht vorhanden'
    if not _wert_vorhanden(a) or not _wert_vorhanden(b):
        return FEHLT, 'Wert fehlt oder Analyse nicht ausgeführt'
    if a['Einheit'] != b['Einheit'] or a['Bezugsflaeche'] != b['Bezugsflaeche']:
        return NICHT, 'Einheit oder Bezugsfläche verschieden'
    if a['Vergleichsbasis_ID'] != b['Vergleichsbasis_ID']:
        return NICHT, 'Vergleichsbasis verschieden (Definition, Kategorien, Abgrenzung bzw. Simulation/Batch/Bilanz)'
    cov = [float(x) if pd.notna(x) else np.nan for x in (a['Abdeckung_pct'], b['Abdeckung_pct'])]
    if any(not np.isfinite(c) for c in cov) or min(cov) < mindestabdeckung:
        return NICHT, f'Abdeckung unter {mindestabdeckung:g} %'
    if min(cov) < 100 - 1e-9 or a['Status'] != 'OK' or b['Status'] != 'OK':
        return BEDINGT, 'Abdeckung unter 100 % oder Kennwert unvollständig'
    return VERGLEICHBAR, ''

def _zeile(index, key):
    if key not in index.index:
        return None
    return {**dict(zip(SCHLUESSEL, key)), **index.loc[key].to_dict()}

def _schlimmster(statusliste):
    return max(statusliste, key=STATUSFOLGE.index) if statusliste else FEHLT

def vergleichbarkeit(kennwerte, referenz, mindestabdeckung=STANDARD_MINDESTABDECKUNG_PCT):
    """Je Kennwert und Szenario: Status gegenüber der Referenz; Gesamtstatus = ungünstigster Status."""
    szen = list(dict.fromkeys(kennwerte.Szenario_ID))
    idx = {s: g.set_index(SCHLUESSEL) for s, g in kennwerte.groupby('Szenario_ID', sort=False)}
    keys = list(dict.fromkeys(map(tuple, kennwerte[SCHLUESSEL].itertuples(index=False, name=None))))
    rows = []
    for key in keys:
        ref = _zeile(idx[referenz], key)
        row = dict(zip(SCHLUESSEL, key))
        stati, gruende = [], []
        for s in szen:
            if s == referenz:
                continue
            other = _zeile(idx[s], key)
            st, grund = status_paar(ref, other, mindestabdeckung)
            row['Status_' + s] = st
            stati.append(st)
            if grund:
                gruende.append(f'{s}: {grund}')
        row['Status'] = _schlimmster(stati)
        row['Hinweis'] = '; '.join(gruende)
        rows.append(row)
    return pd.DataFrame(rows)

# ---------------------------------------------------------------------------
# Ansichten
# ---------------------------------------------------------------------------

def uebersicht(kennwerte, szenarien=None):
    """Breite Tabelle: ein Kennwert je Zeile, ein Szenario je Spalte (Werte unverändert, fehlende bleiben leer)."""
    szenarien = szenarien or list(dict.fromkeys(kennwerte.Szenario_ID))
    wide = kennwerte.pivot_table(index=SCHLUESSEL, columns='Szenario_ID', values='Wert', aggfunc='first', dropna=False, sort=False)
    wide = wide.reindex(columns=szenarien)
    order = list(dict.fromkeys(map(tuple, kennwerte[SCHLUESSEL].itertuples(index=False, name=None))))
    return wide.reindex(pd.MultiIndex.from_tuples(order, names=SCHLUESSEL)).reset_index()

def _differenz(a, b, jahre, anteil):
    out = {'Delta': b - a, 'Relative_Aenderung_pct': 100 * (b - a) / a if a != 0 else np.nan}
    out['Delta_pp'] = b - a if anteil else np.nan
    out['Netto_pro_Jahr'] = (b - a) / jahre if jahre > 0 else np.nan
    return out

def referenzvergleich(kennwerte, meta, referenz, mindestabdeckung=STANDARD_MINDESTABDECKUNG_PCT):
    """Alle Szenarien gegen die Referenz. Differenzen nur für VERGLEICHBAR/BEDINGT_VERGLEICHBAR."""
    jahre = meta.set_index('Szenario_ID').Jahr
    idx = {s: g.set_index(SCHLUESSEL) for s, g in kennwerte.groupby('Szenario_ID', sort=False)}
    rows = []
    for key in idx[referenz].index:
        r = _zeile(idx[referenz], key)
        for s in meta.Szenario_ID:
            if s == referenz:
                continue
            o = _zeile(idx[s], key)
            st, grund = status_paar(r, o, mindestabdeckung)
            dj = int(jahre[s] - jahre[referenz])
            row = {**dict(zip(SCHLUESSEL, key)), 'Referenz': referenz, 'Szenario_ID': s, 'Jahre': dj,
                   'Wert_Referenz': r['Wert'], 'Wert_Szenario': o['Wert'] if o is not None else np.nan, 'Status': st, 'Hinweis': grund}
            if st in (VERGLEICHBAR, BEDINGT):
                row.update(_differenz(float(r['Wert']), float(o['Wert']), dj, key[4] == ANTEILSEINHEIT))
            else:
                row.update({'Delta': np.nan, 'Relative_Aenderung_pct': np.nan, 'Delta_pp': np.nan, 'Netto_pro_Jahr': np.nan})
            if dj <= 0:
                row['Hinweis'] = (row['Hinweis'] + '; ' if row['Hinweis'] else '') + ('gleiches Jahr: keine Jahresrate' if dj == 0 else 'Szenario vor Referenz: keine Jahresrate')
            rows.append(row)
    cols = SCHLUESSEL + ['Referenz', 'Szenario_ID', 'Jahre', 'Wert_Referenz', 'Wert_Szenario', 'Delta', 'Relative_Aenderung_pct', 'Delta_pp', 'Netto_pro_Jahr', 'Status', 'Hinweis']
    return pd.DataFrame(rows, columns=cols)

def differenzen(a, b, total_a, total_b, jahre):
    """Kategoriedifferenzen mit exakter symmetrischer Zerlegung Delta = Flächeneffekt + Struktureffekt."""
    idx = a.index.union(b.index, sort=False)
    a = a.reindex(idx, fill_value=0.); b = b.reindex(idx, fill_value=0.)
    pa = a / total_a; pb = b / total_b
    out = pd.DataFrame({'NGF_A_m2': a, 'NGF_B_m2': b, 'Delta_NGF_m2': b - a, 'Anteil_A_pct': pa * 100, 'Anteil_B_pct': pb * 100, 'Delta_pp': (pb - pa) * 100})
    out['Relative_Aenderung_pct'] = np.divide((b - a).to_numpy() * 100, a.to_numpy(), out=np.full(len(a), np.nan), where=a.to_numpy() != 0)
    out['Netto_m2_pro_Jahr'] = (b - a) / jahre if jahre > 0 else np.nan
    out['Netto_pp_pro_Jahr'] = (pb - pa) * 100 / jahre if jahre > 0 else np.nan
    out['Flaecheneffekt_m2'] = (total_b - total_a) * (pa + pb) / 2
    out['Struktureffekt_m2'] = (total_a + total_b) / 2 * (pb - pa)
    if not np.allclose(out.Delta_NGF_m2, out.Flaecheneffekt_m2 + out.Struktureffekt_m2, rtol=1e-10, atol=.01):
        raise ValueError('Zerlegungsidentität verletzt.')
    return out

def _planversorgung(df):
    return df.assign(energy=df.energy.replace({'FW_Wien': 'DH', 'FW_erneu': 'DH'}))

def paarvergleich(za, zb):
    """Detailvergleich zweier gespeicherter Zustände (aus lade_gespeichertes_szenario)."""
    A = _planversorgung(za['df']); B = _planversorgung(zb['df'])
    ta, tb = float(A.NGF_m2.sum()), float(B.NGF_m2.sum())
    jahre = int(zb['jahr'] - za['jahr'])
    gleiche = abs(ta - tb) <= .01
    kontrollen, teile, grenzen = [], [], []
    def check(label, ist, soll=0., tol=.01):
        ok = bool(np.isfinite(ist) and abs(ist - soll) <= tol)
        kontrollen.append({'Pruefung': label, 'Ist': float(ist), 'Soll': float(soll), 'Status': 'OK' if ok else 'FEHLER'})
        if not ok:
            raise ValueError(f'{label}: {ist} statt {soll}')
    for d in gs.DIMS:
        a = A.groupby(d).NGF_m2.sum().reindex(ORDERS[d], fill_value=0)
        b = B.groupby(d).NGF_m2.sum().reindex(ORDERS[d], fill_value=0)
        tab = differenzen(a, b, ta, tb, jahre).reindex(ORDERS[d])
        check('Delta-Summe ' + d, tab.Delta_NGF_m2.sum(), tb - ta)
        teile.append(tab.rename_axis('Kategorie').reset_index().assign(Merkmal=LABELS[d], Eigenschaft=d))
        lower = .5 * abs(b - a).sum() if gleiche else np.nan
        grenzen.append({'Merkmal': LABELS[d], 'Minimale_Umverteilung_m2': lower, 'Anteil_am_Bestand_pct': lower / ta * 100 if gleiche else np.nan})
    aa = za['df'].set_index(gs.DIMS).NGF_m2; bb = zb['df'].set_index(gs.DIMS).NGF_m2
    typen = differenzen(aa, bb, ta, tb, jahre).reset_index()
    typen.insert(0, 'Archetype', typen[gs.DIMS].agg('|'.join, axis=1))
    check('Typen-Delta-Summe', typen.Delta_NGF_m2.sum(), tb - ta)
    lower = .5 * typen.Delta_NGF_m2.abs().sum() if gleiche else np.nan
    grenzen.append({'Merkmal': 'Vollständiger Typenschlüssel', 'Minimale_Umverteilung_m2': lower, 'Anteil_am_Bestand_pct': lower / ta * 100 if gleiche else np.nan})
    qa = A.pivot_table(index='quality', columns='energy', values='NGF_m2', aggfunc='sum', fill_value=0).reindex(index=gs.QUAL, columns=gs.ENERGY_PLAN, fill_value=0)
    qb = B.pivot_table(index='quality', columns='energy', values='NGF_m2', aggfunc='sum', fill_value=0).reindex(index=gs.QUAL, columns=gs.ENERGY_PLAN, fill_value=0)
    check('Qualität×Versorgung-Delta-Summe', (qb - qa).to_numpy().sum(), tb - ta)
    merkmale = pd.concat(teile, ignore_index=True)
    merkmale = merkmale[['Merkmal', 'Eigenschaft', 'Kategorie'] + [c for c in merkmale.columns if c not in ('Merkmal', 'Eigenschaft', 'Kategorie')]]
    return {'szenario_a': za['name'], 'szenario_b': zb['name'], 'jahr_a': za['jahr'], 'jahr_b': zb['jahr'], 'jahre': jahre,
            'ngf_a': ta, 'ngf_b': tb, 'gleiche_ngf': gleiche, 'merkmale': merkmale, 'untergrenzen': pd.DataFrame(grenzen),
            'typen': typen, 'qe_a': qa, 'qe_b': qb, 'qe_delta': qb - qa, 'kontrollen': pd.DataFrame(kontrollen)}

# ---------------------------------------------------------------------------
# Gesamtablauf
# ---------------------------------------------------------------------------

def vergleiche(szenarien, referenz=None, paar=None, projekt=None, vergleich_id=None, mindestabdeckung=STANDARD_MINDESTABDECKUNG_PCT):
    """Liest gespeicherte Ergebnisse und erstellt Übersicht, Vergleichbarkeit, Referenz- und optional Paarvergleich."""
    projekt = gs.lade_projekt(projekt)
    referenz = referenz or szenarien[0]
    vergleich_id = vergleich_id or '__'.join(szenarien)
    _pruefe_auswahl(vergleich_id, szenarien, referenz, paar)
    daten = lade_kennwerte(szenarien, projekt)
    k, meta = daten['kennwerte'], daten['szenarien']
    erg = {'vergleich_id': vergleich_id, 'szenarien': list(szenarien), 'referenz': referenz, 'paar': paar,
           'mindestabdeckung_pct': mindestabdeckung, 'meta': meta, 'kennwerte': k,
           'uebersicht': uebersicht(k, szenarien), 'vergleichbarkeit': vergleichbarkeit(k, referenz, mindestabdeckung),
           'referenzvergleich': referenzvergleich(k, meta, referenz, mindestabdeckung), 'paarvergleich': None, 'projekt': projekt}
    if paar:
        erg['paarvergleich'] = paarvergleich(daten['zustaende'][paar[0]], daten['zustaende'][paar[1]])
    erg['_eingaben'] = {s: {n: {'datei': gs._relativ(projekt['root'], Path(z['ordner']) / n), 'sha256': gs._sha(Path(z['ordner']) / n)}
                            for n in ['Verteilung.csv', 'Kennwerte.csv', 'laufprotokoll.json']} for s, z in daten['zustaende'].items()}
    return erg

def vergleiche_registriert(vergleich_id, projekt=None):
    projekt = gs.lade_projekt(projekt)
    a = vergleichsauswahl(vergleich_id, projekt)
    return vergleiche(a['szenarien'], a['referenz'], a['paar'], projekt, vergleich_id, a['mindestabdeckung_pct'])

def statusuebersicht(erg):
    """Anzahl Kennwerte je Szenario (gegenüber der Referenz) und Vergleichbarkeitsstatus, getrennt nach Fläche und Energie."""
    r = erg['referenzvergleich'].assign(Art=lambda x: np.where(x.Gruppe.str.startswith('Energie'), 'Energie', 'Fläche'))
    t = r.pivot_table(index=['Szenario_ID', 'Art'], columns='Status', values='Kennwert', aggfunc='count', fill_value=0)
    t = t.reindex(columns=STATUSFOLGE, fill_value=0).reset_index()
    t.insert(0, 'Referenz', erg['referenz'])
    t.columns.name = None
    return t

# ---------------------------------------------------------------------------
# Grafiken
# ---------------------------------------------------------------------------

FARBEN = ['#7B8D9D', '#3F7861', '#C27C2C', '#6B5B95', '#B04A4A', '#2F6690', '#8A9A5B', '#A0522D']

def grafik_uebersicht(erg):
    """Anteile der Merkmalskategorien je Szenario; Auswahl des Merkmals per Menü."""
    k = erg['kennwerte']; szen = erg['szenarien']
    d = k[(k.Bereich == 'Gesamt') & (k.Kennwert == 'NGF-Anteil') & (k.Einheit == ANTEILSEINHEIT)]
    gruppen = list(dict.fromkeys(d.Gruppe))
    fig = go.Figure()
    for gi, g in enumerate(gruppen):
        for si, s in enumerate(szen):
            x = d[(d.Gruppe == g) & (d.Szenario_ID == s)]
            fig.add_bar(y=x.Kategorie, x=x.Wert, name=s, orientation='h', marker_color=FARBEN[si % len(FARBEN)], visible=gi == 0, legendgroup=s, showlegend=True)
    n = len(szen)
    fig.update_layout(template='plotly_white', barmode='group', height=650, title=(gruppen[0] if gruppen else '') + ' · Anteil an der NGF',
                      xaxis_title='% der NGF', yaxis=dict(autorange='reversed'),
                      updatemenus=[dict(x=0, y=1.15, buttons=[dict(label=g, method='update', args=[{'visible': [j // n == i for j in range(n * len(gruppen))]}, {'title': g + ' · Anteil an der NGF'}]) for i, g in enumerate(gruppen)])])
    return fig

def grafik_referenz(erg):
    """Änderung der Kategorieanteile gegenüber der Referenz in Prozentpunkten."""
    r = erg['referenzvergleich']
    d = r[(r.Bereich == 'Gesamt') & (r.Kennwert == 'NGF-Anteil') & r.Status.isin([VERGLEICHBAR, BEDINGT])]
    gruppen = list(dict.fromkeys(d.Gruppe)); szen = [s for s in erg['szenarien'] if s != erg['referenz']]
    fig = go.Figure()
    for gi, g in enumerate(gruppen):
        for si, s in enumerate(szen):
            x = d[(d.Gruppe == g) & (d.Szenario_ID == s)]
            fig.add_bar(y=x.Kategorie, x=x.Delta_pp, name=s, orientation='h', marker_color=FARBEN[(si + 1) % len(FARBEN)], visible=gi == 0)
    n = max(len(szen), 1)
    fig.update_layout(template='plotly_white', barmode='group', height=650, title=(gruppen[0] if gruppen else '') + ' · Änderung gegenüber ' + erg['referenz'],
                      xaxis_title='Prozentpunkte', yaxis=dict(autorange='reversed'),
                      updatemenus=[dict(x=0, y=1.15, buttons=[dict(label=g, method='update', args=[{'visible': [j // n == i for j in range(n * len(gruppen))]}, {'title': g + ' · Änderung gegenüber ' + erg['referenz']}]) for i, g in enumerate(gruppen)])])
    return fig

def grafik_energie(erg):
    """Energiekennwerte (GWh/a, Bereich Gesamt): Referenz und alle Szenarien mit vergleichbaren Werten; None, wenn keine vergleichbar sind."""
    r = erg['referenzvergleich']
    ok = r[(r.Bereich == 'Gesamt') & r.Gruppe.str.startswith('Energie') & (r.Einheit == 'GWh/a') & r.Status.isin([VERGLEICHBAR, BEDINGT])]
    if not len(ok):
        return None
    label = lambda x: x.Kennwert + (' · ' + x.Kategorie).where(x.Kategorie != '', '')
    ref = ok.drop_duplicates(SCHLUESSEL)
    fig = go.Figure()
    fig.add_bar(y=label(ref), x=ref.Wert_Referenz / 1000, name=erg['referenz'], orientation='h', marker_color=FARBEN[0])
    for si, s in enumerate([x for x in erg['szenarien'] if x != erg['referenz']]):
        x = ok[ok.Szenario_ID == s]
        if len(x):
            fig.add_bar(y=label(x), x=x.Wert_Szenario / 1000, name=s, orientation='h', marker_color=FARBEN[(si + 1) % len(FARBEN)])
    fig.update_layout(template='plotly_white', barmode='group', title='Energiekennwerte · Gesamt (nur vergleichbare Werte)', xaxis_title='TWh/a', height=850, yaxis=dict(autorange='reversed'))
    return fig

def grafik_paar_matrix(p):
    fig = go.Figure(); cap = max(float(p['qe_a'].to_numpy().max()), float(p['qe_b'].to_numpy().max())) / 1e6
    labels = [p['szenario_a'], p['szenario_b'], 'B minus A']
    for i, values in enumerate([p['qe_a'], p['qe_b'], p['qe_delta']]):
        z = values.to_numpy() / 1e6; extent = max(float(np.abs(z).max()), 1e-12)
        fig.add_trace(go.Heatmap(x=gs.ENERGY_PLAN, y=gs.QUAL, z=z, visible=i == 2, zmin=-extent if i == 2 else 0, zmax=extent if i == 2 else cap,
                                 colorscale='RdBu' if i == 2 else 'Greens', colorbar=dict(title='Mio. m² NGF'), hovertemplate='%{y} / %{x}<br>%{z:.3f} Mio. m²<extra></extra>'))
    fig.update_layout(template='plotly_white', title='Qualität × Versorgung · B minus A', height=650, yaxis=dict(autorange='reversed'),
                      updatemenus=[dict(x=0, y=1.15, buttons=[dict(label=l, method='update', args=[{'visible': [j == i for j in range(3)]}, {'title': 'Qualität × Versorgung · ' + l}]) for i, l in enumerate(labels)])])
    return fig

def grafiken(erg):
    figs = {'Uebersicht': grafik_uebersicht(erg), 'Referenzvergleich': grafik_referenz(erg)}
    e = grafik_energie(erg)
    if e is not None:
        figs['Energie'] = e
    if erg['paarvergleich'] is not None:
        figs['Paar_Qualitaet_Versorgung'] = grafik_paar_matrix(erg['paarvergleich'])
    return figs

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def exportiere(erg, ersetzen=False, ergebnisordner=None):
    """Schreibt den Vergleich geprüft nach results/vergleiche/<Vergleich_ID>/ (Arbeitsordner, dann veröffentlichen)."""
    projekt = erg['projekt']
    base = Path(ergebnisordner) if ergebnisordner is not None else projekt['ergebnisse']['vergleiche']
    target = base / erg['vergleich_id']
    if target.exists() and not ersetzen:
        raise FileExistsError(f'{target} existiert; ERSETZEN=True setzen, um den Vergleich zu ersetzen.')
    base.mkdir(parents=True, exist_ok=True)
    stage = gs._neuer_arbeitsordner(base, erg['vergleich_id'])
    try:
        p = erg['paarvergleich']
        erg['kennwerte'].to_csv(stage / 'Kennwerte_Alle_Szenarien.csv', sep=';', index=False, encoding='utf-8-sig', float_format='%.12g')
        erg['vergleichbarkeit'].to_csv(stage / 'Vergleichbarkeit.csv', sep=';', index=False, encoding='utf-8-sig')
        erg['referenzvergleich'].to_csv(stage / 'Referenzvergleich.csv', sep=';', index=False, encoding='utf-8-sig', float_format='%.12g')
        paar = p['merkmale'].assign(Szenario_A=p['szenario_a'], Szenario_B=p['szenario_b']) if p is not None else pd.DataFrame(columns=['Hinweis'])
        paar.to_csv(stage / 'Paarvergleich.csv', sep=';', index=False, encoding='utf-8-sig', float_format='%.12g')
        (p['typen'] if p is not None else pd.DataFrame(columns=['Hinweis'])).to_csv(stage / 'Typenvergleich.csv', sep=';', index=False, encoding='utf-8-sig', float_format='%.10f')
        blaetter = {'Szenarien': erg['meta'], 'Status': statusuebersicht(erg), 'Uebersicht': erg['uebersicht'], 'Vergleichbarkeit': erg['vergleichbarkeit'],
                    'Referenzvergleich': erg['referenzvergleich']}
        if p is not None:
            blaetter.update({'Paar_Merkmale': p['merkmale'], 'Paar_Umverteilung': p['untergrenzen'],
                             'Paar_Qual_Vers_Delta': p['qe_delta'].rename_axis('Qualitaet').reset_index(), 'Paar_Kontrollen': p['kontrollen']})
        with pd.ExcelWriter(stage / 'Vergleich.xlsx', engine='openpyxl') as w:
            for name, df in blaetter.items():
                df.to_excel(w, sheet_name=name[:31], index=False)
                w.sheets[name[:31]].freeze_panes = 'B2'
        figs = grafiken(erg)
        seite = ['<!doctype html><html><head><meta charset="utf-8"><title>Szenarienvergleich</title></head><body style="font-family:sans-serif">',
                 '<h1>Szenarienvergleich ' + html.escape(erg['vergleich_id']) + '</h1>',
                 '<p>Referenz: ' + html.escape(erg['referenz']) + ' · Szenarien: ' + html.escape(', '.join(erg['szenarien'])) + '</p>',
                 '<p>Zustandsvergleich gespeicherter Ergebnisse. Jahreswerte sind mittlere Nettoänderungen, keine Brutto-Maßnahmenraten. Gleichjährige Szenarien erhalten keine Jahresraten.</p>',
                 statusuebersicht(erg).to_html(index=False)]
        seite += [f.to_html(full_html=False, include_plotlyjs=(i == 0)) for i, f in enumerate(figs.values())]
        seite.append('</body></html>')
        (stage / 'Vergleich.html').write_text('\n'.join(seite), encoding='utf-8')
        protokoll = {'schema_version': SCHEMA_VERSION, 'vergleich_id': erg['vergleich_id'], 'szenarien': erg['szenarien'], 'referenz': erg['referenz'],
                     'paar': erg['paar'], 'mindestabdeckung_pct': erg['mindestabdeckung_pct'], 'eingaben': erg['_eingaben'],
                     'szenariometadaten': json.loads(erg['meta'].to_json(orient='records', force_ascii=False)),
                     'statusuebersicht': json.loads(statusuebersicht(erg).to_json(orient='records', force_ascii=False)),
                     'regeln': {'differenzen_nur_bei': [VERGLEICHBAR, BEDINGT], 'relative_aenderung': 'nur bei Referenzwert ungleich 0',
                                'jahresrate': 'nur bei positiver Zeitspanne; mittlere Nettoänderung', 'energie_sperrt_flaeche': False,
                                'flussrekonstruktion': False},
                     'paarvergleich': None if p is None else {'szenario_a': p['szenario_a'], 'szenario_b': p['szenario_b'], 'jahre': p['jahre'],
                                                               'gleiche_ngf': p['gleiche_ngf'], 'kontrollen': p['kontrollen'].to_dict('records')},
                     'software': {**gs._software(), 'projektfassung': _projektfassung()}, 'modul_sha256': gs._sha(Path(__file__))}
        protokoll['ausgaben'] = {n: gs._sha(stage / n) for n in EXPORTDATEIEN if n != 'vergleichsprotokoll.json'}
        (stage / 'vergleichsprotokoll.json').write_text(json.dumps(protokoll, ensure_ascii=False, indent=2, allow_nan=False, default=str), encoding='utf-8')
        for n in EXPORTDATEIEN:
            if not (stage / n).is_file():
                raise IOError(f'Export unvollständig: {n}')
        gs.veroeffentliche_ordner(stage, target)
    finally:
        if stage.exists():
            gs.shutil.rmtree(stage)
    return target

def lade_vergleich(vergleich_id, projekt=None, ordner=None):
    """Lädt einen gespeicherten Vergleich und prüft die Ausgabehashes (nur lesen)."""
    if ordner is None:
        ordner = gs.lade_projekt(projekt)['ergebnisse']['vergleiche'] / vergleich_id
    ordner = Path(ordner)
    log = json.loads((ordner / 'vergleichsprotokoll.json').read_text(encoding='utf-8'))
    bad = [n for n, h in log.get('ausgaben', {}).items() if not (ordner / n).is_file() or gs._sha(ordner / n) != h]
    if bad:
        raise ValueError('Gespeicherter Vergleich verändert oder unvollständig: ' + ', '.join(bad))
    lies = lambda n: pd.read_csv(ordner / n, sep=';', encoding='utf-8-sig', keep_default_na=False, na_values=[''])
    return {'protokoll': log, 'kennwerte': lies('Kennwerte_Alle_Szenarien.csv'), 'vergleichbarkeit': lies('Vergleichbarkeit.csv'),
            'referenzvergleich': lies('Referenzvergleich.csv'), 'integritaet': 'OK (SHA-256 der Ausgaben geprüft)' if 'ausgaben' in log else 'ALTFORMAT'}
