"""Server-owned deterministic evidence tools. Model cannot inject numbers or labels."""
from app.cost import cost_scenario


def build_tools(report, data, setting, inputs):
    facts={k:v for k,v in report.items() if k not in {'ground_truth','traces','ai_brief'}}
    selected=next((r for r in data['rows'] if r['id']==setting),None)
    scenario=cost_scenario(data,setting,inputs) if inputs is not None and selected else None
    def diagnosis():return facts
    def energy():
        return {'comparison':selected,'method':data['method'],'limitations':data['limitations'],
                'missing_inputs':[] if selected else ['Select an explicit matched setting for this upload.'],
                'matching_basis':'Recorded component annotations or user-selected setting; not inferred by classifier.'}
    def cost():
        return scenario or {'missing_inputs':['A matched setting and explicit tariff, hours/day, days/year and leakage scenario are required.'],
                            'note':'No cost was calculated. Use the scenario form.'}
    def maintenance():
        return {'status':'draft_requires_human_review','title':'Verify suspected hydraulic pump internal leakage',
                'asset':'Hydraulic power unit — research test-rig recording',
                'cycle_id':report['cycle_id'],'screening_result':report['label_name'],
                'evidence':report['evidence'][:5],'similar_training_cycles':report['similar_training_cycles'],
                'checklist':report['next_checks'],
                'verification':report.get('verification'), 'quality':report.get('quality'),
                'energy_setting_id':selected['id'] if selected else None,'illustrative_cost':scenario,
                'uncertainty':report['uncertainty'],
                'review_fields':['Assigned engineer','Inspection date','Confirmed finding','Approved action'],
                'execution':'No work order sent, no maintenance scheduled, no machine commands available.'}
    return {'inspect_measurement':diagnosis,'compare_energy':energy,'calculate_cost':cost,'draft_work_order':maintenance}
