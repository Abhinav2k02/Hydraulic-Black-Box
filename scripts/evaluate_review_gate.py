"""Evaluate fixed review rules without tuning against test labels."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import server as s

def main():
    rows=[]
    for i in sorted(s.TEST):
        r=s.result(s.X[i],s.T[i],i)
        rows.append({'cycle_id':i+1,'flagged':r['quality']['status']=='review_required','wrong':int(s.PRED[i])!=int(s.P[i,2])})
    flagged=[r for r in rows if r['flagged']];remaining=[r for r in rows if not r['flagged']]
    result={'test_cycles':len(rows),'flagged_cycles':len(flagged),'unflagged_cycles':len(remaining),
        'total_classifier_errors':sum(r['wrong'] for r in rows),'flagged_classifier_errors':sum(r['wrong'] for r in flagged),
        'unflagged_classifier_errors':sum(r['wrong'] for r in remaining),
        'unflagged_accuracy':1-sum(r['wrong'] for r in remaining)/len(remaining) if remaining else None,
        'review_rate':len(flagged)/len(rows),'flagged_correct_predictions':sum(not r['wrong'] for r in flagged),
        'method':s.GATE.check(s.X[0],0,[])['method'],
        'limitations':'Single-rig retrospective held-out evaluation. Rules were not tuned on these labels. Unflagged does not mean safe. No factory validation or calibrated confidence. Current model was not retrained.',
        'examples':rows}
    (s.ROOT/'models/review_gate_metrics.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='examples'},indent=2))
if __name__=='__main__':main()
