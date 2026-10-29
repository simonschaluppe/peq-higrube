"""Regression checks for the 2026-10-29 allocation, including browser parity."""
import ast
import csv
import json
from pathlib import Path
import shutil
import subprocess
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[2]

def function_from_notebook(path, name, scope):
    notebook = json.loads(path.read_text(encoding='utf-8'))
    for cell in notebook['cells']:
        if cell['cell_type'] != 'code':
            continue
        for node in ast.parse(''.join(cell['source'])).body:
            if isinstance(node, ast.FunctionDef) and node.name == name:
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), scope)
                return scope[name]
    raise AssertionError(name)

class AllocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def table(name):
            with (ROOT/'Daten/sektorenmodell'/name).open(encoding='utf-8-sig') as f:
                return {r['metric']:float(r['value_pj']) for r in csv.DictReader(f) if r['scenario']=='transition_2040'}
        cls.g=table('stromerzeugung_2040.csv'); cls.d=table('strombedarf_2040.csv')
        keys=['hydro','wind','biomass','geothermal','hydrogen_electricity','pv','fossil']
        scope=dict(np=np,g=cls.g,d=cls.d,generation_keys=keys,source_residual=-2,model_residual=0,
                   assumptions={'model_net_exports_pj':5})
        cls.allocate=staticmethod(function_from_notebook(ROOT/'Berechnungen/sektorenmodell/allokation.ipynb','allocate',scope))

    def test_reference_and_invariance(self):
        for f in [0,.2,1]:
            for m in [0,.4,.6,.8,1]:
                r=self.allocate(dict(other_pv_share=f,miv_share=m,public_transport_share=1-m,other_transport_share=0))
                self.assertAlmostEqual(r['central_credit_pj'],90*m-41+149*f)
                self.assertAlmostEqual(r['building_target_pj'],0)
                self.assertAlmostEqual(r['building_pv_pj']+r['other_pv_pj'],149)
                self.assertAlmostEqual(r['building_pv_pj']+r['available_credit_pj'],108+90*m+r['central_shortfall_pj'])

    def test_non_miv_split_and_invalid_parameters(self):
        r=self.allocate(dict(other_pv_share=.2,miv_share=.6,public_transport_share=.1,other_transport_share=.3))
        self.assertAlmostEqual(r['central_credit_pj'],42.8)
        for changes in [dict(miv_share=1.1),dict(other_pv_share=-.1),dict(other_transport_share=.5),dict(eligible_nonpv_share={})]:
            with self.assertRaises(AssertionError):
                self.allocate(dict(dict(other_pv_share=0,miv_share=.8,public_transport_share=.2,other_transport_share=0),**changes))

    def test_browser_parity(self):
        import pandas as pd
        scope=dict(np=np,g=self.g,d=self.d,generation_keys=['hydro','wind','biomass','geothermal','hydrogen_electricity','pv','fossil'],
                   model_net_imports=-5,model_residual=0,geometry=pd.DataFrame([{'D':170.,'P':100.}]))
        calc=function_from_notebook(ROOT/'Berechnungen/gebaeudesektormodell/Internes_Kalibrierungsdashboard.ipynb','calculate',scope)
        p=dict(miv=.8,other_transport=0,free_pv=0,saving=0,pv_scale=1,ngf_bgf=.8,
               density_f_res=30.4,density_f_ed=26.4,density_dx=.15,density_cutoff=62)
        cases=[dict(p,miv=m,free_pv=f) for f in [0,.2,1] for m in [0,.4,.8,1]]
        html=(ROOT/'Berechnungen/gebaeudesektormodell/dashboard_template.html').read_text(encoding='utf-8')
        fn=html.split('function calculate(p){',1)[1].split('// Die Browserrechnung',1)[0]
        payload=dict(g=self.g,d=self.d,model_net_imports=-5,geometry=[{'D':170.,'P':100.}])
        script='const S='+json.dumps(payload)+';function calculate(p){'+fn+'\nconsole.log(JSON.stringify('+json.dumps(cases)+'.map(calculate)));'
        result=subprocess.run([shutil.which('node'),'-e',script],capture_output=True,text=True,check=True)
        for p,js in zip(cases,json.loads(result.stdout)):
            py=calc(p)
            for key,value in py.items(): self.assertAlmostEqual(value,js[key],places=7,msg=key)
            self.assertAlmostEqual(py['target_extended'],0)

if __name__=='__main__': unittest.main()
