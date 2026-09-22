"""Independent Decimal arithmetic and cross-source reconciliation of aggregates."""
import argparse
from decimal import Decimal
import json
import math
from pathlib import Path

D = lambda x: Decimal(str(x))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    report = json.loads((args.run_dir/'commercial_evaluation.json').read_text(encoding='utf-8'))
    grid = json.loads((args.run_dir/'commercial_sensitivity_grid.json').read_text(encoding='utf-8'))
    config = report['config']
    profiles = {(p['source_case'],p['capacity'],p['policy'],p['value_case']):p for p in report['policy_profiles']}
    assumptions = {s['name']:s for s in config['scenarios']}
    checked, differences = 0, []
    def compare(actual, expected, identifier):
        nonlocal checked
        checked += 1
        if not math.isclose(float(actual), float(expected), abs_tol=1e-7, rel_tol=1e-11):
            differences.append(identifier)
    for i, row in enumerate(report['scenarios']):
        profile = profiles[(row['source_case'],row['capacity'],row['policy'],row['value_case'])]
        assumption = assumptions[row['scenario']]
        n, churn = D(profile['contacts']), D(profile['churn_units'])
        unit_value = D(config['monthly_fee_cu'])*D(config['horizon_days'])/D(config['days_per_scenario_month'])*D(assumption['margin'])
        value = D(profile['value_index_sum'])*unit_value
        churn_value = D(profile['churn_value_index_sum'])*unit_value
        contact = n*D(assumption['contact_cost'])
        would_churn = churn*D(assumption['redemption'])*D(assumption['incentive_cost'])
        would_renew = (n-churn)*D(assumption['redemption'])*D(assumption['incentive_cost'])
        total = contact+would_churn+would_renew+D(config['fixed_cost_cu'])
        effect = D(assumption['effect'])
        benefit = effect*(churn_value if assumption['effect_type']=='conditional' else value)
        expected = {'assumed_additional_retained': effect*(churn if assumption['effect_type']=='conditional' else n),
            'scenario_benefit_cu':benefit,'contact_cost_cu':contact,'incentive_cost_would_churn_cu':would_churn,
            'incentive_cost_would_renew_cu':would_renew,'total_cost_cu':total,'net_contribution_cu':benefit-total,
            'net_per_contact_cu':(benefit-total)/n,'break_even_conditional_save':total/churn_value,
            'break_even_absolute_effect':total/value}
        for key, result in expected.items():
            compare(row[key],result,f'scenario/{i}/{key}')
    for i, values in enumerate(grid['rows']):
        row = dict(zip(grid['columns'], values))
        profile = profiles[(row['source_case'],.1,'risk_only','uniform')]
        n, q = D(profile['contacts']),D(profile['churn_units'])
        v = D(config['monthly_fee_cu'])*D(config['horizon_days'])/D(config['days_per_scenario_month'])*D(row['margin'])
        cost = n*(D(row['contact_cost'])+D(row['redemption'])*D(row['incentive_cost']))+D(config['fixed_cost_cu'])
        compare(row['net_contribution_cu'],q*D(row['conditional_save'])*v-cost,f'grid/{i}/net')
        compare(row['break_even_conditional_save'],cost/(q*v),f'grid/{i}/conditional')
        compare(row['break_even_absolute_effect'],cost/(n*v),f'grid/{i}/absolute')
    for capacity in config['capacities']:
        for policy in ['risk_only','risk_x_value_proxy']:
            for value_case in ['uniform','payment_proxy']:
                base = profiles[('common_baseline',capacity,policy,value_case)]
                alternate = profiles[('common_full_union',capacity,policy,value_case)]
                for field in ['contacts','value_index_sum','unknown_value_contacts','overlap_with_other_policy','predicted_churn_units']:
                    compare(base[field],alternate[field],f'paired/{capacity}/{policy}/{value_case}/{field}')
    result = {'scenario_rows':len(report['scenarios']),'sensitivity_rows':len(grid['rows']),
        'aggregate_values_checked':checked,'differences':differences,
        'method':'Independent Decimal arithmetic plus paired-source list statistics; no pipeline economics functions imported'}
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    if differences:
        raise ValueError('Commercial verification discrepancy')


if __name__=='__main__':
    main()
