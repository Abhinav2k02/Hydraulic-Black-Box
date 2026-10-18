import os,json,unittest
from unittest.mock import patch,MagicMock
import numpy as np
from app.config import ai_config
from app.server import app,X,P,META
from app.energy import ledger
from app.vertex import generate_brief

class CloudAndEnergyTests(unittest.TestCase):
    def setUp(self):self.client=app.test_client()
    def test_placeholders_disable_ai(self):
        with patch.dict(os.environ,{'GOOGLE_CLOUD_PROJECT':'YOUR_GCP_PROJECT_ID','GEMINI_MODEL':'YOUR_AVAILABLE_GEMINI_MODEL_ID','GOOGLE_APPLICATION_CREDENTIALS':''}):
            self.assertFalse(ai_config()['enabled'])
            self.assertEqual(self.client.post('/api/brief/242').status_code,503)
    def test_energy_matches_independent_raw_feature_calculation(self):
        d=self.client.get('/api/energy').json
        self.assertEqual(d['matched_settings'],48)
        for row in d['rows']:
            baseline=None
            for state in row['states']:
                ix=np.where((P[:,0]==row['cooler'])&(P[:,1]==row['valve'])&(P[:,3]==row['accumulator'])&(P[:,2]==state['leakage'])&(P[:,4]==0))[0]
                power=float(X[ix,META['feature_names'].index('EPS1_mean')].mean())
                if baseline is None:baseline=power
                self.assertAlmostEqual(state['mean_power_w'],power)
                self.assertAlmostEqual(state['extra_energy_wh'],(power-baseline)/60)
                self.assertEqual(state['cycle_ids'],(ix+1).tolist())
    def test_real_vertex_sdk_contract_with_mock_transport(self):
        with patch.dict(os.environ,{'GOOGLE_CLOUD_PROJECT':'test-project','GEMINI_MODEL':'test-model','GOOGLE_APPLICATION_CREDENTIALS':''}):
            with patch('google.genai.Client') as factory:
                model=factory.return_value.__enter__.return_value.models
                model.generate_content.return_value.text='Measured evidence only.'
                out=generate_brief({'sensor':'EPS1','mean_power_w':2500},'Explain the measurement.')
                self.assertEqual(out['text'],'Measured evidence only.')
                self.assertTrue(factory.call_args.kwargs['vertexai'])
                call=model.generate_content.call_args.kwargs
                self.assertEqual(call['model'],'test-model')
                self.assertIn('2500',call['contents'])
    def test_brief_routes_send_correct_evidence(self):
        with patch.dict(os.environ,{'GOOGLE_CLOUD_PROJECT':'test-project','GEMINI_MODEL':'test-model','GOOGLE_APPLICATION_CREDENTIALS':''}):
            with patch('app.server.generate_brief',return_value={'text':'Test response','provider':'Mock'}) as call:
                r=self.client.post('/api/brief/242');self.assertEqual(r.status_code,200)
                facts=call.call_args.args[0];self.assertNotIn('ground_truth',facts)
                key=self.client.get('/api/energy').json['rows'][0]['id']
                r=self.client.post('/api/energy/brief/'+key);self.assertEqual(r.status_code,200)
                self.assertIn('comparison',call.call_args.args[0])
    def test_provider_failure_is_not_fabricated_success(self):
        with patch.dict(os.environ,{'GOOGLE_CLOUD_PROJECT':'test-project','GEMINI_MODEL':'test-model','GOOGLE_APPLICATION_CREDENTIALS':''}):
            with patch('app.server.generate_brief',side_effect=RuntimeError('test provider failure')):
                with self.assertLogs(app.logger,level='ERROR'):
                    self.assertEqual(self.client.post('/api/brief/242').status_code,502)
    def test_unknown_energy_setting(self):
        self.assertEqual(self.client.post('/api/energy/brief/invalid').status_code,404)
if __name__=='__main__':unittest.main()
