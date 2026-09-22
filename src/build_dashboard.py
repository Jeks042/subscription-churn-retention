"""Build a portable Power BI project using ONLY published aggregate JSON.

No customer records, private database, network calls or model refitting required.
Run from repository root: python -m src.build_dashboard
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dashboard'
REPORT = OUT / 'Retention.Report'
MODEL = OUT / 'Retention.SemanticModel'
SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/'
TABLES: dict[str, list[dict]] = {}
MEASURES: dict[str, list[dict]] = {}
LINEAGE: dict[str, str] = {}


def read(name):
    return json.loads((ROOT / 'reports' / (name + '.json')).read_text(encoding='utf-8'))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def table(name, rows, source):
    TABLES[name] = rows
    LINEAGE[name] = source
    MEASURES[name] = []


def measure(table, name, expression, fmt='#,0.00', description=''):
    MEASURES[table].append(dict(name=name, expression=expression, formatString=fmt,
                                description=description or expression))


def scalar(t, col, name=None, fmt='#,0.00'):
    measure(t, name or col.replace('_', ' ').title(),
            f'IF(COUNTROWS(\'{t}\') = 1, SELECTEDVALUE(\'{t}\'[{col}]))', fmt,
            'Single aggregate row only; blank for ambiguous alternatives or totals. ' + LINEAGE[t])


MODEL_LABELS = dict(prevalence='Prevalence', renewal_rule='Renewal rule', recency='Recency',
                    transactions='Transactions', combined='Combined (frozen)', no_duration='No duration')
SOURCE_LABELS = dict(full_baseline='Full baseline | observed', common_baseline='Matched baseline | observed',
                     common_full_union='Matched full union | observed',
                     full_model_probability='Full model | predicted', common_model_probability='Matched model | predicted')


def prepare():
    m, c, p = read('model_evaluation'), read('commercial_evaluation'), read('experiment_power')
    combined = m['models']['combined']['calibrated']
    table('Overview', [combined], 'model_evaluation.json / models / combined / calibrated')
    for col, name, fmt in [('rows','Eligible customers','#,0'),('churn','Reconstructed churn','#,0'),
        ('prevalence','Observed churn rate','0.00%'),('contacts_10pct','Top 10% contacts','#,0'),
        ('recall_10pct','Churn captured','0.00%'),('precision_10pct','List precision','0.00%'),
        ('mean_prediction','Mean predicted risk','0.00%')]: scalar('Overview',col,name,fmt)
    table('Models', [dict(model=k,label=MODEL_LABELS[k],**v['calibrated']) for k,v in m['models'].items()],
          'model_evaluation.json / models / calibrated')
    for col,name,fmt in [('average_precision','Average precision','0.000'),('roc_auc','ROC AUC','0.000'),
                         ('log_loss','Log loss','0.0000'),('brier','Brier','0.0000')]: scalar('Models',col,name,fmt)
    caps=[]
    for pct in [5,10,20]:
        row=dict(capacity=f'{pct:02d}%',capacity_fraction=pct/100)
        for col in ['contacts','tp','fp','fn','precision','recall','lift']: row[col]=combined[f'{col}_{pct}pct']
        row.update(recall_low=m['uncertainty']['models']['combined'][f'recall_{pct}pct'][0],
                   recall_high=m['uncertainty']['models']['combined'][f'recall_{pct}pct'][1])
        caps.append(row)
    table('Capacity',caps,'model_evaluation.json / combined calibrated and uncertainty')
    for col,name,fmt in [('contacts','Contacts','#,0'),('tp','Churn captured count','#,0'),('precision','Precision','0.0%'),
                         ('recall','Recall','0.0%'),('lift','Lift','0.00'),('recall_low','Recall lower 95%','0.0%'),('recall_high','Recall upper 95%','0.0%')]:scalar('Capacity',col,name,fmt)
    table('Calibration',[dict(bin=f"{r['low']:.1f}–{r['high']:.1f}",**r) for r in m['models']['combined']['calibration_bins']],
          'model_evaluation.json / models / combined / calibration_bins (fixed width)')
    for col,name,fmt in [('rows','Bin customers','#,0'),('mean_prediction','Predicted','0.0%'),('churn_rate','Observed','0.0%')]:scalar('Calibration',col,name,fmt)
    seg=[]
    labels=['No listening record','Listening record present','No member record','Member record present','Seen in training','Unseen in training','Capped duration','No capped duration']
    for (k,v),label in zip(m['segments_selected_model'].items(),labels):
        seg.append(dict(segment=k,label=label,rows=v['rows'],churn=v['churn'],prevalence=v['prevalence'],
                        mean_prediction=v['mean_prediction'],roc_auc=v['roc_auc'],
                        global_contacts=v['global_policy']['0.1']['contacted'],
                        global_contact_rate=v['global_policy']['0.1']['contact_rate']))
    table('Segments',seg,'model_evaluation.json / segments_selected_model; global top 10% policy')
    for col,name,fmt in [('rows','Segment customers','#,0'),('prevalence','Segment observed','0.0%'),
                         ('mean_prediction','Segment predicted','0.0%'),('roc_auc','Segment AUC','0.000'),
                         ('global_contacts','Global list contacts','#,0'),('global_contact_rate','Contact share of segment','0.0%')]:scalar('Segments',col,name,fmt)
    table('Cohorts',read('sql_build_summary')['cohorts'],'sql_build_summary.json / cohorts; snapshot denominators, people recur')
    for col,name,fmt in [('mature_eligible','Mature snapshots','#,0'),('churn','Cohort churn','#,0'),('churn_rate','Cohort churn rate','0.0%')]:scalar('Cohorts',col,name,fmt)
    ss=next(r for r in m['source_sensitivity'] if r['split']=='holdout')
    table('Source', [dict(source=label,**ss[key]) for label,key in [('Baseline','baseline_labels'),('Full union','alternative_labels')]],
          'model_evaluation.json / source_sensitivity / holdout; identical 679309 customers, fixed scores')
    for col,name,fmt in [('rows','Matched customers','#,0'),('churn','Matched churn','#,0'),('prevalence','Matched churn rate','0.00%'),
                         ('precision_10pct','Matched precision','0.00%'),('recall_10pct','Matched recall','0.00%')]:scalar('Source',col,name,fmt)
    def key(r):return '|'.join(str(r[k]) for k in ['source_case','capacity','policy','value_case'])
    profiles=[]
    for r in c['policy_profiles']:
        profiles.append(dict(profile_key=key(r),source_label=SOURCE_LABELS[r['source_case']],
                             capacity_label=f"{int(r['capacity']*100):02d}%",
                             **{k:v for k,v in r.items() if k!='reference_economics'},**r['reference_economics']))
    table('Profiles',profiles,'commercial_evaluation.json / policy_profiles; 60 mutually exclusive alternatives')
    scenarios=[dict(profile_key=key(r),**r) for r in c['scenarios']]
    table('Scenarios',scenarios,'commercial_evaluation.json / scenarios; profile + scenario grain')
    table('Scenario choices',c['config']['scenarios'],'commercial_evaluation.json / config / scenarios')
    # Scenario IDs are in the name field of the configuration.
    id_field='name' if 'name' in TABLES['Scenario choices'][0] else 'id'
    for col,name,fmt in [('contacts','Selected contacts','#,0'),('churn_units','Historical or expected churn units','#,0.0'),
                         ('break_even_conditional_save','Reference conditional break-even','0.00%'),('eligible_population','Selected population','#,0')]:scalar('Profiles',col,name,fmt)
    guard="COUNTROWS('Profiles') = 1 && COUNTROWS('Scenario choices') = 1 && COUNTROWS('Scenarios') = 1"
    for col,name,fmt in [('net_contribution_cu','Hypothetical net CU','#,0;−#,0;0'),('total_cost_cu','Assumed cost CU','#,0'),
                         ('break_even_conditional_save','Scenario conditional break-even','0.00%'),
                         ('assumed_absolute_effect','Assumed absolute effect','0.00%')]:
        measure('Scenarios',name,f"IF({guard}, SELECTEDVALUE('Scenarios'[{col}]))",fmt)
    measure('Scenarios','Selection status',f'IF({guard}, "One alternative selected | hypothetical CU", "Select one source, capacity, policy, value and scenario")','')
    # Fixed reference comparison for side-by-side evidence; every row guarded.
    lookup={r['profile_key']:r for r in profiles}
    comp=[]
    for r in scenarios:
        if r['source_case'] in ['common_baseline','common_full_union'] and r['capacity']==.1 and r['policy']=='risk_only' and r['value_case']=='uniform':
            comp.append(dict(source='Baseline' if r['source_case']=='common_baseline' else 'Full union',
                             **r,contacts=lookup[r['profile_key']]['contacts']))
    table('Comparison',comp,'commercial_evaluation.json / scenarios; matched, 10%, risk-only, uniform; 12 alternatives')
    scalar('Comparison','net_contribution_cu','Scenario net CU','#,0;−#,0;0')
    for source_name in ['Baseline','Full union']:
        measure('Comparison',source_name+' net CU',f'CALCULATE([Scenario net CU], \'Comparison\'[source] = "{source_name}")','#,0;−#,0;0')
    table('Power',p['binary_endpoint_power'],'experiment_power.json / binary_endpoint_power; 24 alternative planning designs')
    scalar('Power','total_enrolment','Planned enrolments','#,0')
    table('Commercial power',p['commercial_margin_power'],'experiment_power.json / commercial_margin_power; two alternative planning designs')
    for col,name,fmt in [('total_enrolment','Commercial enrolments','#,0'),('reference_expected_treatment_cost_cu','Expected treatment cost CU','#,0')]:scalar('Commercial power',col,name,fmt)
    grid=read('commercial_sensitivity_grid')
    table('Sensitivity grid',[dict(zip(grid['columns'],r)) for r in grid['rows']],
          'commercial_sensitivity_grid.json; fixed matched risk-only 10% uniform scope')
    scalar('Sensitivity grid','net_contribution_cu','Grid net CU','#,0')
    return id_field


def create_model(scenario_id):
    model=dict(name='Retention aggregates',culture='en-GB',defaultPowerBIDataSourceVersion='powerBI_V3',
               discourageImplicitMeasures=True,tables=[],relationships=[])
    for name,rows in TABLES.items():
        payload=base64.b64encode(json.dumps(rows,ensure_ascii=True,separators=(',',':')).encode()).decode()
        cols=[];casts=[]
        model_measures=copy.deepcopy(MEASURES[name])
        for col in rows[0]:
            vals=[r.get(col) for r in rows if r.get(col) is not None]
            v=vals[0] if vals else ''
            if isinstance(v,bool):typ,mtype='boolean','type logical'
            elif isinstance(v,int):typ,mtype='int64','Int64.Type'
            elif isinstance(v,float):typ,mtype='double','type number'
            elif isinstance(v,str):typ,mtype='string','type text'
            else:raise ValueError((name,col,type(v)))
            colname=model_column(name,col)
            cols.append(dict(name=colname,dataType=typ,sourceColumn=col,summarizeBy='none'))
            if colname!=col:
                for item in model_measures:item['expression']=item['expression'].replace('['+col+']','['+colname+']')
            casts.append('{"'+col+'", '+mtype+'}')
        expr=['let',f'    Source = Table.FromRecords(Json.Document(Binary.FromText("{payload}", BinaryEncoding.Base64))),',
              '    Typed = Table.TransformColumnTypes(Source, {'+', '.join(casts)+'})','in','    Typed']
        model['tables'].append(dict(name=name,description=LINEAGE[name],columns=cols,measures=model_measures,
                                    partitions=[dict(name=name,mode='import',source=dict(type='m',expression=expr))]))
        write(OUT/'aggregates'/(name.replace(' ','_')+'.json'),rows)
    for name,fromcol,to,tocol in [('profile_scenario','profile_key','Profiles','profile_key'),('scenario_choice','scenario','Scenario choices',scenario_id)]:
        model['relationships'].append(dict(name=name,fromTable='Scenarios',fromColumn=fromcol,toTable=to,toColumn=tocol,
                                            crossFilteringBehavior='oneDirection',fromCardinality='many',toCardinality='one'))
    write(MODEL/'model.bim',dict(name='Retention',compatibilityLevel=1606,model=model))
    write(MODEL/'definition.pbism',{'$schema':SCHEMA+'item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0'})
    write(OUT/'Retention.pbip',{'$schema':SCHEMA+'pbip/pbipProperties/1.0.0/schema.json','version':'1.0',
                              'artifacts':[{'report':{'path':'Retention.Report'}}],'settings':{'enableAutoRecovery':True}})
    write(REPORT/'definition.pbir',{'$schema':SCHEMA+'item/report/definitionProperties/2.0.0/schema.json','version':'4.0',
                                   'datasetReference':{'byPath':{'path':'../Retention.SemanticModel'}}})


def lit(v):
    return {'expr':{'Literal':{'Value':('true' if v else 'false') if isinstance(v,bool) else str(v)+'D' if isinstance(v,(float,int)) else "'"+v.replace("'","''")+"'"}}}


def color(v):return {'solid':{'color':lit(v)}}
def prop(**kwargs):return [{'properties':kwargs}]
NAVY='#142D43';TEAL='#007F82';GREY='#516777';AMBER='#AD6500'
PAGES=[]
COUNTER=0


def visual(page,kind,x,y,w,h,title='',query=None,objects=None):
    global COUNTER
    COUNTER+=1;name=f'v{COUNTER:03d}'
    v=dict(visualType=kind,drillFilterOtherVisuals=False,
           visualContainerObjects=dict(background=prop(show=lit(True),color=color('#FFFFFF'),transparency=lit(0)),
              title=prop(show=lit(bool(title)),text=lit(title),fontSize=lit(13),fontColor=color(NAVY),bold=lit(True)),
              border=prop(show=lit(False))))
    if query:v['query']={'queryState':{k:{'projections':p} for k,p in query.items()}}
    if objects:v['objects']=objects
    obj={'$schema':SCHEMA+'item/report/definition/visualContainer/2.4.0/schema.json','name':name,
         'position':dict(x=x,y=y,width=w,height=h,z=COUNTER,tabOrder=COUNTER),'visual':v}
    write(REPORT/'definition/pages'/page/'visuals'/name/'visual.json',obj)
    return obj


def model_column(t,c):
    return 'raw_'+c if c.lower() in {m['name'].lower() for m in MEASURES[t]} else c


def field(t,c,measure=False):
    if not measure:c=model_column(t,c)
    return dict(field={('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':t}},'Property':c}},
                queryRef=t+'.'+c,nativeQueryRef=c)


def text(page,txt,x,y,w,h,size=14,tone=GREY,bg=None):
    paras=[{'textRuns':[{'value':line,'textStyle':{'fontFamily':'Segoe UI','fontSize':f'{size}pt','color':tone}}]} for line in txt.split('\n')]
    v=visual(page,'textbox',x,y,w,h,objects={'general':prop(paragraphs=paras)})
    v['visual']['visualContainerObjects']['background']=prop(show=lit(bool(bg)),color=color(bg or '#FFFFFF'),transparency=lit(0))
    write(REPORT/'definition/pages'/page/'visuals'/v['name']/'visual.json',v)


def page(name,title,subtitle,tag):
    PAGES.append(name)
    write(REPORT/'definition/pages'/name/'page.json',{'$schema':SCHEMA+'item/report/definition/page/2.0.0/schema.json',
        'name':name,'displayName':name.replace('_',' '),'displayOption':'FitToPage','height':800,'width':1440,
        'objects':{'background':prop(color=color('#F1F5F8'),transparency=lit(0))}})
    text(name,'JEKS ANALYTICS  /  RETENTION DECISION SYSTEM',24,14,1100,32,11,TEAL)
    text(name,title,24,47,1390,51,27,NAVY)
    text(name,subtitle,24,107,1390,47,12,GREY)
    text(name,tag+'  •  KKBox retrospective portfolio study  •  Prepared 22 Sep 2026',24,760,1390,29,10,GREY)
    return name


def card(p,t,m,x,y,w=320,title=None):
    visual(p,'card',x,y,w,105,title or m,{'Values':[field(t,m,True)]},
           {'labels':prop(fontSize=lit(30),color=color(TEAL),labelDisplayUnits=lit(1)),
            'categoryLabels':prop(show=lit(False))})


def chart(p,kind,t,category,metrics,x,y,w,h,title):
    visual(p,kind,x,y,w,h,title,{'Category':[field(t,category)],'Y':[field(t,m,True) for m in metrics]},
           {'legend':prop(show=lit(len(metrics)>1),position=lit('Top')),
            'labels':prop(show=lit(kind!='lineChart'),fontSize=lit(10),labelDisplayUnits=lit(1)),
            'categoryAxis':prop(fontSize=lit(10)),'valueAxis':prop(fontSize=lit(10))})


def tabular(p,t,columns,metrics,x,y,w,h,title):
    visual(p,'tableEx',x,y,w,h,title,{'Values':[field(t,c) for c in columns]+[field(t,m,True) for m in metrics]},
           {'grid':prop(rowPadding=lit(8),textSize=lit(11)), 'total':prop(totals=lit(False)),
            'columnHeaders':prop(fontColor=color(NAVY),backColor=color('#EAF1F5'),fontSize=lit(11)),
            'values':prop(fontSize=lit(11))})


def create_report(scenario_id):
    write(REPORT/'definition/version.json',{'$schema':SCHEMA+'item/report/definition/versionMetadata/1.0.0/schema.json','version':'2.0.0'})
    write(REPORT/'definition/report.json',{'$schema':SCHEMA+'item/report/definition/report/2.0.0/schema.json','themeCollection':{}})
    p=page('01_Overview','Risk targeting is promising. Profitable retention is unproven.',
           'Scored 1 Feb 2017 • Mature, lead-eligible subscribers in the February expiry cohort • Full baseline source • Frozen combined model',
           'OBSERVED OUTCOMES + FROZEN PREDICTIONS')
    for i,m in enumerate(['Eligible customers','Observed churn rate','Churn captured','List precision']):card(p,'Overview',m,24+i*352,168,336)
    chart(p,'clusteredColumnChart','Capacity','capacity',['Recall','Precision'],24,290,680,320,'Capacity trade-off | full baseline population')
    text(p,'DECISION\nValidate source history, actual unit economics and treatment response before funding a controlled pilot.\n\nAt 10% capacity: 68,040 contacts capture 25,155 of 38,037 reconstructed churn outcomes. No intervention has been delivered.',730,290,684,205,17,NAVY,'#FFFFFF')
    text(p,'UNCERTAINTY\nRecall 95% interval at 10%: 65.78–66.59%. Conditional on this frozen model and month; excludes source and treatment uncertainty.',730,512,684,98,13,GREY,'#FFFFFF')
    text(p,'READ THIS FIRST  /  “Captured churn” means historical cases found in the ranked list. It does not mean customers saved.\nFeatures use pre-scoring event dates; historical ingestion availability is unverified. Outcomes follow the reconstructed expiry + 30-day definition.',24,635,1390,95,14,NAVY,'#E5EFF3')
    p=page('02_Cohorts_and_segments','Coverage and segment differences change how risk should be used.',
           'Seven scoring dates • People recur across dates • Segment checks below use the 1 Feb 2017 full-baseline holdout',
           'OBSERVED + PREDICTED • DESCRIPTIVE, NOT CAUSAL')
    tabular(p,'Cohorts',['scoring_date','split'],['Mature snapshots','Cohort churn rate'],24,170,605,360,'Mature eligible snapshots | date-specific denominators')
    tabular(p,'Segments',['label'],['Segment customers','Segment observed','Segment predicted','Segment AUC'],650,170,766,420,'Segment reliability | overlapping pairs: never add all rows')
    text(p,'77.20% of holdout customers also appear in training.\nThis evaluates a later month for a largely familiar population; it is not a new-customer-only validation.',24,548,605,158,16,NAVY,'#FFFFFF')
    text(p,'Missing records are not proof of inactivity.\nNo listening record: 133,486 customers; AUC 0.606.\nNo member record: 85,887 customers; AUC 0.616.\nReview coverage and operational fallback before piloting.',650,611,766,120,14,NAVY,'#E5EFF3')
    p=page('03_Model_reliability','The combined model ranks well, with material source uncertainty.',
           'Selection: Oct 2016 • Calibration: Dec 2016 • Frozen before final test: Feb 2017 • No holdout retuning',
           'FROZEN PREDICTIONS COMPARED WITH RECONSTRUCTED OUTCOMES')
    tabular(p,'Models',['label'],['Average precision','ROC AUC','Log loss','Brier'],24,170,675,300,'Calibrated models | same 680,401 customers')
    chart(p,'lineChart','Calibration','bin',['Predicted','Observed'],723,170,690,300,'Calibration | fixed predicted-risk bands')
    tabular(p,'Source',['source'],['Matched customers','Matched churn rate','Matched precision','Matched recall'],24,491,900,180,'Source sensitivity | fixed 10% list of 67,930 in common population')
    text(p,'SAME PEOPLE, DIFFERENT LABELS\n10,572 outcomes change on the matched population.\n22 supplied-label differences remain unresolved.\nFull baseline and matched populations differ.',946,491,469,220,14,NAVY,'#E5EFF3')
    text(p,'Lower log loss / Brier is better. Higher AUC / average precision is better. Calibration bins have unequal counts; see aggregates for denominators.\nBootstrap intervals condition on the frozen model and February month; they do not cover source-version uncertainty.',24,675,902,79,10,GREY)
    p=page('04_Commercial_sensitivity','A plausible save-rate assumption can change from surplus to loss.',
           'HYPOTHETICAL • Matched 679,309 customers • Risk-only top 10%: 67,930 contacts • Uniform contribution • Generic currency units (CU)',
           'COMMERCIAL ASSUMPTIONS • NO REALISED SAVINGS')
    text(p,'REFERENCE VALUE\n60 CU per additional retained subscriber\n90 days × assumed fee and margin',24,170,442,128,17,NAVY,'#FFFFFF')
    text(p,'REFERENCE COST\n3.50 CU per contacted subscriber\n0.50 contact + 10 × 30% redemption',490,170,442,128,17,NAVY,'#FFFFFF')
    text(p,'BREAK-EVEN\n5.83 percentage points absolute uplift\n16.27% / 24.94% conditional saves*',956,170,460,128,17,NAVY,'#FFFFFF')
    tabular(p,'Comparison',['scenario'],['Baseline net CU','Full union net CU'],24,323,895,385,'Named alternatives | CU amounts are scenario outputs, never additive')
    text(p,'*Baseline / full-union labels.\n\nAt 20% conditional saves and reference costs:\nBaseline: +54,445 CU\nFull union: −47,087 CU\n\nA value proxy changes 18.41% of the list; it is not validated customer lifetime value.',944,323,473,282,16,NAVY,'#FFFFFF')
    text(p,'Conditional saves apply to would-churn risk. Absolute uplift applies to all contacts. Include offer cost for already-renewing customers. Fixed setup cost is excluded (assumed zero).',944,624,473,100,12,GREY)
    p=page('05_Scenario_explorer','Choose one alternative to inspect its assumptions and economics.',
           'HYPOTHETICAL • Sources distinguish observed labels from predicted expected counts • Alternative cases cannot be added together',
           'INTERACTIVE ASSUMPTION EXPLORER • GENERIC CU')
    for i,(t,col,title) in enumerate([('Profiles','source_label','Source / evidence'),('Profiles','capacity_label','Capacity'),
        ('Profiles','policy','Policy'),('Profiles','value_case','Value'),('Scenario choices',scenario_id,'Scenario')]):
        visual(p,'slicer',24+i*280,170,264,171,title,{'Values':[field(t,col)]},
               {'selection':prop(singleSelect=lit(True),selectAllCheckboxEnabled=lit(False)), 'data':prop(mode=lit('Dropdown'))})
    card(p,'Profiles','Selected contacts',24,365,325)
    card(p,'Scenarios','Hypothetical net CU',377,365,325)
    card(p,'Scenarios','Assumed cost CU',731,365,325)
    card(p,'Scenarios','Scenario conditional break-even',1085,365,330)
    visual(p,'card',24,488,1391,72,'',{'Values':[field('Scenarios','Selection status',True)]},
           {'labels':prop(fontSize=lit(18),color=color(NAVY)),'categoryLabels':prop(show=lit(False))})
    tabular(p,'Scenario choices',[scenario_id,'effect_type','effect','margin','contact_cost','incentive_cost','redemption'],[],24,580,1390,152,'Selected scenario assumptions | effect is a fraction; CU costs per contact / redemption')
    p=page('06_Experiment_and_gates','Use randomisation to establish whether retention creates value.',
           'DESIGN ONLY • No assignments, offers, outcomes or realised savings • Customer-level 1:1 allocation in a frozen eligible risk pool',
           'PLANNING ASSUMPTIONS • LAUNCH GATES REMAIN OPEN')
    text(p,'PRIMARY ENDPOINT\nPaid, positive, non-refunded renewal after randomisation by frozen expiry + 30 days.\n\nAnalyse everyone as assigned. Missing outcomes stay in the denominator, with bounds and sensitivity analysis.',24,170,680,215,17,NAVY,'#FFFFFF')
    text(p,'COMMERCIAL OUTCOME\n90-day incremental contribution from frozen expiry, including all intervention costs.\n\nReadout requires full follow-up and reconciliation. Historical churn labels are only planning proxies.',728,170,687,215,17,NAVY,'#FFFFFF')
    tabular(p,'Commercial power',['target_power'],['Commercial enrolments','Expected treatment cost CU'],24,411,680,155,'Planning to clear 5.83pp margin | assumes true +8pp effect')
    text(p,'At 90% planning power: 23,564 enrolments.\nIncludes 5% outcome allowance. Binary sizing does not establish power for actual contribution or guardrails.',24,587,680,118,15,GREY,'#E5EFF3')
    text(p,'BEFORE A PILOT\n1  Resolve source history and verify operational data timing.\n2  Validate prices, margins, redemption and contribution variance.\n3  Confirm contact eligibility, consent, tracking and randomisation.\n4  Approve financial stopping rules and complaint / opt-out guardrails.\n5  Freeze analysis and follow-up before launch.',728,411,687,294,16,NAVY,'#E5EFF3')
    write(REPORT/'definition/pages/pages.json',{'$schema':SCHEMA+'item/report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':PAGES,'activePageName':PAGES[0]})


def main():
    scenario_id=prepare()
    create_model(scenario_id)
    create_report(scenario_id)
    sources=['model_evaluation','commercial_evaluation','commercial_sensitivity_grid','experiment_power','sql_build_summary']
    manifest={'status':'built; Desktop validation recorded separately','tables':{k:{'rows':len(v),'source':LINEAGE[k]} for k,v in TABLES.items()},
              'source_sha256':{f+'.json':hashlib.sha256((ROOT/'reports'/(f+'.json')).read_bytes()).hexdigest() for f in sources},
              'pages':PAGES,'visuals':COUNTER,'measures':sum(map(len,MEASURES.values())),
              'privacy':'Only aggregate published evidence; no customer identifiers or customer-level derivatives.',
              'rebuild':'python -m src.build_dashboard; refresh in Power BI Desktop'}
    write(OUT/'build_manifest.json',manifest)
    actual=json.loads((MODEL/'model.bim').read_text(encoding='utf-8'))['model']['tables']
    write(OUT/'measure_catalog.json',{t['name']:t['measures'] for t in actual if t['measures']})
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()

