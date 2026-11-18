"""Prioren aus globalen Zielen ableiten (Stufe A) und Erreichbarkeit prüfen (Stufe B), AP6.3.

Vorstufe zur regulären Zustandsbildung, kein zweiter Szenariorechenkern:
- Stufe A liest eine Szenario-Excel, in der Prior-Zellen oder ganze Prior-Zeilen leer bleiben dürfen
  (Eingabedatei), und schreibt eine vollständige Verteilungsdatei (abgeleitete Datei). Nur diese liest
  ``gebaeudesektor.lade_szenario`` wie jede andere Excel-Verteilung. Kalibrierung auf die ZIEL-Zeilen,
  Zustandsbildung und Zustands-ID bleiben unverändert im Kern (gebaeudesektor.py, distribution_to_json.py).
- Eingegebene Werte haben Vorrang; nur leere Zellen werden befüllt.
- Stufe B prüft einen in der Sitzung gebildeten Zustand gegen die gespeicherten Gegenzustände aller
  registrierten Flächenstrompaare mit der Blockdiagnose (nur lesen, kein Solver, keine Optimierung).

Ableitung (Methode PRIOREN_METHODE):
1. Basis ist ein gespeicherter Zustand A (results/szenarien/<Basis>/): Flächen je Typ und die wirksamen
   (kalibrierten) Verteilungen aus dem Laufprotokoll.
2. Globale Verschiebung auf Kategorieebene: gemeinsame Transportmatrix Qualität × Versorgung (und getrennt PV)
   von A zu den ZIEL-Anteilen von B. Zulässig sind nur Verbleib, Übergänge nach uebergaenge.json, Neubau und
   Abriss nach Bestandsentwicklung.xlsx (Mengen und Freigaben) sowie WP nur in WP-Qualitäten. Gelöst wird die
   Maximum-Entropie-Matrix zu einem Startwert, der Verbleib bevorzugt (Gewicht 1, je geändertem Merkmal
   WECHSELGEWICHT): iteratives proportionales Anpassen wie im Kern; vorab LP-Machbarkeitsprüfung.
3. Prior-Zeilen = Herkunftsmischung: Versorgung (Geometrie, Qualität) = Fläche aus A je Geometrie, die nach
   der Verschiebung in diese Qualität gelangt, mit ihrer verschobenen Versorgung, plus Neubauanteil;
   Qualität je Baujahrband = wirksame A-Zeile · Qualitätsverschiebung plus Neubauanteil; PV je Geometrie analog.
   Geometrie, Speichermasse und Flexibilität (Direkt) übernehmen leere Zellen aus der Basis.
4. Zellen ohne zulässige Herkunft bleiben 0 (strukturelle Nullzellen). Teilweise befüllte Zeilen: leere Zellen
   erhalten den Rest 1 − Summe(eingegeben) im Verhältnis der abgeleiteten Werte.
"""
from pathlib import Path
from itertools import product
import hashlib, json, math, re, zipfile, io, copy
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
from distribution_to_json import DOMAENEN, distribution_to_json, _sheet_specs, _fingerprint

PRIOREN_METHODE = '1.0'
WECHSELGEWICHT = 0.05
MAXITER = 5000
TOL_TRANSPORT = 1e-10
GEOS, QUAL, ENERGY = DOMAENEN['geometrie'], DOMAENEN['qualitaet'], DOMAENEN['versorgung']
PVS, FLEX, MASS = DOMAENEN['pv'], DOMAENEN['flex'], DOMAENEN['masse']
WP = ENERGY[:4]
WP_QUALITY = {'1990-99', 'Neu_10cm', 'Neu_20cm', 'Neu_30cm'}
BLATTFOLGE = ['Geometrie', 'Qualitaet', 'Speichermasse', 'Versorgung', 'PV', 'Flexibilitaet']
FEST_ZEIT = '2000-01-01T00:00:00Z'

AKTUELL, VERALTET, FEHLT, NICHT_KONFIGURIERT = 'AKTUELL', 'VERALTET', 'FEHLT', 'NICHT_KONFIGURIERT'


class PriorenFehler(ValueError):
    pass


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _rel(root, path):
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return Path(path).name


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
def prioren_konfiguration(name, projekt):
    """Profilangaben zur Ableitung aus config/szenarien.json oder None (Szenario ohne Ableitung)."""
    import gebaeudesektor as gs
    cfg = gs.lade_szenarioregister(projekt)
    if name not in cfg['szenarien']:
        raise KeyError(f'Szenario {name!r} ist nicht registriert.')
    p = cfg['szenarien'][name]
    pr = p.get('prioren')
    if pr is None:
        return None
    if not isinstance(pr, dict) or set(pr) - {'eingabe', 'basis', 'rekonstruktion', 'wechselgewicht'} or not {'eingabe', 'basis'} <= set(pr):
        raise PriorenFehler(f'Szenario {name}: "prioren" braucht eingabe und basis (optional rekonstruktion, wechselgewicht).')
    root = Path(projekt['root'])
    eingabe, ziel = root / pr['eingabe'], root / p['verteilungen']
    if Path(pr['eingabe']).is_absolute() or Path(p['verteilungen']).is_absolute():
        raise PriorenFehler('Pfade für Prioren projektrelativ angeben.')
    if eingabe.resolve() == ziel.resolve():
        raise PriorenFehler(f'Szenario {name}: Eingabedatei und abgeleitete Datei (verteilungen) müssen verschieden sein.')
    if pr['basis'] == name:
        raise PriorenFehler('Die Basis muss ein anderes, gespeichertes Szenario sein.')
    theta = pr.get('wechselgewicht', WECHSELGEWICHT)
    if isinstance(theta, bool) or not isinstance(theta, (int, float)) or not 0 < theta <= 1:
        raise PriorenFehler('wechselgewicht muss in (0, 1] liegen.')
    return {'szenario': name, 'profil': p, 'eingabe': eingabe, 'ziel': ziel, 'basis': pr['basis'],
            'rekonstruktion': pr.get('rekonstruktion'), 'wechselgewicht': float(theta)}


def _paar(k, projekt):
    """Registriertes Flächenstrompaar Basis → Szenario (für Regeln und Bestandsbilanz) oder None."""
    reg = json.loads(Path(projekt['konfiguration']['rekonstruktionen']).read_text(encoding='utf-8'))['rekonstruktionen']
    if k['rekonstruktion']:
        if k['rekonstruktion'] not in reg:
            raise PriorenFehler(f'Rekonstruktion {k["rekonstruktion"]} nicht registriert.')
        return k['rekonstruktion'], reg[k['rekonstruktion']]
    treffer = [(rid, r) for rid, r in reg.items() if r['szenario_a'] == k['basis'] and r['szenario_b'] == k['szenario']]
    return treffer[0] if len(treffer) == 1 else (None, None)


# ---------------------------------------------------------------------------
# Eingabedatei lesen (leere Zellen erlaubt)
# ---------------------------------------------------------------------------
def _num(v, ort):
    if v is None or (isinstance(v, float) and math.isnan(v)) or (isinstance(v, str) and not v.strip()):
        return np.nan
    if isinstance(v, (bool, np.bool_)):
        raise PriorenFehler(f'{ort}: boolescher Wert.')
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise PriorenFehler(f'{ort}: nichtnumerischer Anteil {v!r}.') from None
    if not math.isfinite(x) or not 0 <= x <= 1:
        raise PriorenFehler(f'{ort}: Anteil {x!r} außerhalb [0, 1] (Prozent als Anteil, z. B. 0,0978).')
    return x


def lies_eingabe(path):
    """Liest die Eingabedatei. Rückgabe je Blatt: Werte-Spalten, Zielzeile (Rohwerte) und Prior-Zeilen {Schlüssel: Werte mit NaN}."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f'Eingabedatei fehlt: {path.name}')
    out = {}
    with pd.ExcelFile(path, engine='openpyxl') as book:
        for sheet, (keys, values, expected) in _sheet_specs().items():
            if sheet not in book.sheet_names:
                out[sheet] = {'keys': keys, 'values': values, 'ziel': None, 'zeilen': {}, 'wp_gesamt': False}
                continue
            f = pd.read_excel(book, sheet_name=sheet, dtype=object).dropna(how='all')
            f.columns = [str(c).strip() for c in f.columns]
            extras = ['Pruefsumme'] + (['WP_gesamt'] if sheet == 'Versorgung' else [])
            if set(keys + values) - set(f) or set(f) - set(keys + values + extras):
                raise PriorenFehler(f'{sheet}: Spalten fehlen oder sind unbekannt (erwartet {keys + values}).')
            sel = keys[0]
            ist_ziel = f[sel].astype(str).str.strip().str.upper().eq('ZIEL') if sheet in ['Qualitaet', 'Versorgung', 'PV'] else pd.Series(False, index=f.index)
            if ist_ziel.sum() > 1:
                raise PriorenFehler(f'{sheet}: höchstens eine ZIEL-Zeile.')
            ziel = f.loc[ist_ziel].iloc[0] if ist_ziel.any() else None
            zeilen = {}
            for idx, row in f.loc[~ist_ziel].iterrows():
                ort = f'{sheet}, Excel-Zeile {idx + 2}'
                if row[keys].isna().any():
                    if row[values].notna().any():
                        raise PriorenFehler(f'{ort}: Schlüssel fehlt.')
                    continue
                if sheet == 'Qualitaet':
                    try:
                        key = tuple(int(float(row[k])) for k in keys)
                    except (TypeError, ValueError):
                        raise PriorenFehler(f'{ort}: Baujahresgrenzen müssen ganze Zahlen sein.') from None
                else:
                    key = tuple(str(row[k]).strip() for k in keys)
                    if expected is not None and key not in expected:
                        raise PriorenFehler(f'{ort}: unbekannter Schlüssel {key}.')
                if key in zeilen:
                    raise PriorenFehler(f'{ort}: doppelter Schlüssel {key}.')
                if sheet == 'Versorgung' and 'WP_gesamt' in f and pd.notna(row.get('WP_gesamt')):
                    raise PriorenFehler('WP_gesamt darf nur in der Zielzeile befüllt sein.')
                zeilen[key] = np.array([_num(row[c], f'{ort}, {c}') for c in values])
            wp_gesamt = sheet == 'Versorgung' and 'WP_gesamt' in f
            out[sheet] = {'keys': keys, 'values': values, 'ziel': ziel, 'zeilen': zeilen, 'wp_gesamt': wp_gesamt}
    return out


def _ziel(blatt, sheet):
    """Zielanteile als dict oder None (Direkt). Gruppiert: WP_gesamt."""
    row = blatt['ziel']
    if row is None:
        return None
    names = blatt['values']
    if sheet == 'Versorgung' and blatt['wp_gesamt'] and pd.notna(row.get('WP_gesamt')):
        names = ['WP_gesamt'] + ENERGY[4:]
    t = {c: _num(row[c], f'{sheet} ZIEL, {c}') for c in names}
    if any(np.isnan(v) for v in t.values()):
        raise PriorenFehler(f'{sheet}: ZIEL-Zeile unvollständig; alle Zielanteile eintragen (Nullen ausdrücklich).')
    if abs(math.fsum(t.values()) - 1) > 1e-9:
        raise PriorenFehler(f'{sheet}: Zielanteile summieren sich zu {math.fsum(t.values()):.12f}, nicht 1.')
    return t


# ---------------------------------------------------------------------------
# Basis (gespeicherter Zustand A)
# ---------------------------------------------------------------------------
def lade_basis(name, projekt):
    """Gespeicherter Basiszustand mit Integritätsprüfung: Flächen (Planebene, DH) und wirksame Verteilungen."""
    import gebaeudesektor as gs
    import flaechenstroeme as fs
    z = gs.lade_gespeichertes_szenario(name, projekt)
    log = z['protokoll']
    if 'wirksame_konfiguration' not in log or not z['zustand_id']:
        raise PriorenFehler(f'Basis {name}: Laufprotokoll ohne wirksame Verteilungen oder Zustands-ID; in 01 neu speichern.')
    df = fs.validiere_zustand(z['df'])
    return {'name': name, 'zustand_id': z['zustand_id'], 'sha256': z['sha256'], 'jahr': z['jahr'], 'df': df,
            'ngf': float(df.NGF_m2.sum()), 'v': log['wirksame_konfiguration']['verteilungen'],
            'statistikjahr': (log.get('szenarioannahmen') or {}).get('statistikjahr')}


# ---------------------------------------------------------------------------
# Globale Verschiebung (Transport)
# ---------------------------------------------------------------------------
def _erlaubt(dim, regeln):
    import flaechenstroeme as fs
    return fs.erlaubte_paare(dim, regeln)


def _transport(quellen, ziele, a, n_m2, d_m2, erlaubt, wechsel, neubau_ok, abriss_ok, gruppen, theta):
    """Maximum-Entropie-Transport von A-Kategorien zu B-Kategorien mit Neubau-Zeile und Abriss-Spalte.

    quellen/ziele: Kategorielisten; a: A-Fläche je Quelle; erlaubt(i,j): bool; wechsel(i,j): Zahl geänderter Merkmale;
    gruppen: Liste (Spaltenindizes, Sollfläche) für die globalen Ziele. Rückgabe X (nQ+1 × nZ+1), Diagnose.
    """
    nq, nz = len(quellen), len(ziele)
    seed = np.zeros((nq + 1, nz + 1))
    for i, j in product(range(nq), range(nz)):
        if a[i] > 0 and erlaubt(i, j):
            seed[i, j] = a[i] * theta ** wechsel(i, j)
    if d_m2 > 0:
        for i in range(nq):
            if a[i] > 0 and abriss_ok(i):
                seed[i, nz] = a[i] * theta
    if n_m2 > 0:
        for j in range(nz):
            if neubau_ok(j):
                seed[nq, j] = n_m2
    zeilen = [([i], None, a[i]) for i in range(nq)] + [([nq], None, n_m2)]
    spalten = [(None, [nz], d_m2)] + [(None, list(js), soll) for js, soll in gruppen]
    _machbarkeit(seed, zeilen, spalten, quellen, ziele)
    traeger, nullen = _traeger(seed, zeilen, spalten)
    x = np.where(traeger, seed, 0.0)
    soll_z = np.r_[np.asarray(a, float), n_m2]
    # Spaltenbedingungen in überschneidungsfreie Familien (Abriss; Qualitätsziele; Versorgungsziele) zerlegen
    familien, offen = [], list(spalten)
    while offen:
        fam, belegt, rest = [], set(), []
        for sp in offen:
            (rest if belegt & set(sp[1]) else fam).append(sp)
            if fam and fam[-1] is sp:
                belegt |= set(sp[1])
        familien.append(fam); offen = rest
    skala = max(float(np.sum(a)) + n_m2, 1.0)
    res = np.inf
    for it in range(1, MAXITER + 1):
        s = x.sum(1)
        x *= np.divide(soll_z, s, out=np.zeros_like(s), where=s > 0)[:, None]
        for fam in familien:
            f = np.ones(nz + 1)
            for _, cols, soll in fam:
                t = x[:, cols].sum()
                f[cols] = soll / t if t > 0 else 0.0
            x *= f[None, :]
        res = max(np.abs(x.sum(1) - soll_z).max(), max(abs(x[:, c].sum() - s) for _, c, s in spalten)) / skala
        if res < TOL_TRANSPORT:
            break
    return x, {'iterationen': it, 'max_restfehler_anteil': float(res), 'erzwungene_nullfluesse': nullen}


def _system(seed, zeilen, spalten):
    """Gleichungssystem der Verschiebung auf dem Träger seed > 0 (skaliert)."""
    idx = np.argwhere(seed > 0)
    cons = [('z', r, s) for r, _, s in zeilen] + [('s', c, s) for _, c, s in spalten]
    rows, cols = [], []
    for k, (art, sel_idx, _) in enumerate(cons):
        v = np.flatnonzero(np.isin(idx[:, 0] if art == 'z' else idx[:, 1], sel_idx))
        rows += [k] * len(v); cols += list(v)
    skala = max(max(abs(s) for _, _, s in cons), 1.0)
    A = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(cons), len(idx))).tocsr()
    return idx, A, np.array([s for _, _, s in cons]) / skala, skala


def _machbarkeit(seed, zeilen, spalten, quellen, ziele):
    """LP-Prüfung: Gibt es überhaupt eine zulässige Verschiebung? Sonst Fehlmengen je Bedingung nennen."""
    idx, A, b, skala = _system(seed, zeilen, spalten)
    nv, m = A.shape[1], A.shape[0]
    namen = [f'A-Fläche {quellen[r[0]]}' if r[0] < len(quellen) else 'Neubau gesamt' for r, _, _ in zeilen]
    namen += ['Abriss gesamt'] + [f'Ziel {"+".join(map(str, sorted({ziele[j] for j in c})))}'[:80] for _, c, _ in spalten[1:]]
    S = coo_matrix((np.r_[np.ones(m), -np.ones(m)], (np.r_[np.arange(m), np.arange(m)], np.arange(2 * m))), shape=(m, 2 * m))
    from scipy.sparse import hstack
    lp = linprog(np.r_[np.zeros(nv), np.ones(2 * m)], A_eq=hstack([A, S]).tocsr(), b_eq=b, bounds=(0, None), method='highs')
    if lp.status != 0:
        raise PriorenFehler(f'Machbarkeitsprüfung der globalen Verschiebung fehlgeschlagen (Solverstatus {lp.status}).')
    slack = (lp.x[nv:nv + m] + lp.x[nv + m:]) * skala
    if slack.sum() > 1e-7 * skala:
        top = sorted(((s, n) for s, n in zip(slack, namen) if s > 1e-7 * skala), reverse=True)[:10]
        raise PriorenFehler('Globale Ziele mit den Übergangsregeln, Neubau- und Abrissfreigaben nicht erreichbar. '
                            'Größte Fehlmengen: ' + '; '.join(f'{n}: {s:,.0f} m²' for s, n in top) +
                            '. ZIEL-Zeilen, uebergaenge.json oder Freigaben in Bestandsentwicklung.xlsx prüfen.')


TRAEGER_DELTA = 1e-6   # Mindestfluss (Anteil der Gesamtfläche, ≈ 1 000 m²), ab dem ein Übergang als möglich gilt


def _traeger(seed, zeilen, spalten):
    """Übergänge, die in mindestens einer zulässigen Verschiebung positiv sind (LP-Folge). Übrige sind erzwungene Nullen.

    Ohne diesen Schritt bleiben Übergänge, die wegen exakt ausgeschöpfter Ziele 0 sein müssen, im iterativen Anpassen
    minimal positiv und erzeugen später Kleinstkonflikte in der Blockdiagnose."""
    idx, A, b, _ = _system(seed, zeilen, spalten)
    nv = A.shape[1]
    from scipy.sparse import hstack, vstack, identity
    offen, moeglich = np.arange(nv), np.zeros(nv, bool)
    for _ in range(25):
        k = len(offen)
        if k == 0:
            break
        P = coo_matrix((np.ones(k), (np.arange(k), offen)), shape=(k, nv))
        A_ub = hstack([-P, identity(k)]).tocsr()              # y ≤ x
        A_eq = hstack([A, coo_matrix((A.shape[0], k))]).tocsr()
        lp = linprog(np.r_[np.zeros(nv), -np.ones(k)], A_ub=A_ub, b_ub=np.zeros(k), A_eq=A_eq, b_eq=b,
                     bounds=[(0, None)] * nv + [(0, TRAEGER_DELTA)] * k, method='highs')
        if lp.status != 0:
            raise PriorenFehler(f'Trägerbestimmung fehlgeschlagen (Solverstatus {lp.status}).')
        neu = lp.x[nv:] > TRAEGER_DELTA / 2
        if not neu.any():
            break
        moeglich[offen[neu]] = True
        offen = offen[~neu]
    mask = np.zeros_like(seed, bool)
    mask[idx[moeglich, 0], idx[moeglich, 1]] = True
    return mask, int((~moeglich).sum())


# ---------------------------------------------------------------------------
# Ableitung
# ---------------------------------------------------------------------------
def _gruppenziel(t, namen, zielkat, t_b, label):
    """Gruppen (Spaltenindizes, Sollfläche) aus Zielanteilen; zielkat: Zielkategorie je Spalte."""
    gr = []
    for k, soll in t.items():
        mitglieder = WP if k == 'WP_gesamt' else [k]
        js = [j for j, z in enumerate(zielkat) if z in mitglieder]
        gr.append((js, soll * t_b))
    return gr


def _schliesse(werte, frei):
    """Summe exakt 1 (Rundungsrest auf den größten freien Wert); Werte in [0, 1]."""
    w = np.clip(np.asarray(werte, float), 0, 1)
    rest = 1 - math.fsum(w)
    kand = [i for i in np.argsort(-w) if frei[i]] or list(np.argsort(-w))
    w[kand[0]] = min(1.0, max(0.0, w[kand[0]] + rest))
    for _ in range(3):
        rest = 1 - math.fsum(w)
        if rest == 0:
            break
        w[kand[0]] += rest
    return w


def _fuelle(eingabe, abgeleitet, ort):
    """Eingegebene Werte behalten; leere Zellen mit abgeleiteten Werten (skaliert auf den Rest). Rückgabe Werte, Herkunft."""
    e = np.asarray(eingabe, float)
    leer = np.isnan(e)
    if not leer.any():
        return e, ['eingegeben'] * len(e)
    fest = math.fsum(e[~leer])
    if fest > 1 + 1e-12:
        raise PriorenFehler(f'{ort}: eingegebene Anteile summieren sich auf {fest:.12f} > 1.')
    rest = max(0.0, 1 - fest)
    d = np.where(leer, np.asarray(abgeleitet, float), 0.0)
    if rest > 1e-12 and d.sum() <= 0:
        raise PriorenFehler(f'{ort}: Rest {rest:.6f} kann keiner leeren Zelle zugeordnet werden (keine zulässige Herkunft); '
                            'Zeile vollständig eingeben.')
    w = e.copy()
    w[leer] = d[leer] / d.sum() * rest if d.sum() > 0 else 0.0
    w = _schliesse(w, leer)
    return w, ['eingegeben' if not l else 'abgeleitet' for l in leer]


def leite_ab(name, projekt, regeln=None, bilanz=None):
    """Berechnet die vollständigen Prior-Tabellen (ohne zu schreiben). Rückgabe dict mit Blättern, Herkunft, Protokoll."""
    import bestandsbilanz as bb
    import flaechenstroeme as fs
    k = prioren_konfiguration(name, projekt)
    if k is None:
        raise PriorenFehler(f'Szenario {name}: kein Eintrag "prioren" in config/szenarien.json.')
    root = Path(projekt['root'])
    ein = lies_eingabe(k['eingabe'])
    basis = lade_basis(k['basis'], projekt)
    rek_id, rek = _paar(k, projekt)
    regeldatei = root / rek['regeln'] if rek and rek.get('regeln') else Path(projekt['konfiguration']['uebergaenge'])
    regeln = regeln or fs.lade_regeln(regeldatei)
    t_a = basis['ngf']
    if k['profil'].get('ziel_ngf_m2') is not None:
        t_b = float(k['profil']['ziel_ngf_m2'])
    elif basis['statistikjahr'] in (None, k['profil']['statistikjahr']):
        t_b = t_a
    else:
        raise PriorenFehler('Statistikjahr weicht von der Basis ab: ziel_ngf_m2 im Profil angeben.')
    quelle_bilanz = None
    if bilanz is None and rek_id and projekt['konfiguration'].get('bestandsentwicklung') and k['profil']['jahr'] > basis['jahr']:
        bilanz = bb.bilanz_fuer(rek_id, projekt, t_a, t_b, basis['jahr'], k['profil']['jahr'])
    if bilanz is not None and bilanz['status'] == bb.BILANZ_OK:
        n_m2, d_m2 = float(bilanz['neubau_m2']), float(bilanz['abriss_m2'])
        fr_n, fr_d = bilanz['freigabe_neubau'], bilanz['freigabe_abriss']
        quelle_bilanz = bilanz.get('quelle')
    elif abs(t_b - t_a) <= 1.0:
        n_m2 = d_m2 = 0.0
        fr_n = fr_d = {'quality': QUAL, 'energy': ENERGY, 'pv': PVS}   # ohne Neubau/Abriss nicht verwendet
    else:
        st = bilanz['status'] if bilanz else 'keine Bestandsbilanz (kein registriertes Paar Basis → Szenario)'
        raise PriorenFehler(f'NGF Basis {t_a:,.0f} m² ≠ Ziel {t_b:,.0f} m², aber keine Bruttovorgaben für Neubau/Abriss ({st}). '
                            'Paar in rekonstruktionen.json registrieren und Neubau/Abriss in Bestandsentwicklung.xlsx angeben.')
    t_b_eff = t_a - d_m2 + n_m2
    theta = k['wechselgewicht']
    df = basis['df']
    erl = {d: _erlaubt(d, regeln) for d in ['quality', 'energy', 'pv']}

    # --- Qualität × Versorgung ---
    kat = list(product(QUAL, ENERGY))
    zk = [(q, e) for q, e in kat if not (e in WP and q not in WP_QUALITY)]
    a_qe = df.groupby(['quality', 'energy']).NGF_m2.sum()
    a = np.array([float(a_qe.get(c, 0.0)) for c in kat])
    tq, te = _ziel(ein['Qualitaet'], 'Qualitaet'), _ziel(ein['Versorgung'], 'Versorgung')
    gruppen = []
    if tq:
        gruppen += [(js, s) for js, s in _gruppenziel(tq, QUAL, [q for q, _ in zk], t_b_eff, 'Qualitaet')]
    if te:
        gruppen += [(js, s) for js, s in _gruppenziel(te, ENERGY, [e for _, e in zk], t_b_eff, 'Versorgung')]
    X, diag_qe = _transport(
        kat, zk, a, n_m2, d_m2,
        lambda i, j: (kat[i][0], zk[j][0]) in erl['quality'] and (kat[i][1], zk[j][1]) in erl['energy'],
        lambda i, j: (kat[i][0] != zk[j][0]) + (kat[i][1] != zk[j][1]),
        lambda j: zk[j][0] in fr_n['quality'] and zk[j][1] in fr_n['energy'],
        lambda i: kat[i][0] in fr_d['quality'] and kat[i][1] in fr_d['energy'],
        gruppen, theta)
    nq, nz = len(kat), len(zk)
    K = np.divide(X[:nq, :nz], a[:, None], out=np.zeros((nq, nz)), where=a[:, None] > 0)
    KN = X[nq, :nz] / n_m2 if n_m2 > 0 else np.zeros(nz)
    a_g = df.groupby('geometry').NGF_m2.sum()
    agqe = df.groupby(['geometry', 'quality', 'energy']).NGF_m2.sum()
    global_b = X[:, :nz].sum(0)
    abgeleitet = {s: {} for s in BLATTFOLGE}
    for g in GEOS:
        ag = np.array([float(agqe.get((g, q, e), 0.0)) for q, e in kat])
        bg = ag @ K + n_m2 * float(a_g.get(g, 0.0)) / t_a * KN
        for q in QUAL:
            js = [j for j, (qq, _) in enumerate(zk) if qq == q]
            row = np.zeros(len(ENERGY))
            for j in js:
                row[ENERGY.index(zk[j][1])] = bg[j]
            herkunft = 'abgeleitet'
            if row.sum() <= 0:
                for j in js:
                    row[ENERGY.index(zk[j][1])] = global_b[j]
                herkunft = 'abgeleitet (globale Mischung der Qualität)'
            if row.sum() <= 0:
                row = np.array([basis['v']['versorgung_nach_geometrie_qualitaet'][g][q][e] for e in ENERGY])
                herkunft = 'Basis (Qualität ohne Fläche)'
            abgeleitet['Versorgung'][(g, q)] = (row / row.sum(), herkunft)
    # Qualität je Baujahrband
    a_q = np.array([a[[i for i, (qq, _) in enumerate(kat) if qq == q]].sum() for q in QUAL])
    MQ = np.zeros((len(QUAL), len(QUAL)))
    for i, (q, _) in enumerate(kat):
        for j, (q2, _) in enumerate(zk):
            MQ[QUAL.index(q), QUAL.index(q2)] += X[i, j]
    MQ = np.divide(MQ, a_q[:, None], out=np.eye(len(QUAL)), where=a_q[:, None] > 0)
    nQ = np.zeros(len(QUAL))
    for j, (q2, _) in enumerate(zk):
        nQ[QUAL.index(q2)] += X[nq, j]
    for band in basis['v']['qualitaet_nach_baujahr']:
        ra = np.array([band['anteile'][q] for q in QUAL])
        row = ra @ MQ + nQ / t_a
        key = (band['Baujahr_von'], band['Baujahr_bis'])
        abgeleitet['Qualitaet'][key] = ((row / row.sum(), 'abgeleitet') if row.sum() > 0 else (ra, 'Basis'))
    # --- PV ---
    a_p = df.groupby('pv').NGF_m2.sum()
    ap = np.array([float(a_p.get(p, 0.0)) for p in PVS])
    tp = _ziel(ein['PV'], 'PV')
    gr_p = [([PVS.index(p)], s * t_b_eff) for p, s in tp.items()] if tp else []
    XP, diag_pv = _transport(PVS, PVS, ap, n_m2, d_m2, lambda i, j: (PVS[i], PVS[j]) in erl['pv'],
                             lambda i, j: int(i != j), lambda j: PVS[j] in fr_n['pv'], lambda i: PVS[i] in fr_d['pv'], gr_p, theta)
    KP = np.divide(XP[:4, :4], ap[:, None], out=np.zeros((4, 4)), where=ap[:, None] > 0)
    KNP = XP[4, :4] / n_m2 if n_m2 > 0 else np.zeros(4)
    agp = df.groupby(['geometry', 'pv']).NGF_m2.sum()
    for g in GEOS:
        row = np.array([float(agp.get((g, p), 0.0)) for p in PVS]) @ KP + n_m2 * float(a_g.get(g, 0.0)) / t_a * KNP
        abgeleitet['PV'][(g,)] = ((row / row.sum(), 'abgeleitet') if row.sum() > 0 else
                                  (np.array([basis['v']['pv_nach_geometrie'][g][p] for p in PVS]), 'Basis'))
    # --- Direkt-Blätter aus der Basis ---
    for (use, storey) in _sheet_specs()['Geometrie'][2]:
        abgeleitet['Geometrie'][(use, storey)] = (np.array([basis['v']['geometrie_nach_nutzung_geschoss'][use][storey][g] for g in GEOS]), 'Basis')
    for u in DOMAENEN['nutzung']:
        abgeleitet['Speichermasse'][(u,)] = (np.array([basis['v']['masse_nach_nutzung'][u][m] for m in MASS]), 'Basis')
    for e in ENERGY:
        abgeleitet['Flexibilitaet'][(e,)] = (np.array([basis['v']['flex_nach_versorgung'][e][f] for f in FLEX]), 'Basis')

    # --- Zusammenführen: Eingabe hat Vorrang ---
    blaetter, herkunft = {}, []
    for sheet in BLATTFOLGE:
        b = ein[sheet]
        keys, values = b['keys'], b['values']
        if sheet == 'Qualitaet':
            if set(b['zeilen']) - set(abgeleitet['Qualitaet']):
                raise PriorenFehler('Qualitaet: Baujahrbänder der Eingabe weichen von der Basis ab; Bänder der Basis verwenden '
                                        f'({sorted(abgeleitet["Qualitaet"])}) oder alle Zeilen vollständig eingeben.')
            reihen = sorted(abgeleitet['Qualitaet'])
        else:
            reihen = list(abgeleitet[sheet])
        zeilen = []
        for key in reihen:
            d, quelle = abgeleitet[sheet][key]
            e = b['zeilen'].get(key, np.full(len(values), np.nan))
            ort = f'{sheet} {key}'
            if np.isnan(e).all():
                w = _schliesse(d, [True] * len(d))
                hk = [quelle] * len(values)
            else:
                w, hk = _fuelle(e, d, ort)
                hk = [h if h == 'eingegeben' else quelle for h in hk]
            if sheet == 'Versorgung' and key[1] not in WP_QUALITY and any(w[:4] > 0):
                raise PriorenFehler(f'{ort}: WP-Anteil in ausgeschlossener Qualität (Eingabe prüfen).')
            zeilen.append((key, w))
            for c, v, h in zip(values, w, hk):
                herkunft.append({'Blatt': sheet, 'Zeile': ' | '.join(map(str, key)), 'Kategorie': c, 'Wert': float(v), 'Herkunft': h})
        blaetter[sheet] = {'keys': keys, 'values': values, 'zeilen': zeilen, 'ziel': b['ziel'], 'wp_gesamt': b['wp_gesamt']}
    herkunft = pd.DataFrame(herkunft)
    be_quelle = quelle_bilanz or {}
    protokoll = {
        'methode': PRIOREN_METHODE, 'szenario': name,
        'eingabe_datei': _rel(root, k['eingabe']), 'eingabe_sha256': _sha(k['eingabe']),
        'basis_szenario': basis['name'], 'basis_zustand_id': basis['zustand_id'], 'basis_verteilung_sha256': basis['sha256'],
        'regeln_datei': _rel(root, regeldatei), 'regeln_sha256': _sha(regeldatei),
        'rekonstruktion': rek_id or '', 'bestandsentwicklung_datei': be_quelle.get('datei', ''),
        'bestandsentwicklung_sha256': be_quelle.get('sha256', ''),
        'ngf_basis_m2': t_a, 'ngf_ziel_m2': t_b, 'neubau_m2': n_m2, 'abriss_m2': d_m2, 'wechselgewicht': theta,
        'iterationen_qv': diag_qe['iterationen'], 'restfehler_qv': diag_qe['max_restfehler_anteil'],
        'erzwungene_nullfluesse_qv': diag_qe['erzwungene_nullfluesse'], 'erzwungene_nullfluesse_pv': diag_pv['erzwungene_nullfluesse'],
        'iterationen_pv': diag_pv['iterationen'], 'restfehler_pv': diag_pv['max_restfehler_anteil'],
        'zellen_eingegeben': int((herkunft.Herkunft == 'eingegeben').sum()),
        'zellen_abgeleitet': int((herkunft.Herkunft != 'eingegeben').sum()),
        'nullzellen_abgeleitet': int(((herkunft.Herkunft != 'eingegeben') & (herkunft.Wert == 0)).sum())}
    return {'konfiguration': k, 'blaetter': blaetter, 'herkunft': herkunft, 'protokoll': protokoll}


# ---------------------------------------------------------------------------
# Schreiben (deterministisch) und Aktualität
# ---------------------------------------------------------------------------
def _frames(blaetter):
    out = {}
    for sheet in BLATTFOLGE:
        b = blaetter[sheet]
        keys, values = b['keys'], b['values']
        cols = keys + values + (['WP_gesamt'] if b['wp_gesamt'] else []) + ['Pruefsumme']
        rows = []
        for key, w in b['zeilen']:
            r = dict(zip(keys, key)); r.update(dict(zip(values, map(float, w))))
            if b['wp_gesamt']:
                r['WP_gesamt'] = None
            r['Pruefsumme'] = math.fsum(w)
            rows.append(r)
        if b['ziel'] is not None:
            z = b['ziel']
            r = {keys[0]: 'ZIEL', **({keys[1]: 'GLOBAL'} if len(keys) > 1 else {})}
            for c in values + (['WP_gesamt'] if b['wp_gesamt'] else []):
                v = z.get(c)
                r[c] = None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)
            r['Pruefsumme'] = math.fsum(v for c, v in r.items() if c in values + ['WP_gesamt'] and v is not None)
            rows.append(r)
        out[sheet] = pd.DataFrame(rows, columns=cols)
    return out


def _werte_sha(path):
    """Fingerabdruck des fachlichen Inhalts der sechs Verteilungsblätter (wie vom Kern gelesen)."""
    cfg = distribution_to_json(path)
    return _fingerprint({'verteilungen': cfg['verteilungen'], 'kalibrierung': cfg['kalibrierung']})


def _deterministisch(path):
    """Zip-Zeitstempel und Dokumenteigenschaften fest setzen: gleiche Eingaben → byte-gleiche Datei (gleiche Zustands-ID)."""
    data = Path(path).read_bytes()
    zin = zipfile.ZipFile(io.BytesIO(data))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zout:
        for info in sorted(zin.infolist(), key=lambda i: i.filename):
            inhalt = zin.read(info.filename)
            if info.filename == 'docProps/core.xml':
                inhalt = re.sub(rb'(<dcterms:(created|modified)[^>]*>)[^<]*(</dcterms:)', rb'\g<1>' + FEST_ZEIT.encode() + rb'\g<3>', inhalt)
            zi = zipfile.ZipInfo(info.filename, date_time=(2000, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o600 << 16
            zout.writestr(zi, inhalt)
    Path(path).write_bytes(buf.getvalue())


def schreibe_abgeleitet(ergebnis, projekt):
    """Schreibt die abgeleitete Verteilungsdatei (atomar) und gibt den Pfad zurück. Prüft sie mit dem Kernleser."""
    k = ergebnis['konfiguration']
    ziel = Path(k['ziel'])
    ziel.parent.mkdir(parents=True, exist_ok=True)
    tmp = ziel.with_name('.' + ziel.name + '.tmp')
    frames = _frames(ergebnis['blaetter'])
    prot = dict(ergebnis['protokoll'])
    hinweis = pd.DataFrame({'Hinweis': [
        'Abgeleitete Verteilungsdatei (AP6.3, modell/prioren.py). Nicht von Hand ändern: Änderungen in der Eingabedatei '
        f'{prot["eingabe_datei"]} vornehmen und in 01_Szenario mit PRIOREN_ABLEITEN=True neu ableiten.',
        'Eingegebene Zellen sind unverändert übernommen; leere Zellen aus Basis, Übergangsregeln, Neubau/Abriss und globalen Zielen '
        'abgeleitet (Blatt Herkunft). Kalibrierung auf die ZIEL-Zeilen erfolgt wie bei jeder Verteilung im Modell.']})
    with pd.ExcelWriter(tmp, engine='openpyxl') as w:
        for sheet, f in frames.items():
            f.to_excel(w, sheet_name=sheet, index=False)
        hinweis.to_excel(w, sheet_name='Hinweise', index=False)
        pd.DataFrame(list(prot.items()), columns=['Angabe', 'Wert']).to_excel(w, sheet_name='Ableitung', index=False)
        ergebnis['herkunft'].to_excel(w, sheet_name='Herkunft', index=False)
    _deterministisch(tmp)
    try:
        distribution_to_json(tmp)              # gleiche Prüfung wie im Kern (Summen exakt, Nullen, Ziele)
        werte = _werte_sha(tmp)
        with pd.ExcelWriter(tmp, engine='openpyxl', mode='a', if_sheet_exists='replace') as w:
            pd.DataFrame(list({**prot, 'werte_sha256': werte}.items()), columns=['Angabe', 'Wert']).to_excel(w, sheet_name='Ableitung', index=False)
        _deterministisch(tmp)
        tmp.replace(ziel)
    finally:
        if tmp.exists():
            tmp.unlink()
    return ziel


def _protokoll_lesen(path):
    t = pd.read_excel(path, sheet_name='Ableitung', dtype=object)
    return {str(r.Angabe): r.Wert for r in t.itertuples()}


def status(name, projekt):
    """Aktualität der abgeleiteten Datei (nur lesen). Rückgabe dict mit status und gruenden."""
    import gebaeudesektor as gs
    k = prioren_konfiguration(name, projekt)
    if k is None:
        return {'status': NICHT_KONFIGURIERT, 'gruende': [], 'datei': None}
    root = Path(projekt['root'])
    out = {'datei': _rel(root, k['ziel']), 'eingabe': _rel(root, k['eingabe']), 'basis': k['basis']}
    if not k['ziel'].is_file():
        return {**out, 'status': FEHLT, 'gruende': ['abgeleitete Datei fehlt']}
    try:
        p = _protokoll_lesen(k['ziel'])
    except Exception:
        return {**out, 'status': VERALTET, 'gruende': ['Blatt Ableitung fehlt oder ist unlesbar']}
    gruende = []
    if str(p.get('methode')) != PRIOREN_METHODE:
        gruende.append(f'Ableitungsmethode {p.get("methode")} ≠ {PRIOREN_METHODE}')
    if not k['eingabe'].is_file():
        gruende.append('Eingabedatei fehlt')
    elif p.get('eingabe_sha256') != _sha(k['eingabe']):
        gruende.append('Eingabedatei geändert')
    try:
        z = gs.lade_gespeichertes_szenario(k['basis'], projekt)
        if p.get('basis_zustand_id') != z['zustand_id'] or p.get('basis_verteilung_sha256') != z['sha256']:
            gruende.append(f'Basis {k["basis"]} neu gespeichert')
    except Exception as exc:
        gruende.append(f'Basis {k["basis"]} nicht lesbar: {str(exc)[:120]}')
    rd = root / str(p.get('regeln_datei', ''))
    if not rd.is_file() or p.get('regeln_sha256') != _sha(rd):
        gruende.append('Übergangsregeln geändert')
    rek_id, rek = _paar(k, projekt)
    soll_rd = root / rek['regeln'] if rek and rek.get('regeln') else Path(projekt['konfiguration']['uebergaenge'])
    if _rel(root, soll_rd) != p.get('regeln_datei'):
        gruende.append('andere Regeldatei registriert')
    if str(p.get('rekonstruktion') or '') != str(rek_id or ''):
        gruende.append('anderes Flächenstrompaar registriert')
    be = p.get('bestandsentwicklung_datei')
    if isinstance(be, str) and be:
        if not (root / be).is_file() or _sha(root / be) != p.get('bestandsentwicklung_sha256'):
            gruende.append('Bestandsentwicklung.xlsx geändert')
    soll_ngf = k['profil'].get('ziel_ngf_m2')
    if soll_ngf is not None and abs(float(soll_ngf) - float(p.get('ngf_ziel_m2', np.nan))) > 1.0:
        gruende.append('ziel_ngf_m2 geändert')
    if abs(float(p.get('wechselgewicht', np.nan)) - k['wechselgewicht']) > 0:
        gruende.append('wechselgewicht geändert')
    try:
        if p.get('werte_sha256') != _werte_sha(k['ziel']):
            gruende.append('abgeleitete Datei nachträglich verändert')
    except Exception as exc:
        gruende.append(f'abgeleitete Datei ungültig: {str(exc)[:120]}')
    return {**out, 'status': AKTUELL if not gruende else VERALTET, 'gruende': gruende}


def statustabelle(projekt):
    """Übersicht aller Szenarien mit Prior-Ableitung (nur lesen)."""
    import gebaeudesektor as gs
    rows = []
    for name in gs.lade_szenarioregister(projekt)['szenarien']:
        try:
            s = status(name, projekt)
        except Exception as exc:
            s = {'status': 'FEHLER', 'gruende': [str(exc)[:200]]}
        if s['status'] != NICHT_KONFIGURIERT:
            rows.append({'Szenario_ID': name, 'Status': s['status'], 'Eingabe': s.get('eingabe'), 'Abgeleitete_Datei': s.get('datei'),
                         'Basis': s.get('basis'), 'Gruende': '; '.join(s['gruende'])})
    return pd.DataFrame(rows, columns=['Szenario_ID', 'Status', 'Eingabe', 'Abgeleitete_Datei', 'Basis', 'Gruende'])


def ableiten(name, projekt):
    """Leitet ab und schreibt nur, wenn die abgeleitete Datei fehlt oder veraltet ist. Rückgabe (status vorher, Pfad, Ergebnis|None)."""
    vorher = status(name, projekt)
    if vorher['status'] == NICHT_KONFIGURIERT:
        raise PriorenFehler(f'Szenario {name}: keine Prior-Ableitung konfiguriert.')
    if vorher['status'] == AKTUELL:
        return vorher, Path(projekt['root']) / vorher['datei'], None
    erg = leite_ab(name, projekt)
    return vorher, schreibe_abgeleitet(erg, projekt), erg


def protokolltabelle(ergebnis):
    """Ableitungsprotokoll als Tabelle (Anzeige)."""
    return pd.DataFrame(list(ergebnis['protokoll'].items()), columns=['Angabe', 'Wert'])


def herkunftsuebersicht(herkunft):
    """Zählung je Blatt und Herkunft (Anzeige)."""
    t = herkunft.assign(Null=herkunft.Wert.eq(0))
    return t.groupby(['Blatt', 'Herkunft']).agg(Zellen=('Wert', 'size'), Nullzellen=('Null', 'sum')).reset_index()


# ---------------------------------------------------------------------------
# Stufe B: Erreichbarkeit eines in der Sitzung gebildeten Zustands
# ---------------------------------------------------------------------------
def erreichbarkeit(zustand, projekt):
    """Blockdiagnose des Zustands gegen die gespeicherten Gegenzustände aller registrierten Paare (nur lesen, kein Solver).

    Rückgabe (Übersicht, {Rekonstruktion: Konflikttabelle}). Keine Konflikte = notwendige Bedingungen erfüllt
    (Machbarkeit erst durch die Rekonstruktion in 03 nachgewiesen).
    """
    import gebaeudesektor as gs
    import flaechenstroeme as fs
    name = zustand['name']
    reg = json.loads(Path(projekt['konfiguration']['rekonstruktionen']).read_text(encoding='utf-8'))['rekonstruktionen']
    eigen = {'name': name, 'jahr': int(zustand['jahr']), 'df': zustand['verteilung']}
    rows, details = [], {}
    for rid, r in reg.items():
        if name not in (r['szenario_a'], r['szenario_b']):
            continue
        rolle = 'A' if r['szenario_a'] == name else 'B'
        anderer = r['szenario_b'] if rolle == 'A' else r['szenario_a']
        zeile = {'Rekonstruktion': rid, 'Rolle': rolle, 'Gegenzustand': anderer}
        try:
            g = gs.lade_gespeichertes_szenario(anderer, projekt)
        except FileNotFoundError:
            rows.append({**zeile, 'Status': 'GEGENZUSTAND_FEHLT', 'Meldung': f'{anderer} ist nicht gespeichert.'})
            continue
        gegen = {'name': anderer, 'jahr': g['jahr'], 'df': g['df']}
        a, b = (eigen, gegen) if rolle == 'A' else (gegen, eigen)
        try:
            cfg = fs.lade_rekonstruktion(rid, projekt)
            bil = fs._bilanz_laden(rid, projekt, a, b)
            diag = fs.blockdiagnose(a, b, cfg, bil)
        except Exception as exc:
            rows.append({**zeile, 'Status': 'FEHLER', 'Meldung': str(exc)[:200]})
            continue
        details[rid] = diag
        nur_netto = len(diag) and diag.Kategorie.eq('Bilanz').all() and diag.attrs.get('grundlage', '').startswith('keine')
        st = 'NUR_NETTO' if nur_netto else ('KONFLIKTE' if len(diag) else 'KEINE_KONFLIKTE')
        rows.append({**zeile, 'Status': st, 'Bilanzstatus': (bil or {}).get('status', ''), 'Konflikte': int(len(diag)),
                     'Bloecke': diag.attrs.get('bloecke', 0), 'Defizit_max_m2': float(diag.Defizit_m2.max()) if len(diag) else 0.0,
                     'Grundlage': diag.attrs.get('grundlage', ''),
                     'Meldung': {'KEINE_KONFLIKTE': 'notwendige Bedingungen erfüllt; Rekonstruktion in 03 weist Machbarkeit nach',
                                 'KONFLIKTE': 'Zustand mit den Regeln/Freigaben voraussichtlich nicht erreichbar (Details anzeigen)',
                                 'NUR_NETTO': 'NGF A ≠ NGF B ohne Bruttovorgaben: nicht prüfbar'}[st]})
    cols = ['Rekonstruktion', 'Rolle', 'Gegenzustand', 'Status', 'Bilanzstatus', 'Konflikte', 'Bloecke', 'Defizit_max_m2', 'Grundlage', 'Meldung']
    return pd.DataFrame(rows, columns=cols), details
