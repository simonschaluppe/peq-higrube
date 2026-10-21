"""Compare the independently rerun Excel model with the delivered reference."""
import json
from pathlib import Path
import numpy as np
import pandas as pd


def compare(out: Path) -> dict:
    keys = ['Bundesland', 'GK', 'GWR_Nutzung', 'GFZ']
    old = pd.read_csv(out / 'gfz_distribution_by_province_use_storeys.csv').set_index(keys).BGF_m2
    new = pd.read_csv(out / 'recalculated/gfz_distribution_by_province_use_storeys.csv').set_index(keys).BGF_m2
    common = old.index.union(new.index)
    diff = new.reindex(common, fill_value=0) - old.reindex(common, fill_value=0)
    total = float(old.sum())
    report = {
        'comparison': 'original Excel rerun versus delivered reference',
        'delivered_bgf_m2': total,
        'recalculated_bgf_m2': float(new.sum()),
        'national_relative_difference': float((new.sum() - total) / total),
        'sum_absolute_bin_difference_m2': float(diff.abs().sum()),
        'relative_absolute_bin_difference': float(diff.abs().sum() / total),
        'max_absolute_bin_difference_m2': float(diff.abs().max()),
        'delivered_rows': len(old),
        'recalculated_rows': len(new),
        'equal_with_numerical_tolerance': bool(np.allclose(new.reindex(common, fill_value=0), old.reindex(common, fill_value=0), rtol=1e-9, atol=1e-5)),
    }
    (out / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    print(json.dumps(compare(Path(__file__).parent / 'outputs'), indent=2))
