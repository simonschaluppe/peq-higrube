"""Small DataFrame operations; scenario assumptions belong in the notebook."""
import numpy as np
import pandas as pd

DIMENSIONS = ['Geometrie', 'Huelle', 'Heizung', 'PV_Klasse', 'Flexibilitaet', 'Wetter', 'Masse']


def catalog(path, columns):
    frame = pd.read_parquet(path, columns=list(dict.fromkeys(['batch', 'scenario_name', *columns])))
    if frame.duplicated(['batch', 'scenario_name']).any():
        raise ValueError('Doppelte Simulationsidentität')
    parts = frame.scenario_name.str.split('|', expand=True)
    if parts.shape[1] != len(DIMENSIONS):
        raise ValueError('Neue Typologiedimensionen: Zuordnung im Notebook ergänzen')
    parts.columns = DIMENSIONS
    for col in DIMENSIONS:
        frame[col] = parts[col].str.strip()
    frame['Basisarchetyp'] = frame[DIMENSIONS[:3]].agg('|'.join, axis=1)
    frame['Archetype'] = frame.batch + '::' + frame.scenario_name
    frame['Herkunft'] = 'simuliert'
    if frame.duplicated(DIMENSIONS).any():
        raise ValueError('Mehrere Simulationen je Merkmalskombination; Batch auswählen')
    return frame


def add_pv0(frame):
    """No-flex/no-storage electrical approximation. PE results remain unknown."""
    candidates = frame.loc[frame.PV_Klasse.eq('PV30') & frame.Flexibilitaet.eq('noFlex')].copy()
    if not np.allclose(candidates[['Batt_total_charge_input', 'EUIev_el']].fillna(np.inf), 0):
        raise ValueError('PV0-Näherung nur ohne Speicher und Mobilität')
    candidates['PV_Klasse'] = 'PV0'
    keys = DIMENSIONS
    existing = pd.MultiIndex.from_frame(frame[keys])
    candidates = candidates.loc[~pd.MultiIndex.from_frame(candidates[keys]).isin(existing)].copy()
    candidates['Archetype'] += '::synthetic_PV0'
    candidates['Herkunft'] = 'synthetisch PV0/noFlex; PE offen'
    for col in ['PV_total', 'PV_total_direct', 'PV_total_flex', 'PV_to_Egrid', 'VRGrid_to_building']:
        candidates[col] = 0.
    candidates['Grid_to_building_min'] = candidates.EUI_el_total
    for col in candidates:
        if col.startswith('PEI_'):
            candidates[col] = np.nan
    return pd.concat([frame, candidates], ignore_index=True)


def allocate(frame, bases, area_column, shares, weather, mass, eligible, target=0.):
    """Disjoint PEQ/rest allocations, preserving each supplied base area."""
    if not 0 <= target <= 1:
        raise ValueError('PEQ-Ziel außerhalb 0..1')
    for weights in [weather, mass]:
        if any(v < 0 for v in weights.values()) or not np.isclose(sum(weights.values()), 1):
            raise ValueError('Gewichte müssen nichtnegativ sein und eins ergeben')
    if bases.Basisarchetyp.duplicated().any():
        raise ValueError('Basisflächen nicht eindeutig')
    area = bases[area_column]
    if area.isna().any() or (area < 0).any():
        raise ValueError('Basisflächen fehlen oder sind negativ')
    eligible_area = area.loc[eligible].sum()
    requested = target * area.sum()
    if requested > eligible_area + 1e-6:
        raise ValueError(f'PEQ-Ziel {requested:g} m² überschreitet geeignete Fläche {eligible_area:g} m²')
    q = requested / eligible_area if eligible_area else 0.
    rows = []
    for idx, base in bases.iterrows():
        if base[area_column] == 0:
            continue
        peq = q if eligible.loc[idx] else 0.
        for status in ['Bestand', 'Neubau', 'Sanierung']:
            status_share = base[status]
            if pd.isna(status_share) or status_share < 0:
                raise ValueError('Statusanteil fehlt/negativ')
            distribution = shares[status]
            if any(v < 0 for v in distribution.values()) or not np.isclose(sum(distribution.values()), 1):
                raise ValueError('PV/Flex-Anteile müssen eins ergeben')
            for is_peq, fraction, mix in [(True, peq, {('PV70','Flex'):1.}), (False, 1-peq, distribution)]:
                for (pv, flex), weight in mix.items():
                    for w, ww in weather.items():
                        for m, mw in mass.items():
                            value = base[area_column]*status_share*fraction*weight*ww*mw
                            if value > 0:
                                rows.append(dict(Basisarchetyp=base.Basisarchetyp, PV_Klasse=pv,
                                    Flexibilitaet=flex, Wetter=w, Masse=m, Status=status,
                                    PEQ=is_peq, BGF=value))
    allocation = pd.DataFrame(rows)
    keys = ['Basisarchetyp', *DIMENSIONS[3:]]
    result = allocation.merge(frame, on=keys, how='left', validate='many_to_one', indicator=True)
    if result._merge.ne('both').any():
        raise ValueError('Gewichtete Varianten fehlen: '+str(result.loc[result._merge.ne('both'), keys].head().to_dict('records')))
    actual = result.groupby('Basisarchetyp').BGF.sum().reindex(bases.Basisarchetyp, fill_value=0)
    np.testing.assert_allclose(actual, area, rtol=1e-10, atol=1e-6)
    return result.drop(columns='_merge')


def collapse(allocation):
    """One row per simulated variant, with weighted status and PEQ fractions."""
    group = allocation.groupby('Archetype', sort=False)
    result = group.first().drop(columns=['Status', 'PEQ', 'BGF'])
    result['BGF'] = group.BGF.sum()
    for status in ['Bestand', 'Neubau', 'Sanierung']:
        result[status] = allocation.BGF.where(allocation.Status.eq(status), 0).groupby(allocation.Archetype).sum()/result.BGF
    result['PEQ_Anteil_2040'] = allocation.BGF.where(allocation.PEQ, 0).groupby(allocation.Archetype).sum()/result.BGF
    return result.reset_index()
