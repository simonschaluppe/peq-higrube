"""Check delivered results and rebuild aggregates; does not rerun the raw-data KDE."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from gfz_hydrator import PROVINCES


def rebuild(out: Path) -> dict:
    detail = pd.read_csv(out / 'gfz_distribution_by_province_use_storeys.csv')
    audit = pd.read_csv(out / 'allocation_audit.csv', dtype={'GK': str, 'reference_gk': str})
    coverage = pd.read_csv(out / 'reference_coverage.csv', dtype={'GK': str})
    keys = ['Bundesland', 'GK', 'GWR_Nutzung']
    assert set(detail.Bundesland) == set(PROVINCES)
    assert not detail.duplicated(['cell_id', 'GFZ']).any()
    assert not audit.duplicated('cell_id').any()
    assert not coverage.duplicated(keys).any()
    assert np.isfinite(detail[['GFZ', 'BGF_m2']]).all().all()
    assert (detail.BGF_m2 >= 0).all()
    assert detail.GFZ.between(0.05 - 1e-9, 19.95 + 1e-9).all()
    np.testing.assert_allclose((detail.GFZ - .05) / .1,
                               np.round((detail.GFZ - .05) / .1), atol=1e-10)
    cells = detail.groupby('cell_id').BGF_m2.sum()
    assert set(cells.index) == set(audit.cell_id)
    audit = audit.set_index('cell_id')
    actual = cells.reindex(audit.index)
    residual = actual - audit.BGF_target_m2
    np.testing.assert_allclose(actual, audit.BGF_target_m2, rtol=1e-12, atol=1e-5)
    np.testing.assert_allclose(actual, audit.BGF_allocated_m2, rtol=1e-12, atol=1e-5)
    np.testing.assert_allclose(audit.NGF_stat_m2 / .8, audit.BGF_target_m2)
    checked = audit.reset_index().merge(coverage, on=keys, validate='one_to_one', suffixes=('', '_coverage'))
    assert len(checked) == len(audit) == len(coverage)
    np.testing.assert_allclose(checked.BGF_target_m2, checked.BGF_target_m2_coverage)
    expected = np.where(audit.Bundesland == 'Wien', 'Wien', 'Salzburg')
    primary = audit.status == 'reference-exact'
    assert (audit.loc[primary, 'reference_region'] == expected[primary]).all()
    assert (audit.loc[primary, 'GK'] == audit.loc[primary, 'reference_gk']).all()
    assert (audit.n_reference_buildings >= 5).all()
    assert ((checked.status == 'reference-exact') == checked.sufficient).all()
    fallback = audit.loc[~primary]
    total = float(actual.sum())
    national = detail.groupby(['GFZ', 'GWR_Nutzung'], as_index=False).BGF_m2.sum()
    regional = detail.groupby(['Bundesland', 'GFZ'], as_index=False).BGF_m2.sum()
    # Compare independently supplied aggregates before writing refreshed outputs.
    for name, frame, index in [
        ('gfz_distribution_austria_by_use.csv', national, ['GFZ', 'GWR_Nutzung']),
        ('gfz_distribution_by_province.csv', regional, ['Bundesland', 'GFZ']),
    ]:
        old = pd.read_csv(out / name).set_index(index).sort_index()
        new = frame.set_index(index).sort_index()
        pd.testing.assert_index_equal(old.index, new.index)
        np.testing.assert_allclose(old.BGF_m2, new.BGF_m2, rtol=1e-12, atol=1e-5)
        frame.to_csv(out / name, index=False)
    audit['BGF_recomputed_m2'] = actual
    audit['recomputed_delta_m2'] = residual
    audit.to_csv(out / 'category_checks.csv')
    totals = audit.groupby('Bundesland')[['BGF_target_m2', 'BGF_recomputed_m2', 'recomputed_delta_m2']].sum()
    totals.to_csv(out / 'province_checks.csv')
    report = {
        'status': 'delivered_results_checked; see recalculated/validation.json for raw-data run',
        'reference_year': 2021,
        'raw_data_recalculated': False,
        'independent_AT_statistics_checked': False,
        'ngf_per_bgf_assumption': 0.8,
        'allocated_bgf_m2': total,
        'statistical_target_from_delivered_audit_m2': float(audit.BGF_target_m2.sum()),
        'total_allocation_residual_m2': float(residual.sum()),
        'max_absolute_cell_residual_m2': float(residual.abs().max()),
        'n_provinces': len(totals),
        'n_positive_statistical_cells': len(audit),
        'n_fallback_cells': len(fallback),
        'fallback_bgf_m2': float(fallback.BGF_target_m2.sum()),
        'fallback_share_of_total_bgf': float(fallback.BGF_target_m2.sum() / total),
        'fallback_by_type': fallback.groupby('status').BGF_target_m2.sum().to_dict(),
        'fallback_approval': 'User approved existing replacement hierarchy on 2026-10-21',
        'mean_gfz_bgf_weighted': float((detail.GFZ * detail.BGF_m2).sum() / total),
        'bgf_share_above_gfz_8': float(detail.loc[detail.GFZ > 8, 'BGF_m2'].sum() / total),
        'phase_2': 'Documented only; no sensitivity or methodological iteration requested',
        'input_sha256': {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                         for name in ['gfz_distribution_by_province_use_storeys.csv',
                                      'allocation_audit.csv', 'reference_coverage.csv']},
    }
    (out / 'validation_delivered.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('result_dir', nargs='?', type=Path, default=Path(__file__).parent / 'outputs')
    print(json.dumps(rebuild(p.parse_args().result_dir), ensure_ascii=False, indent=2))
