"""Deterministic what-if calculations; input assumptions are never measured factory facts."""
import math
import numpy as np

def cost_scenario(data, setting, inputs):
    row=next((r for r in data['rows'] if r['id']==setting),None)
    if row is None:raise LookupError('Unknown matched setting')
    if not isinstance(inputs,dict):raise ValueError('Provide a JSON object with tariff_inr_kwh, hours_per_day, days_per_year and leakage.')
    bounds={'tariff_inr_kwh':(0,10000),'hours_per_day':(0,24),'days_per_year':(0,366),'leakage':(1,2)}
    clean={}
    for name,(low,high) in bounds.items():
        v=inputs.get(name)
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not low<=v<=high:
            raise ValueError(f'{name} must be a finite number from {low} to {high}.')
        if name in ('days_per_year','leakage') and int(v)!=v:raise ValueError(f'{name} must be a whole number.')
        clean[name]=int(v) if name in ('days_per_year','leakage') else float(v)
    selected=next(s for s in row['states'] if s['leakage']==clean['leakage'])
    watts=selected['extra_power_w'];annual_hours=clean['hours_per_day']*clean['days_per_year']
    energy=watts/1000*annual_hours
    powers=[next(s['extra_power_w'] for s in r['states'] if s['leakage']==clean['leakage']) for r in data['rows']]
    p10,p90=np.percentile(powers,[10,90]).tolist()
    return {'setting_id':setting,'inputs':clean,'currency':'INR','annual_operating_hours':annual_hours,
      'measured_extra_power_w':watts,'annual_extra_energy_kwh':energy,'annual_extra_cost_inr':energy*clean['tariff_inr_kwh'],
      'average_monthly_extra_cost_inr':energy*clean['tariff_inr_kwh']/12,
      'sensitivity':{'settings_count':len(powers),'power_p10_w':p10,'power_p90_w':p90,
        'annual_cost_p10_inr':p10/1000*annual_hours*clean['tariff_inr_kwh'],
        'annual_cost_p90_inr':p90/1000*annual_hours*clean['tariff_inr_kwh'],
        'meaning':'10th–90th percentile across the observed matched settings using the same schedule and tariff. This is cross-setting sensitivity, not a confidence interval for the selected setting; its point estimate can lie outside this range.'},
      'formula':'Annual extra cost (INR) = measured extra watts / 1000 × hours per day × operating days per year × tariff (INR/kWh). Monthly figure = annual figure / 12.',
      'assumptions':['The selected test-rig power gap persists throughout every entered operating hour.','Schedule and tariff are user assumptions, not observed factory data.','Flat electricity tariff; taxes, demand charges, maintenance costs and downtime are excluded.','No factory-size multiplier is applied.'],
      'limitations':'Illustrative extrapolation from stable test-rig recordings, not a factory bill, confirmed repair savings or a causal estimate. Validate load, temperatures, pump sizing and actual electricity metering before applying it to a plant.'}
