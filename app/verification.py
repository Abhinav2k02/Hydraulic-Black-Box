"""Deterministic decision support; no new measurements or calibrated probabilities."""
import numpy as np

MANUAL_URL = 'https://www.parker.com/content/dam/Parker-com/Literature/Hydraulic-Pump-Division/P1-PD-18cc-140cc-Service-Manual.pdf'
MANUAL = {
    'id': 'PARKER-P1PD-2019-P3',
    'title': 'Parker P1/PD A-Mod Service Information',
    'section': 'General Information, printed page 3',
    'url': MANUAL_URL + '#page=3',
    'reviewed_on': '2026-10-18',
    'summary': 'The manual discusses case-drain plumbing, inlet restrictions, fluid temperature and viscosity, and checking troubleshooting guidance before overhaul.',
    'applicability': 'Reference example only. The dataset pump model is not verified as Parker P1/PD. Confirm the installed pump and use its exact OEM manual before testing. No Parker limits are applied to these readings.',
    'method': 'Curated source summary, not a live manual search or full-document RAG.'
}

class ReviewGate:
    def __init__(self, features, train, labels, names):
        self.low = features[train].min(axis=0)
        self.high = features[train].max(axis=0)
        self.names = names

    def check(self, x, prediction, neighbors):
        outside = np.flatnonzero((x < self.low) | (x > self.high))
        disagreement = any(n['label'] != prediction for n in neighbors)
        reasons = []
        if len(outside): reasons.append(f'{len(outside)} derived features fall outside the training minimum/maximum range.')
        if disagreement: reasons.append('The three nearest training examples do not all agree with this prediction.')
        return {'status': 'review_required' if reasons else 'screening_only',
                'title': 'Pause and verify' if reasons else 'Screening result available',
                'reasons': reasons or ['No range or neighbor-disagreement flag was found. This does not confirm pump health.'],
                'outside_features': [self.names[i] for i in outside],
                'neighbor_disagreement': disagreement,
                'method': 'Flag any feature outside training min/max, or any of the three nearest training labels differing from the prediction. Rules fixed before evaluating the held-out split; no vote-share cutoff.',
                'limitation': 'Conservative review aid, not a calibrated confidence score or validated factory out-of-distribution detector. All results require engineer review.'}


def verification_plan(report):
    top = report['evidence'][:3]
    refs = [e['sensor'] for e in top]
    checks = [
        {'id': 'context', 'title': 'Confirm the operating conditions',
         'why': 'Load, speed and oil temperature can change pressure, flow and motor power.',
         'needed': 'Pump identity, circuit drawing, speed, load and cycle stage; confirm sensor locations and calibration.',
         'decision': 'Compare readings only at equivalent operating conditions.', 'references': []},
        {'id': 'pump', 'title': 'Verify suspected internal leakage',
         'why': f"Classifier screening: {report['label_name']}. This is a hypothesis, not a confirmed failure.",
         'needed': 'Qualified engineer inspection using the installed pump OEM procedure; case-drain measurements only where applicable.',
         'decision': 'Compare verified measurements with the correct OEM limits before deciding on repair.', 'references': [MANUAL['id']]},
        {'id': 'alternatives', 'title': 'Check other explanations',
         'why': 'Cooling, fluid condition, inlet restrictions and valve behavior can affect the same signals.',
         'needed': 'Engineer review of temperature, cooler, inlet and valve condition alongside pump evidence.',
         'decision': 'Record which alternative was supported or ruled out; do not attribute every change to the pump.', 'references': [MANUAL['id']]}
    ]
    if report.get('quality', {}).get('status') == 'review_required':
        checks.insert(0, {'id': 'quality', 'title': 'Resolve the uncertainty flag first',
            'why': ' '.join(report['quality']['reasons']),
            'needed': 'Check sensor units, timing, calibration and whether this operating condition is represented in the training data.',
            'decision': 'Treat the predicted leakage class as provisional.', 'references': []})
    return {'title': 'What should we check next?', 'evidence_sensors': refs,
            'hypotheses': ['Internal pump leakage', 'Different load or operating stage', 'Cooling, fluid, inlet or valve issue'],
            'checks': checks, 'manual_references': [MANUAL],
            'missing_context': ['Installed pump model and applicable manual', 'Verified operating load and speed', 'Engineer inspection findings'],
            'note': 'Suggested checks are decision support, not instructions to operate or adjust a press.'}
