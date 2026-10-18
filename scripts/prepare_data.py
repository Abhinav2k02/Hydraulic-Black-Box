"""Fetch original UCI measurements; derive features without synthesizing samples."""
from pathlib import Path
import argparse, hashlib, json, zipfile, urllib.request
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
URL = 'https://archive.ics.uci.edu/static/public/447/condition+monitoring+of+hydraulic+systems.zip'
SENSORS = {**{f'PS{i}': ['Pressure', 'bar', 100] for i in range(1,7)}, 'EPS1':['Motor power','W',100], 'FS1':['Flow','L/min',10], 'FS2':['Flow','L/min',10], **{f'TS{i}':['Temperature','°C',1] for i in range(1,5)}, 'VS1':['Vibration','mm/s',1]}
STATS=['mean','std','min','max','range','end_minus_start']
def main():
 p=argparse.ArgumentParser(); p.add_argument('--archive',type=Path,default=ROOT/'data'/'original.zip'); a=p.parse_args()
 a.archive.parent.mkdir(parents=True,exist_ok=True)
 if not a.archive.exists():
  print('Downloading original UCI archive (approximately 73 MiB)...',flush=True)
  urllib.request.urlretrieve(URL,a.archive)
 digest=hashlib.sha256(a.archive.read_bytes()).hexdigest()
 z=zipfile.ZipFile(a.archive); profile=np.loadtxt(z.open('profile.txt'),dtype=int)
 features=[]; traces=[]; names=[]
 for sensor,(_,_,hz) in SENSORS.items():
  print('Processing',sensor,flush=True)
  arr=np.loadtxt(z.open(sensor+'.txt'),dtype=np.float64)
  assert arr.shape==(2205,60*hz) and np.isfinite(arr).all()
  features.append(np.stack([arr.mean(1),arr.std(1),arr.min(1),arr.max(1),np.ptp(arr,axis=1),arr[:,-1]-arr[:,0]],axis=1))
  # Original samples at t=0,1,...,59 seconds, not interpolation or generated data.
  traces.append(arr[:,::hz].astype(np.float32)); names.extend([sensor+'_'+s for s in STATS])
 out=ROOT/'data'; out.mkdir(exist_ok=True)
 np.savez_compressed(out/'measurements.npz',features=np.concatenate(features,axis=1),traces=np.stack(traces,axis=1),profile=profile)
 meta={'source_url':URL,'doi':'https://doi.org/10.24432/C5CW21','archive_sha256':digest,'cycles':len(profile),'duration_seconds':60,'sensors':SENSORS,'feature_names':names,'provenance':'Real experimental hydraulic test-rig measurements; not a production factory dataset. No synthetic measurements.','trace_transform':'One original sample per second; cast to float32. Features computed from every raw sample at original sampling rate.','excluded':['CE','CP','SE'],'license':'CC BY 4.0','authors':'Nikolai Helwig, Eliseo Pignanelli, Andreas Schütze (2015)'}
 (out/'metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
 for name in ['description.txt','documentation.txt']:
  (out/('UCI_'+name)).write_text(z.read(name).decode('latin-1'),encoding='utf-8')
 print('Saved real derived measurements; SHA256:',digest)
if __name__=='__main__': main()
