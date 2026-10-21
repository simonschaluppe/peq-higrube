import unittest
from .sankey import calculation, figure
from .model import GEN


class SankeyTests(unittest.TestCase):
    def test_baseline_and_reference_residuals(self):
        r = calculation()
        self.assertEqual(r['baseline_year'], 2020)
        self.assertEqual(r['generation']['generation_published_total'] - r['baseline_generation']['published_total'], 208)
        self.assertEqual(r['electricity_residual_pj'], -2)
        self.assertEqual(r['published_electricity_residual_pj'], 0)
        self.assertEqual(sum(x['reduction_pj'] for x in r['comparison'] if x['energy_basis'] == 'energetic_final'), 330)

    def test_variant_preserves_source_and_has_no_credit(self):
        reference = calculation()
        for pv in [0, 1]:
            r = calculation(pv_decentral_share=pv, transport_split={'miv':.6,'ov':.3},
                            savings={'gebaeude':.1}, assumption_source='Test, no normative value')
            self.assertEqual(r['generation'], reference['generation'])
            self.assertEqual(r['endenergy'], reference['endenergy'])
            self.assertAlmostEqual(r['demand']['gebaeude'], .9*reference['demand']['gebaeude'])
            self.assertAlmostEqual(r['electricity_residual_pj'], reference['electricity_residual_pj']+.1*reference['demand']['gebaeude'])
            self.assertIsNone(r['new_mobility_credit'])
            trace = figure(r).data[0]
            labels = list(trace.node.label)
            pv_index = next(i for i,label in enumerate(labels) if label.startswith('Photovoltaik:'))
            self.assertEqual(sum(v for s,v in zip(trace.link.source,trace.link.value) if s == pv_index), r['generation']['pv'])

    def test_invalid_assumptions_are_rejected(self):
        for kwargs in [dict(pv_decentral_share=0),dict(transport_split={'miv':.9,'ov':.2}),
                       dict(savings={'gebaeude':1.01}),dict(pv_decentral_share=float('nan')),
                       dict(savings={'unknown':.1}),dict(baseline_year=2026)]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError): calculation(**kwargs)

    def test_export_and_retirement_are_positive_and_not_double_counted(self):
        r=calculation(); trace=figure(r).data[0]; labels=list(trace.node.label)
        self.assertTrue(all(v >= 0 for v in trace.link.value))
        index=labels.index('Nettoexport')
        self.assertEqual(sum(v for t,v in zip(trace.link.target,trace.link.value) if t==index), 7)
        index=labels.index('Ertrag 2020')
        self.assertEqual(sum(v for s,v in zip(trace.link.source,trace.link.value) if s==index), sum(r['baseline_generation'][k] for k in GEN))


if __name__ == '__main__': unittest.main()
