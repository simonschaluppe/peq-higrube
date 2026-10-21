"""Regression tests: python -m unittest -v test_gfz_hydrator.py"""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from gfz_hydrator import (
    norm_gk, norm_usage, estimate_distribution,
    calculate, read_statistics, PROVINCES, STOREYS, USES,
)


class GFZTests(unittest.TestCase):
    def test_storey_class_normalization(self):
        for example in ("6 bis 10", "6-10", "6010", "6–10"):
            self.assertEqual(norm_gk(example), "6-10")
        self.assertEqual(norm_gk("11+"), "11+")
        self.assertEqual(norm_gk(2), "2")
        self.assertEqual(norm_usage("Mehrfamilienhaus klein"), "Mehrfamilienhaus")

    def test_area_weights_not_building_counts(self):
        group = pd.DataFrame({"GFZ": [0.05, 0.15], "BGF": [1.0, 9.0]})
        mass, _ = estimate_distribution(group, np.array([0.05, 0.15, 0.25]), method="histogram")
        np.testing.assert_allclose(mass, [0.1, 0.9, 0], atol=1e-12)

    def test_allocation_preserves_area(self):
        rows = [("Salzburg", "6-10", "Mehrfamilienhaus", x, bgf)
                for x, bgf in [(1.15, 50), (1.75, 200), (2.15, 80), (1.25, 120), (0.95, 100)]]
        rows += [("Wien", "6-10", "Mehrfamilienhaus", x, 100)
                 for x in [3.25, 3.45, 3.65, 4.05, 4.25]]
        samples = pd.DataFrame(rows, columns=["Bundesland", "GK", "GWR_Nutzung", "GFZ", "BGF"])
        targets = pd.DataFrame({"NUTS": ["Salzburg", "Tirol", "Wien"],
                                "GK": ["6-10"]*3, "GWR_Nutzung": ["Mehrfamilienhaus"]*3,
                                "NGF_m2": [100, 200, 300], "BGF_target_m2": [125, 250, 375]})
        detail, audit = calculate(samples, targets, gfz_step=0.1, gfz_max=10,
                                  min_samples=5, fallback="error", method="kde")
        self.assertEqual(audit["status"].tolist(), ["reference-exact"] * 3)
        self.assertEqual(audit["reference_region"].tolist(), ["Salzburg", "Salzburg", "Wien"])
        self.assertAlmostEqual(float(detail["BGF_m2"].sum()), 750.0, places=7)
        for _, row in audit.iterrows():
            self.assertAlmostEqual(row.BGF_target_m2, row.BGF_allocated_m2, places=7)

    def test_missing_reference_must_be_explicit(self):
        s = pd.DataFrame({"Bundesland": ["Wien"] * 5, "GK": ["2"]*5,
                          "GWR_Nutzung": ["Gemeinschaftsgebäude"]*5,
                          "GFZ": [1.1, 1.2, 1.3, 1.4, 1.5], "BGF": [10.0]*5})
        t = pd.DataFrame({"NUTS": ["Tirol"], "GK": ["2"],
                          "GWR_Nutzung": ["Gemeinschaftsgebäude"],
                          "NGF_m2": [800.0], "BGF_target_m2": [1000.0]})
        with self.assertRaisesRegex(ValueError, "Insufficient reference"):
            calculate(s,t,gfz_step=0.1,gfz_max=5,min_samples=5,fallback="error",method="kde")
        result, audit = calculate(s,t,gfz_step=0.1,gfz_max=5,min_samples=5,fallback="vienna",method="kde")
        self.assertEqual(audit.iloc[0]["status"], "fallback-vienna-exact")
        self.assertAlmostEqual(result["BGF_m2"].sum(), 1000.0)

    def test_statistics_sum_reconciliation(self):
        rows=[]
        for nuts in [*PROVINCES, "AT"]:
            for gk in STOREYS:
                row={"NUTS":nuts,"GK":gk}
                row.update({u: 0.0 for u in USES})
                row["Mehrfamilienhaus"] = 90.0 if nuts == "AT" else 10.0
                rows.append(row)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"statistics.csv"
            pd.DataFrame(rows).to_csv(path,index=False)
            target,meta=read_statistics(path,ngf_per_bgf=0.8)
            self.assertAlmostEqual(meta["statistics_ngf_total_m2"],630.0)
            self.assertAlmostEqual(target["BGF_target_m2"].sum(), 787.5)
            rows[0]["Mehrfamilienhaus"]=12.0
            pd.DataFrame(rows).to_csv(path,index=False)
            with self.assertRaisesRegex(ValueError, "do not add up"):
                read_statistics(path,ngf_per_bgf=0.8)

    def test_original_workbook_aggregates_are_not_double_counted(self):
        rows = []
        for region in [*PROVINCES, 'AT', 'AT ohne Wien und Salzburg', 'Alles']:
            for gk in STOREYS:
                rows.append({'NUTS': region, 'GK': gk,
                             **{u: 9.0 if region == 'AT' else 1.0 for u in USES}})
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'statistics.csv'
            pd.DataFrame(rows).to_csv(path, index=False)
            target, meta = read_statistics(path, ngf_per_bgf=0.8)
            self.assertEqual(len(target), 9 * 7 * 9)
            self.assertEqual(meta['excluded_legacy_aggregate_rows'],
                             {'AT ohne Wien und Salzburg': 7, 'Alles': 7})
            rows.append({'NUTS': 'Unknown', 'GK': '1', **{u: 1 for u in USES}})
            pd.DataFrame(rows).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, 'Unknown geographic'):
                read_statistics(path, ngf_per_bgf=0.8)


if __name__ == "__main__":
    unittest.main()
