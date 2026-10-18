import unittest,json,io,csv
import numpy as np
from app.server import app,ROOT,X,P,TRAIN,TEST,E,MODEL,parse_input
class ProductTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.client=app.test_client()
 def test_health_and_views(self):
  for url in ['/', '/static/style.css','/static/app.js','/health','/api/meta']:
   with self.client.get(url) as response: self.assertEqual(response.status_code,200,url)
 def test_held_out_groups_and_metrics(self):
  test=np.array(sorted(TEST));self.assertFalse(set(E['groups'][TRAIN])&set(E['groups'][test]))
  self.assertEqual(len(set(TRAIN)|TEST),2205)
  pred=MODEL.predict(X[test]);m=json.loads((ROOT/'models/metrics.json').read_text())
  self.assertAlmostEqual(float(np.mean(pred==P[test,2])),m['accuracy'])
  self.assertEqual(int(sum(map(sum,m['confusion_matrix']))),len(TEST))
 def test_source_sample_matches_feature_pipeline(self):
  sample=json.loads((ROOT/'data/sample-cycle.json').read_text());x,_=parse_input(sample)
  np.testing.assert_allclose(x,X[sample['cycle_id']-1],rtol=1e-10,atol=1e-10)
  a=self.client.post('/api/analyze',json=sample);self.assertEqual(a.status_code,200)
  b=self.client.get('/api/cycles/'+str(sample['cycle_id'])).json
  self.assertEqual(a.json['prediction'],b['prediction'])
  np.testing.assert_allclose(a.json['vote_shares'],b['vote_shares'],rtol=1e-14,atol=1e-14)
  self.assertIsNone(a.json['ground_truth'])
 def test_labels_do_not_change_upload_prediction(self):
  p=json.loads((ROOT/'data/sample-cycle.json').read_text());a=self.client.post('/api/analyze',json=p).json
  p['profile']=[100,100,0,130,0];p['label']='No leakage'
  b=self.client.post('/api/analyze',json=p).json;np.testing.assert_allclose(a['vote_shares'],b['vote_shares'],rtol=1e-14,atol=1e-14)
 def test_error_filter_contains_actual_held_out_errors(self):
  d=self.client.get('/api/cycles?split=test&errors=1').json
  self.assertGreater(d['total'],0)
  for c in d['items']:self.assertEqual(c['split'],'test');self.assertNotEqual(c['label'],c['prediction'])
 def test_bad_measurements_rejected(self):
  for p in [None,[],{}, {'sensors':{}}]:self.assertEqual(self.client.post('/api/analyze',json=p).status_code,400)
  p=json.loads((ROOT/'data/sample-cycle.json').read_text());p['sensors']['PS1'][0]=float('nan')
  self.assertEqual(self.client.post('/api/analyze',json=p).status_code,400)
 def test_not_found_and_csv(self):
  self.assertEqual(self.client.get('/api/cycles/9999').status_code,404)
  data=self.client.get('/api/cycles/1/csv');self.assertEqual(data.status_code,200)
  rows=list(csv.reader(io.StringIO(data.text)));self.assertEqual(len(rows),61);self.assertEqual(len(rows[0]),15)
 def test_ai_missing_configuration_is_explicit(self):
  import os
  from unittest.mock import patch
  with patch.dict(os.environ,{'GOOGLE_CLOUD_PROJECT':'','GEMINI_MODEL':''}):
   self.assertFalse(self.client.get('/api/meta').json['ai_enabled'])
   self.assertEqual(self.client.post('/api/brief/1').status_code,503)
if __name__=='__main__':unittest.main()
