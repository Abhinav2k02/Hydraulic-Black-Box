from pathlib import Path
import csv, io, json, os, threading
import numpy as np
import joblib
from app.config import ai_config
from app.vertex import generate_brief
from app.energy import ledger
from app.cost import cost_scenario
from app.verification import ReviewGate, verification_plan
from flask import Flask, jsonify, request, send_from_directory, Response

ROOT=Path(__file__).resolve().parents[1]
app=Flask(__name__,static_folder='static'); app.config['MAX_CONTENT_LENGTH']=2*1024*1024
D=np.load(ROOT/'data/measurements.npz'); X=D['features']; T=D['traces']; P=D['profile']
META=json.loads((ROOT/'data/metadata.json').read_text()); METRICS=json.loads((ROOT/'models/metrics.json').read_text())
E=np.load(ROOT/'models/evaluation.npz'); TRAIN=E['train']; TEST=set(E['test'].tolist()); PRED=E['predictions']; PROBS=E['probabilities']
MODEL=joblib.load(ROOT/'models/pump_model.joblib')
SENSORS=list(META['sensors']); LABELS=['No leakage','Weak leakage','Severe leakage']
BASE=X[TRAIN[P[TRAIN,2]==0]]; CENTER=BASE.mean(0); SCALE=np.maximum(BASE.std(0),1e-6)
REF_SCALE=np.maximum(X[TRAIN].std(0),1e-6)
AI_LOCK=threading.BoundedSemaphore(2)
GATE=ReviewGate(X,TRAIN,P[:,2],META['feature_names'])

def summary(i):
 return {'id':i+1,'label':int(P[i,2]),'prediction':int(PRED[i]),'vote_share':round(float(PROBS[i].max()),4),'split':'test' if i in TEST else 'train','stable':bool(P[i,4]==0),'cooler':int(P[i,0]),'valve':int(P[i,1]),'accumulator':int(P[i,3])}
def evidence(x, pred):
 # Observed deviations against training no-leakage reference; not causal attributions.
 out=[]
 for si,s in enumerate(SENSORS):
  j=si*6; z=float((x[j]-CENTER[j])/SCALE[j])
  out.append({'sensor':s,'quantity':META['sensors'][s][0],'unit':META['sensors'][s][1],'mean':round(float(x[j]),4),'baseline':round(float(CENTER[j]),4),'deviation_sd':round(z,2)})
 return sorted(out,key=lambda r:abs(r['deviation_sd']),reverse=True)
def result(x,traces,cycle=None):
 proba=MODEL.predict_proba(x.reshape(1,-1))[0]; pred=int(MODEL.classes_[np.argmax(proba)])
 dist=np.mean(((X[TRAIN]-x)/REF_SCALE)**2,axis=1)
 # Exclude self when inspecting a training recording.
 if cycle is not None: dist[TRAIN==cycle]=np.inf
 near=TRAIN[np.argsort(dist)[:3]]
 report={'cycle_id':None if cycle is None else cycle+1,'prediction':pred,'label_name':LABELS[pred],'vote_shares':proba.tolist(),'evidence':evidence(x,pred),'similar_training_cycles':[{'id':int(i+1),'label':int(P[i,2]),'distance':round(float(np.sqrt(dist[np.where(TRAIN==i)[0][0]])),3)} for i in near], 'traces':{s:traces[j].tolist() for j,s in enumerate(SENSORS)},'ground_truth':None if cycle is None else summary(cycle),'scope':'Pump internal leakage screening on a hydraulic test rig. Factory use is a proposed application.','uncertainty':'Tree vote shares are uncalibrated. Correlated faults can influence signals; this is not a confirmed root-cause diagnosis.'}
 report['next_checks']=['Compare flow, pressure and power at the same load and fluid temperature.','Have a qualified maintenance engineer confirm suspected internal leakage using the pump maker’s test procedure.','Review cooler, valve and accumulator condition before attributing changes to the pump.'] if pred else ['Continue trending at comparable load and fluid temperature.','A no-leakage prediction does not certify the rest of the hydraulic system as healthy.']
 report['quality']=GATE.check(x,pred,report['similar_training_cycles'])
 report['verification']=verification_plan(report)
 return report
@app.get('/')
def home():return send_from_directory(app.static_folder,'index.html')
@app.get('/health')
def health():return jsonify(status='ok',model='ExtraTrees',cycles=len(P))
@app.get('/api/meta')
def meta():
 return jsonify(metadata=META,metrics=METRICS,labels=LABELS,ai_enabled=ai_config()['enabled'],ai_status=ai_config()['reason'],default_cycle=next(i+1 for i in sorted(TEST) if P[i,2]==2),class_counts=np.bincount(P[:,2]).tolist())
@app.get('/api/cycles')
def cycles():
 try: page=max(1,int(request.args.get('page',1))); cls=int(request.args.get('class',-1))
 except ValueError:return jsonify(error='Invalid page or class'),400
 split=request.args.get('split','all'); q=request.args.get('q','').strip(); errors=request.args.get('errors')=='1'
 ids=[i for i in range(len(P)) if (cls==-1 or P[i,2]==cls) and (split=='all' or (i in TEST)==(split=='test')) and (not q or q in str(i+1)) and (not errors or PRED[i]!=P[i,2])]
 return jsonify(total=len(ids),page=page,items=[summary(i) for i in ids[(page-1)*15:page*15]])
@app.get('/api/cycles/<int:cid>')
def cycle(cid):
 if not 1<=cid<=len(P):return jsonify(error='Cycle not found'),404
 return jsonify(result(X[cid-1],T[cid-1],cid-1))
@app.get('/api/cycles/<int:cid>/csv')
def export(cid):
 if not 1<=cid<=len(P):return jsonify(error='Cycle not found'),404
 f=io.StringIO();w=csv.writer(f);w.writerow(['second']+SENSORS)
 for t in range(60):w.writerow([t]+[float(T[cid-1,j,t]) for j in range(len(SENSORS))])
 return Response(f.getvalue(),mimetype='text/csv',headers={'Content-Disposition':f'attachment; filename=cycle-{cid}-original-samples-1hz.csv'})
@app.get('/api/sample')
def sample():return send_from_directory(ROOT/'data','sample-cycle.json',as_attachment=True)
def parse_input(payload):
 if not isinstance(payload,dict) or not isinstance(payload.get('sensors'),dict):raise ValueError('Expected JSON object with a sensors object. Download the real example file.')
 arrays=[]; features=[];trace=[]
 for s in SENSORS:
  a=np.asarray(payload['sensors'].get(s,[]),dtype=float)
  hz=META['sensors'][s][2]
  if a.shape!=(hz*60,) or not np.isfinite(a).all() or np.any(np.abs(a)>1e9):raise ValueError(f'{s}: expected {hz*60} finite numeric samples for one 60-second cycle.')
  features.extend([a.mean(),a.std(),a.min(),a.max(),np.ptp(a),a[-1]-a[0]]);trace.append(a[::hz]);arrays.append(a)
 return np.array(features),np.array(trace)
@app.post('/api/analyze')
def analyze():
 try:x,t=parse_input(request.get_json(silent=True));return jsonify(result(x,t))
 except (ValueError,TypeError):return jsonify(error='Invalid measurements. Each sensor must contain exactly 60 seconds at its native rate: PS/EPS 6000, FS 600, TS/VS 60 finite numeric samples.'),400
@app.post('/api/brief/<int:cid>')
def brief(cid):
 if not 1<=cid<=len(P):return jsonify(error='Cycle not found'),404
 if not ai_config()['enabled']:return jsonify(error=ai_config()['reason']),503
 if not AI_LOCK.acquire(blocking=False):return jsonify(error='Investigation busy; try again shortly.'),429
 try:
  report=result(X[cid-1],T[cid-1],cid-1)
  # Recorded labels and related component labels deliberately excluded from model briefing.
  facts={k:report[k] for k in ['prediction','label_name','vote_shares','evidence','similar_training_cycles','scope','uncertainty','next_checks']}
  return jsonify(generate_brief(facts,'Write a maintenance investigation with Observations, Alternative explanations, and Recommended verification.'))
 except Exception:
  app.logger.exception('Gemini request failed')
  return jsonify(error='Gemini request failed. Check server logs, credentials, model access and project billing. No AI brief was generated.'),502
 finally:AI_LOCK.release()
@app.get('/api/energy')
def energy():
 return jsonify(ledger(X,P,META['feature_names'],request.args.get('stable','1')!='0'))
@app.post('/api/energy/cost/<setting>')
def energy_cost(setting):
 try:return jsonify(cost_scenario(ledger(X,P,META['feature_names']),setting,request.get_json(silent=True)))
 except LookupError as exc:return jsonify(error=str(exc)),404
 except ValueError as exc:return jsonify(error=str(exc)),400
@app.post('/api/energy/brief/<setting>')
def energy_brief(setting):
 data=ledger(X,P,META['feature_names'])
 row=next((r for r in data['rows'] if r['id']==setting),None)
 if row is None:return jsonify(error='Unknown matched setting'),404
 scenario=None
 if request.data:
  try:scenario=cost_scenario(data,setting,request.get_json(silent=True))
  except ValueError as exc:return jsonify(error=str(exc)),400
 if not ai_config()['enabled']:return jsonify(error=ai_config()['reason']),503
 if not AI_LOCK.acquire(blocking=False):return jsonify(error='Investigation busy; try again shortly.'),429
 try:
  return jsonify(generate_brief({'comparison':row,'method':data['method'],'limitations':data['limitations'],'cost_scenario':scenario},'Explain this matched-condition energy comparison. Summarize observed electrical energy differences, variation across cycles, and additional measurements needed before estimating factory savings. Recorded component labels are retrospective grouping data, not model predictions. If cost_scenario is supplied, quote its server-calculated INR figures and explain its formula and user assumptions. Explain that the cross-setting sensitivity range is not a confidence interval, and do not present any estimate as guaranteed factory savings.'))
 except Exception:
  app.logger.exception('Vertex energy brief failed')
  return jsonify(error='Vertex AI request failed. Check server logs, model access, credentials and billing.'),502
 finally:AI_LOCK.release()
@app.get('/api/agents')
def agents_status():
 return jsonify(agents=['coordinator','diagnosis','energy','maintenance'],enabled=ai_config()['enabled'],
                reason=ai_config()['reason'],max_model_calls=12,deadline_seconds=70)
@app.post('/api/investigate')
def agent_investigation():
 from app.agents import investigate
 from app.agents.tools import build_tools
 payload=request.get_json(silent=True)
 try:
  if not isinstance(payload,dict):raise ValueError('Expected a JSON object.')
  question=payload.get('question','')
  if not isinstance(question,str) or not 1<=len(question.strip())<=2000:raise ValueError('Question must contain 1–2000 characters.')
  history=payload.get('history',[])
  if not isinstance(history,list) or len(history)>8:raise ValueError('History must contain at most 8 messages.')
  for msg in history:
   if not isinstance(msg,dict) or msg.get('role') not in ('user','assistant') or not isinstance(msg.get('text'),str) or len(msg['text'])>6000:raise ValueError('Invalid conversation history.')
  if not isinstance(payload.get('full_investigation',False),bool):raise ValueError('Invalid investigation mode.')
  if 'measurement' in payload:
   x,t=parse_input(payload['measurement']); report=result(x,t); setting=payload.get('setting_id')
  else:
   cid=payload.get('cycle_id')
   if isinstance(cid,bool) or not isinstance(cid,int) or not 1<=cid<=len(P):raise ValueError('Select a valid recorded cycle or upload measurements.')
   report=result(X[cid-1],T[cid-1],cid-1)
   setting='-'.join(str(int(P[cid-1,j])) for j in (0,1,3))
  data=ledger(X,P,META['feature_names'])
  if setting is not None and (not isinstance(setting,str) or not any(r['id']==setting for r in data['rows'])):raise ValueError('Select an existing matched setting.')
  inputs=payload.get('cost_inputs')
  if inputs is not None:
   if setting is None:raise ValueError('Choose a matched setting before calculating upload costs.')
   cost_scenario(data,setting,inputs)
  tools=build_tools(report,data,setting,inputs)
 except (ValueError,TypeError,LookupError) as exc:return jsonify(error=str(exc)),400
 if not ai_config()['enabled']:return jsonify(error=ai_config()['reason']),503
 if not AI_LOCK.acquire(blocking=False):return jsonify(error='Investigation busy; try again shortly.'),429
 try:
  response=investigate(question,{'cycle_id':report['cycle_id'],'source':'User upload' if report['cycle_id'] is None else 'Recorded UCI cycle',
      'history':history,'full_investigation':payload.get('full_investigation',False),
      'cost_inputs_supplied':inputs is not None},tools)
  response['work_order']=next((e['evidence'] for e in reversed(response['trace']) if e['tool']=='draft_work_order' and e['status']=='completed'),None)
  response['quality']=report['quality']
  response['verification']=report['verification']
  return jsonify(response)
 except Exception:
  app.logger.exception('Agent investigation failed')
  return jsonify(error='Agent investigation could not finish. Check Vertex credentials, model function-calling support and billing, or retry a narrower question. No completed AI investigation is available.'),502
 finally:AI_LOCK.release()

@app.get('/api/quality/evaluation')
def quality_evaluation():
 path=ROOT/'models/review_gate_metrics.json'
 if not path.exists():return jsonify(error='Run scripts/evaluate_review_gate.py first.'),503
 return jsonify(json.loads(path.read_text()))

@app.post('/api/report.pdf')
def inspection_pdf():
 from app.reporting import render_report
 from app.agents.tools import build_tools
 payload=request.get_json(silent=True)
 try:
  if not isinstance(payload,dict):raise ValueError('Expected a JSON object.')
  if 'measurement' in payload:
   x,t=parse_input(payload['measurement']);report=result(x,t);setting=payload.get('setting_id')
  else:
   cid=payload.get('cycle_id')
   if isinstance(cid,bool) or not isinstance(cid,int) or not 1<=cid<=len(P):raise ValueError('Choose a valid cycle.')
   report=result(X[cid-1],T[cid-1],cid-1)
   setting='-'.join(str(int(P[cid-1,j])) for j in (0,1,3))
  data=ledger(X,P,META['feature_names'])
  if setting is not None and (not isinstance(setting,str) or not any(r['id']==setting for r in data['rows'])):raise ValueError('Unknown comparison setting.')
  inputs=payload.get('cost_inputs')
  if inputs is not None:
   if setting is None:raise ValueError('Select a comparison setting for costs.')
   cost_scenario(data,setting,inputs)
  notes=payload.get('notes','');engineer=payload.get('engineer','')
  if not isinstance(notes,str) or len(notes)>2000 or not isinstance(engineer,str) or len(engineer)>120:raise ValueError('Invalid review notes.')
  draft=build_tools(report,data,setting,inputs)['draft_work_order']()
  content=render_report(report,draft,engineer,notes)
  return Response(content,mimetype='application/pdf',headers={'Content-Disposition':'attachment; filename=hydraulic-inspection.pdf','Cache-Control':'no-store'})
 except (ValueError,TypeError,LookupError):return jsonify(error='Invalid report inputs. Select a recording or valid measurements and check cost assumptions.'),400

@app.errorhandler(413)
def large(e):return jsonify(error='File exceeds 2 MiB limit.'),413
if __name__=='__main__': app.run(host='127.0.0.1',port=int(os.getenv('PORT','8080')),debug=False)
