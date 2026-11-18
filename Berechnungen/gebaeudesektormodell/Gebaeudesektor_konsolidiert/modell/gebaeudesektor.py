"""Gebäudesektormodell – Szenariokern.

Erstellt, analysiert, speichert und lädt reguläre Szenariozustände. Alle Pfade kommen aus
config/projekt.json (relativ zum Projektordner). Keine Flussrekonstruktion, keine Zielsteuerung.
"""
from pathlib import Path
from itertools import product
from collections import defaultdict
import json, hashlib, platform, warnings, re, shutil, copy, uuid
import numpy as np
import pandas as pd
import plotly.graph_objects as go
try:
    from IPython.display import display
except ImportError:  # Betrieb ohne Jupyter
    def display(obj):
        print(obj)
from distribution_to_json import DOMAENEN, distribution_to_json, validiere_eingabe
SCHEMA_VERSION = '1.0'
MODELLVERSION = '1.3.0-AP3'
PROJEKTDATEI = Path('config') / 'projekt.json'
ZUSTANDSSPALTEN = ['Szenario', 'Jahr', 'Archetype', 'geometry', 'quality', 'energy', 'pv', 'flex', 'weather', 'mass', 'NGF_m2', 'BGF_m2', 'Flaechenanteil']
KENNWERTSPALTEN = ['Szenario_ID', 'Zustand_ID', 'Jahr', 'Bereich', 'Gruppe', 'Kennwert', 'Kategorie', 'Wert', 'Einheit', 'Bezugsflaeche', 'Abdeckung_pct', 'Status', 'Vergleichsbasis_ID']
ENERGIE_NICHT_ANGEFORDERT = 'Nicht ausgeführt (nicht angefordert)'
WP_QUALITAETEN = frozenset(['1990-99', 'Neu_10cm', 'Neu_20cm', 'Neu_30cm'])
GEOS = DOMAENEN['geometrie']
QUAL = DOMAENEN['qualitaet']
ENERGY_PLAN = DOMAENEN['versorgung']
ENERGY = ['WP_Sole', 'WP_Wasser', 'WP_Luft', 'WP_Sole_fc', 'FW_Wien', 'FW_erneu', 'Bio', 'Erdgas', 'Oel', 'Elektro']
PVS = DOMAENEN['pv']
FLEX = DOMAENEN['flex']
WEATHER = ['Wien', 'Innsbruck']
MASS = DOMAENEN['masse']
DIMS = ['geometry', 'quality', 'energy', 'pv', 'flex', 'weather', 'mass']
REGION_WEATHER = {'Ost': 'Wien', 'Sued': 'Wien', 'West': 'Innsbruck'}
FW_WEATHER = {'Wien': 'FW_Wien', 'Innsbruck': 'FW_erneu'}
RES_USES = {'Wohngebäude mit einer Wohnung', 'Wohngebäude mit zwei Wohnungen', 'Wohngebäude mit drei und mehr Wohnungen'}
WOHN_GEOS = ['EFH_1G', 'EFH_2G', 'RH_2G', 'MFH_2G', 'MFH_4G', 'GWB_5G', 'GWB_7G']

def _sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

# ---------------------------------------------------------------------------
# Projektpfade: alle Pfade kommen aus config/projekt.json, relativ zum Projektordner.
# ---------------------------------------------------------------------------

def finde_projektwurzel(start=None):
    """Sucht ab `start` (Standard: aktuelles Verzeichnis) aufwärts den Ordner mit config/projekt.json."""
    start = Path.cwd() if start is None else Path(start)
    start = start.resolve()
    for folder in [start, *start.parents]:
        if (folder / PROJEKTDATEI).is_file():
            return folder
    raise FileNotFoundError(f'Kein Projektordner mit {PROJEKTDATEI.as_posix()} oberhalb von {start} gefunden.')

def _pfad(root, value):
    path = Path(value)
    return path if path.is_absolute() else Path(root) / path

def _relativ(root, path):
    """Projektrelativer Pfad (POSIX) für Protokolle; externe Dateien bleiben absolut."""
    path = Path(path)
    try:
        return path.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return str(path)

def lade_projekt(root=None):
    """Liest config/projekt.json und löst alle Pfade auf. Startet keine Berechnung."""
    if isinstance(root, dict) and 'root' in root:
        return root
    root = finde_projektwurzel(root)
    cfg = json.loads((root / PROJEKTDATEI).read_text(encoding='utf-8'))
    if cfg.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('Unbekanntes Projektschema in config/projekt.json.')
    for block in ['konfiguration', 'dateien', 'ergebnisse']:
        if not isinstance(cfg.get(block), dict):
            raise ValueError(f'config/projekt.json: Abschnitt {block} fehlt.')
    return {'root': root, 'cfg': cfg,
            'konfiguration': {k: _pfad(root, v) for k, v in cfg['konfiguration'].items()},
            'dateien': {k: _pfad(root, v) for k, v in cfg['dateien'].items()},
            'ergebnisse': {k: _pfad(root, v) for k, v in cfg['ergebnisse'].items()}}

def lade_szenarioregister(projekt=None):
    projekt = lade_projekt(projekt)
    cfg = json.loads(projekt['konfiguration']['szenarien'].read_text(encoding='utf-8'))
    if cfg.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('Unbekanntes Szenarioschema.')
    for name, p in cfg['szenarien'].items():
        if not re.fullmatch(r'[A-Za-z0-9_-]+', name):
            raise ValueError(f'Szenario-ID {name!r} ist kein sicherer Ordnername.')
        for key in ['jahr', 'statistikjahr', 'verteilungen']:
            if key not in p:
                raise ValueError(f'Szenario {name}: Angabe {key} fehlt.')
    return cfg

def registrierte_szenarien(projekt=None):
    """Übersicht der registrierten Szenarien (nur lesen)."""
    projekt = lade_projekt(projekt)
    cfg = lade_szenarioregister(projekt)
    rows = []
    for name, p in cfg['szenarien'].items():
        excel = _pfad(projekt['root'], p['verteilungen'])
        rows.append({'Szenario_ID': name, 'Typ': p.get('typ', ''), 'Jahr': p['jahr'], 'Statistikjahr': p['statistikjahr'],
                     'Ziel_NGF_m2': p.get('ziel_ngf_m2'), 'Verteilungsdatei': _relativ(projekt['root'], excel),
                     'Datei_vorhanden': excel.is_file(), 'Beschreibung': p.get('beschreibung', '')})
    return pd.DataFrame(rows)

def pruefe_projekt(projekt=None):
    """Prüft Projektpfade und Abhängigkeiten (nur lesen, keine Berechnung)."""
    projekt = lade_projekt(projekt)
    rows = []
    for gruppe in ['konfiguration', 'dateien']:
        for key, path in projekt[gruppe].items():
            optional = key in ('parquet',)
            ok = path.is_file()
            rows.append({'Bereich': gruppe, 'Eintrag': key, 'Pfad': _relativ(projekt['root'], path),
                         'Status': 'OK' if ok else ('FEHLT (optional)' if optional else 'FEHLT'),
                         'Hinweis': 'nur für die Energieanalyse erforderlich' if key == 'parquet' else ''})
    for key, path in projekt['ergebnisse'].items():
        rows.append({'Bereich': 'ergebnisse', 'Eintrag': key, 'Pfad': _relativ(projekt['root'], path),
                     'Status': 'OK' if path.is_dir() else 'wird beim ersten Export angelegt', 'Hinweis': ''})
    for modul, pflicht in [('numpy', True), ('pandas', True), ('scipy', True), ('openpyxl', True), ('plotly', True), ('pyarrow', False), ('IPython', False)]:
        try:
            m = __import__(modul)
            rows.append({'Bereich': 'python', 'Eintrag': modul, 'Pfad': getattr(m, '__version__', ''), 'Status': 'OK', 'Hinweis': ''})
        except ImportError:
            rows.append({'Bereich': 'python', 'Eintrag': modul, 'Pfad': '', 'Status': 'FEHLT' if pflicht else 'FEHLT (optional)',
                         'Hinweis': 'für scenarios.parquet erforderlich' if modul == 'pyarrow' else ''})
    rows.append({'Bereich': 'python', 'Eintrag': 'python', 'Pfad': platform.python_version(), 'Status': 'OK', 'Hinweis': ''})
    return pd.DataFrame(rows)

def _quellpfad(eingabe, source):
    return _pfad(eingabe['root'], source['datei'])

def lade_szenario(name, projekt=None):
    """Lädt und prüft die Eingaben eines registrierten Szenarios. Startet keine Zustandsberechnung."""
    projekt = lade_projekt(projekt)
    root = projekt['root']
    cfg = lade_szenarioregister(projekt)
    if name not in cfg['szenarien']:
        raise KeyError(f'Szenario {name!r} ist nicht in config/szenarien.json registriert.')
    p = cfg['szenarien'][name]
    files = dict(projekt['dateien'])
    excel = _pfad(root, p['verteilungen'])
    for path in [files['basis'], files['statistik'], excel]:
        if not path.is_file():
            raise FileNotFoundError(path)
    if not files['katalog'].exists() and (not files['parquet'].exists()):
        raise FileNotFoundError('Katalog oder Parquet erforderlich.')
    eingabe = distribution_to_json(excel, basis_json=files['basis'])
    pruefe_wp_prior(eingabe)
    register = projekt['konfiguration']['szenarien']
    sources = {k: {'datei': _relativ(root, v), 'sha256': _sha(v)} for k, v in {**files, 'excel': excel, 'szenarioregister': register}.items() if v.exists() and k != 'parquet'}
    # Das Szenarioregister enthält alle Szenarien; maßgeblich für die Zustands-ID ist nur das eigene Profil (payload 'profil').
    # Prüfsumme des Registers bleibt im Herkunftsnachweis (quellen), geht aber nicht in den Fingerprint ein (AP3).
    fp_sources = {k: v for k, v in copy.deepcopy(sources).items() if k != 'szenarioregister'}
    if files['parquet'].exists():
        st = files['parquet'].stat()
        sources['parquet'] = {'datei': _relativ(root, files['parquet']), 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns,
                              'nachweis': 'schwach (Pfad/Größe/Zeitstempel), kein Inhaltshash'}
        fp_sources['parquet'] = {'datei': files['parquet'].name, 'bytes': st.st_size}
    payload = {'name': name, 'profil': p, 'bilanz': cfg['bilanz'], 'cfg': eingabe, 'quellen': fp_sources, 'regeln': {'wp_qualitaeten': sorted(WP_QUALITAETEN)}}
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return dict(root=root, projekt=projekt, name=name, profil=copy.deepcopy(p), bilanz=copy.deepcopy(cfg['bilanz']), dateien=files, excel=excel, cfg=eingabe,
                quellen=sources, fingerprint=fingerprint, ergebnisordner=projekt['ergebnisse']['szenarien'] / name,
                snapshots={k: _pfad(root, v['datei']).read_bytes() for k, v in sources.items() if 'sha256' in v})

def zeige_eingaben(eingabe):
    """Tabellen zu Szenarioprofil und Eingabedateien (nur lesen)."""
    profil = pd.DataFrame([{'Angabe': k, 'Wert': str(v)} for k, v in eingabe['profil'].items()]
                          + [{'Angabe': 'ngf_zu_bgf_faktor', 'Wert': str(eingabe['cfg'].get('ngf_zu_bgf_faktor'))},
                             {'Angabe': 'parquet_batch', 'Wert': str(eingabe['cfg'].get('parquet_batch'))}])
    quellen = pd.DataFrame([{'Quelle': k, 'Datei': v['datei'], 'Nachweis': v.get('sha256', v.get('nachweis', ''))} for k, v in eingabe['quellen'].items()])
    return profil, quellen

def pruefe_wp_prior(cfg):
    for geo, table in cfg['verteilungen']['versorgung_nach_geometrie_qualitaet'].items():
        for q, mix in table.items():
            if q not in WP_QUALITAETEN and any((mix[e] > 0 for e in ENERGY_PLAN[:4])):
                raise ValueError(f'WP-Zulässigkeit verletzt: {geo}/{q}')

def pruefe_zieltypen(frame):
    invalid = frame.energy.isin(ENERGY_PLAN[:4]) & ~frame.quality.isin(WP_QUALITAETEN) & frame.NGF_m2.gt(0)
    if invalid.any():
        raise ValueError('Positive WP-Fläche in ausgeschlossener Qualität.')
    return True

def vorbereite_uebergang(a, b, unveraenderlich=('geometry', 'weather', 'mass')):
    for s in [a, b]:
        pruefe_zieltypen(s['verteilung'])
    for d in unveraenderlich:
        if d not in DIMS:
            raise ValueError(d)
    return {'schema_version': SCHEMA_VERSION, 'modus': 'Rekonstruktion', 'ausgang': {'szenario': a['name'], 'jahr': a['jahr'], 'zustand_id': a['zustand_id']}, 'ziel': {'szenario': b['name'], 'jahr': b['jahr'], 'zustand_id': b['zustand_id']}, 'unveraenderlich': list(unveraenderlich), 'wp_zielqualitaeten': sorted(WP_QUALITAETEN), 'neubau_abriss': None, 'zuordnungsprinzip': None, 'status': 'Nur Schnittstelle; keine Flüsse berechnet; Regeln noch festzulegen'}

def _initialisiere(eingabe):
    ROOT = eingabe['root']
    PROFIL = eingabe['name']
    SZENARIOTYP = eingabe['profil'].get('typ', 'nicht angegeben')
    eingabe_profil = copy.deepcopy(eingabe['profil'])
    SZENARIO = PROFIL
    SZENARIOJAHR = eingabe['profil']['jahr']
    STATISTIKJAHR = eingabe['profil']['statistikjahr']
    ZIEL_NGF_M2 = eingabe['profil'].get('ziel_ngf_m2')
    STAT_FILE = eingabe['dateien']['statistik']
    CATALOG_CSV = eingabe['dateien']['katalog']
    PARQUET = eingabe['dateien']['parquet']
    BASE_CONFIG_FILE = eingabe['dateien']['basis']
    EXCEL_FILE = eingabe['excel']
    CONFIG_FILE = BASE_CONFIG_FILE
    CFG = copy.deepcopy(eingabe['cfg'])
    V = CFG['verteilungen']
    BGF_FAKTOR = float(CFG['ngf_zu_bgf_faktor'])
    if not np.isfinite(BGF_FAKTOR) or BGF_FAKTOR <= 0:
        raise ValueError('Ungültiger NGF/BGF-Faktor.')
    HWB_BEZUG = eingabe['bilanz']['hwb_bezug']
    MIT_HILFSENERGIE = eingabe['bilanz']['mit_hilfsenergie']
    if HWB_BEZUG not in ['NGF', 'BGF']:
        raise ValueError('HWB-Bezug ungültig.')
    UMWELT_RW_COLUMN = eingabe['bilanz'].get('umwelt_rw_spalte')
    UMWELT_WW_COLUMN = eingabe['bilanz'].get('umwelt_ww_spalte')
    ENERGIE_ANALYSE = False  # Energie nur über analysiere_zustand(..., energie=True)
    ERLAUBE_REKONSTRUIERTEN_KATALOG = False
    AUDIT = []

    def check(label, actual, expected, tol=0.01):
        ok = bool(np.isfinite(actual) and abs(actual - expected) <= tol)
        AUDIT.append(dict(Pruefung=label, Ist=float(actual), Soll=float(expected), Status='OK' if ok else 'FEHLER'))
        if not ok:
            raise AssertionError(f'{label}: {actual} statt {expected}')

    def mix(dist, allowed, label):
        if not isinstance(dist, dict) or set(dist) != set(allowed):
            raise ValueError(f'{label}: Kategorien unvollständig oder unbekannt.')
        a = np.array(list(dist.values()), float)
        if not np.isfinite(a).all() or (a < 0).any():
            raise ValueError(f'{label}: ungültige Anteile.')
        check(label + ' Summe', a.sum(), 1, 1e-08)

    def positive(dist):
        return [(k, float(v)) for k, v in dist.items() if v > 0]

    def compare_series(label, a, b):
        idx = a.index.union(b.index)
        err = (a.reindex(idx, fill_value=0) - b.reindex(idx, fill_value=0)).abs().max()
        check(label, float(err) if len(idx) else 0.0, 0.0)

    def show(frame):
        return frame

    def style(fig, title, height=600):
        fig.update_layout(title=title, height=height, template='plotly_white', font=dict(size=12), margin=dict(t=120, b=70, l=150, r=40))
        return fig
    return locals()

def _pruefe_eingaben(state):
    STATISTIKJAHR = state['STATISTIKJAHR']
    V = state['V']
    mix = state['mix']
    required = {'geometrie_nach_nutzung_geschoss', 'qualitaet_nach_baujahr', 'masse_nach_nutzung', 'versorgung_nach_geometrie_qualitaet', 'pv_nach_geometrie', 'flex_nach_versorgung'}
    if set(V) != required:
        raise ValueError('Die sechs Verteilungsblöcke prüfen.')
    G_MAP = V['geometrie_nach_nutzung_geschoss']
    for use, storeys in G_MAP.items():
        for storey, dist in storeys.items():
            mix(dist, GEOS, f'Geometrie {use}/{storey}')
    next_year = 0
    intervals = sorted(V['qualitaet_nach_baujahr'], key=lambda b: b['Baujahr_von'])
    for band in intervals:
        lo, hi = (band['Baujahr_von'], band['Baujahr_bis'])
        if any((isinstance(x, bool) or not isinstance(x, int) for x in [lo, hi])):
            raise ValueError('Jahresgrenzen müssen ganzzahlig sein.')
        if lo != next_year or hi < lo:
            raise ValueError('Qualitätsintervalle haben Lücken oder Überlappungen.')
        mix(band['anteile'], QUAL, f'Qualität {lo}–{hi}')
        next_year = hi + 1
    if next_year <= STATISTIKJAHR:
        raise ValueError('Qualitätszuordnung deckt Statistikjahr nicht ab.')
    if set(V['masse_nach_nutzung']) != {'Wohnen', 'Nichtwohnen'}:
        raise ValueError('Massen-Nutzungsgruppen prüfen.')
    for use, dist in V['masse_nach_nutzung'].items():
        mix(dist, MASS, 'Masse ' + use)
    if set(V['versorgung_nach_geometrie_qualitaet']) != set(GEOS) or set(V['pv_nach_geometrie']) != set(GEOS):
        raise ValueError('Geometrien für Versorgung/PV prüfen.')
    if set(V['flex_nach_versorgung']) != set(ENERGY_PLAN):
        raise ValueError('Versorgungen für Flex prüfen.')
    for g in GEOS:
        if set(V['versorgung_nach_geometrie_qualitaet'][g]) != set(QUAL):
            raise ValueError('Versorgungsqualitäten unvollständig.')
        for q, dist in V['versorgung_nach_geometrie_qualitaet'][g].items():
            mix(dist, ENERGY_PLAN, 'Versorgung ' + g + '/' + q)
        mix(V['pv_nach_geometrie'][g], PVS, 'PV ' + g)
    for e, dist in V['flex_nach_versorgung'].items():
        mix(dist, FLEX, 'Flex ' + e)
    return {k: v for k, v in locals().items() if k != 'state'}

def _bilde_flaechen(state):
    herkunft = []
    CFG = state['CFG']
    G_MAP = state['G_MAP']
    STATISTIKJAHR = state['STATISTIKJAHR']
    STAT_FILE = state['STAT_FILE']
    ZIEL_NGF_M2 = state['ZIEL_NGF_M2']
    check = state['check']
    compare_series = state['compare_series']
    positive = state['positive']
    raw = pd.read_excel(STAT_FILE, sheet_name='Datenblatt 0', header=None).fillna('')
    starts = [i for i, v in enumerate(raw.iloc[6]) if str(v).strip().removesuffix('.0') == str(STATISTIKJAHR)]
    if len(starts) != 1:
        raise ValueError('Statistikjahr im Tabellenkopf nicht eindeutig.')
    cols = {'Ost': starts[0] + 1, 'Sued': starts[0] + 3, 'West': starts[0] + 5}
    if any(('nettogrundfläche' not in str(raw.iat[8, c]).lower() for c in cols.values())):
        raise ValueError('NGF-Spalten prüfen.')
    block = raw.iloc[10:640].copy()
    if len(block) != 630:
        raise ValueError('630 statistische Kategorien erwartet.')
    for c in [1, 2]:
        block[c] = block[c].replace('', np.nan).ffill()

    def numeric(v):
        if isinstance(v, str) and v.strip() in ['-', '–']:
            return 0.0
        n = float(v)
        if not np.isfinite(n) or n < 0:
            raise ValueError('Ungültige Statistikfläche.')
        return n
    STAT = pd.DataFrame([[str(r[1]).strip(), str(r[2]).strip(), str(r[3]).strip(), reg, numeric(r[c])] for _, r in block.iterrows() for reg, c in cols.items()], columns=['use', 'storey', 'period', 'region', 'ngf'])
    STAT_NGF = float(STAT.ngf.sum())
    TOTAL = STAT_NGF if ZIEL_NGF_M2 is None else float(ZIEL_NGF_M2)
    if not np.isfinite(TOTAL) or TOTAL <= 0 or STAT_NGF <= 0:
        raise ValueError('Gesamtfläche muss positiv sein.')
    SCALE = TOTAL / STAT_NGF
    YEAR_MAP = {'Vor 1919': [1918], '1919 bis 1944': range(1919, 1945), '1945 bis 1960': range(1945, 1961), '1961 bis 1970': range(1961, 1971), '1971 bis 1980': range(1971, 1981), '1981 bis 1990': range(1981, 1991), '1991 bis 2000': range(1991, 2001), '2001 bis 2010': range(2001, 2011), '2011 und später': range(2011, STATISTIKJAHR + 1)}
    if set(STAT.period) - set(YEAR_MAP):
        raise ValueError('Unbekannte statistische Bauperiode.')
    from distribution_to_json import baujahr_ngf_aus_statistik, kalibriere_qualitaet
    BAUJAHR_NGF = baujahr_ngf_aus_statistik(STAT, YEAR_MAP)
    BAUJAHR_NGF['ngf'] *= SCALE
    Q_ERGEBNIS, qualitaetsbericht = kalibriere_qualitaet(CFG, BAUJAHR_NGF)
    V = Q_ERGEBNIS['wirksame_verteilungen']
    intervals = sorted(V['qualitaet_nach_baujahr'], key=lambda b: b['Baujahr_von'])
    Q_YEAR = {}
    for band in intervals:
        for y in range(band['Baujahr_von'], min(band['Baujahr_bis'], STATISTIKJAHR) + 1):
            Q_YEAR[y] = positive(band['anteile'])
    PERIOD_Q = {}
    for p, years in YEAR_MAP.items():
        if not len(years) or max(years) > STATISTIKJAHR:
            raise ValueError('Bauperioden passen nicht zum Statistikjahr.')
        d = defaultdict(float)
        for y in years:
            for q, s in Q_YEAR[y]:
                d[q] += s / len(years)
        PERIOD_Q[p] = dict(d)
        check('Bauperiode ' + p, sum(d.values()), 1, 1e-08)
    cohorts = defaultdict(float)
    for r in STAT.itertuples(index=False):
        if r.use not in G_MAP or r.storey not in G_MAP[r.use]:
            raise ValueError(f'Geometriezuordnung fehlt: {r.use}/{r.storey}')
        if not r.ngf:
            continue
        u = 'Wohnen' if r.use in RES_USES else 'Nichtwohnen'
        for g, gs in positive(G_MAP[r.use][r.storey]):
            for q, qs in PERIOD_Q[r.period].items():
                cohorts[g, q, REGION_WEATHER[r.region], u] += r.ngf * SCALE * gs * qs
                herkunft.append([r.use, r.storey, r.period, r.region, g, q, REGION_WEATHER[r.region], u, r.ngf * SCALE * gs * qs])
    COHORT = pd.DataFrame([list(k) + [v] for k, v in cohorts.items()], columns=['geometry', 'quality', 'weather', 'usegroup', 'ngf'])
    check('NGF Geometrie/Qualität', COHORT.ngf.sum(), TOTAL)
    from distribution_to_json import kalibriere_verteilungen
    ERGEBNIS, kalibrierbericht = kalibriere_verteilungen(CFG, COHORT, qualitaet_ergebnis=Q_ERGEBNIS)
    V = ERGEBNIS['wirksame_verteilungen']
    for ziel in kalibrierbericht['Globale_Ziele'].itertuples(index=False):
        if pd.notna(ziel.Soll_Anteil):
            check(f'Globales Ziel {ziel.Verteilung}/{ziel.Kategorie}', ziel.Ist_NGF_m2, ziel.Soll_Anteil * TOTAL)
    rows = []
    for r in COHORT.itertuples(index=False):
        for e, es in positive(V['versorgung_nach_geometrie_qualitaet'][r.geometry][r.quality]):
            for p, ps in positive(V['pv_nach_geometrie'][r.geometry]):
                for f, fs in positive(V['flex_nach_versorgung'][e]):
                    for m, ms in positive(V['masse_nach_nutzung'][r.usegroup]):
                        rows.append([r.geometry, r.quality, FW_WEATHER[r.weather] if e == 'DH' else e, p, f, r.weather, m, r.ngf * es * ps * fs * ms])
    BASE = pd.DataFrame(rows, columns=DIMS + ['ngf']).groupby(DIMS, as_index=False, sort=False).ngf.sum()
    check('Szenario-NGF', BASE.ngf.sum(), TOTAL)
    if not np.isfinite(BASE.ngf).all() or (BASE.ngf < 0).any():
        raise ValueError('Ungültige Typenflächen.')
    wrong = BASE.energy.isin(FW_WEATHER.values()) & BASE.energy.ne(BASE.weather.map(FW_WEATHER))
    check('Fernwärme/Wetter', BASE.loc[wrong, 'ngf'].sum(), 0)
    PLAN_BASE = BASE.assign(energy=BASE.energy.replace({'FW_Wien': 'DH', 'FW_erneu': 'DH'}))
    for dim in ['geometry', 'quality', 'weather']:
        compare_series('Randsumme ' + dim, BASE.groupby(dim).ngf.sum(), COHORT.groupby(dim).ngf.sum())
    expected = defaultdict(float)
    for r in COHORT.itertuples(index=False):
        for e, s in positive(V['versorgung_nach_geometrie_qualitaet'][r.geometry][r.quality]):
            expected[r.geometry, r.quality, e] += r.ngf * s
    s = pd.Series(expected)
    s.index = pd.MultiIndex.from_tuples(s.index, names=['geometry', 'quality', 'energy'])
    compare_series('Versorgung je Geometrie/Qualität', PLAN_BASE.groupby(['geometry', 'quality', 'energy']).ngf.sum(), s)
    for dim, table in [('pv', 'pv_nach_geometrie')]:
        s = pd.Series({(g, k): a * v for g, a in COHORT.groupby('geometry').ngf.sum().items() for k, v in V[table][g].items()})
        s.index = pd.MultiIndex.from_tuples(s.index, names=['geometry', dim])
        compare_series('PV je Geometrie', BASE.groupby(['geometry', dim]).ngf.sum(), s)
    s = pd.Series({(e, f): a * v for e, a in PLAN_BASE.groupby('energy').ngf.sum().items() for f, v in V['flex_nach_versorgung'][e].items()})
    s.index = pd.MultiIndex.from_tuples(s.index, names=['energy', 'flex'])
    compare_series('Flex je Versorgung', PLAN_BASE.groupby(['energy', 'flex']).ngf.sum(), s)
    s = pd.Series({m: sum((a * V['masse_nach_nutzung'][u][m] for u, a in COHORT.groupby('usegroup').ngf.sum().items())) for m in MASS})
    compare_series('Masse je Nutzung', BASE.groupby('mass').ngf.sum(), s)
    HERKUNFT = pd.DataFrame(herkunft, columns=['use', 'storey', 'period', 'region', 'geometry', 'quality', 'weather', 'usegroup', 'ngf'])
    return {k: v for k, v in locals().items() if k != 'state'}

def _verbinde_katalog(state):
    BASE = state['BASE']
    BGF_FAKTOR = state['BGF_FAKTOR']
    CATALOG_CSV = state['CATALOG_CSV']
    CFG = state['CFG']
    ENERGIE_ANALYSE = state['ENERGIE_ANALYSE']
    ERLAUBE_REKONSTRUIERTEN_KATALOG = state['ERLAUBE_REKONSTRUIERTEN_KATALOG']
    PARQUET = state['PARQUET']
    SZENARIO = state['SZENARIO']
    SZENARIOJAHR = state['SZENARIOJAHR']
    TOTAL = state['TOTAL']
    UMWELT_RW_COLUMN = state['UMWELT_RW_COLUMN']
    UMWELT_WW_COLUMN = state['UMWELT_WW_COLUMN']
    check = state['check']
    show = state['show']
    THERMAL = ['district_heating', 'natural_gas', 'biomass', 'other']
    WANTED = ['UED_heating', 'NFA_total', 'GFA_total', 'EUI_el_total', 'EUIev_el', 'PV_total', 'Grid_to_building_min', 'PV_total_direct', 'PV_total_flex', 'PV_to_Egrid', 'VRGrid_to_building', 'EUIh_el', 'EUIdhw_el', 'EUIdhwdirect_el', 'EUIh_el_aux', 'Edhw_aux_el', 'PEI_import', 'PEI_export', 'PEI_saldo_project', 'PEI_grid_import', 'PEI_flex_import']
    WANTED += ['EUI_' + s for s in THERMAL] + ['EUIh_' + s for s in THERMAL] + ['EUIdhw_' + s for s in THERMAL]
    WANTED += [c for c in [UMWELT_RW_COLUMN, UMWELT_WW_COLUMN] if c]
    WANTED = list(dict.fromkeys(WANTED))
    EXPECTED = set(product(GEOS, QUAL, ENERGY, PVS, FLEX, WEATHER, MASS))
    SIM = None
    PARQUET_VALIDATED = False
    SIM_COLUMNS = []
    if PARQUET.exists():
        import pyarrow.parquet as pq
        available = pq.ParquetFile(PARQUET).schema_arrow.names
        if 'scenario_name' not in available:
            raise ValueError('scenario_name fehlt im Parquet.')
        keycols = ['scenario_name'] + (['batch'] if 'batch' in available else [])
        SIM_COLUMNS = [c for c in WANTED if c in available] if ENERGIE_ANALYSE else []
        loaded = pd.read_parquet(PARQUET, columns=keycols + SIM_COLUMNS)
        if not ENERGIE_ANALYSE:
            loaded = loaded.drop_duplicates()
        catalog = loaded[keycols].copy()
        SIM = loaded if ENERGIE_ANALYSE else None
        CATALOG_SOURCE = _relativ(state['ROOT'], PARQUET)
        PARQUET_VALIDATED = True
    elif CATALOG_CSV.exists():
        catalog = pd.read_csv(CATALOG_CSV, keep_default_na=False)
        CATALOG_SOURCE = _relativ(state['ROOT'], CATALOG_CSV)
    elif ERLAUBE_REKONSTRUIERTEN_KATALOG:
        catalog = pd.DataFrame({'scenario_name': ['|'.join(t) for t in product(GEOS, QUAL, ENERGY, PVS, FLEX, WEATHER, MASS)]})
        CATALOG_SOURCE = 'Rekonstruierter Domänenkatalog; nicht gegen Simulationen geprüft'
        warnings.warn(CATALOG_SOURCE)
    else:
        raise FileNotFoundError('Parquet oder typologien_43200.csv bereitstellen; Rekonstruktion nur ausdrücklich freigeben.')
    batch = CFG.get('parquet_batch')
    if batch is not None:
        if 'batch' not in catalog:
            raise ValueError('Batch-Auswahl ohne batch-Spalte.')
        select = catalog.batch.astype(str).eq(str(batch))
        catalog = catalog.loc[select].copy()
        if SIM is not None:
            SIM = SIM.loc[select].copy()

    def canonical(name):
        if not isinstance(name, str):
            raise ValueError('Typenname muss Text sein.')
        t = tuple((v.strip() for v in name.split('|')))
        if t not in EXPECTED:
            raise ValueError(f'Unbekannter vollständiger Typ: {name}')
        return t
    if 'scenario_name' not in catalog:
        raise ValueError('scenario_name fehlt im Katalog.')
    keys = catalog.scenario_name.map(canonical)
    if keys.duplicated().any():
        raise ValueError('Typenschlüssel nicht eindeutig; Batch oder doppelte Simulationszeilen prüfen.')
    if set(keys) != EXPECTED:
        raise ValueError(f'Katalog unvollständig: {len(EXPECTED - set(keys))} Typen fehlen.')
    CATALOG = catalog.reset_index(drop=True)
    for i, d in enumerate(DIMS):
        CATALOG[d] = [k[i] for k in keys]
    Verteilung = CATALOG.merge(BASE, on=DIMS, how='left', validate='one_to_one')
    Verteilung['NGF_m2'] = Verteilung.pop('ngf').fillna(0.0)
    Verteilung['BGF_m2'] = Verteilung.NGF_m2 * BGF_FAKTOR
    Verteilung['Flaechenanteil'] = Verteilung.NGF_m2 / TOTAL
    Verteilung['Szenario'] = SZENARIO
    Verteilung['Jahr'] = SZENARIOJAHR
    Verteilung['Archetype'] = Verteilung.pop('scenario_name')
    Verteilung['Parquet_geprueft'] = PARQUET_VALIDATED
    columns = ['Szenario', 'Jahr', 'Archetype'] + (['batch'] if 'batch' in Verteilung else []) + DIMS + ['NGF_m2', 'BGF_m2', 'Flaechenanteil', 'Parquet_geprueft']
    Verteilung = Verteilung[columns]
    check('Katalogumfang', len(Verteilung), 43200, 0)
    check('Übergabe-NGF', Verteilung.NGF_m2.sum(), TOTAL)
    check('Übergabe-BGF', Verteilung.BGF_m2.sum(), TOTAL * BGF_FAKTOR)
    check('Anteilsumme', Verteilung.Flaechenanteil.sum(), 1, 1e-08)
    show(Verteilung.head())
    return {k: v for k, v in locals().items() if k != 'state'}

def _eigenschaften(state):
    SZENARIO = state['SZENARIO']
    TOTAL = state['TOTAL']
    Verteilung = state['Verteilung']
    show = state['show']
    style = state['style']
    DIM_LABELS = {'geometry': 'Geometrie', 'quality': 'Qualität', 'energy': 'Planversorgung', 'pv': 'PV', 'flex': 'Flexibilität', 'weather': 'Wetter', 'mass': 'Speichermasse'}
    ORDERS = {'geometry': GEOS, 'quality': QUAL, 'energy': ENERGY_PLAN, 'pv': PVS, 'flex': FLEX, 'weather': WEATHER, 'mass': MASS}
    propdata = Verteilung.assign(energy=Verteilung.energy.replace({'FW_Wien': 'DH', 'FW_erneu': 'DH'}))
    props = []
    fig_properties = go.Figure()
    for i, dim in enumerate(DIMS):
        tab = propdata.groupby(dim).agg(NGF_m2=('NGF_m2', 'sum'), BGF_m2=('BGF_m2', 'sum'), Belegte_Typen=('NGF_m2', lambda s: int(s.gt(0).sum()))).reindex(ORDERS[dim], fill_value=0)
        tab['NGF_Anteil_pct'] = tab.NGF_m2 / TOTAL * 100
        props.append(tab.rename_axis('Auspraegung').reset_index().assign(Merkmal=DIM_LABELS[dim]))
        fig_properties.add_bar(x=tab.NGF_m2 / 1000000.0, y=tab.index, orientation='h', name=DIM_LABELS[dim], visible=i == 0, marker_color='#64856B', customdata=tab.NGF_Anteil_pct.to_numpy(), hovertemplate='%{y}<br>%{x:.3f} Mio. m² NGF<br>%{customdata:.2f} %<extra></extra>')
    Eigenschaften = pd.concat(props, ignore_index=True)
    show(Eigenschaften[['Merkmal', 'Auspraegung', 'NGF_m2', 'BGF_m2', 'NGF_Anteil_pct', 'Belegte_Typen']])
    fig_properties.update_layout(updatemenus=[dict(x=0, y=1.14, buttons=[dict(label=DIM_LABELS[d], method='update', args=[{'visible': [j == i for j in range(len(DIMS))]}, {'title': DIM_LABELS[d] + ' · ' + SZENARIO}]) for i, d in enumerate(DIMS)])], xaxis_title='Mio. m² NGF', yaxis=dict(autorange='reversed'), showlegend=False)
    style(fig_properties, 'Geometrie · ' + SZENARIO)
    Q_E = propdata.pivot_table(index='quality', columns='energy', values='NGF_m2', aggfunc='sum', fill_value=0).reindex(index=QUAL, columns=ENERGY_PLAN, fill_value=0)
    show(Q_E / 1000000.0)
    matrices = [('Fläche', Q_E / 1000000.0, 'Mio. m² NGF'), ('Zeilenprozente', Q_E.div(Q_E.sum(axis=1).replace(0, np.nan), axis=0) * 100, '% der Qualität'), ('Spaltenprozente', Q_E.div(Q_E.sum(axis=0).replace(0, np.nan), axis=1) * 100, '% der Versorgung')]
    fig_matrix = go.Figure()
    for i, (label, tab, unit) in enumerate(matrices):
        fig_matrix.add_trace(go.Heatmap(x=tab.columns, y=tab.index, z=tab.to_numpy(), visible=i == 0, colorscale=[[0, '#FAFBF9'], [1, '#365A42']], zmin=0, zmax=100 if i else None, colorbar=dict(title=unit), hoverongaps=False, hovertemplate='%{y} / %{x}<br>%{z:.3f} ' + unit + '<extra></extra>'))
    fig_matrix.update_layout(updatemenus=[dict(x=0, y=1.14, buttons=[dict(label=label, method='update', args=[{'visible': [j == i for j in range(3)]}, {'title': 'Qualität × Versorgung · ' + label + ' · ' + SZENARIO}]) for i, (label, tab, unit) in enumerate(matrices)])], xaxis_title='Planversorgung', yaxis=dict(title='Qualität', autorange='reversed'))
    style(fig_matrix, 'Qualität × Versorgung · Fläche · ' + SZENARIO)
    return {k: v for k, v in locals().items() if k != 'state'}

def _energie_basis(state):
    BGF_FAKTOR = state['BGF_FAKTOR']
    ENERGIE_ANALYSE = state['ENERGIE_ANALYSE']
    SIM = state['SIM']
    SIM_COLUMNS = state['SIM_COLUMNS']
    Verteilung = state['Verteilung']
    canonical = state['canonical']
    data = Verteilung.copy()
    ENERGIE_BEREIT = bool(ENERGIE_ANALYSE and SIM is not None)
    ENERGY_STATUS = ENERGIE_NICHT_ANGEFORDERT if not ENERGIE_ANALYSE else 'Kein Simulations-Parquet vorhanden'
    Energiekennwerte = pd.DataFrame()
    Endenergie = pd.DataFrame()
    Raumwaerme_Warmwasser = pd.DataFrame()
    PV_Geometrie = pd.DataFrame()
    Haushaltsvergleich = pd.DataFrame()
    if ENERGIE_BEREIT:
        sim = SIM[['scenario_name'] + [c for c in SIM_COLUMNS if c in SIM]].copy()
        sim['_key'] = sim.scenario_name.map(canonical)
        if sim._key.duplicated().any():
            raise ValueError('Simulationen nach Batch-Auswahl nicht eindeutig.')
        data['_key'] = data.Archetype.map(canonical)
        data = data.merge(sim.drop(columns='scenario_name'), on='_key', how='left', validate='one_to_one', indicator='_simulation')
        if data.loc[data.NGF_m2.gt(0), '_simulation'].ne('both').any():
            raise ValueError('Belegte Szenariotypen ohne Simulationsergebnis.')
        data = data.drop(columns=['_key', '_simulation'])
        if {'NFA_total', 'GFA_total'} <= set(data):
            active = data.NGF_m2.gt(0)
            ratio = pd.to_numeric(data.NFA_total, errors='coerce') / pd.to_numeric(data.GFA_total, errors='coerce')
            if not np.isfinite(ratio.loc[active]).all():
                raise ValueError('NFA/GFA-Verhältnis fehlt auf belegter Fläche.')
            np.testing.assert_allclose(ratio.loc[active], 1 / BGF_FAKTOR, rtol=1e-05, atol=1e-08)
        ENERGY_STATUS = 'Ausgeführt'
    else:
        print('Energetische Auswertung:', ENERGY_STATUS)
    r = 1 / BGF_FAKTOR
    for original, alias in [('geometry', 'Geometrie'), ('quality', 'Huelle'), ('energy', 'Heizung'), ('pv', 'PV_Klasse'), ('flex', 'Flexibilitaet'), ('weather', 'Wetter'), ('mass', 'Masse')]:
        data[alias] = data[original]

    def value(name):
        if name is None or name not in data:
            return pd.Series(np.nan, index=data.index, dtype=float)
        return pd.to_numeric(data[name], errors='coerce').replace([np.inf, -np.inf], np.nan)

    def add(names):
        return pd.concat([value(c) for c in names], axis=1).sum(axis=1, min_count=len(names))

    def energy_total(values, mask=None, basis='NGF'):
        if mask is None:
            mask = pd.Series(True, index=data.index)
        weights = data['NGF_m2' if basis == 'NGF' else 'BGF_m2'].where(mask, 0.0)
        active = weights.gt(0)
        valid = np.isfinite(values)
        total_area = float(weights.sum())
        missing = float(weights.loc[active & ~valid].sum())
        known = float((values.loc[active & valid] * weights.loc[active & valid]).sum())
        kwh = known if missing == 0 else np.nan
        ngf = float(data.loc[mask, 'NGF_m2'].sum())
        bgf = float(data.loc[mask, 'BGF_m2'].sum())
        return {'kWh': kwh, 'GWh/a': kwh / 1000000.0, 'TWh/a': kwh / 1000000000.0, 'PJ/a': kwh * 3.6e-09, 'kWh/(m² NGF a)': kwh / ngf if ngf else np.nan, 'kWh/(m² BGF a)': kwh / bgf if bgf else np.nan, 'Abdeckung_pct': 100 * (1 - missing / total_area) if total_area else np.nan, 'bekannt_GWh': known / 1000000.0, 'Status': 'keine Fläche' if not total_area else 'OK' if not missing else 'Kennwerte unvollständig'}
    return {k: v for k, v in locals().items() if k != 'state'}

def _energie_bilanzen(state):
    ENERGIE_BEREIT = state['ENERGIE_BEREIT']
    HWB_BEZUG = state['HWB_BEZUG']
    MIT_HILFSENERGIE = state['MIT_HILFSENERGIE']
    SZENARIOJAHR = state['SZENARIOJAHR']
    THERMAL = state['THERMAL']
    UMWELT_RW_COLUMN = state['UMWELT_RW_COLUMN']
    UMWELT_WW_COLUMN = state['UMWELT_WW_COLUMN']
    add = state['add']
    data = state['data']
    energy_total = state['energy_total']
    value = state['value']
    if ENERGIE_BEREIT:
        is_oil = data.energy.eq('Oel')
        data['Strombedarf'] = value('EUI_el_total') - value('EUIev_el')
        data['PV_Erzeugung'] = value('PV_total')
        ee_rw = add(['EUIh_el'] + ['EUIh_' + s for s in THERMAL])
        ee_ww = add(['EUIdhw_el', 'EUIdhwdirect_el'] + ['EUIdhw_' + s for s in THERMAL])
        el_rw = value('EUIh_el')
        el_ww = value('EUIdhw_el') + value('EUIdhwdirect_el')
        if not MIT_HILFSENERGIE:
            el_rw -= value('EUIh_el_aux')
            el_ww -= value('Edhw_aux_el')
            ee_rw -= value('EUIh_el_aux')
            ee_ww -= value('Edhw_aux_el')
        metric_specs = [('Wärme', 'Heizwärmebedarf', value('UED_heating'), HWB_BEZUG), ('Wärme', 'Endenergie Raumwärme ohne Umgebungswärme', ee_rw, 'NGF'), ('Wärme', 'Endenergie Warmwasser ohne Umgebungswärme', ee_ww, 'NGF'), ('Wärme', 'Endenergie RW + WW ohne Umgebungswärme', ee_rw + ee_ww, 'NGF'), ('Strom', 'Strom-Bruttobedarf ohne Mobilität', data.Strombedarf, 'NGF'), ('Strom', 'Netzbezug', value('Grid_to_building_min'), 'NGF'), ('Strom', 'Flexibler Bezug', value('VRGrid_to_building'), 'NGF'), ('PV', 'PV-Erzeugung', value('PV_total'), 'NGF'), ('PV', 'PV-Direktverbrauch', value('PV_total_direct'), 'NGF'), ('PV', 'PV-Flexverbrauch', value('PV_total_flex'), 'NGF'), ('PV', 'PV-Einspeisung', value('PV_to_Egrid'), 'NGF')]
        masks = {'Gesamt': pd.Series(True, index=data.index), 'Haushalte': data.geometry.isin(WOHN_GEOS), 'Nichtwohnen': ~data.geometry.isin(WOHN_GEOS)}
        records = []
        for sector, mask in masks.items():
            for group, label, series, basis in metric_specs:
                records.append({'Bereich': sector, 'Gruppe': group, 'Kennwert': label, **energy_total(series, mask, basis)})
        Energiekennwerte = pd.DataFrame(records)
        pe = []
        for sector, mask in masks.items():
            for c in ['PEI_grid_import', 'PEI_flex_import', 'PEI_import', 'PEI_export', 'PEI_saldo_project']:
                a = energy_total(value(c), mask)
                pe.append({'Bereich': sector, 'Kennwert': c, 'GWh_PE/a': a['GWh/a'], 'PJ_PE/a': a['PJ/a'], 'Abdeckung_pct': a['Abdeckung_pct'], 'Status': a['Status']})
        Primaerenergie = pd.DataFrame(pe)
        carriers = {'Strom ohne Mobilität': data.Strombedarf, 'Fernwärme': value('EUI_district_heating'), 'Erdgas': value('EUI_natural_gas'), 'Biomasse': value('EUI_biomass'), 'Heizöl': value('EUI_other').where(is_oil, 0), 'Sonstige thermisch': value('EUI_other').where(~is_oil, 0)}
        end = []
        applications = []
        rw = {k: value('EUIh_' + s) for k, s in [('Fernwärme', 'district_heating'), ('Erdgas', 'natural_gas'), ('Biomasse', 'biomass')]}
        ww = {k: value('EUIdhw_' + s) for k, s in [('Fernwärme', 'district_heating'), ('Erdgas', 'natural_gas'), ('Biomasse', 'biomass')]}
        rw.update({'Heizöl': value('EUIh_other').where(is_oil, 0), 'Sonstige thermisch': value('EUIh_other').where(~is_oil, 0), 'Elektrische Energie': el_rw, 'Umgebungswärme': value(UMWELT_RW_COLUMN)})
        ww.update({'Heizöl': value('EUIdhw_other').where(is_oil, 0), 'Sonstige thermisch': value('EUIdhw_other').where(~is_oil, 0), 'Elektrische Energie': el_ww, 'Umgebungswärme': value(UMWELT_WW_COLUMN)})
        for sector, mask in masks.items():
            sector_end = []
            for label, series in carriers.items():
                a = energy_total(series, mask)
                sector_end.append(a['kWh'])
                end.append({'Bereich': sector, 'Träger': label, **a})
            total = np.sum(sector_end)
            end.append({'Bereich': sector, 'Träger': 'SUMME ohne Umgebungswärme', 'kWh': total, 'GWh/a': total / 1000000.0, 'PJ/a': total * 3.6e-09, 'Status': 'OK' if np.isfinite(total) else 'Kennwerte unvollständig'})
            for label in rw:
                h = energy_total(rw[label], mask)
                w = energy_total(ww[label], mask)
                applications.append({'Bereich': sector, 'Träger': label, 'Raumwärme [GWh/a]': h['GWh/a'], 'Warmwasser [GWh/a]': w['GWh/a'], 'RW + WW [GWh/a]': h['GWh/a'] + w['GWh/a'], 'Abdeckung_RW_pct': h['Abdeckung_pct'], 'Abdeckung_WW_pct': w['Abdeckung_pct']})
            sub = pd.DataFrame([a for a in applications if a['Bereich'] == sector])
            applications.append({'Bereich': sector, 'Träger': 'SUMME', **sub[['Raumwärme [GWh/a]', 'Warmwasser [GWh/a]', 'RW + WW [GWh/a]']].sum(skipna=False).to_dict()})
        Endenergie = pd.DataFrame(end)
        Raumwaerme_Warmwasser = pd.DataFrame(applications)
        pv = []
        for label in GEOS + ['GESAMT']:
            mask = masks['Gesamt'] if label == 'GESAMT' else data.geometry.eq(label)
            pv.append({'Geometrie': label, 'NGF_m2': float(data.loc[mask, 'NGF_m2'].sum()), 'BGF_m2': float(data.loc[mask, 'BGF_m2'].sum()), **energy_total(value('PV_total'), mask)})
        PV_Geometrie = pd.DataFrame(pv)
        Haushaltsvergleich = Raumwaerme_Warmwasser.loc[Raumwaerme_Warmwasser.Bereich.eq('Haushalte')].set_index('Träger').copy()
        if SZENARIOJAHR == 2024:
            soll = pd.Series({'Heizöl': 7846.0, 'Erdgas': 13936.0, 'Biomasse': 24208.0, 'Elektrische Energie': 9952.0, 'Umgebungswärme': 5724.0, 'Fernwärme': 10351.0, 'SUMME': 72017.0})
            Haushaltsvergleich['Soll2024 [GWh/a]'] = soll.reindex(Haushaltsvergleich.index)
            Haushaltsvergleich['Abweichung [GWh/a]'] = Haushaltsvergleich['RW + WW [GWh/a]'] - Haushaltsvergleich['Soll2024 [GWh/a]']
            Haushaltsvergleich['Abweichung_pct'] = 100 * Haushaltsvergleich['Abweichung [GWh/a]'] / Haushaltsvergleich['Soll2024 [GWh/a]']
        else:
            print('Haushalts-Sollwerte2024 werden für dieses Szenariojahr nicht angewendet.')
    else:
        Primaerenergie = pd.DataFrame()
    return {k: v for k, v in locals().items() if k != 'state'}

def _energie_grafik(state):
    ENERGIE_BEREIT = state['ENERGIE_BEREIT']
    Endenergie = state['Endenergie']
    Energiekennwerte = state['Energiekennwerte']
    Haushaltsvergleich = state['Haushaltsvergleich']
    PV_Geometrie = state['PV_Geometrie']
    Primaerenergie = state['Primaerenergie']
    Raumwaerme_Warmwasser = state['Raumwaerme_Warmwasser']
    SZENARIO = state['SZENARIO']
    show = state['show']
    style = state['style']
    ENERGIE_BEREICH = 'Gesamt'
    if ENERGIE_BEREIT:
        show(Energiekennwerte.loc[Energiekennwerte.Bereich.eq(ENERGIE_BEREICH), ['Kennwert', 'GWh/a', 'PJ/a', 'kWh/(m² NGF a)', 'Abdeckung_pct', 'Status']])
        show(Endenergie.loc[Endenergie.Bereich.eq(ENERGIE_BEREICH), ['Träger', 'GWh/a', 'PJ/a', 'Abdeckung_pct', 'Status']])
        show(Raumwaerme_Warmwasser.loc[Raumwaerme_Warmwasser.Bereich.eq(ENERGIE_BEREICH)])
        show(PV_Geometrie[['Geometrie', 'BGF_m2', 'GWh/a', 'kWh/(m² BGF a)', 'Abdeckung_pct', 'Status']])
        show(Haushaltsvergleich)
        show(Primaerenergie.loc[Primaerenergie.Bereich.eq(ENERGIE_BEREICH)])
        groups = []
        for group in ['Wärme', 'Strom', 'PV']:
            sub = Energiekennwerte.loc[Energiekennwerte.Bereich.eq(ENERGIE_BEREICH) & Energiekennwerte.Gruppe.eq(group)]
            groups.append((group, sub.Kennwert, sub['PJ/a']))
        sub = Endenergie.loc[Endenergie.Bereich.eq(ENERGIE_BEREICH) & ~Endenergie.Träger.str.startswith('SUMME')]
        groups.append(('Energieträger', sub.Träger, sub['PJ/a']))
        fig_energy = go.Figure()
        for i, (label, y, x) in enumerate(groups):
            fig_energy.add_bar(x=x, y=y, orientation='h', name=label, visible=i == 0, marker_color='#64856B')
        fig_energy.update_layout(updatemenus=[dict(x=0, y=1.14, buttons=[dict(label=label, method='update', args=[{'visible': [j == i for j in range(len(groups))]}, {'title': label + ' · ' + ENERGIE_BEREICH + ' · ' + SZENARIO}]) for i, (label, y, x) in enumerate(groups)])], xaxis_title='PJ/a', yaxis=dict(autorange='reversed'), showlegend=False)
        style(fig_energy, 'Wärme · ' + ENERGIE_BEREICH + ' · ' + SZENARIO)
    return {k: v for k, v in locals().items() if k != 'state'}

def _exportiere_kompatibel(state,stage):
    AUDIT=state['AUDIT']
    BGF_FAKTOR=state['BGF_FAKTOR']
    CATALOG_CSV=state['CATALOG_CSV']
    CATALOG_SOURCE=state['CATALOG_SOURCE']
    CFG=state['CFG']
    CONFIG_FILE=state['CONFIG_FILE']
    ENERGIE_BEREIT=state['ENERGIE_BEREIT']
    ENERGY_STATUS=state['ENERGY_STATUS']
    ERGEBNIS=state['ERGEBNIS']
    Eigenschaften=state['Eigenschaften']
    Endenergie=state['Endenergie']
    Energiekennwerte=state['Energiekennwerte']
    G_MAP=state['G_MAP']
    HWB_BEZUG=state['HWB_BEZUG']
    Haushaltsvergleich=state['Haushaltsvergleich']
    MIT_HILFSENERGIE=state['MIT_HILFSENERGIE']
    PARQUET=state['PARQUET']
    PARQUET_VALIDATED=state['PARQUET_VALIDATED']
    PROFIL=state['PROFIL']
    PV_Geometrie=state['PV_Geometrie']
    Primaerenergie=state['Primaerenergie']
    Q_E=state['Q_E']
    Raumwaerme_Warmwasser=state['Raumwaerme_Warmwasser']
    SCALE=state['SCALE']
    SIM_COLUMNS=state['SIM_COLUMNS']
    STATISTIKJAHR=state['STATISTIKJAHR']
    STAT_FILE=state['STAT_FILE']
    STAT_NGF=state['STAT_NGF']
    SZENARIO=state['SZENARIO']
    SZENARIOJAHR=state['SZENARIOJAHR']
    TOTAL=state['TOTAL']
    UMWELT_RW_COLUMN=state['UMWELT_RW_COLUMN']
    UMWELT_WW_COLUMN=state['UMWELT_WW_COLUMN']
    V=state['V']
    Verteilung=state['Verteilung']
    WANTED=state['WANTED']
    ZIEL_NGF_M2=state['ZIEL_NGF_M2']
    batch=state['batch']
    intervals=state['intervals']
    kalibrierbericht=state['kalibrierbericht']
    show=state['show']
    EXPORT_ERSETZEN=True
    CONFIG_FILE=stage/'eingaben'/'annahmen_aufgeloest.json'
    CHECKS=pd.DataFrame(AUDIT)
    show(CHECKS.groupby('Status').size().to_frame('Pruefungen'))
    slug=re.sub(r'[^A-Za-z0-9_-]+','_',SZENARIO).strip('_')
    if not slug:raise ValueError('Ungültige Szenario-Speicherkennung.')
    OUT=stage;OUT.mkdir(parents=True,exist_ok=True)
    paths=[OUT/'Verteilung.csv',OUT/'Szenario.xlsx',OUT/'laufprotokoll.json']
    if not EXPORT_ERSETZEN and any(p.exists() for p in paths):raise FileExistsError('Ausgabe existiert; Namen oder EXPORT_ERSETZEN prüfen.')
    Verteilung.to_csv(paths[0],sep=';',index=False,encoding='utf-8-sig',float_format='%.10f')
    G_TABLE=pd.DataFrame([{'Nutzung':u,'Geschoss':s,**d} for u,ss in G_MAP.items() for s,d in ss.items()])
    Q_TABLE=pd.DataFrame([{'Baujahr_von':b['Baujahr_von'],'Baujahr_bis':b['Baujahr_bis'],**b['anteile']} for b in intervals])
    frames={'Verteilung':Verteilung,'Kontrollen':CHECKS,'Eigenschaften':Eigenschaften,
        'Qualitaet_Versorgung':Q_E.rename_axis('Qualitaet').reset_index(),
        'Geometriezuordnung':G_TABLE,'Qualitaetszuordnung':Q_TABLE,
        'Analyse_Status':pd.DataFrame([{'Energieanalyse':ENERGY_STATUS,'Parquet_geprueft':PARQUET_VALIDATED,
            'HWB_Bezug':HWB_BEZUG,'Hilfsenergie_RW_WW':MIT_HILFSENERGIE}])}
    frames.update({'Kalib_Ziele':kalibrierbericht['Globale_Ziele'],'Kalib_Bedingt':kalibrierbericht['Bedingte_Verteilungen'],
                   'Kalib_Kontrollen':kalibrierbericht['Kontrollen'],'Kalib_Rundungen':kalibrierbericht['Rundungen']})
    if ENERGIE_BEREIT:
        frames.update({'Energiekennwerte':Energiekennwerte,'Endenergietraeger':Endenergie,
            'Raumwaerme_Warmwasser':Raumwaerme_Warmwasser,'PV_Geometrie':PV_Geometrie,
            'Haushaltsvergleich':Haushaltsvergleich.reset_index(),'Primaerenergie':Primaerenergie})
    with pd.ExcelWriter(paths[1],engine='openpyxl') as writer:
        for name,frame in frames.items():
            frame.to_excel(writer,sheet_name=name,index=False);writer.sheets[name].freeze_panes='B2'
    def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    used={'szenario':{'name':SZENARIO,'jahr':SZENARIOJAHR,'statistikjahr':STATISTIKJAHR,'ngf_m2':TOTAL},
        'ngf_zu_bgf_faktor':BGF_FAKTOR,'parquet_batch':batch,'verteilungen':V,
        'region_nach_wetter':REGION_WEATHER,'fernwaerme_nach_wetter':FW_WEATHER}
    log={'wirksame_konfiguration':used,'kalibrierungsnachweis':ERGEBNIS['metadaten'],
        'kalibrierung_eingabe':CFG.get('kalibrierung',{}),
        'szenarioannahmen':{'typ':state['SZENARIOTYP'],'beschreibung':state['eingabe_profil'].get('beschreibung',''),
            'konstante_gesamtflaeche':ZIEL_NGF_M2 is None,'neubau_abriss_explizit':False,'zukuenftige_kennwerte_oder_klimadaten':False},'statistik_ngf_m2':STAT_NGF,'skalierung':SCALE,
        'katalogquelle':CATALOG_SOURCE,'parquet_geprueft':PARQUET_VALIDATED,
        'typen':len(Verteilung),'positive_typen':int(Verteilung.NGF_m2.gt(0).sum()),
        'eingaben':{'json':{'datei':str(CONFIG_FILE),'sha256':sha(CONFIG_FILE)},
                   'statistik':{'datei':_relativ(state['ROOT'],STAT_FILE),'sha256':sha(STAT_FILE)}},
        'excel_verteilungen':CFG.get('eingabe_verteilungen',{}),
        'energieanalyse':{'status':ENERGY_STATUS,'hwb_spalte':'UED_heating','hwb_bezug':HWB_BEZUG,
            'hilfsenergie_rw_ww':MIT_HILFSENERGIE,'umwelt_rw_spalte':UMWELT_RW_COLUMN,'umwelt_ww_spalte':UMWELT_WW_COLUMN,
            'fehlende_spalten':sorted(set(WANTED)-set(SIM_COLUMNS)) if ENERGIE_BEREIT else [],
            'abgrenzung':'EUI/PV je NGF; Strom ohne Mobilität, kein Abzug des PV-Eigenverbrauchs'},
        'kontrollen':CHECKS.to_dict('records'),
        'software':_software()}
    if PARQUET.exists():log['eingaben']['parquet']={'datei':_relativ(state['ROOT'],PARQUET),'bytes':PARQUET.stat().st_size,'mtime_ns':PARQUET.stat().st_mtime_ns,'nachweis':'schwach (Pfad/Größe/Zeitstempel)'}
    elif CATALOG_CSV.exists():log['eingaben']['katalog_csv']={'datei':_relativ(state['ROOT'],CATALOG_CSV),'sha256':sha(CATALOG_CSV)}
    paths[2].write_text(json.dumps(log,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    for p in paths:
        if not p.is_file() or not p.stat().st_size:raise IOError(f'Export fehlt: {p}')

    return log

def _software():
    info = {'python': platform.python_version(), 'pandas': pd.__version__, 'numpy': np.__version__, 'modellversion': MODELLVERSION}
    for name in ['scipy', 'openpyxl', 'plotly', 'pyarrow']:
        try:
            info[name] = __import__(name).__version__
        except ImportError:
            info[name] = None
    return info

def erstelle_zustand(eingabe):
    """Erstellt den Flächenzustand (vollständiger 43.200-Typen-Katalog). Keine Energieanalyse."""
    for source in eingabe['quellen'].values():
        if 'sha256' in source and _sha(_quellpfad(eingabe, source)) != source['sha256']:
            raise ValueError('Eingabe seit dem Laden verändert: ' + source['datei'])
    state = _initialisiere(eingabe)
    for step in [_pruefe_eingaben, _bilde_flaechen, _verbinde_katalog]:
        state.update(step(state))
    pruefe_zieltypen(state['Verteilung'])
    identity = {'eingabe': eingabe['fingerprint'], 'kern_sha256': _sha(__file__), 'kalibrierung_sha256': _sha(Path(__file__).with_name('distribution_to_json.py'))}
    zustand_id = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return {'name': eingabe['name'], 'jahr': eingabe['profil']['jahr'], 'zustand_id': zustand_id, 'verteilung': state['Verteilung'].copy(),
            'herkunftskohorten': state['HERKUNFT'].copy(), 'kontrollen': pd.DataFrame(state['AUDIT']).copy(), '_arbeitsdaten': state, 'eingabe': eingabe}

def _lade_simulation(state, eingabe):
    """Lädt Simulationskennwerte für die Energieanalyse (nur auf ausdrückliche Anforderung)."""
    PARQUET = state['PARQUET']
    if not PARQUET.exists():
        return {'SIM': None, 'SIM_COLUMNS': [], 'ENERGIE_ANALYSE': True}
    quelle = eingabe['quellen'].get('parquet')
    st = PARQUET.stat()
    if quelle is None or quelle['bytes'] != st.st_size or quelle['mtime_ns'] != st.st_mtime_ns:
        raise ValueError('Simulationsdatei seit dem Laden der Eingaben verändert oder ersetzt.')
    import pyarrow.parquet as pq
    available = pq.ParquetFile(PARQUET).schema_arrow.names
    keycols = ['scenario_name'] + (['batch'] if 'batch' in available else [])
    columns = [c for c in state['WANTED'] if c in available]
    sim = pd.read_parquet(PARQUET, columns=keycols + columns)
    batch = state['CFG'].get('parquet_batch')
    if batch is not None:
        if 'batch' not in sim:
            raise ValueError('Batch-Auswahl ohne batch-Spalte.')
        sim = sim.loc[sim.batch.astype(str).eq(str(batch))].copy()
    return {'SIM': sim, 'SIM_COLUMNS': columns, 'ENERGIE_ANALYSE': True}

def analysiere_zustand(zustand, eingabe=None, energie=False):
    """Eigenschaftsanalyse; Energieanalyse nur mit energie=True und vorhandenem Simulations-Parquet."""
    if eingabe is not None and eingabe['fingerprint'] != zustand['eingabe']['fingerprint']:
        raise ValueError('Andere Eingabe als im Zustand.')
    state = dict(zustand['_arbeitsdaten'])
    state.update({'SIM': None, 'SIM_COLUMNS': [], 'ENERGIE_ANALYSE': False})
    if energie:
        state.update(_lade_simulation(state, zustand['eingabe']))
    for step in [_eigenschaften, _energie_basis, _energie_bilanzen, _energie_grafik]:
        state.update(step(state))
    bewertung = {'eigenschaften': state['Eigenschaften'], 'energiestatus': state['ENERGY_STATUS'], '_arbeitsdaten': state, 'zustand_id': zustand['zustand_id']}
    bewertung['kennwerte'] = kennwerttabelle(zustand, bewertung)
    return bewertung

def zeige_ergebnisse(zustand, bewertung):
    display(bewertung['eigenschaften'])
    state = bewertung['_arbeitsdaten']
    for key in ['fig_properties', 'fig_matrix', 'fig_energy']:
        if key in state:
            state[key].show()
    print('Energie:', bewertung['energiestatus'])

def bilanzkontrollen(zustand):
    """Kontrollen der Flächenbildung als Tabelle (Ist/Soll/Status)."""
    return zustand['kontrollen'].copy()

# ---------------------------------------------------------------------------
# Kennwerttabelle (gemeinsames Schema für Szenarioexport und Mehrszenarienvergleich)
# ---------------------------------------------------------------------------

def _kurzhash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]

def vergleichsbasis(state):
    """Kennungen der Vergleichsbasis: gleiche Kennung = gleiche Definition, Kategorien und Abgrenzung."""
    kategorien = {'geometry': GEOS, 'quality': QUAL, 'energy': ENERGY_PLAN, 'pv': PVS, 'flex': FLEX, 'weather': WEATHER, 'mass': MASS}
    flaeche = {'schema': SCHEMA_VERSION, 'kategorien': kategorien, 'bezug': 'NGF', 'abgrenzung': 'Gebäudesektor Österreich, Statistik-NGF', 'ngf_zu_bgf_faktor': state['BGF_FAKTOR']}
    quelle = state.get('_parquet_quelle') or {}
    energie = {'simulation': {'datei': Path(str(quelle.get('datei', ''))).name, 'bytes': quelle.get('bytes')},
               'batch': state['CFG'].get('parquet_batch'), 'ngf_zu_bgf_faktor': state['BGF_FAKTOR'], 'hwb_bezug': state['HWB_BEZUG'],
               'hilfsenergie_rw_ww': state['MIT_HILFSENERGIE'], 'umwelt_rw_spalte': state['UMWELT_RW_COLUMN'], 'umwelt_ww_spalte': state['UMWELT_WW_COLUMN'],
               'abgrenzung': 'EUI/PV je NGF; Strom ohne Mobilität, kein Abzug des PV-Eigenverbrauchs'}
    return {'flaeche': 'F-' + _kurzhash(flaeche), 'energie': 'E-' + _kurzhash(energie), 'definition_flaeche': flaeche, 'definition_energie': energie}

def _status(text):
    return {'OK': 'OK', 'Kennwerte unvollständig': 'UNVOLLSTAENDIG', 'keine Fläche': 'KEINE_FLAECHE'}.get(text, str(text))

def kennwerttabelle(zustand, bewertung):
    """Langformat-Kennwerte eines Zustands (Flächen, Anteile, Typen, Energie falls berechnet)."""
    state = bewertung['_arbeitsdaten']
    state['_parquet_quelle'] = zustand['eingabe']['quellen'].get('parquet')
    basis = vergleichsbasis(state)
    v = zustand['verteilung']
    base = {'Szenario_ID': zustand['name'], 'Zustand_ID': zustand['zustand_id'], 'Jahr': int(zustand['jahr'])}
    rows = []
    def add(**kw):
        row = dict(base, Bereich='Gesamt', Kategorie='', Bezugsflaeche='NGF', Abdeckung_pct=100.0, Status='OK', Vergleichsbasis_ID=basis['flaeche'])
        row.update(kw)
        rows.append(row)
    masks = {'Gesamt': pd.Series(True, index=v.index), 'Haushalte': v.geometry.isin(WOHN_GEOS), 'Nichtwohnen': ~v.geometry.isin(WOHN_GEOS)}
    for bereich, mask in masks.items():
        add(Bereich=bereich, Gruppe='Fläche', Kennwert='NGF', Wert=float(v.loc[mask, 'NGF_m2'].sum()), Einheit='m²')
        add(Bereich=bereich, Gruppe='Fläche', Kennwert='BGF', Wert=float(v.loc[mask, 'BGF_m2'].sum()), Einheit='m²', Bezugsflaeche='BGF')
        add(Bereich=bereich, Gruppe='Typen', Kennwert='Positiv belegte Typen', Wert=float(v.loc[mask, 'NGF_m2'].gt(0).sum()), Einheit='Anzahl', Bezugsflaeche='')
    for _, r in bewertung['eigenschaften'].iterrows():
        add(Gruppe=r['Merkmal'], Kennwert='NGF', Kategorie=r['Auspraegung'], Wert=float(r['NGF_m2']), Einheit='m²')
        add(Gruppe=r['Merkmal'], Kennwert='NGF-Anteil', Kategorie=r['Auspraegung'], Wert=float(r['NGF_Anteil_pct']), Einheit='% NGF')
        add(Gruppe=r['Merkmal'], Kennwert='Positiv belegte Typen', Kategorie=r['Auspraegung'], Wert=float(r['Belegte_Typen']), Einheit='Anzahl', Bezugsflaeche='')
    if state.get('ENERGIE_BEREIT'):
        for _, r in state['Energiekennwerte'].iterrows():
            common = dict(Bereich=r['Bereich'], Gruppe='Energie: ' + r['Gruppe'], Kennwert=r['Kennwert'], Abdeckung_pct=float(r['Abdeckung_pct']), Status=_status(r['Status']), Vergleichsbasis_ID=basis['energie'])
            add(Wert=float(r['GWh/a']), Einheit='GWh/a', **common)
            add(Wert=float(r['kWh/(m² NGF a)']), Einheit='kWh/(m² NGF a)', **common)
        for _, r in state['Endenergie'].iterrows():
            add(Bereich=r['Bereich'], Gruppe='Energie: Endenergieträger', Kennwert='Endenergie', Kategorie=r['Träger'], Wert=float(r['GWh/a']), Einheit='GWh/a',
                Abdeckung_pct=float(r['Abdeckung_pct']) if pd.notna(r.get('Abdeckung_pct')) else np.nan, Status=_status(r['Status']), Vergleichsbasis_ID=basis['energie'])
    else:
        add(Gruppe='Energie', Kennwert='Energieanalyse', Wert=np.nan, Einheit='', Bezugsflaeche='', Abdeckung_pct=np.nan,
            Status='NICHT_AUSGEFUEHRT' if bewertung['energiestatus'] == ENERGIE_NICHT_ANGEFORDERT else 'KENNWERT_FEHLT', Vergleichsbasis_ID=basis['energie'])
    out = pd.DataFrame(rows)[KENNWERTSPALTEN]
    out.attrs['vergleichsbasis'] = basis
    return out

# ---------------------------------------------------------------------------
# Speichern und Wiederladen
# ---------------------------------------------------------------------------

def _neuer_arbeitsordner(parent, name):
    """Arbeitsordner neben dem Ziel. Bewusst ohne tempfile.mkdtemp: dieses setzt unter Windows
    (Python >= 3.12.4) eine nur für den Ersteller lesbare Zugriffsliste."""
    parent.mkdir(parents=True, exist_ok=True)
    stage = parent / f'.{name}_arbeit_{uuid.uuid4().hex[:12]}'
    stage.mkdir()
    return stage

def veroeffentliche_ordner(stage, target):
    """Ersetzt `target` atomar durch `stage` (mit Rücksicherung bei Fehlern)."""
    backup = None
    if target.exists():
        backup = target.with_name('.' + target.name + '_backup_' + uuid.uuid4().hex[:8])
        target.rename(backup)
    try:
        stage.rename(target)
    except Exception:
        if backup is not None:
            backup.rename(target)
        raise
    if backup is not None:
        shutil.rmtree(backup)
    return target

def speichere_szenario(zustand, bewertung, eingabe=None, ersetzen=False, ergebnisordner=None):
    """Speichert Verteilung.csv, Kennwerte.csv, Szenario.xlsx, laufprotokoll.json und eingaben/.
    Vorhandene Ergebnisse werden nur mit ersetzen=True ersetzt."""
    eingabe = zustand['eingabe'] if eingabe is None else eingabe
    if eingabe['fingerprint'] != zustand['eingabe']['fingerprint'] or bewertung['zustand_id'] != zustand['zustand_id']:
        raise ValueError('Zustand, Bewertung und Eingabe passen nicht zusammen.')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', eingabe['name']):
        raise ValueError('Szenario-ID ist kein sicherer Ordnername.')
    target = Path(ergebnisordner) / eingabe['name'] if ergebnisordner is not None else eingabe['ergebnisordner']
    if target.exists() and not ersetzen:
        raise FileExistsError(f'{target} existiert bereits. Zum Ersetzen ERSETZEN = True setzen.')
    stage = _neuer_arbeitsordner(target.parent, eingabe['name'])
    try:
        snap = stage / 'eingaben'
        snap.mkdir()
        for key, source in eingabe['quellen'].items():
            path = _quellpfad(eingabe, source)
            if 'sha256' in source:
                if _sha(path) != source['sha256']:
                    raise ValueError('Eingabedatei während des Laufs verändert: ' + str(path))
                (snap / (key + '_' + path.name)).write_bytes(eingabe['snapshots'][key])
                if _sha(snap / (key + '_' + path.name)) != source['sha256']:
                    raise ValueError('Snapshotprüfung fehlgeschlagen.')
        (snap / 'annahmen_aufgeloest.json').write_text(json.dumps(eingabe['cfg'], ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        log = _exportiere_kompatibel(bewertung['_arbeitsdaten'], stage)
        zustand['herkunftskohorten'].to_csv(stage / 'Herkunftskohorten.csv', sep=';', index=False, float_format='%.10f')
        kennwerte = bewertung.get('kennwerte')
        if kennwerte is None:
            kennwerte = kennwerttabelle(zustand, bewertung)
        kennwerte.to_csv(stage / 'Kennwerte.csv', sep=';', index=False, encoding='utf-8-sig', float_format='%.10g')
        log.update(schema_version=SCHEMA_VERSION, modellversion=MODELLVERSION, zustand_id=zustand['zustand_id'], szenario_id=eingabe['name'], jahr=int(zustand['jahr']),
                   eingabe_fingerprint=eingabe['fingerprint'], modellregeln={'wp_qualitaeten': sorted(WP_QUALITAETEN)},
                   eingabesnapshot={'cfg': 'eingaben/annahmen_aufgeloest.json', 'quellen': eingabe['quellen']},
                   vergleichsbasis={k: v for k, v in kennwerte.attrs.get('vergleichsbasis', {}).items()})
        log['eingaben']['json']['datei'] = 'eingaben/annahmen_aufgeloest.json'
        log['modellsoftware'] = {p.name: _sha(p) for p in [Path(__file__), Path(__file__).with_name('distribution_to_json.py')]}
        log['ausgaben'] = {name: _sha(stage / name) for name in ['Verteilung.csv', 'Kennwerte.csv', 'Herkunftskohorten.csv', 'Szenario.xlsx']}
        (stage / 'laufprotokoll.json').write_text(json.dumps(log, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        return veroeffentliche_ordner(stage, target)
    finally:
        if stage.exists():
            shutil.rmtree(stage)

def erwarteter_katalog():
    return set(product(GEOS, QUAL, ENERGY, PVS, FLEX, WEATHER, MASS))

def pruefe_zustandstabelle(df, tol=0.01):
    """Schema- und Plausibilitätsprüfung eines gespeicherten Zustands. Gibt Fehlerliste zurück."""
    errors = []
    missing = [c for c in ZUSTANDSSPALTEN if c not in df]
    if missing:
        return ['Spalten fehlen: ' + ', '.join(missing)]
    if df[ZUSTANDSSPALTEN].isna().any().any():
        errors.append('Fehlende Werte in Kernspalten.')
    if df.Szenario.nunique() != 1 or df.Jahr.nunique() != 1:
        errors.append('Genau eine Szenario-ID und ein Jahr je Zustand erforderlich.')
    keys = list(df[DIMS].astype(str).apply(lambda c: c.str.strip()).itertuples(index=False, name=None))
    if len(set(keys)) != len(keys):
        errors.append('Doppelte Typenschlüssel.')
    expected = erwarteter_katalog()
    if set(keys) != expected:
        errors.append(f'Typenkatalog unvollständig/unbekannt: {len(expected - set(keys))} fehlen, {len(set(keys) - expected)} unbekannt.')
    for c in ['NGF_m2', 'BGF_m2', 'Flaechenanteil']:
        x = pd.to_numeric(df[c], errors='coerce')
        if not np.isfinite(x).all() or (x < 0).any():
            errors.append(f'{c}: ungültige oder negative Werte.')
    total = float(df.NGF_m2.sum())
    if total <= 0:
        errors.append('Gesamt-NGF ist nicht positiv.')
    elif abs(float(df.Flaechenanteil.sum()) - 1) > 1e-8:
        errors.append('Flächenanteile summieren nicht zu 1.')
    return errors

def lade_gespeichertes_szenario(szenario_id, projekt=None, ordner=None):
    """Lädt einen gespeicherten Zustand aus results/szenarien/<ID>/ (nur lesen, keine Berechnung)."""
    if ordner is None:
        projekt = lade_projekt(projekt)
        ordner = projekt['ergebnisse']['szenarien'] / szenario_id
    ordner = Path(ordner)
    path = ordner / 'Verteilung.csv'
    if not path.is_file():
        raise FileNotFoundError(f'{path} fehlt. Szenario zuerst in 01_Szenario.ipynb erstellen und speichern.')
    df = pd.read_csv(path, sep=';', encoding='utf-8-sig', keep_default_na=False, na_values=[''])
    errors = pruefe_zustandstabelle(df)
    if errors:
        raise ValueError(f'{path}: ' + ' '.join(errors))
    logpath = ordner / 'laufprotokoll.json'
    log = json.loads(logpath.read_text(encoding='utf-8')) if logpath.is_file() else {}
    integritaet = 'ALTFORMAT (keine Ausgabehashes im Protokoll)'
    if 'ausgaben' in log:
        bad = [n for n, h in log['ausgaben'].items() if not (ordner / n).is_file() or _sha(ordner / n) != h]
        if bad:
            raise ValueError('Gespeicherte Ausgaben wurden nach dem Export verändert oder fehlen: ' + ', '.join(bad))
        integritaet = 'OK (SHA-256 der Ausgaben geprüft)'
    kpath = ordner / 'Kennwerte.csv'
    kennwerte = pd.read_csv(kpath, sep=';', encoding='utf-8-sig', keep_default_na=False, na_values=['']) if kpath.is_file() else None
    name = str(df.Szenario.iloc[0])
    if szenario_id is not None and name != szenario_id:
        raise ValueError(f'Ordner {szenario_id} enthält Szenario {name}.')
    return {'name': name, 'jahr': int(df.Jahr.iloc[0]), 'df': df, 'datei': str(path), 'sha256': _sha(path),
            'zustand_id': log.get('zustand_id'), 'protokoll_sha256': _sha(logpath) if logpath.is_file() else None,
            'protokoll': log, 'kennwerte': kennwerte, 'integritaet': integritaet,
            'energiestatus': log.get('energieanalyse', {}).get('status', 'unbekannt'), 'ordner': str(ordner)}

def ergebnisuebersicht(projekt=None):
    """Status vorhandener Szenarioergebnisse (nur lesen)."""
    projekt = lade_projekt(projekt)
    base = projekt['ergebnisse']['szenarien']
    rows = []
    if base.is_dir():
        for folder in sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith('.')):
            row = {'Szenario_ID': folder.name, 'Ordner': _relativ(projekt['root'], folder)}
            try:
                z = lade_gespeichertes_szenario(folder.name, ordner=folder)
                row.update(Status='LESBAR', Jahr=z['jahr'], NGF_m2=float(z['df'].NGF_m2.sum()), Positive_Typen=int(z['df'].NGF_m2.gt(0).sum()),
                           Zustand_ID=(z['zustand_id'] or '')[:16], Energie=z['energiestatus'], Kennwerte=z['kennwerte'] is not None, Integritaet=z['integritaet'])
            except PermissionError:
                row.update(Status='NICHT_LESBAR (Zugriffsrechte)')
            except Exception as exc:
                row.update(Status='FEHLERHAFT', Hinweis=str(exc)[:200])
            rows.append(row)
    return pd.DataFrame(rows)
