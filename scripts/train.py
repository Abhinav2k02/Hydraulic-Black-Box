"""Reproducible group-held-out pump leakage benchmark; labels never enter features."""
from pathlib import Path
import json, hashlib
import numpy as np
import joblib
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, confusion_matrix, classification_report
ROOT=Path(__file__).resolve().parents[1]
def main():
 d=np.load(ROOT/'data/measurements.npz'); x=d['features']; p=d['profile']; y=p[:,2]
 # Consecutive runs with unchanged component settings are kept in one partition.
 # Stability flag is not a component setting and must not split a run.
 groups=np.r_[0,np.cumsum(np.any(p[1:,:4]!=p[:-1,:4],axis=1))]
 train,test=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=42).split(x,y,groups))
 assert not set(groups[train]) & set(groups[test])
 assert set(y[train])==set(y[test])=={0,1,2}
 model=ExtraTreesClassifier(n_estimators=180,min_samples_leaf=2,class_weight='balanced',random_state=42,n_jobs=2)
 model.fit(x[train],y[train]); pred=model.predict(x[test]); all_pred=model.predict(x); probs=model.predict_proba(x)
 stable=test[p[test,4]==0]; unstable=test[p[test,4]==1]
 metric={'accuracy':float(accuracy_score(y[test],pred)),'balanced_accuracy':float(balanced_accuracy_score(y[test],pred)),'macro_f1':float(f1_score(y[test],pred,average='macro')),'confusion_matrix':confusion_matrix(y[test],pred,labels=[0,1,2]).tolist(),'classification_report':classification_report(y[test],pred,output_dict=True),'train_cycles':len(train),'test_cycles':len(test),'train_groups':len(set(groups[train])),'test_groups':len(set(groups[test])),'split':'GroupShuffleSplit(test_size=0.25, random_state=42); groups are consecutive runs with identical cooler, valve, pump and accumulator settings.','limitations':'Single test rig; nearby groups and repeated settings can remain correlated. This is not external factory validation, a chronological deployment test, or remaining-life prediction. Vote shares are not calibrated probabilities.','stable_test_accuracy':float(accuracy_score(y[stable],model.predict(x[stable]))) if len(stable) else None,'unstable_test_accuracy':float(accuracy_score(y[unstable],model.predict(x[unstable]))) if len(unstable) else None,'feature_importances':model.feature_importances_.tolist(),'data_sha256':hashlib.sha256((ROOT/'data/measurements.npz').read_bytes()).hexdigest()}
 (ROOT/'models').mkdir(exist_ok=True)
 joblib.dump(model,ROOT/'models/pump_model.joblib',compress=3)
 np.savez_compressed(ROOT/'models/evaluation.npz',train=train,test=test,groups=groups,predictions=all_pred,probabilities=probs)
 (ROOT/'models/metrics.json').write_text(json.dumps(metric,indent=2))
 print(json.dumps({k:metric[k] for k in ['accuracy','balanced_accuracy','macro_f1','train_cycles','test_cycles','train_groups','test_groups']},indent=2))
if __name__=='__main__':main()
