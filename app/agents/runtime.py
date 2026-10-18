"""Manual Gemini function calling. No canned agent answers or hidden offline fallback."""
import json
import time
import uuid
from app.config import ai_config
from app.agents.prompts import PROMPTS

AGENTS = ('coordinator', 'diagnosis', 'energy', 'maintenance')
MAX_CALLS = 12
MAX_SECONDS = 70


def declaration(types, name, description, fields=None):
    return types.FunctionDeclaration(name=name, description=description,
        parameters_json_schema={'type':'object','properties':fields or {},'additionalProperties':False})


class Run:
    def __init__(self, client, types, cfg, tools):
        self.client,self.types,self.cfg,self.tools=client,types,cfg,tools
        self.trace=[];self.calls=0;self.started=time.monotonic();self.completed={}

    def event(self, agent, tool, status, **extra):
        self.trace.append({'agent':agent,'tool':tool,'status':status,
                           'elapsed_ms':round((time.monotonic()-self.started)*1000),**extra})

    def generate(self, **kw):
        remaining=MAX_SECONDS-(time.monotonic()-self.started)
        if self.calls>=MAX_CALLS or remaining<1:
            raise RuntimeError('Investigation budget exhausted. Ask a narrower question.')
        self.calls+=1
        # No request retry: each call is bounded by the remaining investigation deadline.
        kw['config'].http_options=self.types.HttpOptions(timeout=min(20000,int(remaining*1000)),
            retry_options=self.types.HttpRetryOptions(attempts=1))
        return self.client.models.generate_content(model=self.cfg['model'],**kw)

    def agent(self, name, question, context):
        t=self.types
        if name=='coordinator':
            declarations=[declaration(t,'ask_'+a,'Delegate to the '+a+' specialist.',
                {'question':{'type':'string','description':'Focused task with relevant prior findings.'}}) for a in AGENTS[1:]]
        else:
            specs={
                'diagnosis':[('inspect_measurement','Get model screening, sensor evidence and similar training cycles.')],
                'energy':[('compare_energy','Get retrospective power comparison for a recorded matched setting.'),
                          ('calculate_cost','Calculate illustrative INR cost using explicit scenario inputs.')],
                'maintenance':[('draft_work_order','Create a grounded inspection work-order draft for human review.')]
            }
            declarations=[declaration(t,n,d) for n,d in specs[name]]
        history=[t.Content(role='user',parts=[t.Part.from_text(text=json.dumps({'question':question,'context':context}))])]
        used=set(); final=''
        for turn in range(5 if name=='coordinator' else 3):
            available=[d for d in declarations if d.name not in used]
            if name=='energy' and turn==0:available=[d for d in available if d.name=='compare_energy']
            config=t.GenerateContentConfig(system_instruction=PROMPTS[name],temperature=0.1,
                max_output_tokens=1800,automatic_function_calling=t.AutomaticFunctionCallingConfig(disable=True))
            if available:
                config.tools=[t.Tool(function_declarations=available)]
                config.tool_config=t.ToolConfig(function_calling_config=t.FunctionCallingConfig(mode='ANY' if turn==0 or (name=='coordinator' and context.get('full_investigation') and available) or (name=='energy' and context.get('cost_inputs_supplied') and available) else 'AUTO'))
            else:
                config.tool_config=t.ToolConfig(function_calling_config=t.FunctionCallingConfig(mode='NONE'))
            response=self.generate(contents=history,config=config)
            calls=response.function_calls or []
            if not calls:
                if not used or (name=='coordinator' and context.get('full_investigation') and available):
                    raise RuntimeError('Gemini did not complete the required tool delegation.')
                if name=='energy' and context.get('cost_inputs_supplied') and 'calculate_cost' not in used:
                    raise RuntimeError('Energy agent did not calculate the supplied cost scenario.')
                final=response.text or ''
                if not final.strip():raise RuntimeError('Gemini returned an empty specialist response.')
                self.completed[name]={'text':final,'tools_used':sorted(used)}
                return self.completed[name]
            if not response.candidates:raise RuntimeError('Gemini returned no function-call content.')
            history.append(response.candidates[0].content)
            parts=[]
            for call in calls:
                if call.name not in [d.name for d in available] or call.name in used:
                    raise RuntimeError('Gemini requested an unavailable or repeated tool.')
                args=dict(call.args or {})
                self.event(name,call.name,'started')
                if name=='coordinator':
                    if set(args)-{'question'} or not isinstance(args.get('question',question),str):
                        raise RuntimeError('Invalid specialist arguments.')
                    child=call.name.removeprefix('ask_')
                    value=self.agent(child,args.get('question',question)[:4000],context)
                else:
                    if args:raise RuntimeError('Evidence tools do not accept model-supplied values.')
                    value=self.tools[call.name]()
                used.add(call.name)
                self.event(name,call.name,'completed',evidence=value)
                parts.append(t.Part.from_function_response(name=call.name,response={'result':value}))
            history.append(t.Content(role='tool',parts=parts))
        raise RuntimeError('Agent turn limit reached. Ask a narrower question.')


def investigate(question, context, tools):
    from google import genai
    from google.genai import types
    cfg=ai_config()
    if not cfg['enabled']:raise ValueError(cfg['reason'])
    with genai.Client(vertexai=True,project=cfg['project'],location=cfg['location'],
        http_options=types.HttpOptions(timeout=20000,retry_options=types.HttpRetryOptions(attempts=1))) as client:
        run=Run(client,types,cfg,tools)
        answer=run.agent('coordinator',question,context)
        return {'run_id':str(uuid.uuid4()),'answer':answer['text'],'agents':run.completed,
                'trace':run.trace,'model':cfg['model'],'provider':'Gemini on Vertex AI',
                'model_calls':run.calls,'elapsed_ms':round((time.monotonic()-run.started)*1000),
                'agent_roster':list(AGENTS),'source':'Recorded UCI hydraulic test-rig data',
                'limits':{'max_model_calls':MAX_CALLS,'deadline_seconds':MAX_SECONDS}}
