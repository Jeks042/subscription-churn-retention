"""Independently reconcile exported aggregates, embedded M, DAX guards and PBIR.

python -m src.verify_dashboard [--schemas]
The optional schema pass fetches Microsoft's public JSON schemas.
"""
import argparse
import base64
import hashlib
import json
import math
from pathlib import Path
import re
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dashboard'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--schemas',action='store_true');args=ap.parse_args()
    count=0
    def check(ok,label):
        nonlocal count
        assert ok,label
        count+=1
    def equal(a,b,label):check(math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-7),label)
    def read(p):return json.loads(p.read_text(encoding='utf-8'))
    tables={p.stem.replace('_',' '):read(p) for p in (OUT/'aggregates').glob('*.json')}
    model=read(OUT/'Retention.SemanticModel/model.bim')['model']
    mt={t['name']:t for t in model['tables']}
    manifest=read(OUT/'build_manifest.json')
    for name,sha in manifest['source_sha256'].items():check(hashlib.sha256((ROOT/'reports'/name).read_bytes()).hexdigest()==sha,'source '+name)
    for name,rows in tables.items():
        expression='\n'.join(mt[name]['partitions'][0]['source']['expression'])
        embedded=json.loads(base64.b64decode(re.search(r'Binary.FromText\("([A-Za-z0-9+/=]+)"',expression)[1]))
        check(embedded==rows,'embedded aggregate '+name)
        check(len(rows)==manifest['tables'][name]['rows'],'row count '+name)
        cols={c['name'].lower() for c in mt[name]['columns']}
        for measure in mt[name]['measures']:
            check(measure['name'].lower() not in cols,'case-insensitive field uniqueness')
            if measure['name']!='Selection status':check(('COUNTROWS(' in measure['expression'] and ' = 1' in measure['expression']) or '[Scenario net CU]' in measure['expression'],'single-row guard '+measure['name'])
    source=read(ROOT/'reports/model_evaluation.json')
    check(tables['Overview'][0]==source['models']['combined']['calibrated'],'overview exact')
    for row in tables['Models']:
        for key,value in source['models'][row['model']]['calibrated'].items():equal(row[key],value,'model '+row['model']+' '+key)
    for row in tables['Capacity']:
        equal(row['tp']+row['fp'],row['contacts'],'contact accounting')
        equal(row['tp']+row['fn'],tables['Overview'][0]['churn'],'churn accounting')
        equal(row['precision'],row['tp']/row['contacts'],'precision denominator')
        equal(row['recall'],row['tp']/tables['Overview'][0]['churn'],'recall denominator')
    equal(sum(r['rows'] for r in tables['Calibration']),680401,'calibration bin population')
    for i in range(0,8,2):equal(sum(r['rows'] for r in tables['Segments'][i:i+2]),680401,'segment pair denominator')
    check(len(tables['Cohorts'])==7,'seven scoring cohorts')
    profiles={p['profile_key']:p for p in tables['Profiles']}
    check(len(profiles)==60,'profile primary key')
    configs={c['name']:c for c in tables['Scenario choices']}
    unique={(s['profile_key'],s['scenario']) for s in tables['Scenarios']}
    check(len(unique)==360,'scenario composite key')
    for s in tables['Scenarios']:
        p=profiles[s['profile_key']];c=configs[s['scenario']]
        n,q=p['contacts'],p['churn_units']
        contribution=40*3*c['margin']
        base=p['churn_value_index_sum'] if c['effect_type']=='conditional' else p['value_index_sum']
        benefit=c['effect']*base*contribution
        cost=n*(c['contact_cost']+c['redemption']*c['incentive_cost'])
        equal(s['net_contribution_cu'],benefit-cost,'scenario net')
        equal(s['total_cost_cu'],cost,'scenario cost')
        equal(s['break_even_conditional_save'],cost/(p['churn_value_index_sum']*contribution),'scenario conditional threshold')
        equal(s['break_even_absolute_effect'],cost/(p['value_index_sum']*contribution),'scenario absolute threshold')
        equal(s['incentive_cost_would_renew_cu'],(n-q)*c['redemption']*c['incentive_cost'],'already-renewer incentive cost')
    for row in tables['Comparison']:
        original=next(s for s in tables['Scenarios'] if s['profile_key']==row['profile_key'] and s['scenario']==row['scenario'])
        check(all(row[k]==v for k,v in original.items()),'comparison exact source row')
    check(len(model['relationships'])==2,'only two one-way star relationships')
    for rel in model['relationships']:
        check(rel['fromTable']=='Scenarios' and rel['crossFilteringBehavior']=='oneDirection' and rel['toCardinality']=='one','relationship direction')
    files=list((OUT/'Retention.Report/definition').rglob('*.json'))
    for path in files:
        obj=read(path)
        for role in obj.get('visual',{}).get('query',{}).get('queryState',{}).values():
            for projection in role['projections']:
                field=projection['field'];typ=next(iter(field));f=field[typ]
                name=f['Expression']['SourceRef']['Entity'];col=f['Property']
                valid={x['name'] for x in mt[name]['measures' if typ=='Measure' else 'columns']}
                check(col in valid,'visual field binding '+str(path)+' '+col)
    schema_count=0
    if args.schemas:
        import jsonschema
        from referencing import Registry,Resource
        cache={}
        def retrieve(uri):
            if uri not in cache:cache[uri]=json.load(urllib.request.urlopen(uri))
            return Resource.from_contents(cache[uri])
        registry=Registry(retrieve=retrieve)
        for path in OUT.rglob('*'):
            if path.suffix not in ['.json','.pbip','.pbir','.pbism'] or '.pbi' in path.parts:continue
            obj=read(path)
            if not isinstance(obj,dict) or '$schema' not in obj:continue
            jsonschema.Draft7Validator(retrieve(obj['$schema']).contents,registry=registry).validate(obj)
            schema_count+=1
    result=dict(status='passed',aggregate_and_binding_checks=count,microsoft_schema_documents=schema_count,
                scope='Published aggregates, embedded M payloads, independent scenario arithmetic, denominators, DAX guard structure, visual field bindings.',
                runtime='Desktop refresh, visual rendering and slicer interaction are recorded separately in docs/dashboard_workflow.md.')
    (ROOT/'reports/dashboard_verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
