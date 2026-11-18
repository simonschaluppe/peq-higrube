"""Hilfen für die lokale Gesamtprüfung (AP7). Nur lesen und vergleichen – keine Zustandsbildung, keine Optimierung, kein Schreiben.

abnahmestand(projekt)
    Übersicht aller registrierten Szenarien, Vergleiche und Flächenstrompaare: gespeichert? Integrität (SHA-256)?
    gehören gespeicherte Flüsse zu den aktuellen Zuständen? stimmen die gespeicherten Maßnahmenraten mit einer
    erneuten Auswertung aus den gespeicherten Flüssen überein (Abnahmeschritt 8)?
wiederholbarkeit(neu, gespeichert, definition)
    Vergleicht eine neu gerechnete Rekonstruktion mit dem gespeicherten Ergebnis desselben Paares (Abnahmeschritt 9).
    Maßgeblich sind die Zielwerte und die Bilanz-/Ratengrößen; einzelne Flüsse dürfen bei gleichwertigen
    LP-Lösungen abweichen (Zuordnung nicht eindeutig) und werden nur als HINWEIS ausgewiesen.

Numerische Toleranz: tol = max(1 m², 1e-7 · T_A). Begründung: HiGHS arbeitet mit relativen Primal-/Dual-Toleranzen
von 1e-7; bei T_A ≈ 9 · 10^8 m² entspricht das rund 90 m² (≈ 1e-5 %-Punkte der Ausgangs-NGF).
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

import gebaeudesektor as gs
import flaechenstroeme as fs
import massnahmen as ms

REL_TOL = 1e-7


def toleranz_m2(t_a):
    return max(1.0, REL_TOL * float(t_a))


def _fassung(log):
    return ((log or {}).get('software') or {}).get('projektfassung') or 'vor 1.6.0'


def _zeile(objekt, oid, status, fassung, detail):
    return {'Objekt': objekt, 'ID': oid, 'Status': status, 'Fassung': fassung, 'Detail': detail}


def _szenarien(projekt):
    rows = []
    for _, s in gs.registrierte_szenarien(projekt).iterrows():
        sid = s.Szenario_ID
        if not (Path(projekt['ergebnisse']['szenarien']) / sid).is_dir():
            rows.append(_zeile('Szenario', sid, 'FEHLT', '–', 'nicht gespeichert (01_Szenario, BERECHNEN und EXPORTIEREN)'))
            continue
        try:
            z = gs.lade_gespeichertes_szenario(sid, projekt)
            ok = z['integritaet'].startswith('OK')
            rows.append(_zeile('Szenario', sid, 'OK' if ok else 'HINWEIS', (z['protokoll'].get('software') or {}).get('modellversion', '–'),
                               f"{z['integritaet']}; NGF {float(z['df'].NGF_m2.sum()):,.0f} m²; Energie: {z['energiestatus']}; "
                               f"Kennwerte {'vorhanden' if z['kennwerte'] is not None else 'fehlen'}; Zustand-ID {str(z['zustand_id'])[:16]}"))
        except Exception as e:
            rows.append(_zeile('Szenario', sid, 'FEHLERHAFT', '–', f'{type(e).__name__}: {e}'[:300]))
    return rows


def _vergleiche(projekt):
    import szenarienvergleich as sv
    rows = []
    for vid in sv.lade_vergleichsregister(projekt).get('vergleiche', {}):
        if not (Path(projekt['ergebnisse']['vergleiche']) / vid).is_dir():
            rows.append(_zeile('Vergleich', vid, 'FEHLT', '–', 'nicht gespeichert (02_Szenarienvergleich, EXPORTIEREN)'))
            continue
        try:
            v = sv.lade_vergleich(vid, projekt)
            rows.append(_zeile('Vergleich', vid, 'OK' if v['integritaet'].startswith('OK') else 'HINWEIS', _fassung(v['protokoll']),
                               f"{v['integritaet']}; {v['kennwerte'].shape[0]} Kennwertzeilen"))
        except Exception as e:
            rows.append(_zeile('Vergleich', vid, 'FEHLERHAFT', '–', f'{type(e).__name__}: {e}'[:300]))
    return rows


def wiederauswertung(r, d, ordner):
    """Vergleicht gespeicherte Massnahmenraten.csv mit einer erneuten Auswertung aus den gespeicherten Flüssen."""
    datei = Path(ordner) / 'Massnahmenraten.csv'
    if not datei.is_file():
        return 'HINWEIS', 'Massnahmenraten.csv fehlt (vor AP5 gespeichert)'
    alt = pd.read_csv(datei, sep=';', encoding='utf-8-sig').set_index('Massnahme').Flaeche_m2
    neu = ms.massnahmenraten(r, d).set_index('Massnahme').Flaeche_m2
    gemeinsam = alt.index.intersection(neu.index)
    tol = toleranz_m2(ms.massnahmenraten(r, d).attrs['nenner_m2'])
    diff = float((alt[gemeinsam] - neu[gemeinsam]).abs().max()) if len(gemeinsam) else np.nan
    fehlend = [m for m in neu.index if m not in alt.index]
    if not len(gemeinsam) or diff > tol:
        return 'FEHLER', f'gespeicherte und neu ausgewertete Raten weichen ab (max. {diff:,.2f} m²)'
    t = f'{len(gemeinsam)} Raten identisch neu ausgewertet (max. Abweichung {diff:.3g} m²)'
    if fehlend:
        return 'HINWEIS', t + f'; nicht in der gespeicherten Datei (ältere Fassung): {len(fehlend)} Zeilen, u. a. Dekarbonisierung – wird aus den Flüssen ausgewertet, Fossilbilanz.csv erst nach Neu-Speichern'
    return 'OK', t


def _fluesse(projekt):
    rows = []
    d = ms.lade_definition(projekt) if projekt['konfiguration'].get('massnahmen') else None
    for _, x in fs.registrierte_rekonstruktionen(projekt).iterrows():
        rid = x.Rekonstruktion_ID
        ordner = Path(projekt['ergebnisse']['flaechenstroeme']) / rid
        if not ordner.is_dir():
            rows.append(_zeile('Flächenströme', rid, 'FEHLT', '–', 'nicht gespeichert (03_Flaechenstroeme, Rekonstruktion und EXPORTIEREN)'))
            continue
        r = fs.analysiere_rekonstruktion(rid, projekt)          # Modus VorhandeneFluesse: nur lesen, kein Solver
        try:
            fassung = _fassung(json.loads((ordner / 'flussprotokoll.json').read_text(encoding='utf-8')))
        except Exception:
            fassung = '–'
        if r.get('quelle') != 'gespeichert':
            rows.append(_zeile('Flächenströme', rid, 'FEHLERHAFT', fassung, f"{r['status']}: {r.get('meldung') or r.get('statusbedeutung', '')}"[:300]))
            continue
        detail = f"{r['status']}; Bilanz {r.get('bilanzstatus', '–')}; Quellen A/B aktuell"
        status = 'OK'
        if r['status'] == fs.MACHBAR and d is not None:
            s, t = wiederauswertung(r, d, ordner)
            k = ms.kontrollen(r, d)
            if (k.Status == 'FEHLER').any():
                s, t = 'FEHLER', t + '; Maßnahmenkontrollen: ' + ', '.join(k.loc[k.Status == 'FEHLER', 'Pruefung'])
            status = s if s != 'OK' else status
            detail += '; ' + t
        elif r['status'] != fs.MACHBAR:
            status = 'HINWEIS'
        rows.append(_zeile('Flächenströme', rid, status, fassung, detail))
    return rows


def abnahmestand(projekt=None):
    """Stand aller registrierten Ergebnisse für die Abnahme (nur lesen)."""
    projekt = gs.lade_projekt(projekt)
    return pd.DataFrame(_szenarien(projekt) + _vergleiche(projekt) + _fluesse(projekt))


def _p(rows, name, status, detail, diff=np.nan):
    rows.append({'Pruefung': name, 'Status': status, 'Detail': detail, 'Differenz_m2': diff})


def wiederholbarkeit(neu, gespeichert, d=None):
    """Neu gerechnete Rekonstruktion gegen gespeichertes Ergebnis desselben Paares (nur vergleichen).

    FEHLER: Status, Zielwerte oder Neubau/Abriss außerhalb der Toleranz. HINWEIS: Raten oder Flüsse je Typpaar weichen ab,
    obwohl die Zielwerte übereinstimmen (gleichwertige alternative Zuordnung; nicht eindeutig)."""
    rows = []
    if neu.get('quelle') == 'gespeichert':
        raise ValueError('„neu“ wurde aus dem Ergebnisordner geladen; für die Wiederholbarkeit zuerst neu rekonstruieren.')
    _p(rows, 'Status gleich', 'OK' if neu['status'] == gespeichert['status'] else 'FEHLER', f"{neu['status']} / {gespeichert['status']}")
    if neu['status'] != fs.MACHBAR or gespeichert['status'] != fs.MACHBAR:
        return pd.DataFrame(rows)
    fn, fg = neu['fluesse'], gespeichert['fluesse']
    ab = gespeichert.get('abriss')
    t_a = float(fg.NGF_m2.sum()) + (float(pd.to_numeric(ab.NGF_m2).sum()) if isinstance(ab, pd.DataFrame) and len(ab) else 0.0)
    tol = toleranz_m2(t_a)
    zn, zg = neu.get('zielwerte') or {}, gespeichert.get('zielwerte') or {}
    for k, name in [('geaendert_m2', 'Zielwert geänderte Bestandsfläche'), ('versorgungswechsel_m2', 'Zielwert Versorgungswechsel')]:
        if k in zn and k in zg:
            dv = abs(float(zn[k]) - float(zg[k]))
            _p(rows, name, 'OK' if dv <= tol else 'FEHLER', f'{float(zn[k]):,.2f} / {float(zg[k]):,.2f} m² (Toleranz {tol:,.1f} m²)', dv)
        else:
            _p(rows, name, 'HINWEIS', 'Zielwert nicht in beiden Ergebnissen vorhanden')
    for k, name in [('neubau', 'Neubau gesamt'), ('abriss', 'Abriss gesamt')]:
        a = float(pd.to_numeric(neu[k].NGF_m2).sum()) if isinstance(neu.get(k), pd.DataFrame) and len(neu[k]) else 0.0
        b = float(pd.to_numeric(gespeichert[k].NGF_m2).sum()) if isinstance(gespeichert.get(k), pd.DataFrame) and len(gespeichert[k]) else 0.0
        _p(rows, name, 'OK' if abs(a - b) <= tol else 'FEHLER', f'{a:,.2f} / {b:,.2f} m²', abs(a - b))
    if d is not None:
        rn = ms.massnahmenraten(neu, d).set_index('Massnahme'); rg = ms.massnahmenraten(gespeichert, d).set_index('Massnahme')
        haupt = rn.index[rn.Ebene.isin(['Rate', 'Summe'])]
        dv = (rn.loc[haupt, 'Flaeche_m2'] - rg.loc[haupt, 'Flaeche_m2']).abs()
        _p(rows, 'Maßnahmenraten (Haupt- und Summenzeilen)', 'OK' if float(dv.max()) <= tol else 'HINWEIS',
           f'{len(haupt)} Kennzahlen; größte Abweichung {dv.idxmax()}: {float(dv.max()):,.2f} m²', float(dv.max()))
    key = ['Herkunft_Typ', 'Ziel_Typ']
    m = fn.groupby(key).NGF_m2.sum().to_frame('neu').join(fg.groupby(key).NGF_m2.sum().to_frame('alt'), how='outer').fillna(0.0)
    dv = float((m.neu - m.alt).abs().sum()) / 2
    _p(rows, 'Flüsse je Typpaar', 'OK' if dv <= tol else 'HINWEIS',
       f'verschobene Fläche {dv:,.2f} m² ({100 * dv / t_a:.4f} % von T_A)' + ('' if dv <= tol else '; gleichwertige alternative Zuordnung, Zielwerte maßgeblich'), dv)
    return pd.DataFrame(rows)
