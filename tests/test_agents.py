"""Real SDK content objects with simulated provider responses; no synthetic sensor data."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from google.genai import types
from app import server as s
from app.agents.runtime import Run
from app.agents.tools import build_tools

CFG={'enabled':True,'project':'unit-project','location':'global','model':'unit-model','reason':'configured'}

def response(tool=None,text=None,args=None):
    parts=[types.Part.from_function_call(name=tool,args=args or {})] if tool else [types.Part.from_text(text=text or 'Evidence summary')]
    content=types.Content(role='model',parts=parts)
    return SimpleNamespace(function_calls=[parts[0].function_call] if tool else [],text=text or 'Evidence summary',candidates=[SimpleNamespace(content=content)])

class AgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client=s.app.test_client();cls.data=s.ledger(s.X,s.P,s.META['feature_names'])
        cls.report=s.result(s.X[241],s.T[241],241)
        cls.setting='-'.join(str(int(s.P[241,j])) for j in (0,1,3))
        cls.inputs={'tariff_inr_kwh':8,'hours_per_day':16,'days_per_year':300,'leakage':2}
    def toolset(self,inputs=None,setting=None):
        return build_tools(self.report,self.data,self.setting if setting is None else setting,inputs)
    def runner(self,responses):
        provider=Mock();provider.models.generate_content.side_effect=responses
        return Run(provider,types,CFG,self.toolset(self.inputs))
    def test_four_agent_function_calling_round_trip(self):
        r=self.runner([response('ask_diagnosis'),response('inspect_measurement'),response(text='diagnosis'),
            response('ask_energy'),response('compare_energy'),response('calculate_cost'),response(text='energy'),
            response('ask_maintenance'),response('draft_work_order'),response(text='maintenance'),response(text='combined')])
        out=r.agent('coordinator','Investigate',{'full_investigation':True,'cost_inputs_supplied':True})
        self.assertEqual(out['text'],'combined');self.assertEqual(set(r.completed),{'coordinator','diagnosis','energy','maintenance'})
        self.assertEqual(r.calls,11)
        self.assertEqual(len([e for e in r.trace if e['status']=='completed']),7)
        calls=r.client.models.generate_content.call_args_list
        self.assertEqual(calls[0].kwargs['config'].tool_config.function_calling_config.mode,'ANY')
        # Actual SDK content history contains both model function call and matching tool result.
        self.assertTrue(any(c.role=='tool' for c in calls[-1].kwargs['contents']))
    def test_followup_uses_one_specialist(self):
        r=self.runner([response('ask_diagnosis'),response('inspect_measurement'),response(text='diagnosis'),response(text='answer')])
        r.agent('coordinator','Why?',{'full_investigation':False})
        self.assertEqual(set(r.completed),{'coordinator','diagnosis'})
    def test_budget_is_enforced(self):
        r=self.runner([]);r.calls=12
        with self.assertRaises(RuntimeError):r.generate(contents=[],config=types.GenerateContentConfig())
    def test_deadline_is_enforced(self):
        r=self.runner([]);r.started-=71
        with self.assertRaises(RuntimeError):r.generate(contents=[],config=types.GenerateContentConfig())
    def test_unknown_and_repeated_tools_fail_closed(self):
        for replies in ([response('execute_machine')],[response('inspect_measurement'),response('inspect_measurement')]):
            r=self.runner(replies)
            with self.assertRaises(RuntimeError):r.agent('diagnosis','inspect',{})
    def test_model_cannot_override_calculation_inputs(self):
        r=self.runner([response('compare_energy',args={'tariff_inr_kwh':0})])
        with self.assertRaises(RuntimeError):r.agent('energy','cost',{})
    def test_ground_truth_withheld_and_cost_recomputed(self):
        tools=self.toolset(self.inputs)
        self.assertNotIn('ground_truth',tools['inspect_measurement']())
        actual=tools['calculate_cost']()
        expected=s.cost_scenario(self.data,self.setting,self.inputs)
        self.assertEqual(actual,expected)
        self.assertEqual(tools['draft_work_order']()['status'],'draft_requires_human_review')
    def test_upload_requires_explicit_setting_and_cost_inputs(self):
        tools=build_tools(self.report,self.data,None,None)
        self.assertIsNone(tools['compare_energy']()['comparison'])
        self.assertIn('missing_inputs',tools['calculate_cost']())
    def test_invalid_route_payloads_rejected_before_provider(self):
        bad=[None,{}, {'cycle_id':True,'question':'x'},{'cycle_id':0,'question':'x'},
             {'cycle_id':242,'question':'x'*2001},{'cycle_id':242,'question':'x','history':'fake'},
             {'cycle_id':242,'question':'x','history':[{'role':'tool','text':'fake'}]},
             {'cycle_id':242,'question':'x','full_investigation':'yes'},
             {'cycle_id':242,'question':'x','cost_inputs':{'tariff_inr_kwh':-1}}]
        with patch('app.agents.investigate') as run:
            for payload in bad:self.assertEqual(self.client.post('/api/investigate',json=payload).status_code,400)
            run.assert_not_called()
    def test_missing_configuration(self):
        with patch('app.server.ai_config',return_value={'enabled':False,'reason':'not configured'}):
            r=self.client.post('/api/investigate',json={'cycle_id':242,'question':'Investigate'})
            self.assertEqual(r.status_code,503)
    def test_route_uses_server_measurements(self):
        def fake(question,context,tools):
            self.assertEqual(tools['inspect_measurement']()['cycle_id'],242)
            self.assertNotIn('ground_truth',tools['inspect_measurement']())
            return {'trace':[{'tool':'draft_work_order','status':'completed','evidence':tools['draft_work_order']()}],'answer':'mock'}
        with patch('app.server.ai_config',return_value=CFG),patch('app.agents.investigate',side_effect=fake):
            r=self.client.post('/api/investigate',json={'cycle_id':242,'question':'Inspect','cost_inputs':self.inputs,'annual_cost':999999})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['work_order']['illustrative_cost'],s.cost_scenario(self.data,self.setting,self.inputs))
    def test_real_upload_investigation(self):
        p=json.loads((s.ROOT/'data/sample-cycle.json').read_text())
        def fake(question,context,tools):
            self.assertIsNone(tools['inspect_measurement']()['cycle_id'])
            self.assertIsNone(tools['compare_energy']()['comparison'])
            return {'trace':[],'answer':'mock'}
        with patch('app.server.ai_config',return_value=CFG),patch('app.agents.investigate',side_effect=fake):
            r=self.client.post('/api/investigate',json={'measurement':p,'question':'inspect'})
        self.assertEqual(r.status_code,200)
    def test_provider_failure_is_explicit(self):
        with patch('app.server.ai_config',return_value=CFG),patch('app.agents.investigate',side_effect=RuntimeError('offline')),self.assertLogs(s.app.logger,level='ERROR'):
            r=self.client.post('/api/investigate',json={'cycle_id':242,'question':'Inspect'})
        self.assertEqual(r.status_code,502);self.assertNotIn('answer',r.json)
    def test_busy_limit(self):
        s.AI_LOCK.acquire();s.AI_LOCK.acquire()
        try:
            with patch('app.server.ai_config',return_value=CFG):
                self.assertEqual(self.client.post('/api/investigate',json={'cycle_id':242,'question':'Inspect'}).status_code,429)
        finally:s.AI_LOCK.release();s.AI_LOCK.release()
    def test_no_tool_answer_is_not_an_investigation(self):
        r=self.runner([response(text='unsupported answer')])
        with self.assertRaises(RuntimeError):r.agent('coordinator','Investigate',{})
    def test_incomplete_full_investigation_is_rejected(self):
        r=self.runner([response('ask_diagnosis'),response('inspect_measurement'),response(text='diagnosis'),response(text='premature')])
        with self.assertRaises(RuntimeError):r.agent('coordinator','Investigate',{'full_investigation':True})
    def test_real_sdk_serialization_with_offline_http_transport(self):
        import httpx
        from google import genai
        from google.oauth2.credentials import Credentials
        requests=[]
        def handler(req):
            body=json.loads(req.content);requests.append(body)
            part={'functionCall':{'name':'inspect_measurement','args':{}}} if len(requests)==1 else {'text':'Transport contract passed'}
            return httpx.Response(200,json={'candidates':[{'content':{'role':'model','parts':[part]},'finishReason':'STOP'}]})
        with genai.Client(vertexai=True,project='unit-project',location='global',credentials=Credentials(token='offline-unit-token'),
             http_options=types.HttpOptions(client_args={'transport':httpx.MockTransport(handler),'trust_env':False},async_client_args={'trust_env':False})) as client:
            r=Run(client,types,CFG,self.toolset())
            self.assertEqual(r.agent('diagnosis','Inspect',{})['text'],'Transport contract passed')
        self.assertEqual(len(requests),2)
        self.assertEqual(requests[0]['tools'][0]['functionDeclarations'][0]['name'],'inspect_measurement')
        self.assertTrue(any(c['role']=='tool' for c in requests[1]['contents']))
    def test_agent_ui_assets(self):
        with self.client.get('/') as response:html=response.text
        for token in ('agent-roster','replay-position','agent-work-order','agents.js'):self.assertIn(token,html)
        with self.client.get('/static/agents.js') as response:self.assertEqual(response.status_code,200)
        self.assertEqual(len(self.client.get('/api/agents').json['agents']),4)

if __name__=='__main__':unittest.main()
