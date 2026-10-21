"""Published scenario tables and separate, explicitly parameterized allocation layers."""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'Daten/sektorenmodell'
SCENARIOS = ['legacy_streicher', 'transition_2040', 'wem_2025', 'wam_2025', 'wem_2023', 'wam_2023']
LABELS = dict(zip(SCENARIOS, ['Legacy 2023', 'Transition 2040', 'WEM 2025', 'WAM 2025', 'WEM 2023', 'WAM 2023']))
GEN = ['hydro', 'wind', 'pv', 'biomass', 'geothermal', 'hydrogen_electricity', 'fossil']
DEMAND = ['verkehr', 'gebaeude', 'industrie', 'landwirtschaft', 'verbrauch_sektor_energie', 'transportverluste', 'umwandlungseinsatz']
EEV = ['verkehr', 'industrie', 'gebaeude', 'landwirtschaft']
NAMES = {'hydro': 'Wasserkraft', 'wind': 'Windkraft', 'pv': 'Photovoltaik', 'biomass': 'Biomasse inkl. Biomethan',
         'geothermal': 'Geothermie / sonstige Erzeugung¹', 'hydrogen_electricity': 'Wasserstoff-Rückverstromung',
         'fossil': 'Fossile Erzeugung', 'verkehr': 'Verkehr', 'gebaeude': 'Gebäude', 'industrie': 'Industrie',
         'landwirtschaft': 'Landwirtschaft', 'verbrauch_sektor_energie': 'Verbrauch Sektor Energie',
         'transportverluste': 'Transportverluste', 'umwandlungseinsatz': 'Umwandlungseinsatz',
         'generation_published_total': 'Publizierte Erzeugung gesamt', 'net_imports': 'Nettoimporte (− = Export)',
         'electricity_demand_published_total': 'Publizierter Strombedarf gesamt', 'eev_published_total': 'Publizierte Endenergie gesamt'}
SPECS = {
    'endenergie_2040.csv': (EEV + ['eev_published_total'], 'energetic_final'),
    'stromerzeugung_2040.csv': (GEN + ['generation_published_total', 'net_imports'], 'electricity_generation_or_net_import'),
    'strombedarf_2040.csv': (DEMAND + ['electricity_demand_published_total'], 'electricity_demand'),
}


def rows(name, base=DATA):
    with (base / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def load(name, base=DATA):
    metrics, basis = SPECS[name]
    source_ids = {r['source_id'] for r in rows('sources.csv', base)}
    result = {}
    for row in rows(name, base):
        sid, metric = row['scenario'], row['metric']
        if sid not in SCENARIOS[1:] or metric not in metrics or row['year'] != '2040':
            raise ValueError(f'Unexpected scenario/year/metric: {row}')
        if row['energy_basis'] != basis or row['source_id'] not in source_ids or not row['source_location']:
            raise ValueError(f'Invalid energy basis or source: {row}')
        value = float(row['value_pj'])
        if not math.isfinite(value) or (metric != 'net_imports' and value < 0):
            raise ValueError(f'Invalid value: {row}')
        target = result.setdefault(sid, {})
        if metric in target:
            raise ValueError(f'Duplicate key: {sid}/{metric}')
        target[metric] = {**row, 'value_pj': value}
    if set(result) != set(SCENARIOS[1:]) or any(set(v) != set(metrics) for v in result.values()):
        raise ValueError(f'Incomplete scenarios or metrics in {name}')
    return result


def values(table, sid):
    return {k: r['value_pj'] for k, r in table[sid].items()}


def validate_baselines(base=DATA):
    specs = {'electricity_generation': GEN + ['net_imports', 'published_total'],
             'electricity_demand': DEMAND + ['published_total'],
             'energetic_final': EEV + ['published_total']}
    sources = {r['source_id'] for r in rows('sources.csv', base)}
    expected = {(str(year), basis, metric) for year in [2020, 2023] for basis, metrics in specs.items() for metric in metrics}
    found = set()
    for row in rows('baseline_energy.csv', base):
        key = (row['year'], row['energy_basis'], row['metric'])
        if key not in expected or key in found or row['source_id'] not in sources or not row['source_location']:
            raise ValueError(f'Invalid baseline key/source: {row}')
        value = float(row['value_pj'])
        if not math.isfinite(value) or (row['metric'] != 'net_imports' and value < 0):
            raise ValueError(f'Invalid baseline value: {row}')
        found.add(key)
    if found != expected:
        raise ValueError('Incomplete baseline data')


def validate(base=DATA):
    validate_baselines(base)
    e, g, d = (load(n, base) for n in SPECS)
    reports = []
    for sid in SCENARIOS[1:]:
        ev, gv, dv = (values(t, sid) for t in (e, g, d))
        report = {
            'scenario': sid,
            'eev_rounding_difference_pj': sum(ev[k] for k in EEV) - ev['eev_published_total'],
            'generation_rounding_difference_pj': sum(gv[k] for k in GEN) - gv['generation_published_total'],
            'electricity_rounding_difference_pj': sum(dv[k] for k in DEMAND) - dv['electricity_demand_published_total'],
            'electricity_balance_residual_pj': gv['generation_published_total'] + gv['net_imports'] - dv['electricity_demand_published_total'],
        }
        expected = next(r for r in rows('validierung_veroeffentlichte_summen.csv', base) if r['scenario'] == sid)
        for key, limit in [('eev_rounding_difference_pj', 2), ('generation_rounding_difference_pj', 2),
                           ('electricity_rounding_difference_pj', 3), ('electricity_balance_residual_pj', 3)]:
            if abs(report[key]) > limit or report[key] != float(expected[key]):
                raise ValueError(f'Unexpected residual {sid}/{key}: {report[key]}')
        reports.append(report)
    if values(e, 'wem_2025')['eev_published_total'] != 1003:
        raise ValueError('WEM 2025 published EEV must remain 1003 PJ')
    legacy = rows('legacy_gutschriften_nutzungen.csv', base)
    if {r['usage']: float(r['credit_kwh_pe_per_m2_ngf_a']) for r in legacy} != dict(wohnen=14.11, buero_gewerbe=41.47, bildung=12.93, handel_sonstige=29.97):
        raise ValueError('Legacy credits changed')
    return reports


def check_parameters(parameters):
    if set(parameters) != set(SCENARIOS):
        raise ValueError('Parameters must explicitly list all scenarios')
    for sid, config in parameters.items():
        shares = config['central_generation_share']
        if set(shares) != set(GEN):
            raise ValueError(f'Incomplete source shares for {sid}')
        for v in [*shares.values(), config['miv_share_of_transport_electricity']]:
            if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1):
                raise ValueError('Shares must be null or finite numbers in [0,1]')
        if any(v is not None for v in shares.values()) or config['miv_share_of_transport_electricity'] is not None:
            if not config['parameter_source']:
                raise ValueError('Non-null shares require a documented parameter_source')
        # Subsequent priority/PE conversion is deliberately not implemented.
        for field in ['priority_rule', 'import_allocation_rule', 'primary_energy_factors']:
            if config[field] is not None:
                raise ValueError(f'{field} is documented but not implemented; no credit may be inferred')


def build_structure(parameters, base=DATA):
    check_parameters(parameters)
    gen, demand = load('stromerzeugung_2040.csv', base), load('strombedarf_2040.csv', base)
    node_ids = [*GEN, 'electricity_system', 'imports', 'exports', *DEMAND,
                'central_pool', 'decentral_pool', 'miv', 'other_transport', 'credit_budget_pe', 'mobility_credit_pe']
    nodes = [{'id': n, 'label': NAMES.get(n, n)} for n in node_ids]
    reports = {r['scenario']: r for r in validate(base)}
    result = {'schema_version': 1, 'unit': 'PJ/a, energy_basis required per layer',
              'sources': rows('sources.csv', base), 'nodes': nodes, 'scenarios': {}}
    scenario_meta = {r['scenario']: r for r in rows('szenarien.csv', base)}
    legacy_values = {r['metric']: r for r in rows('legacy_operationalisierung_2023.csv', base)}
    for sid in SCENARIOS:
        config = parameters[sid]
        links = []
        def link(source, target, value, basis, kind, origin, location, status='documented'):
            links.append(dict(source=source, target=target, value_pj=value, energy_basis=basis,
                              flow_kind=kind, source_id=origin, source_location=location, status=status))
        if sid != 'legacy_streicher':
            for metric in GEN:
                r = gen[sid][metric]
                link(metric, 'electricity_system', r['value_pj'], 'electricity', 'physical', r['source_id'], r['source_location'])
            r = gen[sid]['net_imports']
            link('imports' if r['value_pj'] >= 0 else 'electricity_system',
                 'electricity_system' if r['value_pj'] >= 0 else 'exports', abs(r['value_pj']),
                 'electricity', 'physical', r['source_id'], r['source_location'])
            for metric in DEMAND:
                r = demand[sid][metric]
                link('electricity_system', metric, r['value_pj'], 'electricity', 'physical', r['source_id'], r['source_location'])
            for metric in GEN:
                share = config['central_generation_share'][metric]
                for pool, fraction in [('central_pool', share), ('decentral_pool', None if share is None else 1-share)]:
                    link(metric, pool, None if fraction is None else gen[sid][metric]['value_pj'] * fraction,
                         'electricity', 'normative_allocation', 'PARAMETER', config['parameter_source'], 'pending' if fraction is None else 'explicit_assumption')
            for target, fraction in [('miv', config['miv_share_of_transport_electricity']),
                                     ('other_transport', None if config['miv_share_of_transport_electricity'] is None else 1-config['miv_share_of_transport_electricity'])]:
                link('verkehr', target, None if fraction is None else demand[sid]['verkehr']['value_pj'] * fraction,
                     'electricity', 'normative_allocation', 'PARAMETER', config['parameter_source'], 'pending' if fraction is None else 'explicit_assumption')
        for target in ['industrie', 'other_transport', 'miv']:
            link('central_pool', target, None, 'electricity', 'normative_allocation', 'PARAMETER', 'Priority and eligibility rule outstanding', 'pending')
        credit = float(legacy_values['mobilitaetsbudget_primärenergie']['value']) * 3.6 if sid == 'legacy_streicher' else None
        link('credit_budget_pe', 'mobility_credit_pe', credit, 'primary_energy', 'virtual_credit',
             'SCHNEIDER2023' if credit is not None else 'PARAMETER', 'Table 8; TWh × 3.6 = PJ' if credit is not None else 'PE factors and allocation pending',
             'documented' if credit is not None else 'pending')
        physical = [l for l in links if l['flow_kind'] == 'physical']
        result['scenarios'][sid] = {
            'label': LABELS[sid], 'links': links,
            'target_year': scenario_meta[sid]['target_year'],
            'role': scenario_meta[sid]['role'],
            'legacy_documented_metrics': list(legacy_values.values()) if sid == 'legacy_streicher' else [],
            'physical_data_complete': sid != 'legacy_streicher',
            'normative_allocation_complete': False,
            'residuals': reports.get(sid),
            'plotly_physical': {'type': 'sankey', 'node': {'label': [n['label'] for n in nodes]},
                'link': {'source': [node_ids.index(l['source']) for l in physical],
                         'target': [node_ids.index(l['target']) for l in physical],
                         'value': [l['value_pj'] for l in physical]}},
            'notes': 'Printed rounding and source discrepancies retained; no artificial balancing flows. Legacy has no complete comparable electricity table.',
        }
    return result


def table(name, metrics, title, identifier, citation, base=DATA):
    data = load(name, base)
    order = SCENARIOS[1:]
    lines = ['| ' + title + ' | ' + ' | '.join(LABELS[s] for s in order) + ' |', '|---|' + '---:|' * len(order)]
    for metric in metrics:
        lines.append('| ' + NAMES[metric] + ' | ' + ' | '.join(f'{data[s][metric]["value_pj"]:g}' for s in order) + ' |')
    lines.extend(['', f': {citation} {{#{identifier}}}', ''])
    return '\n'.join(lines)


def artifacts(parameters):
    report = validate()
    structure = build_structure(parameters)
    generation = table('stromerzeugung_2040.csv', GEN + ['generation_published_total', 'net_imports'], 'Stromerzeugung 2040 [PJ_el/a]',
        'tbl-allokation-stromerzeugung-2040', 'Publizierte Stromerzeugung und Nettoimporte. Transition: REP-0880, Tab. 16, S. 63; WEM/WAM 2023: REP-0882, Zusammenfassung, Tab. D, S. 8; WEM/WAM 2025: REP-0995, Tab. E, S. 12 [@uba2023transition; @uba2023zusammenfassung; @uba2025szenarien].')
    demand = table('strombedarf_2040.csv', DEMAND + ['electricity_demand_published_total'], 'Strombedarf 2040 [PJ_el/a]',
        'tbl-allokation-strombedarf-2040', 'Publizierter Strombedarf einschließlich Energiebranche, Verlusten und Umwandlung. Transition: REP-0880, Tab. 15, S. 60; WEM/WAM 2023: REP-0882, Tab. 12, S. 39; WEM/WAM 2025: REP-0995, Tab. 18, S. 62 [@uba2023transition; @uba2023szenarien; @uba2025szenarien].')
    rounding = '| Szenario | Erzeugung: Komponenten − Gesamt | Bedarf: Komponenten − Gesamt | Erzeugung + Nettoimport − Bedarf |\n|---|---:|---:|---:|\n'
    for r in report:
        rounding += '| ' + LABELS[r['scenario']] + ' | ' + ' | '.join(f'{r[k]:+g}' for k in ['generation_rounding_difference_pj', 'electricity_rounding_difference_pj', 'electricity_balance_residual_pj']) + ' |\n'
    rounding += '\n: Dokumentierte Rundungs- und Bilanzreste in PJ_el/a, aus denselben publizierten Tabellen berechnet. Keine Verteilung auf Einzelpositionen. {#tbl-szenario-bilanzreste}\n'
    content = '<!-- Generated by Berechnungen/sektorenmodell/generate.py; edit CSV inputs, not tables. -->\n\n' + generation + '\n' + demand + '\n¹ Transition: Geothermie; die Vergleichstabellen verwenden die breitere Kategorie „Umgebungswärme etc.“. Striche bei WEM/WAM 2023 wurden in der übergebenen Normierung als null geführt.\n\n' + rounding
    eev = table('endenergie_2040.csv', EEV + ['eev_published_total'], 'Endenergie 2040 [PJ_end/a]', 'tbl-eev-data-only',
        'Separater Sektorausweis, nicht Teil der Stromallokation. Quellen: REP-0880 Tab. A S. 7, REP-0882 Zusammenfassung Tab. B S. 5, REP-0995 Tab. B S. 10.')
    return {ROOT / 'Kapitel/_generated/transition-stromtabellen.qmd': content,
            DATA / 'endenergie_vergleich.md': eev,
            DATA / 'scenario_validation.json': json.dumps(report, ensure_ascii=False, indent=2) + '\n',
            DATA / 'sankey_structure.json': json.dumps(structure, ensure_ascii=False, indent=2) + '\n'}
