"""Maßnahmenraten und Maßnahmenkombinationen aus gültigen Flüssen (AP5).

Wertet nur eine vorhandene, gültige Flusstabelle (Status MACHBAR) samt expliziter Neubau-/Abrissflüsse aus.
Keine Optimierung, keine Zustandsbildung, kein Schreiben. Definitionen: config/flaechenstroeme/massnahmen.json.

Einheitlicher Nenner (Festlegung 16.11.2026): Ausgangs-NGF T_A,
    r_M = 100 · A_M / (T_A · (J_B − J_A))   in % der Ausgangs-NGF pro Jahr,
mit A_M = der Maßnahme zugeordnete NGF im Zeitraum. Lineare mittlere Periodenrate; keine beobachtete Jahreszeitreihe,
keine jährlich wiederholte Übergangswahrscheinlichkeit. Bei J_B − J_A ≤ 0 wird keine Rate ausgewiesen.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from distribution_to_json import DOMAENEN

SCHEMA = '1.1'   # 1.1: Abschnitt dekarbonisierung (Ergänzung 17.11.2026)
MACHBAR = 'MACHBAR'
DIMS = ['geometry', 'quality', 'energy', 'pv', 'flex', 'weather', 'mass']
UNVERAENDERLICH = ['geometry', 'weather', 'mass']
HINWEIS = ('Rekonstruktionsbasierte Raten einer ausgewählten zulässigen Zuordnung zwischen zwei Endzuständen '
           '(maximal unveränderte Fläche, bei Gleichheit minimaler Versorgungswechsel). '
           'Zwischenzeitliche Mehrfachwechsel, wiederholte Sanierungen oder Neubau mit anschließendem Abriss sind nicht identifizierbar; '
           'die Werte sind keine beobachteten Bruttomaßnahmenraten. Einzelraten nicht addieren – dieselbe Fläche kann mehrere Maßnahmen '
           'zugleich erhalten (siehe Kombinationen und „mindestens eine Änderung“). PV bezeichnet betroffene NGF, nicht kWp.')


def lade_definition(projekt_oder_pfad):
    """Liest und prüft massnahmen.json (Projekt-Dict mit konfiguration.massnahmen oder Pfad). Rechnet nichts."""
    if isinstance(projekt_oder_pfad, dict):
        pfad = projekt_oder_pfad['konfiguration'].get('massnahmen')
        if pfad is None:
            raise ValueError('config/projekt.json: konfiguration.massnahmen fehlt.')
    else:
        pfad = projekt_oder_pfad
    d = json.loads(Path(pfad).read_text(encoding='utf-8'))
    validiere_definition(d)
    return d


def validiere_definition(d):
    if str(d.get('schema_version')) != SCHEMA:
        raise ValueError(f'massnahmen.json: schema_version {SCHEMA} erwartet.')
    if d.get('nenner') != 'ausgangs_ngf':
        raise ValueError("massnahmen.json: nenner muss 'ausgangs_ngf' sein (Festlegung: Ausgangs-NGF).")
    for k in ['thermische_sanierung', 'versorgungswechsel', 'dekarbonisierung', 'pv', 'flex']:
        if not isinstance(d.get(k), dict) or not d[k].get('bezeichnung'):
            raise ValueError(f'massnahmen.json: Abschnitt {k} mit bezeichnung fehlt.')
    q = DOMAENEN['qualitaet']
    paare = sanierungspaare(d)
    if not paare:
        raise ValueError('massnahmen.json: thermische_sanierung.verbesserungen ist leer.')
    for a, b in paare:
        if a not in q or b not in q:
            raise ValueError(f'massnahmen.json: unbekannte Qualität in Sanierungspaar {a} → {b}.')
        if a == b:
            raise ValueError(f'massnahmen.json: Sanierungspaar {a} → {b} ohne Wechsel.')
    g = d['versorgungswechsel'].get('gruppen') or {}
    zugeordnet = [e for v in g.values() for e in v]
    if sorted(zugeordnet) != sorted(DOMAENEN['versorgung']) or len(set(zugeordnet)) != len(zugeordnet):
        raise ValueError('massnahmen.json: versorgungswechsel.gruppen muss jede Versorgungskategorie genau einmal enthalten.')
    dk = d['dekarbonisierung']; fo = list(dk.get('fossil') or []); ee = list(dk.get('erneuerbar') or [])
    if not fo or not ee:
        raise ValueError('massnahmen.json: dekarbonisierung.fossil und dekarbonisierung.erneuerbar dürfen nicht leer sein.')
    if set(fo) & set(ee) or sorted(fo + ee) != sorted(DOMAENEN['versorgung']):
        raise ValueError('massnahmen.json: dekarbonisierung.fossil und .erneuerbar müssen jede Versorgungskategorie genau einmal enthalten.')
    if d['pv'].get('folge') != DOMAENEN['pv']:
        raise ValueError(f"massnahmen.json: pv.folge muss {DOMAENEN['pv']} sein.")
    if d['flex'].get('folge') != DOMAENEN['flex']:
        raise ValueError(f"massnahmen.json: flex.folge muss {DOMAENEN['flex']} sein.")
    return True


def sanierungspaare(d):
    return sorted({(a, b) for g in d['thermische_sanierung'].get('verbesserungen', []) for a in g['pre'] for b in g['post'] if a != b})


def pruefe_gegen_regeln(d, regeln):
    """Vergleicht die Sanierungsklassifikation mit den zulässigen Qualitätsübergängen der Regeldatei (nur Hinweise)."""
    import flaechenstroeme as fs
    erlaubt = {p for p in fs.erlaubte_paare('quality', regeln) if p[0] != p[1]}
    s = set(sanierungspaare(d))
    rows = []
    ok = erlaubt == s
    rows.append({'Pruefung': 'Sanierungsklassifikation = zulässige Qualitätswechsel', 'Status': 'OK' if ok else 'HINWEIS',
                 'Detail': f'{len(s)} Paare klassifiziert, {len(erlaubt)} zulässig' + ('' if ok else
                           f"; zulässig, aber nicht klassifiziert: {sorted(erlaubt - s)}; klassifiziert, aber nicht zulässig: {sorted(s - erlaubt)}")})
    return pd.DataFrame(rows)


def _basis(result):
    if result.get('status') != MACHBAR:
        raise ValueError('Keine gültigen Flüsse verfügbar (Status ≠ MACHBAR).')
    f = result['fluesse']
    n = result.get('neubau'); a = result.get('abriss')
    n = n if isinstance(n, pd.DataFrame) and len(n) else pd.DataFrame(columns=['NGF_m2'] + ['post_' + x for x in DIMS])
    a = a if isinstance(a, pd.DataFrame) and len(a) else pd.DataFrame(columns=['NGF_m2'] + ['pre_' + x for x in DIMS])
    t_a = float(f.NGF_m2.sum()) + float(pd.to_numeric(a.NGF_m2).sum())
    jahre = int(result['jahr_b'] - result['jahr_a'])
    return f, n, a, t_a, jahre


def _rang(folge, s):
    return s.map({k: i for i, k in enumerate(folge)})


def merkmale(result, d):
    """Maßnahmenmerkmale je Bestandsfluss (bool-Spalten) – Grundlage für Raten und Kombinationen."""
    f, _, _, _, _ = _basis(result)
    s = set(sanierungspaare(d))
    paar = list(zip(f.pre_quality, f.post_quality))
    qw = f.pre_quality.ne(f.post_quality)
    san = pd.Series([p in s for p in paar], index=f.index) & qw
    pv = _rang(d['pv']['folge'], f.post_pv) - _rang(d['pv']['folge'], f.pre_pv)
    fx = _rang(d['flex']['folge'], f.post_flex) - _rang(d['flex']['folge'], f.pre_flex)
    m = pd.DataFrame({
        'Sanierung': san,
        'Qualitaet_nicht_klassifiziert': qw & ~san,
        'Versorgungswechsel': f.pre_energy.ne(f.post_energy),
        'Dekarbonisierung': f.pre_energy.isin(d['dekarbonisierung']['fossil']) & f.post_energy.isin(d['dekarbonisierung']['erneuerbar']),
        'Refossilisierung': f.pre_energy.isin(d['dekarbonisierung']['erneuerbar']) & f.post_energy.isin(d['dekarbonisierung']['fossil']),
        'PV_Ausbau': pv > 0,
        'PV_Rueckbau': pv < 0,
        'Flexibilisierung': fx > 0,
        'Flex_Rueckbau': fx < 0,
        'Unveraenderliches_Merkmal': np.logical_or.reduce([f['pre_' + x].ne(f['post_' + x]) for x in UNVERAENDERLICH]),
    }, index=f.index)
    m['Mindestens_eine_Aenderung'] = ~f.Herkunft_Typ.eq(f.Ziel_Typ)
    return m


def _zeile(bereich, ebene, name, flaeche, t_a, jahre, basis, rate=True):
    anteil = 100 * flaeche / t_a if t_a > 0 else np.nan
    return {'Bereich': bereich, 'Ebene': ebene, 'Massnahme': name, 'Flaeche_m2': flaeche, 'Anteil_Ausgangs_NGF_pct': anteil,
            'Rate_pct_pro_Jahr': anteil / jahre if rate and jahre > 0 and t_a > 0 else np.nan, 'Flaechenbasis': basis}


def massnahmenraten(result, d):
    """Maßnahmenraten in % der Ausgangs-NGF pro Jahr. Einzelraten überschneiden sich und dürfen nicht addiert werden.

    Ebene 'Rate' = Hauptkennzahl, 'davon' = Aufschlüsselung, 'Rückwärts' = getrennt ausgewiesene Rückentwicklung,
    'Summe' = überschneidungsfreie Kennzahlen, 'Extern' = explizite Neubau-/Abrissflüsse (Neubau getrennt vom Bestand)."""
    f, n, a, t_a, jahre = _basis(result)
    m = merkmale(result, d)
    w = f.NGF_m2
    gruppe = {e: g for g, v in d['versorgungswechsel']['gruppen'].items() for e in v}
    S = lambda mask: float(w[mask].sum())
    rows = []

    def z(bereich, ebene, name, flaeche, basis, rate=True):
        rows.append(_zeile(bereich, ebene, name, flaeche, t_a, jahre, basis, rate))
    z('Bestand', 'Rate', d['thermische_sanierung']['bezeichnung'], S(m.Sanierung), 'Bestandsflüsse mit als Verbesserung klassifiziertem Qualitätswechsel')
    for q in DOMAENEN['qualitaet']:
        v = S(m.Sanierung & f.post_quality.eq(q))
        if v > 0:
            z('Bestand', 'davon', f'davon Zielqualität {q}', v, 'Sanierungsflüsse nach Zielqualität')
    z('Bestand', 'Rückwärts', 'Qualitätswechsel nicht als Sanierung klassifiziert', S(m.Qualitaet_nicht_klassifiziert), 'getrennt ausgewiesen, nicht mit Sanierung verrechnet')
    z('Bestand', 'Rate', d['versorgungswechsel']['bezeichnung'], S(m.Versorgungswechsel), 'Bestandsflüsse mit Änderung der Versorgungskategorie (umgangssprachlich „Kesseltauschrate“)')
    for g in d['versorgungswechsel']['gruppen']:
        v = S(m.Versorgungswechsel & f.post_energy.map(gruppe).eq(g))
        z('Bestand', 'davon', f'davon nach {g}', v, 'Versorgungswechsel nach Zielgruppe')
    for g in d['versorgungswechsel']['gruppen']:
        v = S(m.Versorgungswechsel & f.pre_energy.map(gruppe).eq(g))
        z('Bestand', 'davon', f'davon aus {g}', v, 'Versorgungswechsel nach Herkunftsgruppe')
    dk = d['dekarbonisierung']
    z('Bestand', 'Rate', dk['bezeichnung'], S(m.Dekarbonisierung), 'Bestandsflüsse fossil (' + ', '.join(dk['fossil']) + ') → erneuerbar bzw. nicht fossil; Teilmenge der Versorgungswechsel')
    for g in d['versorgungswechsel']['gruppen']:
        if set(d['versorgungswechsel']['gruppen'][g]) <= set(dk['erneuerbar']):
            z('Bestand', 'davon', f'davon fossil → {g}', S(m.Dekarbonisierung & f.post_energy.map(gruppe).eq(g)), 'Dekarbonisierung nach Zielgruppe')
    for e in dk['fossil']:
        z('Bestand', 'davon', f'davon aus {e}', S(m.Dekarbonisierung & f.pre_energy.eq(e)), 'Dekarbonisierung nach fossilem Ausgangsenergieträger')
    z('Bestand', 'Rückwärts', 'Wechsel erneuerbar → fossil', S(m.Refossilisierung), 'getrennt ausgewiesen, nicht mit Dekarbonisierung verrechnet')
    z('Bestand', 'Rate', d['pv']['bezeichnung'], S(m.PV_Ausbau), 'Bestandsflüsse mit höherer PV-Kategorie (NGF, nicht kWp)')
    z('Bestand', 'davon', 'davon Erstausstattung (PV0 → PV > 0)', S(m.PV_Ausbau & f.pre_pv.eq(d['pv']['folge'][0])), 'PV-Ausbau ohne vorherige PV')
    z('Bestand', 'Rückwärts', 'PV-Rückbau (niedrigere PV-Kategorie)', S(m.PV_Rueckbau), 'getrennt ausgewiesen')
    z('Bestand', 'Rate', d['flex']['bezeichnung'], S(m.Flexibilisierung), 'Bestandsflüsse noFlex → Flex')
    z('Bestand', 'Rückwärts', 'Flex-Rückbau (Flex → noFlex)', S(m.Flex_Rueckbau), 'getrennt ausgewiesen')
    z('Bestand', 'Summe', 'Bestandsfläche mit mindestens einer Änderung (ohne Doppelzählung)', S(m.Mindestens_eine_Aenderung), 'jede Bestandsfläche höchstens einmal')
    z('Bestand', 'Summe', 'Bestandsfläche ohne Änderung', S(~m.Mindestens_eine_Aenderung), 'vollständig unveränderter Typ (Bestandsanteil, keine Maßnahmenrate)', rate=False)
    if result.get('extern') is not None:
        z('Extern', 'Rate', 'Neubaurate', float(pd.to_numeric(n.NGF_m2).sum()), 'explizite Neubau-NGF (getrennt vom Bestand)')
        z('Extern', 'Rate', 'Abrissrate', float(pd.to_numeric(a.NGF_m2).sum()), 'explizite Abriss-NGF')
    out = pd.DataFrame(rows)
    out.attrs['hinweis'] = HINWEIS
    out.attrs['nenner_m2'] = t_a
    out.attrs['jahre'] = jahre
    return out


KOMBI = [('Sanierung', 'Sanierung'), ('Versorgungswechsel', 'Versorgungswechsel'), ('PV_Ausbau', 'PV-Ausbau'), ('Flexibilisierung', 'Flexibilisierung')]


def massnahmenkombinationen(result, d):
    """Überschneidungsfreie Aufteilung der Bestandsfläche auf Maßnahmenkombinationen (jede Fläche genau einmal).
    'Sonstige Änderung' = nicht klassifizierter Qualitätswechsel, PV-/Flex-Rückbau (getrennt, nicht verrechnet)."""
    f, _, _, t_a, jahre = _basis(result)
    m = merkmale(result, d)
    sonst = m.Qualitaet_nicht_klassifiziert | m.PV_Rueckbau | m.Flex_Rueckbau | m.Unveraenderliches_Merkmal
    k = m[[c for c, _ in KOMBI]].copy(); k['Sonstige_Aenderung'] = sonst; k['NGF_m2'] = f.NGF_m2
    t = k.groupby([c for c, _ in KOMBI] + ['Sonstige_Aenderung'], as_index=False).NGF_m2.sum()
    def name(r):
        teile = [lab for c, lab in KOMBI if r[c]] + (['sonstige Änderung'] if r['Sonstige_Aenderung'] else [])
        return ' + '.join(teile) if teile else 'keine Maßnahme'
    t.insert(0, 'Kombination', t.apply(name, axis=1))
    t.insert(1, 'Anzahl_Massnahmen', t[[c for c, _ in KOMBI]].sum(axis=1).astype(int))
    t = t.rename(columns={'NGF_m2': 'Flaeche_m2'})
    t['Anteil_Ausgangs_NGF_pct'] = 100 * t.Flaeche_m2 / t_a if t_a > 0 else np.nan
    t['Rate_pct_pro_Jahr'] = t.Anteil_Ausgangs_NGF_pct / jahre if jahre > 0 else np.nan
    t.loc[t.Kombination.eq('keine Maßnahme'), 'Rate_pct_pro_Jahr'] = np.nan   # Bestandsanteil, keine Maßnahmenrate
    t = t.sort_values(['Anzahl_Massnahmen', 'Flaeche_m2'], ascending=[True, False]).reset_index(drop=True)
    return t


def versorgungswechsel_matrix(result, d):
    """Versorgungswechsel Herkunftsgruppe × Zielgruppe (m² NGF), nur Flüsse mit Änderung der Versorgungskategorie."""
    f, _, _, _, _ = _basis(result)
    g = {e: k for k, v in d['versorgungswechsel']['gruppen'].items() for e in v}; namen = list(d['versorgungswechsel']['gruppen'])
    x = f[f.pre_energy.ne(f.post_energy)]
    t = pd.DataFrame({'Herkunft': x.pre_energy.map(g), 'Ziel': x.post_energy.map(g), 'NGF_m2': x.NGF_m2})
    return t.pivot_table(index='Herkunft', columns='Ziel', values='NGF_m2', aggfunc='sum', fill_value=0.0).reindex(index=namen, columns=namen, fill_value=0.0)


def fossilbilanz(result, d):
    """Fossilbilanz der NGF (Ergänzung 17.11.2026): Verbleib der fossil versorgten Ausgangsfläche F_A und Herkunft der
    fossil versorgten Zielfläche F_B. F_A = Abriss + Dekarbonisierung + Wechsel innerhalb fossil + fossil unverändert;
    F_B = Wechsel innerhalb fossil + fossil unverändert + Wechsel erneuerbar → fossil + Neubau fossil.
    Raten bezogen auf T_A (wie alle Maßnahmenraten) und zusätzlich auf F_A."""
    f, n, a, t_a, jahre = _basis(result)
    fo = d['dekarbonisierung']['fossil']; ee = d['dekarbonisierung']['erneuerbar']
    w = f.NGF_m2; pre = f.pre_energy; post = f.post_energy
    S = lambda mask: float(w[mask].sum())
    abr = float(pd.to_numeric(a.NGF_m2[a['pre_energy'].isin(fo)]).sum()) if len(a) else 0.0
    neu = float(pd.to_numeric(n.NGF_m2[n['post_energy'].isin(fo)]).sum()) if len(n) else 0.0
    dek = S(pre.isin(fo) & post.isin(ee)); inner = S(pre.isin(fo) & post.isin(fo) & pre.ne(post))
    gleich = S(pre.isin(fo) & pre.eq(post)); rueck = S(pre.isin(ee) & post.isin(fo))
    f_a = S(pre.isin(fo)) + abr
    f_b = S(post.isin(fo)) + neu
    zeilen = [('Ausgangszustand', 'Fossil versorgte Fläche im Ausgangszustand F_A', f_a, False),
              ('Verbleib F_A', 'davon abgerissen', abr, True),
              ('Verbleib F_A', 'davon Wechsel zu erneuerbar (Dekarbonisierung)', dek, True),
              ('Verbleib F_A', 'davon Wechsel innerhalb fossil (Erdgas ↔ Öl)', inner, False),
              ('Verbleib F_A', 'davon fossil unverändert', gleich, False),
              ('Herkunft F_B', 'Wechsel erneuerbar → fossil', rueck, True),
              ('Herkunft F_B', 'Neubau fossil', neu, True),
              ('Zielzustand', 'Fossil versorgte Fläche im Zielzustand F_B', f_b, False),
              ('Saldo', 'Rückgang fossil versorgter Fläche F_A − F_B', f_a - f_b, True)]
    rows = []
    for teil, name, v, rate in zeilen:
        r = _zeile('Fossilbilanz', teil, name, v, t_a, jahre, '', rate)
        r.pop('Flaechenbasis')
        r['Anteil_fossile_Ausgangsflaeche_pct'] = 100 * v / f_a if f_a > 0 else np.nan
        r['Rate_fossil_pct_pro_Jahr'] = r['Anteil_fossile_Ausgangsflaeche_pct'] / jahre if rate and jahre > 0 and f_a > 0 else np.nan
        rows.append(r)
    out = pd.DataFrame(rows).rename(columns={'Ebene': 'Teil', 'Massnahme': 'Position'})
    out.attrs['fossil'] = list(fo); out.attrs['erneuerbar'] = list(ee)
    return out


def extern_merkmale(result, d, art='Neubau'):
    """Merkmale der expliziten Neubau- oder Abrissfläche (getrennt von Maßnahmen im Bestand).
    Anteil bezogen auf die Neubau- bzw. Abrissfläche selbst; Rate bezogen auf T_A."""
    f, n, a, t_a, jahre = _basis(result)
    if art not in ('Neubau', 'Abriss'):
        raise ValueError("art muss 'Neubau' oder 'Abriss' sein.")
    x, p = (n, 'post_') if art == 'Neubau' else (a, 'pre_')
    gesamt = float(pd.to_numeric(x.NGF_m2).sum()) if len(x) else 0.0
    g = {e: k for k, v in d['versorgungswechsel']['gruppen'].items() for e in v}
    rows = []
    def add(merkmal, kat, v):
        rows.append({'Art': art, 'Merkmal': merkmal, 'Kategorie': kat, 'Flaeche_m2': v,
                     f'Anteil_{art}_pct': 100 * v / gesamt if gesamt > 0 else np.nan,
                     'Rate_pct_pro_Jahr': 100 * v / (t_a * jahre) if jahre > 0 and t_a > 0 else np.nan})
    if len(x):
        for q, v in x.groupby(p + 'quality').NGF_m2.sum().reindex(DOMAENEN['qualitaet'], fill_value=0.0).items():
            if v > 0:
                add('Qualität', q, float(v))
        gs_ = pd.Series(pd.to_numeric(x.NGF_m2).to_numpy(), index=x[p + 'energy'].map(g).to_numpy()).groupby(level=0).sum()
        for k, v in gs_.reindex(list(d['versorgungswechsel']['gruppen']), fill_value=0.0).items():
            if v > 0:
                add('Versorgungsgruppe', k, float(v))
        add('PV', 'mit PV (> PV0)', float(x.loc[x[p + 'pv'].ne(d['pv']['folge'][0]), 'NGF_m2'].sum()))
        add('Flexibilität', 'Flex', float(x.loc[x[p + 'flex'].eq('Flex'), 'NGF_m2'].sum()))
    add('Gesamt', art, gesamt)
    return pd.DataFrame(rows)


def kontrollen(result, d):
    """Konsistenzprüfungen der Raten- und Kombinationsbilanz."""
    f, n, a, t_a, jahre = _basis(result)
    r = massnahmenraten(result, d).set_index('Massnahme').Flaeche_m2
    k = massnahmenkombinationen(result, d)
    m = merkmale(result, d)
    tol = 0.01 + 1e-9 * max(t_a, 1.0)
    fl = float(f.NGF_m2.sum()); min1 = r['Bestandsfläche mit mindestens einer Änderung (ohne Doppelzählung)']
    rows = []
    def p(name, ok, detail, sonst='FEHLER'):
        rows.append({'Pruefung': name, 'Status': 'OK' if ok else sonst, 'Detail': detail})
    p('Nenner T_A = Bestandsflüsse + Abriss', t_a > 0, f'T_A = {t_a:,.2f} m²')
    ngf_a = result.get('kontrollen')
    if isinstance(ngf_a, pd.DataFrame) and len(ngf_a) and 'NGF_A_m2' in ngf_a and ngf_a.Block.eq('GESAMT').any():
        soll = float(ngf_a.loc[ngf_a.Block.eq('GESAMT'), 'NGF_A_m2'].iloc[0])
        p('Nenner T_A = NGF des Ausgangszustands', abs(soll - t_a) <= tol, f'{t_a:,.2f} vs. {soll:,.2f} m²')
    p('Kombinationen decken die Bestandsfläche genau einmal ab', abs(float(k.Flaeche_m2.sum()) - fl) <= tol, f'{k.Flaeche_m2.sum():,.2f} vs. {fl:,.2f} m²')
    p('Mindestens eine Änderung + ohne Änderung = Bestandsflüsse', abs(min1 + r['Bestandsfläche ohne Änderung'] - fl) <= tol, f'{min1:,.2f} + {r["Bestandsfläche ohne Änderung"]:,.2f} m²')
    einzel = {k_: float(f.NGF_m2[m[k_]].sum()) for k_ in ['Sanierung', 'Versorgungswechsel', 'PV_Ausbau', 'Flexibilisierung']}
    p('Jede Einzelmaßnahme ≤ mindestens eine Änderung', all(v <= min1 + tol for v in einzel.values()), '; '.join(f'{k_} {v:,.0f}' for k_, v in einzel.items()))
    fb = fossilbilanz(result, d).set_index('Position').Flaeche_m2
    p('Dekarbonisierung ≤ Versorgungswechsel', float(f.NGF_m2[m.Dekarbonisierung].sum()) <= einzel['Versorgungswechsel'] + tol,
      f"{f.NGF_m2[m.Dekarbonisierung].sum():,.0f} ≤ {einzel['Versorgungswechsel']:,.0f} m²")
    verbleib = fb.iloc[1:5].sum(); herkunft = fb.iloc[3:7].sum()
    p('Fossilbilanz Verbleib F_A geschlossen', abs(verbleib - fb.iloc[0]) <= tol, f'{verbleib:,.2f} vs. {fb.iloc[0]:,.2f} m²')
    p('Fossilbilanz Herkunft F_B geschlossen', abs(herkunft - fb.iloc[7]) <= tol, f'{herkunft:,.2f} vs. {fb.iloc[7]:,.2f} m²')
    p('Unveränderliche Merkmale ohne Wechsel', not m.Unveraenderliches_Merkmal.any(), 'Geometrie, Wetter, Speichermasse')
    p('Zeitspanne für Jahresraten', jahre > 0, f'{jahre} Jahre' + ('' if jahre > 0 else ' – keine Jahresrate ausgewiesen'), 'HINWEIS')
    return pd.DataFrame(rows)
