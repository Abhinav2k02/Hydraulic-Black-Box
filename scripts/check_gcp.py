"""Check configuration and optional live Vertex connectivity without printing secrets."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import ai_config
p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--agents',action='store_true',help='Run a real full four-agent investigation on recorded cycle 242; incurs Vertex usage.');args=p.parse_args();cfg=ai_config()
if not cfg['enabled']:print('Not configured:',cfg['reason']);sys.exit(1)
print('Configuration present. Model access and credentials have not yet been verified.')
if args.live:
    from app.vertex import generate_brief
    try:
        answer=generate_brief({'purpose':'connection test'},'Reply with CONNECTION_OK only.')
        print('Vertex AI returned text successfully. Model:',answer['model'])
    except Exception as exc:
        print('Connection failed:',type(exc).__name__,'. Check credentials, IAM, billing, model ID and location.');sys.exit(1)

if args.agents:
    from app.server import app
    try:
        with app.test_client() as client:
            response=client.post('/api/investigate',json={'cycle_id':242,'question':'Run diagnosis, energy comparison and maintenance drafting. Cite evidence.','full_investigation':True})
        if response.status_code!=200:raise RuntimeError(response.json.get('error','Agent check failed'))
        if set(response.json['agents'])!={'coordinator','diagnosis','energy','maintenance'}:raise RuntimeError('Incomplete delegation')
        print('Four-agent live check passed. Model calls:',response.json['model_calls'])
        print('Inspect complete findings and tool evidence in the browser workspace.')
    except Exception as exc:
        print('Agent check failed:',type(exc).__name__,'. Check logs, function-calling model support, IAM, billing and credentials.');sys.exit(1)
