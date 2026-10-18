"""Plan by default. --apply enables APIs/IAM and deploys source to private Cloud Run."""
import argparse,json,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def commands(cfg,env_path):
    project=cfg['project_id']; runtime=cfg['runtime_service_account']+'@'+project+'.iam.gserviceaccount.com';build=cfg['build_service_account']+'@'+project+'.iam.gserviceaccount.com'
    common=['--project',project,'--quiet']
    return [
      ['services','enable','run.googleapis.com','cloudbuild.googleapis.com','artifactregistry.googleapis.com','aiplatform.googleapis.com','iam.googleapis.com']+common,
      ['iam','service-accounts','create',cfg['runtime_service_account']]+common,
      ['iam','service-accounts','create',cfg['build_service_account']]+common,
      ['projects','add-iam-policy-binding',project,'--member=serviceAccount:'+runtime,'--role=roles/aiplatform.user','--condition=None','--quiet'],
      ['projects','add-iam-policy-binding',project,'--member=serviceAccount:'+build,'--role=roles/run.builder','--condition=None','--quiet'],
      ['run','deploy',cfg['service_name'],'--source',str(ROOT),'--region',cfg['region'],'--service-account',runtime,'--build-service-account','projects/'+project+'/serviceAccounts/'+build,'--memory','1Gi','--cpu','1','--concurrency','4','--max-instances','2','--timeout','90','--no-allow-unauthenticated','--env-vars-file',str(env_path)]+common]
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,default=ROOT/'config/gcp.json');parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    if not args.config.exists():parser.error('Copy config/gcp.example.json to config/gcp.json and fill the project/model values.')
    cfg=json.loads(args.config.read_text())
    for key in ['project_id','region','vertex_location','gemini_model','service_name','runtime_service_account','build_service_account']:
        if not isinstance(cfg.get(key),str) or not cfg[key] or 'YOUR_' in cfg[key] or not re.fullmatch(r'[a-zA-Z0-9._-]+',cfg[key]):parser.error('Replace/validate '+key+' in config.')
    env={'GOOGLE_CLOUD_PROJECT':cfg['project_id'],'GOOGLE_CLOUD_LOCATION':cfg['vertex_location'],'GEMINI_MODEL':cfg['gemini_model']}
    with tempfile.TemporaryDirectory(prefix='hydraulic-deploy-') as tmp:
        env_path=Path(tmp)/'environment.yaml';env_path.write_text(''.join(k+': '+json.dumps(v)+'\n' for k,v in env.items()))
        steps=commands(cfg,env_path)
        if not args.apply:
            print('PLAN ONLY. No cloud requests. Run again with --apply to execute.')
            for step in steps:print('gcloud '+ ' '.join(step))
            print('Runtime environment:',json.dumps(env));return
        gcloud=shutil.which('gcloud')
        if not gcloud:parser.error('Install Google Cloud CLI, or run from Google Cloud Shell.')
        for step in steps:
            if step[:3]==['iam','service-accounts','create']:
                email=step[3]+'@'+cfg['project_id']+'.iam.gserviceaccount.com'
                # List fails closed on permissions/network errors; do not mistake errors for absence.
                listed=subprocess.run([gcloud,'iam','service-accounts','list','--project',cfg['project_id'],'--format=json'],check=True,capture_output=True,text=True)
                if any(x['email']==email for x in json.loads(listed.stdout)):continue
            subprocess.run([gcloud]+step,cwd=ROOT,check=True)
        print('Deployment finished. Obtain URL and verify live Gemini; service is IAM-restricted.')
if __name__=='__main__':main()
