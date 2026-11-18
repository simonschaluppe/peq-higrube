"""NGF-Eingaben und Kalibrierung für Qualität, Versorgung und PV.

Ablauf: distribution_to_json -> CFG; nach STAT/YEAR_MAP:
BAUJAHR_NGF=baujahr_ngf_aus_statistik(STAT,YEAR_MAP)
Q_ERG,_=kalibriere_qualitaet(CFG,BAUJAHR_NGF)
V=Q_ERG['wirksame_verteilungen']; Q_YEAR/PERIOD_Q/COHORT neu bilden.
ERG,BERICHT=kalibriere_verteilungen(CFG,COHORT,qualitaet_ergebnis=Q_ERG)
V=ERG['wirksame_verteilungen']; CFG bleibt unveränderte Eingabe.

ZIEL-Zeilen: Qualität Baujahr_von=ZIEL, Baujahr_bis=GLOBAL;
Versorgung/PV Geometrie=ZIEL (Versorgung Qualitaet=GLOBAL).
Keine Zielzeile bedeutet Direkt. Geometrie, Masse, Flexibilität bleiben Direkt.
Nullzellen bleiben gesperrt. Vollständige Anteile in [0,1] mit Summe1 erforderlich.
Keine stille fachliche Normierung oder Erhöhung der Toleranz bei Rundungsfehlern.
Tests: python distribution_to_json.py self-test
"""
from pathlib import Path
from itertools import product, combinations
from importlib.metadata import version, PackageNotFoundError
import argparse
import copy
import hashlib
import json
import math
import os
import platform
import tempfile
import numpy as np
import pandas as pd

DOMAENEN = {'geometrie': ['EFH_1G', 'GWB_7G', 'EFH_2G', 'NiWo_2G', 'NiWo_3G', 'RH_2G', 'MFH_2G', 'MFH_4G', 'NiWo_1G', 'GWB_5G'], 'qualitaet': ['vor1919', '1919-44', '1945-59', '1960-79', '1980-89', '1990-99', 'Neu_10cm', 'Neu_20cm', 'Neu_30cm'], 'versorgung': ['WP_Sole', 'WP_Wasser', 'WP_Luft', 'WP_Sole_fc', 'DH', 'Bio', 'Erdgas', 'Oel', 'Elektro'], 'masse': ['Leicht', 'mittel', 'schwer'], 'pv': ['PV0', 'PV30', 'PV70', 'PV90'], 'flex': ['noFlex', 'Flex'], 'nutzung': ['Wohnen', 'Nichtwohnen'], 'stat_nutzung': ['Gebäude für Gemeinschaften', 'Hotels und ähnliche Gebäude', 'Bürogebäude', 'Groß- und Einzelhandelsgebäude', 'Gebäude des Verkehrs- und Nachrichtenwesens', 'Industrie- und Lagergebäude', 'Gebäude für Kultur- und Freizeitzwecke sowie des Bildungs- und Gesundheitswesens', 'Wohngebäude mit einer Wohnung', 'Wohngebäude mit zwei Wohnungen', 'Wohngebäude mit drei und mehr Wohnungen'], 'stat_geschoss': ['1 Geschoß', '2 Geschoße', '3 Geschoße', '4 Geschoße', '5 Geschoße', '6 bis 10 Geschoße', '11 und mehr Geschoße']}
GEOS = DOMAENEN['geometrie']
QUAL = DOMAENEN['qualitaet']
ENERGY = DOMAENEN['versorgung']
MASS = DOMAENEN['masse']
PVS = DOMAENEN['pv']
FLEX = DOMAENEN['flex']
USES = DOMAENEN['nutzung']
WP = ENERGY[:4]
TOLERANZ = 1e-12
VERTEILUNGEN = {'geometrie_nach_nutzung_geschoss', 'qualitaet_nach_baujahr',
    'masse_nach_nutzung', 'versorgung_nach_geometrie_qualitaet',
    'pv_nach_geometrie', 'flex_nach_versorgung'}


class Eingabefehler(ValueError):
    pass


class Kalibrierungsfehler(RuntimeError):
    pass


def _check_tolerance(tol):
    if not math.isfinite(tol) or not 0 < tol <= 1e-10:
        raise Eingabefehler('Toleranz muss positiv und höchstens 1e-10 sein.')


def _keys(mapping, expected, label):
    if not isinstance(mapping, dict) or set(mapping) != set(expected):
        raise Eingabefehler(f'{label}: fehlende oder unbekannte Kategorien; erwartet {list(expected)}.')


def _mix(mapping, names, label, tol):
    """Strenge Prüfung mit benannten Ursachen; keine fachliche Normierung."""
    _keys(mapping,names,label)
    missing=[k for k in names if pd.api.types.is_scalar(mapping[k]) and pd.isna(mapping[k]) or isinstance(mapping[k],str) and not mapping[k].strip()]
    if missing:
        raise Eingabefehler(f'{label}: fehlende Anteile für {missing}. Alle Kategorien befüllen, echte Nullen ausdrücklich eintragen. Formeln benötigen gespeicherte Ergebnisse.')
    booleans=[k for k in names if isinstance(mapping[k],(bool,np.bool_))]
    if booleans:raise Eingabefehler(f'{label}: boolesche Werte bei {booleans}, numerische Anteile erforderlich.')
    converted={}
    invalid=[]
    for k in names:
        try:converted[k]=float(mapping[k])
        except (ValueError,TypeError):invalid.append(f'{k}={mapping[k]!r}')
    if invalid:raise Eingabefehler(f'{label}: nichtnumerische Anteile: {", ".join(invalid)}. Prozent als Excel-Zahl, nicht als Text eingeben.')
    values=np.array([converted[k] for k in names])
    bad=[f'{k}={converted[k]!r}' for k in names if not math.isfinite(converted[k]) or not 0<=converted[k]<=1]
    if bad:raise Eingabefehler(f'{label}: Anteile außerhalb [0,1] oder nicht endlich: {", ".join(bad)}. Beispiel: 9,78 % oder 0,0978, nicht 9,78.')
    total=math.fsum(values)
    if abs(total-1)>tol:
        entries='; '.join(f'{k}={100*converted[k]:.12g} %' for k in names)
        raise Eingabefehler(f'{label}: Summe={100*total:.12f} % (Anteil {total:.17g}); erwartet 100 %. '
            f'Abweichung={(total-1)*100:+.12f} Prozentpunkte; Toleranz={tol:g} als Anteil. '
            f'Werte: {entries}. Gespeicherte Werte korrigieren; keine automatische Normierung.')
    return dict(zip(names,map(float,values)))


def _quality_intervals(bands, year, tol):
    if not isinstance(bands, list) or not bands:
        raise Eingabefehler('Qualitätsintervalle fehlen.')
    for row in bands:
        if not isinstance(row,dict) or set(row)!={'Baujahr_von','Baujahr_bis','anteile'}:
            raise Eingabefehler('Qualitätsintervalle benötigen Baujahr_von, Baujahr_bis und anteile.')
        if any(isinstance(row[k],bool) or not isinstance(row[k],int) for k in ['Baujahr_von','Baujahr_bis']):
            raise Eingabefehler('Baujahresgrenzen müssen ganzzahlig sein.')
    ordered = sorted(bands, key=lambda row: row['Baujahr_von'])
    next_year = 0
    for row in ordered:
        lo, hi = row['Baujahr_von'], row['Baujahr_bis']
        if any(isinstance(v, bool) or not isinstance(v, int) for v in [lo, hi]):
            raise Eingabefehler('Baujahresgrenzen müssen ganzzahlig sein.')
        if lo != next_year or hi < lo:
            raise Eingabefehler('Qualitätsintervalle: Start 0, keine Lücken/Überlappungen, von<=bis erforderlich.')
        _mix(row['anteile'], QUAL, f'Qualität {lo}..{hi}', tol)
        next_year = hi + 1
    if next_year <= year:
        raise Eingabefehler(f'Qualitätsintervalle decken das Ausgangsjahr {year} nicht ab.')
    return ordered


def validiere_eingabe(cfg, tol=TOLERANZ):
    """Öffentliche gemeinsame Prüfung; keine Mutation und kein Dateizugriff."""
    _check_tolerance(tol)
    if not isinstance(cfg, dict) or 'verteilungen' not in cfg:
        raise Eingabefehler('Eingabekonfiguration mit verteilungen erwartet, kein Berechnungsergebnis.')
    v = cfg['verteilungen']
    _keys(v, VERTEILUNGEN, 'Verteilungen')
    _keys(v['geometrie_nach_nutzung_geschoss'], DOMAENEN['stat_nutzung'], 'Geometrie-Nutzungen')
    for use, storeys in v['geometrie_nach_nutzung_geschoss'].items():
        _keys(storeys, DOMAENEN['stat_geschoss'], 'Geschosse '+use)
        for storey, dist in storeys.items():
            _mix(dist, GEOS, f'Geometrie {use}/{storey}', tol)
    year=cfg.get('ausgangsjahr',2024)
    if isinstance(year,bool) or not isinstance(year,int) or year<1918:
        raise Eingabefehler('ausgangsjahr muss eine ganze Zahl ab1918 sein.')
    _quality_intervals(v['qualitaet_nach_baujahr'], year, tol)
    _keys(v['masse_nach_nutzung'], USES, 'Massen-Nutzungen')
    for use, dist in v['masse_nach_nutzung'].items():
        _mix(dist, MASS, 'Masse '+use, tol)
    _keys(v['versorgung_nach_geometrie_qualitaet'], GEOS, 'Versorgungsgeometrien')
    _keys(v['pv_nach_geometrie'], GEOS, 'PV-Geometrien')
    _keys(v['flex_nach_versorgung'], ENERGY, 'Flex-Versorgungen')
    for geo in GEOS:
        _keys(v['versorgung_nach_geometrie_qualitaet'][geo], QUAL, 'Qualitäten '+geo)
        for quality, dist in v['versorgung_nach_geometrie_qualitaet'][geo].items():
            _mix(dist, ENERGY, geo+'/'+quality, tol)
        _mix(v['pv_nach_geometrie'][geo], PVS, 'PV '+geo, tol)
    for energy, dist in v['flex_nach_versorgung'].items():
        _mix(dist, FLEX, 'Flex '+energy, tol)
    settings = cfg.get('kalibrierung', {})
    if not isinstance(settings,dict):raise Eingabefehler('kalibrierung muss ein Objekt sein.')
    if set(settings)-{'Qualitaet','Versorgung', 'PV'}:
        raise Eingabefehler('Kalibrierung nur für Qualitaet, Versorgung und PV vorgesehen.')
    for name, setting in settings.items():
        if not isinstance(setting,dict):raise Eingabefehler(name+': Kalibrierungseinstellung muss ein Objekt sein.')
        if set(setting)-{'modus', 'ziele'}:
            raise Eingabefehler(f'{name}: Eingabe erwartet nur modus/ziele. Gespeicherte Ergebnis-Prioren nicht verwenden; Excel neu importieren.')
        mode = setting.get('modus', 'Direkt')
        if mode not in ['Direkt', 'Ziel+Tendenz']:
            raise Eingabefehler(f'{name}: unbekannter Modus {mode}.')
        if mode == 'Ziel+Tendenz':
            target = setting.get('ziele', {})
            names = ['WP_gesamt']+ENERGY[4:] if name == 'Versorgung' and 'WP_gesamt' in target else ENERGY if name == 'Versorgung' else QUAL if name == 'Qualitaet' else PVS
            _mix(target, names, name+' Ziele', tol)
    return True


def _sheet_specs():
    return {
        'Geometrie': (['Nutzung','Geschoss'], GEOS, list(product(DOMAENEN['stat_nutzung'], DOMAENEN['stat_geschoss']))),
        'Qualitaet': (['Baujahr_von','Baujahr_bis'], QUAL, None),
        'Speichermasse': (['Nutzung'], MASS, [(u,) for u in USES]),
        'Versorgung': (['Geometrie','Qualitaet'], ENERGY, list(product(GEOS, QUAL))),
        'PV': (['Geometrie'], PVS, [(g,) for g in GEOS]),
        'Flexibilitaet': (['Versorgung'], FLEX, [(e,) for e in ENERGY])}


def _read_excel(path):
    """Nur I/O: Tabellen laden, keine fachliche Kalibrierung."""
    with pd.ExcelFile(path, engine='openpyxl') as book:
        if set(_sheet_specs())-set(book.sheet_names):
            raise Eingabefehler('Mindestens eines der sechs Verteilungsblätter fehlt.')
        return {s: pd.read_excel(book, sheet_name=s, dtype=object).dropna(how='all') for s in _sheet_specs()}


def _extract_target(frame, sheet, values, tol):
    selector='Baujahr_von' if sheet=='Qualitaet' else 'Geometrie'
    target_rows = frame[selector].astype(str).str.strip().str.upper().eq('ZIEL')
    if target_rows.sum() > 1:
        raise Eingabefehler(sheet+': höchstens eine ZIEL-Zeile.')
    setting = {'modus': 'Direkt'}
    if target_rows.any():
        row = frame.loc[target_rows].iloc[0]
        if sheet == 'Versorgung' and pd.notna(row.Qualitaet) and str(row.Qualitaet).strip().upper() != 'GLOBAL':
            raise Eingabefehler('Zielzeile Versorgung: Qualität muss GLOBAL oder leer sein.')
        if sheet=='Qualitaet' and pd.notna(row.Baujahr_bis) and str(row.Baujahr_bis).strip().upper()!='GLOBAL':
            raise Eingabefehler('Zielzeile Qualitaet: Baujahr_bis muss GLOBAL oder leer sein.')
        grouped = sheet == 'Versorgung' and 'WP_gesamt' in frame and pd.notna(row.WP_gesamt)
        if grouped and any(pd.notna(row[c]) for c in WP):
            raise Eingabefehler('WP_gesamt und WP-Einzelziele nicht gleichzeitig eingeben.')
        names = ['WP_gesamt']+ENERGY[4:] if grouped else values
        setting = {'modus': 'Ziel+Tendenz', 'ziele': _mix({c: row[c] for c in names}, names, f'{sheet} Ziele, Excel-Zeile {frame.index[target_rows][0]+2}', tol)}
    remaining = frame.loc[~target_rows].copy()
    if sheet == 'Versorgung' and 'WP_gesamt' in remaining and remaining.WP_gesamt.notna().any():
        raise Eingabefehler('WP_gesamt darf nur in der Zielzeile befüllt sein.')
    return remaining, setting


def _parse_table(frame, sheet, tol):
    """Nur Validierung/Transformation eines bereits geladenen DataFrames."""
    keys, values, expected = _sheet_specs()[sheet]
    frame = frame.copy()
    frame.columns = [str(c).strip() for c in frame.columns]
    extras = ['Pruefsumme']+(['WP_gesamt'] if sheet == 'Versorgung' else [])
    if set(keys+values)-set(frame) or set(frame)-set(keys+values+extras) or frame.columns.duplicated().any():
        raise Eingabefehler(sheet+': Spalten fehlen, sind unbekannt oder doppelt.')
    setting = None
    if sheet in ['Qualitaet','Versorgung', 'PV']:
        frame, setting = _extract_target(frame, sheet, values, tol)
    frame = frame[keys+values].copy()
    if frame.empty or frame[keys].isna().any().any():
        raise Eingabefehler(sheet+': leere Tabelle oder Schlüssel.')
    for key in keys:
        if sheet == 'Qualitaet':
            if frame[key].map(lambda v:isinstance(v,(bool,np.bool_))).any():
                raise Eingabefehler('Boolesche Werte sind keine Jahresgrenzen.')
            nums = pd.to_numeric(frame[key], errors='coerce')
            if not np.isfinite(nums).all() or (nums < 0).any() or (nums % 1 != 0).any():
                raise Eingabefehler('Qualitäts-Jahresgrenzen müssen ganze nichtnegative Zahlen sein.')
            frame[key] = nums.astype(int)
        else:
            frame[key] = frame[key].astype(str).str.strip()
    if frame.duplicated(keys).any():
        raise Eingabefehler(sheet+': doppelte Schlüssel.')
    actual = list(frame[keys].itertuples(index=False, name=None))
    if expected is not None and set(actual) != set(expected):
        raise Eingabefehler(sheet+': Schlüssel fehlen oder sind unbekannt.')
    lookup = {}
    for key, (idx, row) in zip(actual, frame.iterrows()):
        if row[values].isna().any():
            raise Eingabefehler(f'{sheet}, Excel-Zeile {idx+2}, {key}: Anteil fehlt; Null ausdrücklich eintragen. Formeln benötigen gespeicherte Ergebnisse.')
        lookup[key] = _mix({c: row[c] for c in values}, values, f'{sheet} {key}', tol)
    order = sorted(lookup) if expected is None else expected
    return {k: lookup[k] for k in order}, setting


def _assemble_distributions(parsed):
    return {
        'geometrie_nach_nutzung_geschoss': {u: {s: parsed['Geometrie'][(u,s)] for s in DOMAENEN['stat_geschoss']} for u in DOMAENEN['stat_nutzung']},
        'qualitaet_nach_baujahr': [{'Baujahr_von': int(a), 'Baujahr_bis': int(b), 'anteile': dist} for (a,b), dist in parsed['Qualitaet'].items()],
        'masse_nach_nutzung': {u: parsed['Speichermasse'][(u,)] for u in USES},
        'versorgung_nach_geometrie_qualitaet': {g: {q: parsed['Versorgung'][(g,q)] for q in QUAL} for g in GEOS},
        'pv_nach_geometrie': {g: parsed['PV'][(g,)] for g in GEOS},
        'flex_nach_versorgung': {e: parsed['Flexibilitaet'][(e,)] for e in ENERGY}}


def distribution_to_json(excel, ziel_json=None, basis_json=None, *, overwrite=False, tol=TOLERANZ):
    """Excel-Eingabe erstellen; optional explizit speichern. Kein Fit."""
    _check_tolerance(tol)
    cfg = {} if basis_json is None else json.loads(Path(basis_json).read_text(encoding='utf-8-sig'))
    if not isinstance(cfg, dict):
        raise Eingabefehler('Basis-JSON muss ein Objekt enthalten.')
    parsed, settings = {}, {}
    for sheet, frame in _read_excel(excel).items():
        parsed[sheet], setting = _parse_table(frame, sheet, tol)
        if setting is not None:
            settings[sheet] = setting
    cfg['verteilungen'] = _assemble_distributions(parsed)
    cfg['kalibrierung'] = settings
    cfg['eingabe_verteilungen'] = {'datei': Path(excel).name,
        'sha256': hashlib.sha256(Path(excel).read_bytes()).hexdigest(), 'anteilsbasis': 'NGF',
        'ausgangsjahr': cfg.get('ausgangsjahr', 2024), 'fernwaerme': 'DH; Auflösung nach Wetter im Modell'}
    validiere_eingabe(cfg, tol)
    if ziel_json is not None:
        if Path(ziel_json).resolve() == Path(excel).resolve():
            raise Eingabefehler('Excel-Eingabe und JSON-Ziel dürfen nicht dieselbe Datei sein.')
        schreibe_json(cfg, ziel_json, overwrite=overwrite)
    return cfg


excel_zu_annahmen = distribution_to_json


def _prepare_weights(cohort):
    if not isinstance(cohort, pd.DataFrame) or not {'geometry','quality','ngf'} <= set(cohort):
        raise Eingabefehler('COHORT benötigt geometry, quality und ngf.')
    table = cohort[['geometry','quality','ngf']].copy()
    table['ngf'] = pd.to_numeric(table.ngf, errors='raise')
    if table.ngf.isna().any() or not np.isfinite(table.ngf).all() or (table.ngf < 0).any() or table.ngf.sum() <= 0:
        raise Eingabefehler('NGF-Gewichte müssen endlich, nichtnegativ und insgesamt positiv sein.')
    if not set(table.geometry) <= set(GEOS) or not set(table.quality) <= set(QUAL):
        raise Eingabefehler('Unbekannte oder leere Geometrie/Qualität in COHORT.')
    index = pd.MultiIndex.from_product([GEOS, QUAL], names=['geometry','quality'])
    grouped = table.groupby(['geometry','quality']).ngf.agg(lambda s: math.fsum(map(float, s)))
    return grouped.reindex(index, fill_value=0.)


def _target_vector(mapping, names, label, tol):
    checked = _mix(mapping, names, label, tol)
    original = np.array([checked[k] for k in names])
    total = math.fsum(original)
    target = original / total
    target[int(np.argmax(target))] += 1 - math.fsum(target)
    correction = {'Verteilung': label, 'Summe_Eingabe': total,
                  'Summe_verwendet': math.fsum(target),
                  'Max_Korrektur_Anteil': float(np.abs(target-original).max())}
    return target, correction


def _prepare_transport(prior, weights, target, label, tol):
    prior = np.asarray(prior, dtype=float)
    weights = np.asarray(weights, dtype=float)
    target = np.asarray(target, dtype=float)
    if prior.shape != (len(weights), len(target)) or len(target) > 9:
        raise Eingabefehler(label+': Matrixdimensionen prüfen; maximal 9 Kategorien unterstützt.')
    if not np.isfinite(prior).all() or (prior < 0).any() or not np.allclose(prior.sum(1), 1, rtol=0, atol=tol):
        raise Eingabefehler(label+': ungültige Priorverteilungen.')
    if not np.isfinite(weights).all() or (weights < 0).any() or weights.sum() <= 0:
        raise Eingabefehler(label+': ungültige Flächengewichte.')
    if not np.isfinite(target).all() or (target < 0).any() or abs(math.fsum(target)-1) > tol:
        raise Eingabefehler(label+': ungültige Zielverteilung.')
    active = weights > 0
    rows = weights[active] / math.fsum(weights)
    rows[int(np.argmax(rows))] += 1-math.fsum(rows)
    support = (prior[active] > 0) & (target[None, :] > 0)
    if not support.any(1).all():
        raise Eingabefehler(label+': belegte Gruppe ohne zulässige Zelle für die globalen Ziele.')
    return prior, weights, target, active, rows, support


def _prune_support(support, rows, target, names, label, tol):
    """Enge Kapazitäten erkennen; zusätzliche erzwungene Nullzellen ableiten.

    Teilmengenprüfung ist auf maximal 9 Zielkategorien begrenzt. Sie ersetzt
    keine weichen Trends durch harte Monotoniebedingungen.
    """
    allowed = support.copy()
    columns = np.flatnonzero(target > 0)
    subsets = [list(c) for size in range(1,len(columns)+1) for c in combinations(columns,size)]
    for _ in range(int(allowed.sum())+1):
        changed = False
        for subset in subsets:
            neighbors = allowed[:,subset].any(1)
            capacity = math.fsum(rows[neighbors])
            demand = math.fsum(target[subset])
            if demand > capacity+tol:
                categories = [names[j] for j in subset]
                raise Eingabefehler(f'{label}: Ziel {categories}={demand:.6%}, zulässige NGF höchstens {capacity:.6%}.')
            outside = np.setdiff1d(columns,subset)
            if abs(demand-capacity) <= tol and len(outside):
                cut = np.ix_(neighbors,outside)
                if allowed[cut].any():
                    allowed[cut] = False
                    changed = True
        if not changed:
            break
    if not allowed.any(1).all():
        raise Eingabefehler(label+': Kapazitätsbedingungen lassen eine Gruppe ohne zulässige Zelle.')
    return allowed


def _check_feasibility(support, rows, target, label):
    from scipy.optimize import linprog
    from scipy.sparse import coo_matrix
    i,j = np.where(support)
    count = len(i)
    equality = coo_matrix((np.ones(2*count),
        (np.r_[i,len(rows)+j], np.r_[np.arange(count),np.arange(count)])),
        shape=(len(rows)+len(target),count)).tocsr()
    solution = linprog(np.zeros(count), A_eq=equality, b_eq=np.r_[rows,target],
                       bounds=(0,None), method='highs')
    if not solution.success:
        raise Eingabefehler(label+': Ziele und Ausschlüsse sind nicht gemeinsam erfüllbar: '+solution.message)


def _scale_ipf(seed, rows, target, support, label, tol, maxiter):
    fitted = seed.copy()
    fitted[~support] = 0
    for iteration in range(1,maxiter+1):
        totals = fitted.sum(0)
        if ((totals == 0) & (target > 0)).any():
            raise Kalibrierungsfehler(label+': numerischer Verlust einer Zielkategorie.')
        fitted *= np.divide(target,totals,out=np.zeros_like(target),where=totals>0)
        totals = fitted.sum(1)
        if (totals <= 0).any():
            raise Kalibrierungsfehler(label+': numerisch leere Zeile.')
        fitted *= (rows/totals)[:,None]
        error = max(np.abs(fitted.sum(0)-target).max(), np.abs(fitted.sum(1)-rows).max())
        if error <= tol:
            return fitted, iteration, float(error)
    raise Kalibrierungsfehler(f'{label}: machbar, aber keine Konvergenz nach {maxiter} Iterationen. Fehler={error:.3g}; keine Teillösung ausgegeben.')


def _verify_fit(fitted, prior, weights, target, active, label, tol):
    actual = (fitted*weights[:,None]).sum(0)/math.fsum(weights)
    if not np.allclose(actual,target,rtol=0,atol=tol*2):
        raise Kalibrierungsfehler(label+': globale Abschlussprüfung fehlgeschlagen.')
    if not np.allclose(fitted.sum(1),1,rtol=0,atol=tol*2):
        raise Kalibrierungsfehler(label+': Zeilenabschlussprüfung fehlgeschlagen.')
    if not np.isfinite(fitted).all() or (fitted < 0).any() or (fitted[prior == 0] != 0).any():
        raise Kalibrierungsfehler(label+': Nichtnegativität/Nullzellen verletzt.')
    if not np.array_equal(fitted[~active],prior[~active]):
        raise Kalibrierungsfehler(label+': unbelegte Priorzeilen verändert.')


def _fit_matrix(prior, weights, target, names, label, tol, maxiter):
    p,w,t,active,rows,support = _prepare_transport(prior,weights,target,label,tol)
    allowed = _prune_support(support,rows,t,names,label,tol)
    _check_feasibility(allowed,rows,t,label)
    amounts,iterations,error = _scale_ipf(rows[:,None]*p[active],rows,t,allowed,label,tol,maxiter)
    fitted = p.copy()
    fitted[active] = amounts/rows[:,None]
    _verify_fit(fitted,p,w,t,active,label,tol)
    return fitted, {'Iterationen':iterations, 'Max_Randfehler_Anteil':error,
        'Zusaetzlich_erzwungene_Nullzellen':int(((p[active]>0)&~allowed).sum())}


def _version(package):
    try:
        return version(package)
    except PackageNotFoundError:
        return None


def _fingerprint(obj):
    text = json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _kalibriere_versorgung_pv(cfg, cohort, *, tol=TOLERANZ, maxiter=20000):
    """Rückgabe (ERGEBNIS, BERICHT). CFG und COHORT werden nicht verändert.

    ERGEBNIS trennt eingabe, wirksame_verteilungen, metadaten. Das Modell
    verwendet V=ERGEBNIS['wirksame_verteilungen']; CFG bleibt Eingabe.
    """
    validiere_eingabe(cfg,tol)
    if isinstance(maxiter,bool) or not isinstance(maxiter,int) or maxiter<1:
        raise Eingabefehler('maxiter muss eine positive ganze Zahl sein.')
    weights_gq = _prepare_weights(cohort)
    effective = copy.deepcopy(cfg['verteilungen'])
    settings = cfg.get('kalibrierung',{})
    global_rows,detail_rows,audit_rows,rounding_rows = [],[],[],[]
    for name,key,names,groups in [
        ('Versorgung','versorgung_nach_geometrie_qualitaet',ENERGY,list(product(GEOS,QUAL))),
        ('PV','pv_nach_geometrie',PVS,[(g,) for g in GEOS])]:
        setting = settings.get(name,{'modus':'Direkt'})
        mode = setting.get('modus','Direkt')
        table = cfg['verteilungen'][key]
        prior = np.array([[table[g][q][e] for e in names] for g,q in groups]) if name=='Versorgung' else np.array([[table[g][e] for e in names] for (g,) in groups])
        weights = weights_gq.to_numpy() if name=='Versorgung' else weights_gq.groupby(level='geometry').sum().reindex(GEOS).to_numpy()
        targets = setting.get('ziele',{})
        grouped = mode=='Ziel+Tendenz' and name=='Versorgung' and 'WP_gesamt' in targets
        columns = ['WP_gesamt']+ENERGY[4:] if grouped else names
        seed = np.column_stack([prior[:,:4].sum(1),prior[:,4:]]) if grouped else prior
        diagnostic = {'Iterationen':0,'Max_Randfehler_Anteil':0.,'Zusaetzlich_erzwungene_Nullzellen':0}
        if mode=='Ziel+Tendenz':
            target,correction = _target_vector(targets,columns,name,tol)
            rounding_rows.append(correction)
            fitted,diagnostic = _fit_matrix(seed,weights,target,columns,name,tol,maxiter)
            if grouped:
                result = prior.copy()
                within_wp = np.divide(prior[:,:4],seed[:,[0]],out=np.zeros_like(prior[:,:4]),where=seed[:,[0]]>0)
                result[:,:4] = within_wp*fitted[:,[0]]
                result[:,4:] = fitted[:,1:]
                result[weights==0] = prior[weights==0]
            else:
                result = fitted
        else:
            result,fitted = prior.copy(),seed.copy()
            target = None
        before = (seed*weights[:,None]).sum(0)/math.fsum(weights)
        after = (fitted*weights[:,None]).sum(0)/math.fsum(weights)
        for j,category in enumerate(columns):
            goal = float(target[j]) if target is not None else np.nan
            global_rows.append({'Verteilung':name,'Modus':mode,'Kategorie':category,'Soll_Anteil':goal,
                'Prior_Anteil':before[j],'Ist_Anteil':after[j],'Abweichung_pp':100*(after[j]-goal),
                'Ist_NGF_m2':after[j]*math.fsum(weights)})
        for i,group in enumerate(groups):
            for j,category in enumerate(names):
                detail_rows.append({'Verteilung':name,'Geometrie':group[0],
                    'Qualitaet':group[1] if len(group)>1 else '', 'Kategorie':category,
                    'NGF_Gruppe_m2':weights[i],'Prior_Anteil':prior[i,j], 'Ist_Anteil':result[i,j],
                    'Aenderung_pp':100*(result[i,j]-prior[i,j]),'Nullzelle':bool(prior[i,j]==0),
                    'Ist_NGF_m2':weights[i]*result[i,j]})
        if name=='Versorgung':
            effective[key] = {g:{q:dict(zip(names,map(float,result[i*len(QUAL)+j]))) for j,q in enumerate(QUAL)} for i,g in enumerate(GEOS)}
        else:
            effective[key] = {g:dict(zip(names,map(float,result[i]))) for i,g in enumerate(GEOS)}
        audit_rows.append({'Verteilung':name,'Modus':mode,'Status':'OK','NGF_m2':math.fsum(weights),**diagnostic,
            'Tendenzen':'weiche Prioren; keine garantierte Monotonie/Geschossunabhängigkeit'})
    weight_records = weights_gq.rename('ngf').reset_index().to_dict('records')
    input_hash,weight_hash = _fingerprint(cfg),_fingerprint(weight_records)
    result = {'eingabe':copy.deepcopy(cfg),'wirksame_verteilungen':effective,
        'metadaten':{'toleranz_anteil':tol,'maxiter':maxiter,'eingabe_sha256':input_hash,
            'gewichte_sha256':weight_hash,'gewichte_ngf':weight_records,
            'methode':'IPF mit Machbarkeitsprüfung und strukturellen Nullzellen',
            'software':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':_version('scipy')}}}
    controls = pd.DataFrame(audit_rows).assign(Eingabe_SHA256=input_hash,Gewichte_SHA256=weight_hash)
    report = {'Globale_Ziele':pd.DataFrame(global_rows),'Bedingte_Verteilungen':pd.DataFrame(detail_rows),
              'Kontrollen':controls,'Rundungen':pd.DataFrame(rounding_rows,columns=['Verteilung','Summe_Eingabe','Summe_verwendet','Max_Korrektur_Anteil'])}
    return result,report



def baujahr_ngf_aus_statistik(stat,year_map):
    """Bauperioden wie im Modell auf Kalenderjahre verteilen; keine neuen Flächen."""
    if not isinstance(stat,pd.DataFrame) or not {'period','ngf'}<=set(stat):
        raise Eingabefehler('STAT benötigt period und ngf.')
    frame=stat[['period','ngf']].copy()
    if frame.isna().any().any():raise Eingabefehler('Fehlende Bauperiode/NGF in STAT.')
    frame['ngf']=pd.to_numeric(frame.ngf,errors='raise')
    if not np.isfinite(frame.ngf).all() or (frame.ngf<0).any() or frame.ngf.sum()<=0:
        raise Eingabefehler('Ungültige statistische NGF.')
    if set(frame.period)-set(year_map):raise Eingabefehler('YEAR_MAP unvollständig.')
    records=[]
    for period,amount in frame.groupby('period').ngf.sum().items():
        years=list(year_map[period])
        if not years or len(set(years))!=len(years) or any(isinstance(y,bool) or not isinstance(y,(int,np.integer)) or y<0 for y in years):
            raise Eingabefehler(f'YEAR_MAP {period}: eindeutige nichtnegative Kalenderjahre erforderlich.')
        records.extend((int(y),float(amount)/len(years)) for y in years)
    return pd.DataFrame(records,columns=['year','ngf']).groupby('year',as_index=False).ngf.sum()


def _quality_weights(cfg,area,tol):
    if not isinstance(area,pd.DataFrame) or not {'year','ngf'}<=set(area):raise Eingabefehler('Baujahresgewichte benötigen year und ngf.')
    a=area[['year','ngf']].copy()
    if a.isna().any().any():raise Eingabefehler('Fehlende Baujahre/NGF.')
    for key in ['year','ngf']:a[key]=pd.to_numeric(a[key],errors='raise')
    if not np.isfinite(a.to_numpy(float)).all() or (a.ngf<0).any() or a.ngf.sum()<=0 or (a.year<0).any() or (a.year%1!=0).any():
        raise Eingabefehler('Ganzzahlige Baujahre und endliche nichtnegative NGF erforderlich.')
    a['year']=a.year.astype(int)
    bands=_quality_intervals(cfg['verteilungen']['qualitaet_nach_baujahr'],cfg.get('ausgangsjahr',2024),tol)
    weights=[];covered=np.zeros(len(a),bool)
    for b in bands:
        mask=(a.year>=b['Baujahr_von'])&(a.year<=b['Baujahr_bis'])
        weights.append(math.fsum(a.loc[mask,'ngf']));covered|=mask.to_numpy()
    if not covered.all():raise Eingabefehler('Baujahre außerhalb der Qualitätsintervalle.')
    return bands,np.array(weights,float),a


def _pack_report(report):
    return {k:{'spalten':list(df.columns),'zeilen':df.astype(object).where(pd.notna(df),None).to_dict('records')} for k,df in report.items()}


def kalibriere_qualitaet(cfg,baujahr_ngf,*,tol=TOLERANZ,maxiter=20000):
    """Vor Q_YEAR/COHORT: feste NGF je Baujahresintervall, globale Qualitätsziele."""
    validiere_eingabe(cfg,tol)
    if isinstance(maxiter,bool) or not isinstance(maxiter,int) or maxiter<1:raise Eingabefehler('maxiter muss eine positive ganze Zahl sein.')
    bands,weights,area=_quality_weights(cfg,baujahr_ngf,tol)
    prior=np.array([[b['anteile'][q] for q in QUAL] for b in bands],float)
    setting=cfg.get('kalibrierung',{}).get('Qualitaet',{'modus':'Direkt'})
    mode=setting.get('modus','Direkt')
    target=None;corrections=[]
    diag={'Iterationen':0,'Max_Randfehler_Anteil':0.,'Zusaetzlich_erzwungene_Nullzellen':0}
    if mode=='Ziel+Tendenz':
        target,correction=_target_vector(setting['ziele'],QUAL,'Qualitaet',tol)
        corrections.append(correction)
        fitted,diag=_fit_matrix(prior,weights,target,QUAL,'Qualitaet',tol,maxiter)
    else:fitted=prior.copy()
    effective=copy.deepcopy(cfg['verteilungen'])
    effective['qualitaet_nach_baujahr']=[{**b,'anteile':dict(zip(QUAL,map(float,fitted[i])))} for i,b in enumerate(bands)]
    total=math.fsum(weights);before=(prior*weights[:,None]).sum(0)/total;after=(fitted*weights[:,None]).sum(0)/total
    glob=[];detail=[]
    for j,q in enumerate(QUAL):
        goal=float(target[j]) if target is not None else np.nan
        glob.append({'Verteilung':'Qualitaet','Modus':mode,'Kategorie':q,'Soll_Anteil':goal,'Prior_Anteil':before[j],
                     'Ist_Anteil':after[j],'Abweichung_pp':100*(after[j]-goal),'Ist_NGF_m2':total*after[j]})
    for i,b in enumerate(bands):
        for j,q in enumerate(QUAL):
            detail.append({'Verteilung':'Qualitaet','Baujahr_von':b['Baujahr_von'],'Baujahr_bis':b['Baujahr_bis'],
                           'Kategorie':q,'NGF_Gruppe_m2':weights[i],'Prior_Anteil':prior[i,j],'Ist_Anteil':fitted[i,j],
                           'Aenderung_pp':100*(fitted[i,j]-prior[i,j]),'Nullzelle':bool(prior[i,j]==0),'Ist_NGF_m2':weights[i]*fitted[i,j]})
    report={'Globale_Ziele':pd.DataFrame(glob),'Bedingte_Verteilungen':pd.DataFrame(detail),
            'Kontrollen':pd.DataFrame([{'Verteilung':'Qualitaet','Modus':mode,'Status':'OK','NGF_m2':total,**diag}]),
            'Rundungen':pd.DataFrame(corrections,columns=['Verteilung','Summe_Eingabe','Summe_verwendet','Max_Korrektur_Anteil'])}
    result={'eingabe':copy.deepcopy(cfg),'wirksame_verteilungen':effective,'metadaten':{'eingabe_sha256':_fingerprint(cfg),
            'gewichte_baujahr':area.to_dict('records'),'ngf_m2':total,'toleranz_anteil':tol,'maxiter':maxiter},'bericht':_pack_report(report)}
    return result,report


def kalibriere_verteilungen(cfg,cohort,*,qualitaet_ergebnis=None,tol=TOLERANZ,maxiter=20000):
    """Nach COHORT: Qualitätsnachweis prüfen, dann Versorgung/PV berechnen."""
    validiere_eingabe(cfg,tol)
    setting=cfg.get('kalibrierung',{}).get('Qualitaet',{'modus':'Direkt'})
    if setting.get('modus','Direkt')=='Ziel+Tendenz' and qualitaet_ergebnis is None:
        raise Eingabefehler('Qualitätsziele vor Q_YEAR/COHORT mit kalibriere_qualitaet berechnen und qualitaet_ergebnis übergeben.')
    quality_report=None
    if qualitaet_ergebnis is not None:
        if qualitaet_ergebnis['metadaten']['eingabe_sha256']!=_fingerprint(cfg):raise Eingabefehler('Qualitätsnachweis gehört zu einer anderen Eingabe.')
        qcfg={'verteilungen':qualitaet_ergebnis['wirksame_verteilungen'],'ausgangsjahr':cfg.get('ausgangsjahr',2024)}
        bands,w,_=_quality_weights(qcfg,pd.DataFrame(qualitaet_ergebnis['metadaten']['gewichte_baujahr']),tol)
        expected=sum(w[i]*np.array([b['anteile'][q] for q in QUAL]) for i,b in enumerate(bands))/math.fsum(w)
        actual_weights=_prepare_weights(cohort)
        total=math.fsum(actual_weights)
        actual=actual_weights.groupby(level='quality').sum().reindex(QUAL,fill_value=0).to_numpy()/total
        if not np.allclose(actual,expected,rtol=0,atol=tol*5):
            raise Eingabefehler('COHORT entspricht nicht der kalibrierten Qualität. Q_YEAR und PERIOD_Q mit dem wirksamen V neu bilden.')
        if setting.get('modus')=='Ziel+Tendenz':
            target,_=_target_vector(setting['ziele'],QUAL,'Qualitaet',tol)
            if not np.allclose(actual,target,rtol=0,atol=tol*5):raise Eingabefehler('COHORT erreicht Qualitätsziele nicht.')
        quality_report={k:pd.DataFrame(v['zeilen'],columns=v['spalten']) for k,v in qualitaet_ergebnis['bericht'].items()}
        scale=total/qualitaet_ergebnis['metadaten']['ngf_m2']
        for df in quality_report.values():
            for col in ['NGF_m2','NGF_Gruppe_m2','Ist_NGF_m2']:
                if col in df:df[col]*=scale
    result,report=_kalibriere_versorgung_pv(cfg,cohort,tol=tol,maxiter=maxiter)
    if qualitaet_ergebnis is not None:
        result['wirksame_verteilungen']['qualitaet_nach_baujahr']=copy.deepcopy(qualitaet_ergebnis['wirksame_verteilungen']['qualitaet_nach_baujahr'])
        result['metadaten']['qualitaet']=copy.deepcopy(qualitaet_ergebnis['metadaten'])
        for key in report:
            cols=list(dict.fromkeys(list(quality_report[key].columns)+list(report[key].columns)))
            report[key]=pd.DataFrame(quality_report[key].to_dict('records')+report[key].to_dict('records'),columns=cols)
    return result,report


def _atomic_write(path, writer, overwrite=False):
    path = Path(path)
    if path.exists() and not overwrite:
        raise FileExistsError(f'{path} existiert; overwrite=True erforderlich.')
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix=path.stem+'.',suffix=path.suffix,delete=False) as handle:
            temporary = Path(handle.name)
        writer(temporary)
        os.replace(temporary,path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def schreibe_json(obj, path, overwrite=False):
    payload = json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    _atomic_write(path,lambda tmp:tmp.write_text(payload,encoding='utf-8'),overwrite)


def berichte_speichern(report, path, overwrite=False):
    def write(temporary):
        with pd.ExcelWriter(temporary,engine='openpyxl') as writer:
            for sheet,frame in report.items():
                frame.to_excel(writer,sheet_name=sheet,index=False)
                writer.sheets[sheet].freeze_panes='B2'
    _atomic_write(path,write,overwrite)


def _test_configuration():
    """Kleine, vollständig synthetische Testeingabe; keine Modell-Standardwerte."""
    uniform = lambda names: {k:1/len(names) for k in names}
    v = {
        'geometrie_nach_nutzung_geschoss': {u:{s:uniform(GEOS) for s in DOMAENEN['stat_geschoss']} for u in DOMAENEN['stat_nutzung']},
        'qualitaet_nach_baujahr': [{'Baujahr_von':0,'Baujahr_bis':2024,'anteile':uniform(QUAL)}],
        'masse_nach_nutzung': {u:uniform(MASS) for u in USES},
        'versorgung_nach_geometrie_qualitaet': {g:{q:uniform(ENERGY) for q in QUAL} for g in GEOS},
        'pv_nach_geometrie': {g:{'PV0':.7,'PV30':.1,'PV70':.1,'PV90':.1} for g in GEOS},
        'flex_nach_versorgung': {e:uniform(FLEX) for e in ENERGY}}
    cfg = {'verteilungen':v,'kalibrierung':{
        'Qualitaet':{'modus':'Direkt'},
        'Versorgung':{'modus':'Ziel+Tendenz','ziele':uniform(ENERGY)},
        'PV':{'modus':'Ziel+Tendenz','ziele':{'PV0':.4,'PV30':.3,'PV70':.2,'PV90':.1}}}}
    c = pd.DataFrame([(g,q,float(i+1)) for i,(g,q) in enumerate(product(GEOS,QUAL))],columns=['geometry','quality','ngf'])
    return cfg,c


def run_self_tests():
    import unittest
    class Tests(unittest.TestCase):
        def test_no_mutation_and_direct_tables(self):
            cfg,c = _test_configuration()
            original = copy.deepcopy(cfg)
            r,b = kalibriere_verteilungen(cfg,c)
            self.assertEqual(cfg,original)
            self.assertNotEqual(r['wirksame_verteilungen']['pv_nach_geometrie'],cfg['verteilungen']['pv_nach_geometrie'])
            for k in VERTEILUNGEN-{'pv_nach_geometrie','versorgung_nach_geometrie_qualitaet'}:
                self.assertEqual(r['wirksame_verteilungen'][k],cfg['verteilungen'][k])
            self.assertLess(b['Globale_Ziele'].Abweichung_pp.abs().max(),1e-8)
        def test_repeat_and_input_edit(self):
            cfg,c = _test_configuration()
            a,_ = kalibriere_verteilungen(cfg,c)
            b,_ = kalibriere_verteilungen(cfg,c)
            self.assertEqual(a,b)
            edited=copy.deepcopy(cfg)
            edited['verteilungen']['pv_nach_geometrie'][GEOS[0]]={'PV0':.1,'PV30':.1,'PV70':.1,'PV90':.7}
            d,_=kalibriere_verteilungen(edited,c)
            self.assertNotEqual(a['wirksame_verteilungen'],d['wirksame_verteilungen'])
        def test_result_is_not_input(self):
            cfg,c = _test_configuration()
            result,_ = kalibriere_verteilungen(cfg,c)
            with self.assertRaises(Eingabefehler):kalibriere_verteilungen(result,c)
        def test_direct(self):
            cfg,c = _test_configuration()
            cfg['kalibrierung']={}
            r,_=kalibriere_verteilungen(cfg,c)
            self.assertEqual(r['wirksame_verteilungen'],cfg['verteilungen'])
        def test_tolerances(self):
            with self.assertRaises(Eingabefehler):
                _mix({'a':.5,'b':.499999999},['a','b'],'Test',TOLERANZ)
            t,record=_target_vector({'a':.5,'b':.5-1e-14},['a','b'],'Test',TOLERANZ)
            self.assertEqual(math.fsum(t),1)
            self.assertGreater(record['Max_Korrektur_Anteil'],0)
        def test_structural_zero_and_boundary(self):
            p=np.array([[.5,.5],[0,1.]])
            f,_=_fit_matrix(p,np.array([.5,.5]),np.array([.5,.5]),['a','b'],'Test',TOLERANZ,20000)
            np.testing.assert_allclose(f,[[1,0],[0,1]],atol=2*TOLERANZ)
            self.assertEqual(f[1,0],0)
        def test_impossible(self):
            with self.assertRaises(Eingabefehler):
                _fit_matrix(np.array([[1.,0],[1.,0]]),np.array([1.,1]),np.array([.5,.5]),['a','b'],'Test',TOLERANZ,20000)
        def test_zero_target_and_unused_group(self):
            p=np.array([[.4,.6],[.7,.3]])
            f,_=_fit_matrix(p,np.array([1.,0]),np.array([0.,1]),['a','b'],'Test',TOLERANZ,20000)
            np.testing.assert_array_equal(f[1],p[1])
            np.testing.assert_allclose(f[0],[0,1])
        def test_old_result_prior_rejected(self):
            cfg,c=_test_configuration()
            cfg['kalibrierung']['PV']['prior']={}
            with self.assertRaises(Eingabefehler):kalibriere_verteilungen(cfg,c)
        def test_excel_import(self):
            cfg,_ = _test_configuration()
            v=cfg['verteilungen']
            frames={
                'Geometrie':pd.DataFrame([{'Nutzung':u,'Geschoss':s,**dist} for u,ss in v['geometrie_nach_nutzung_geschoss'].items() for s,dist in ss.items()]),
                'Qualitaet':pd.DataFrame([{'Baujahr_von':b['Baujahr_von'],'Baujahr_bis':b['Baujahr_bis'],**b['anteile']} for b in v['qualitaet_nach_baujahr']]),
                'Speichermasse':pd.DataFrame([{'Nutzung':u,**dist} for u,dist in v['masse_nach_nutzung'].items()]),
                'Versorgung':pd.DataFrame([{'Geometrie':'ZIEL','Qualitaet':'GLOBAL',**cfg['kalibrierung']['Versorgung']['ziele']}]+[{'Geometrie':g,'Qualitaet':q,**dist} for g,qs in v['versorgung_nach_geometrie_qualitaet'].items() for q,dist in qs.items()]),
                'PV':pd.DataFrame([{'Geometrie':'ZIEL',**cfg['kalibrierung']['PV']['ziele']}]+[{'Geometrie':g,**dist} for g,dist in v['pv_nach_geometrie'].items()]),
                'Flexibilitaet':pd.DataFrame([{'Versorgung':e,**dist} for e,dist in v['flex_nach_versorgung'].items()])}
            with tempfile.TemporaryDirectory() as folder:
                excel=Path(folder)/'input.xlsx'
                with pd.ExcelWriter(excel,engine='openpyxl') as writer:
                    for name,frame in frames.items():frame.to_excel(writer,sheet_name=name,index=False)
                parsed=distribution_to_json(excel)
                self.assertEqual(parsed['verteilungen'],cfg['verteilungen'])
                self.assertEqual(parsed['kalibrierung'],cfg['kalibrierung'])
            bad=frames['PV'].copy()
            bad.loc[1,'PV0']=np.nan
            with self.assertRaises(Eingabefehler):_parse_table(bad,'PV',TOLERANZ)
            bad=frames['Versorgung'].copy()
            bad=pd.concat([bad,bad.iloc[[0]]],ignore_index=True)
            with self.assertRaises(Eingabefehler):_parse_table(bad,'Versorgung',TOLERANZ)
        def test_grouped_wp(self):
            cfg,c=_test_configuration()
            cfg['kalibrierung']['Versorgung']['ziele']={'WP_gesamt':4/9,**{e:1/9 for e in ENERGY[4:]}}
            r,b=kalibriere_verteilungen(cfg,c)
            target=b['Globale_Ziele'].query("Kategorie == 'WP_gesamt'").iloc[0]
            self.assertAlmostEqual(target.Ist_Anteil,4/9,places=10)
            self.assertEqual(len(r['wirksame_verteilungen']['versorgung_nach_geometrie_qualitaet'][GEOS[0]][QUAL[0]]),9)
        def test_missing_weights(self):
            cfg,c=_test_configuration()
            c['ngf']=c.ngf.astype('Float64')
            c.loc[0,'ngf']=pd.NA
            with self.assertRaises(Eingabefehler):kalibriere_verteilungen(cfg,c)
        def test_diagnostic_sum(self):
            with self.assertRaisesRegex(Eingabefehler,'100.010000000000'):
                _mix({'a':.5,'b':.5001},['a','b'],'Qualitaet Ziele',TOLERANZ)
        def test_diagnostic_missing(self):
            with self.assertRaisesRegex(Eingabefehler,'Neu_30cm'):
                _mix({'a':1.,'Neu_30cm':np.nan},['a','Neu_30cm'],'Qualitaet Ziele',TOLERANZ)
        def test_diagnostic_range(self):
            with self.assertRaisesRegex(Eingabefehler,'a=9.78'):
                _mix({'a':9.78,'b':0},['a','b'],'Qualitaet Ziele',TOLERANZ)
        def test_diagnostic_text(self):
            with self.assertRaisesRegex(Eingabefehler,'nichtnumerisch'):
                _mix({'a':'9,78 %','b':0},['a','b'],'Qualitaet Ziele',TOLERANZ)
        def test_quality_stage(self):
            cfg,_=_test_configuration()
            p=lambda old:{q:old if q==QUAL[0] else 1-old if q==QUAL[7] else 0. for q in QUAL}
            cfg['verteilungen']['qualitaet_nach_baujahr']=[{'Baujahr_von':0,'Baujahr_bis':1999,'anteile':p(.8)},
                 {'Baujahr_von':2000,'Baujahr_bis':2024,'anteile':p(0.)}]
            cfg['kalibrierung']['Qualitaet']={'modus':'Ziel+Tendenz','ziele':p(.4)}
            original=copy.deepcopy(cfg)
            area=pd.DataFrame({'year':[1950,2010],'ngf':[75.,25.]})
            q,b=kalibriere_qualitaet(cfg,area)
            self.assertEqual(cfg,original)
            self.assertEqual(q['wirksame_verteilungen']['qualitaet_nach_baujahr'][1]['anteile'][QUAL[0]],0.)
            rows=[]
            for band,ngf in zip(q['wirksame_verteilungen']['qualitaet_nach_baujahr'],[75.,25.]):
                rows.extend((GEOS[0],k,ngf*v) for k,v in band['anteile'].items() if v>0)
            cohort=pd.DataFrame(rows,columns=['geometry','quality','ngf'])
            r,report=kalibriere_verteilungen(cfg,cohort,qualitaet_ergebnis=q)
            self.assertLess(report['Globale_Ziele'].Abweichung_pp.abs().max(),1e-8)
            with self.assertRaises(Eingabefehler):kalibriere_verteilungen(cfg,cohort)
            bad=cohort.copy();bad.loc[0,'ngf']+=1
            with self.assertRaises(Eingabefehler):kalibriere_verteilungen(cfg,bad,qualitaet_ergebnis=q)
            impossible=copy.deepcopy(cfg);impossible['kalibrierung']['Qualitaet']['ziele']=p(1.)
            with self.assertRaises(Eingabefehler):kalibriere_qualitaet(impossible,area)
            with tempfile.TemporaryDirectory() as folder:schreibe_json(q,Path(folder)/'q.json')
        def test_quality_goal_parser(self):
            cfg,_=_test_configuration()
            rows=[{'Baujahr_von':b['Baujahr_von'],'Baujahr_bis':b['Baujahr_bis'],**b['anteile']} for b in cfg['verteilungen']['qualitaet_nach_baujahr']]
            goals={q:1/len(QUAL) for q in QUAL}
            rows.append({'Baujahr_von':'ZIEL','Baujahr_bis':'GLOBAL',**goals})
            priors,settings=_parse_table(pd.DataFrame(rows),'Qualitaet',TOLERANZ)
            self.assertEqual(len(priors),1)
            self.assertEqual(settings['ziele'],goals)
        def test_atomic_json(self):
            with tempfile.TemporaryDirectory() as folder:
                p=Path(folder)/'a.json'
                schreibe_json({'a':1},p)
                with self.assertRaises(FileExistsError):schreibe_json({'a':2},p)
                self.assertEqual(json.loads(p.read_text()),{'a':1})
                with self.assertRaises(ValueError):schreibe_json({'a':np.nan},p,True)
                self.assertEqual(json.loads(p.read_text()),{'a':1})
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    return result.wasSuccessful()


def main():
    parser=argparse.ArgumentParser(description='Excel-Verteilungen und NGF-Kalibrierung, Eingabe/Ergebnis getrennt.')
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('convert')
    p.add_argument('excel')
    p.add_argument('--basis')
    p.add_argument('--output',default='annahmen_aus_excel.json')
    p.add_argument('--overwrite',action='store_true')
    p=sub.add_parser('fit')
    p.add_argument('json')
    p.add_argument('cohort_csv')
    p.add_argument('--baujahre',help='CSV year;ngf für die Qualitätskalibrierung; COHORT muss bereits dazu passen.')
    p.add_argument('--output',default='kalibrierung_ergebnis.json')
    p.add_argument('--bericht')
    p.add_argument('--overwrite',action='store_true')
    sub.add_parser('self-test')
    args=parser.parse_args()
    try:
        if args.command=='self-test':return 0 if run_self_tests() else 1
        if args.command=='convert':
            distribution_to_json(args.excel,args.output,args.basis,overwrite=args.overwrite)
        else:
            # Preflight verhindert die gewöhnliche Teilausgabe bei vorhandener Berichtsdatei.
            for path in [args.output,args.bericht]:
                if path and Path(path).exists() and not args.overwrite:raise FileExistsError(path)
            if args.bericht and Path(args.output).resolve()==Path(args.bericht).resolve():
                raise Eingabefehler('JSON-Ergebnis und Excel-Bericht benötigen verschiedene Dateinamen.')
            cfg=json.loads(Path(args.json).read_text(encoding='utf-8-sig'))
            cohort=pd.read_csv(args.cohort_csv,sep=';')
            qresult=None
            if args.baujahre:qresult,_=kalibriere_qualitaet(cfg,pd.read_csv(args.baujahre,sep=';'))
            result,report=kalibriere_verteilungen(cfg,cohort,qualitaet_ergebnis=qresult)
            schreibe_json(result,args.output,args.overwrite)
            if args.bericht:berichte_speichern(report,args.bericht,args.overwrite)
        print('Geschrieben:',args.output)
        return 0
    except (ValueError,RuntimeError,OSError,KeyError) as err:
        parser.exit(1,str(err)+'\n')


if __name__=='__main__':
    raise SystemExit(main())
