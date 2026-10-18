"""Retrospective comparisons of real measured power; never synthetic sensor data."""
import numpy as np

def ledger(features,profile,feature_names,stable_only=True):
    eps=features[:,feature_names.index('EPS1_mean')]
    flow=features[:,feature_names.index('FS1_mean')]
    allowed=(profile[:,4]==0) if stable_only else np.ones(len(profile),dtype=bool)
    rows=[]
    for key in sorted(set(map(tuple,profile[:,[0,1,3]]))):
        mask=allowed&(profile[:,0]==key[0])&(profile[:,1]==key[1])&(profile[:,3]==key[2])
        states=[]
        for cls in (0,1,2):
            ids=np.where(mask&(profile[:,2]==cls))[0]
            if not len(ids):break
            states.append({'leakage':cls,'count':len(ids),'cycle_ids':(ids+1).tolist(),'mean_power_w':float(eps[ids].mean()),'cycle_power_sd_w':float(eps[ids].std()),'mean_energy_wh':float(eps[ids].mean()/60),'mean_flow_l_min':float(flow[ids].mean())})
        if len(states)!=3:continue
        base=states[0]['mean_power_w']
        for s in states:
            s['extra_power_w']=s['mean_power_w']-base
            s['extra_energy_wh']=s['extra_power_w']/60
        rows.append({'id':'-'.join(map(str,key)),'cooler':int(key[0]),'valve':int(key[1]),'accumulator':int(key[2]),'states':states})
    delta=[r['states'][2]['extra_power_w'] for r in rows]
    return {'stable_only':stable_only,'matched_settings':len(rows),'mean_severe_extra_power_w':float(np.mean(delta)) if delta else None,'median_severe_extra_power_w':float(np.median(delta)) if delta else None,'rows':rows,'method':'Mean EPS1 motor power by recorded pump condition, matched on cooler, valve and accumulator labels. Equal weight per matched setting in summary. Energy per 60-second cycle = average watts / 60 Wh.','limitations':'Retrospective label-based analysis of the full test-rig dataset, separate from held-out classification. Matching these labels does not guarantee identical temperatures or all other operating conditions. Observed differences are not guaranteed repair savings or causal estimates. Repeated cycles are correlated; cycle SD is descriptive, not a confidence interval.'}
