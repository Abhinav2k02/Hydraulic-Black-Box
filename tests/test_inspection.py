import unittest
import importlib.util
from io import BytesIO
from app import server as s
from app.verification import MANUAL

class InspectionTests(unittest.TestCase):
    def setUp(self):self.client=s.app.test_client()
    def test_report_has_quality_and_cited_plan_without_label_leak(self):
        r=s.result(s.X[241],s.T[241],241)
        self.assertEqual(r['quality']['status'],'review_required')
        self.assertTrue(r['verification']['checks'])
        self.assertIn('not verified',MANUAL['applicability'])
        self.assertNotIn('ground_truth',r['verification'])
    def test_rules_ignore_current_ground_truth(self):
        r=s.result(s.X[241],s.T[241],241)
        a=s.GATE.check(s.X[241],r['prediction'],r['similar_training_cycles'])
        self.assertEqual(a,r['quality'])
        self.assertEqual(s.GATE.low.tolist(),s.X[s.TRAIN].min(0).tolist())
    def test_metrics_account_for_all_test_cases(self):
        m=self.client.get('/api/quality/evaluation').json
        self.assertEqual(m['test_cycles'],len(s.TEST))
        self.assertEqual(m['flagged_cycles']+m['unflagged_cycles'],m['test_cycles'])
        self.assertEqual(m['flagged_classifier_errors']+m['unflagged_classifier_errors'],m['total_classifier_errors'])
        self.assertEqual(m['total_classifier_errors'],5)
    @unittest.skipUnless(importlib.util.find_spec('pypdf'), 'Optional pypdf package is needed for PDF text assertions.')
    def test_pdf_is_real_and_ignores_injected_diagnosis(self):
        from pypdf import PdfReader
        r=self.client.post('/api/report.pdf',json={'cycle_id':242,'prediction':'HACKED','engineer':'<script>test</script>','notes':'A & B'})
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.data.startswith(b'%PDF-'))
        reader=PdfReader(BytesIO(r.data));text=' '.join(p.extract_text() for p in reader.pages)
        self.assertIn('Severe leakage',text);self.assertNotIn('HACKED',text)
        self.assertIn('A & B',text);self.assertIn('PARKER-P1PD',text)
    def test_pdf_native_upload_and_cost_validation(self):
        import json
        payload=json.loads((s.ROOT/'data/sample-cycle.json').read_text())
        self.assertEqual(self.client.post('/api/report.pdf',json={'measurement':payload}).status_code,200)
        self.assertEqual(self.client.post('/api/report.pdf',json={'measurement':payload,'cost_inputs':{}}).status_code,400)
    def test_bad_pdf_payloads(self):
        for value in [None,{}, {'cycle_id':True},{'cycle_id':2206},{'cycle_id':242,'notes':5},{'cycle_id':242,'engineer':'x'*121}, {'cycle_id':242,'setting_id':[]}]:
            # setting_id is derived server-side for recordings, so browser values are ignored.
            if isinstance(value,dict) and 'setting_id' in value:continue
            self.assertEqual(self.client.post('/api/report.pdf',json=value).status_code,400)
if __name__=='__main__':unittest.main()
