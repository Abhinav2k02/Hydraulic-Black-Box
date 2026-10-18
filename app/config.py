"""Local .env loader; Cloud Run's environment takes precedence. No credentials in responses."""
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
def load_env():
    path=ROOT/'.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            line=line.strip()
            if not line or line.startswith('#'): continue
            key,sep,value=line.partition('=')
            if sep and key.strip().replace('_','').isalnum():
                value=value.strip()
                if len(value)>1 and value[0]==value[-1] and value[0] in ('"', "'"): value=value[1:-1]
                os.environ.setdefault(key.strip(),value)
    path=os.getenv('GOOGLE_APPLICATION_CREDENTIALS','').strip()
    if path and not Path(path).is_absolute():os.environ['GOOGLE_APPLICATION_CREDENTIALS']=str(ROOT/path)
def placeholder(value):
    return not value or any(t in value.upper() for t in ('YOUR_', 'REPLACE_', '<', '>'))
def ai_config():
    project=os.getenv('GOOGLE_CLOUD_PROJECT','').strip();model=os.getenv('GEMINI_MODEL','').strip()
    reason=''
    if placeholder(project) or placeholder(model):reason='Fill GOOGLE_CLOUD_PROJECT and GEMINI_MODEL in .env, or in Cloud Run environment variables.'
    path=os.getenv('GOOGLE_APPLICATION_CREDENTIALS','').strip()
    if path and (placeholder(path) or not Path(path).is_file()):reason='Credential file is missing. Supply the downloaded JSON file or leave GOOGLE_APPLICATION_CREDENTIALS blank to use ADC.'
    return {'enabled':not bool(reason),'reason':reason,'project':project,'model':model,'location':os.getenv('GOOGLE_CLOUD_LOCATION','global')}
load_env()
