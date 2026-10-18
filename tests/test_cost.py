import os,unittest
from unittest.mock import patch
import numpy as np
from app.cost import cost_scenario
from app.server import app

class CostTests(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client();self.data=self.client.get('/api/energy').json
        self.setting=self.data['rows'][0]['id'];self.inputs={'leakage':2,'tariff_inr_kwh':8,'hours_per_day':16,'days_per_year':300}
    def test_units_against_known_calculation(self):
        fixture={'rows':[{'id':'math-check','states':[{'leakage':1,'extra_power_w':50},{'leakage':2,'extra_power_w':100}]}]}
        r=cost_scenario(fixture,'math-check',self.inputs)
        self.assertEqual(r['annual_operating_hours'],4800)
        self.assertEqual(r['annual_extra_energy_kwh'],480)
        self.assertEqual(r['annual_extra_cost_inr'],3840)
        self.assertEqual(r['average_monthly_extra_cost_inr'],320)
    def test_real_setting_and_sensitivity(self):
        for leakage in [1,2]:
            inputs={**self.inputs,'leakage':leakage}
            response=self.client.post('/api/energy/cost/'+self.setting,json=inputs)
            self.assertEqual(response.status_code,200);r=response.json
            state=next(s for s in self.data['rows'][0]['states'] if s['leakage']==leakage)
            self.assertAlmostEqual(r['annual_extra_cost_inr'],state['extra_power_w']/1000*4800*8)
            watts=[next(s['extra_power_w'] for s in row['states'] if s['leakage']==leakage) for row in self.data['rows']]
            q=np.percentile(watts,[10,90])
            self.assertAlmostEqual(r['sensitivity']['annual_cost_p10_inr'],q[0]/1000*4800*8)
            self.assertAlmostEqual(r['sensitivity']['annual_cost_p90_inr'],q[1]/1000*4800*8)
    def test_zero_schedule_and_free_electricity(self):
        for key in ['hours_per_day','days_per_year','tariff_inr_kwh']:
            r=cost_scenario(self.data,self.setting,{**self.inputs,key:0})
            self.assertEqual(r['annual_extra_cost_inr'],0)
            self.assertEqual(r['sensitivity']['annual_cost_p90_inr'],0)
        r=cost_scenario(self.data,self.setting,{**self.inputs,'tariff_inr_kwh':0})
        self.assertGreater(r['annual_extra_energy_kwh'],0)
    def test_invalid_inputs(self):
        bad=[None,[],{},dict(self.inputs,hours_per_day=25),dict(self.inputs,hours_per_day=-1),dict(self.inputs,days_per_year=300.5),dict(self.inputs,days_per_year=367),dict(self.inputs,tariff_inr_kwh=float('nan')),dict(self.inputs,tariff_inr_kwh=float('inf')),dict(self.inputs,leakage=True),dict(self.inputs,leakage=0),dict(self.inputs,leakage=1.5),dict(self.inputs,tariff_inr_kwh='8')]
        for inputs in bad:
            with self.subTest(inputs=inputs):self.assertEqual(self.client.post('/api/energy/cost/'+self.setting,json=inputs).status_code,400)
        self.assertEqual(self.client.post('/api/energy/cost/not-found',json=self.inputs).status_code,404)
    def test_fractional_hours_and_leap_year(self):
        r=cost_scenario(self.data,self.setting,{**self.inputs,'hours_per_day':7.5,'days_per_year':366,'tariff_inr_kwh':8.25})
        self.assertEqual(r['annual_operating_hours'],2745)
        self.assertAlmostEqual(r['annual_extra_cost_inr'],r['measured_extra_power_w']/1000*2745*8.25)
    def test_gemini_uses_recomputed_cost_not_client_claim(self):
        with patch.dict(os.environ,{'GOOGLE_CLOUD_PROJECT':'test-project','GEMINI_MODEL':'test-model','GOOGLE_APPLICATION_CREDENTIALS':''}):
            with patch('app.server.generate_brief',return_value={'text':'mock'}) as mock:
                payload={**self.inputs,'annual_extra_cost_inr':99999999}
                response=self.client.post('/api/energy/brief/'+self.setting,json=payload)
                self.assertEqual(response.status_code,200)
                sent=mock.call_args.args[0]['cost_scenario']
                self.assertEqual(sent,cost_scenario(self.data,self.setting,self.inputs))
                self.assertNotEqual(sent['annual_extra_cost_inr'],99999999)
    def test_invalid_cost_never_calls_provider(self):
        with patch('app.server.generate_brief') as mock:
            response=self.client.post('/api/energy/brief/'+self.setting,json={'hours_per_day':40})
            self.assertEqual(response.status_code,400);mock.assert_not_called()
if __name__=='__main__':unittest.main()
