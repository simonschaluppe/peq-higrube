import copy
import json
import unittest
from .model import DATA, build_structure, check_parameters, validate


class ScenarioTests(unittest.TestCase):
    def setUp(self):
        self.parameters = json.loads((DATA / 'allocation_parameters.json').read_text(encoding='utf-8'))

    def test_documented_residuals_and_legacy_credits(self):
        report = {r['scenario']: r for r in validate()}
        self.assertEqual(report['transition_2040']['electricity_rounding_difference_pj'], 2)
        self.assertEqual(report['wam_2025']['electricity_balance_residual_pj'], 2)

    def test_unset_parameters_do_not_become_zero_or_new_credit(self):
        payload = build_structure(self.parameters)
        for sid, scenario in payload['scenarios'].items():
            self.assertFalse(scenario['normative_allocation_complete'])
            for link in scenario['links']:
                if link['flow_kind'] == 'normative_allocation':
                    self.assertIsNone(link['value_pj'])
                if link['flow_kind'] == 'virtual_credit' and sid != 'legacy_streicher':
                    self.assertIsNone(link['value_pj'])
            physical = [l for l in scenario['links'] if l['flow_kind'] == 'physical']
            self.assertTrue(all(l['energy_basis'] == 'electricity' and l['value_pj'] >= 0 for l in physical))
        self.assertFalse(payload['scenarios']['legacy_streicher']['physical_data_complete'])

    def test_export_direction_and_pv_parameter_do_not_change_physical_flows(self):
        original = build_structure(self.parameters)['scenarios']['transition_2040']
        p = copy.deepcopy(self.parameters)
        p['transition_2040']['central_generation_share']['pv'] = 0
        p['transition_2040']['parameter_source'] = 'TEST ONLY: 100 percent decentral PV; not an approved default'
        modified = build_structure(p)['scenarios']['transition_2040']
        self.assertEqual(original['plotly_physical'], modified['plotly_physical'])
        pv = next(l for l in modified['links'] if l['source'] == 'pv' and l['target'] == 'decentral_pool')
        self.assertEqual(pv['value_pj'], 149)
        export = next(l for l in modified['links'] if l['target'] == 'exports')
        self.assertEqual(export['value_pj'], 7)
        self.assertFalse(modified['normative_allocation_complete'])

    def test_reject_unreferenced_or_invalid_normative_parameters(self):
        for value in [-.1, 1.1, float('nan'), True]:
            p = copy.deepcopy(self.parameters)
            p['transition_2040']['central_generation_share']['pv'] = value
            with self.assertRaises(ValueError):
                check_parameters(p)
        p = copy.deepcopy(self.parameters)
        p['transition_2040']['central_generation_share']['pv'] = 0
        with self.assertRaises(ValueError):
            check_parameters(p)


if __name__ == '__main__':
    unittest.main()
