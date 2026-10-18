"""Package source + model + real derived data. Never include local credentials/config."""
from pathlib import Path
import hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1]
def include(p):
    rel=p.relative_to(ROOT)
    if not p.is_file() or any(s in {'.venv','__pycache__','.git'} for s in rel.parts):return False
    if p.suffix in {'.pyc','.zip'} or p.name=='SHA256SUMS.txt':return False
    if p.name.startswith('.env') and p.name!='.env.example':return False
    if rel.as_posix()=='config/gcp.json':return False
    if rel.parts[0]=='credentials' and p.suffix=='.json':return False
    return True
def main():
    paths=sorted(p for p in ROOT.rglob('*') if include(p))
    inventory=ROOT/'SHA256SUMS.txt'
    inventory.write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix() for p in paths)+'\n')
    output=ROOT.parent/'Hydraulic-Black-Box.zip'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for p in paths+[inventory]:archive.write(p,ROOT.name+'/'+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(output) as archive:
        if archive.testzip():raise RuntimeError('ZIP integrity check failed')
    print(str(output));print('Size:',output.stat().st_size,'bytes; files:',len(paths)+1)
if __name__=='__main__':main()
