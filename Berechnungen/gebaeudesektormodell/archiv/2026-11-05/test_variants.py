import unittest
import pandas as pd
from variants import allocate, collapse


class AllocationTests(unittest.TestCase):
    def setUp(self):
        self.bases = pd.DataFrame({'Basisarchetyp':['a','b'], 'area':[60.,40.],
            'Bestand':[1.,1.], 'Neubau':[0.,0.], 'Sanierung':[0.,0.]})
        self.frame = pd.DataFrame([dict(Basisarchetyp=b,PV_Klasse=pv,Flexibilitaet=f,
            Wetter='W',Masse='M',Archetype=b+pv) for b in ['a','b']
            for pv,f in [('PV0','noFlex'),('PV70','Flex')]])
        self.rules={s:{('PV0','noFlex'):1.} for s in ['Bestand','Neubau','Sanierung']}

    def run_case(self, frame=None, target=.2):
        return allocate(self.frame if frame is None else frame,self.bases,'area',self.rules,
            {'W':1.},{'M':1.},pd.Series([True,False]),target)

    def test_area_and_target(self):
        result=self.run_case()
        self.assertAlmostEqual(result.BGF.sum(),100)
        self.assertAlmostEqual(result.loc[result.PEQ,'BGF'].sum(),20)
        self.assertAlmostEqual(collapse(result).BGF.sum(),100)

    def test_new_unweighted_variant_does_not_change_area(self):
        extra=self.frame.iloc[[0]].assign(PV_Klasse='PV90',Archetype='extra')
        pd.testing.assert_frame_equal(self.run_case(),self.run_case(pd.concat([self.frame,extra])))

    def test_missing_weighted_variant(self):
        with self.assertRaisesRegex(ValueError,'Varianten fehlen'):
            self.run_case(self.frame.iloc[1:])

    def test_unreachable_target(self):
        with self.assertRaisesRegex(ValueError,'überschreitet'):
            self.run_case(target=.8)

    def test_parameter_changes_and_reset(self):
        self.assertAlmostEqual(self.run_case(target=.4).query('PEQ').BGF.sum(),40)
        self.assertAlmostEqual(self.run_case().query('PEQ').BGF.sum(),20)

    def test_invalid_weights(self):
        self.rules['Bestand']={('PV0','noFlex'):.8}
        with self.assertRaisesRegex(ValueError,'eins'):
            self.run_case()


if __name__ == '__main__':
    unittest.main()
