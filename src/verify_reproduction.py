"""Compare independent output values while keeping provenance differences explicit."""
from pathlib import Path
import argparse, json, math
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run-dir',type=Path,required=True)
parser.add_argument('--reference-dir',type=Path,default=Path(__file__).resolve().parents[1]/'reports')
args=parser.parse_args()
run=args.run_dir
pairs={
 'original_log_audit.json':'logs/auxiliary_audit.json',
 'sql_build_summary.json':'analytics/sql_build_summary.json',
 'listening_build_summary.json':'analytics/listening_build_summary.json',
 'sql_reconstruction_check.json':'label_check.json',
 'listening_feature_check.json':'listening_check.json',
 'model_source_sensitivity_build.json':'sensitivity/source_sensitivity_build.json',
 'model_freeze.json':'models/model_freeze.json',
 'model_evaluation.json':'models/model_evaluation.json',
 'model_metric_check.json':'model_metric_check.json',
 'commercial_evaluation.json':'commercial/commercial_evaluation.json',
 'commercial_sensitivity_grid.json':'commercial/commercial_sensitivity_grid.json',
 'experiment_power.json':'commercial/experiment_power.json',
 'commercial_verification.json':'commercial_check.json',
}
provenance={'frozen_utc','audited_cache_sha256','audit_report_sha256','feature_manifest_sha256','model_bundle_sha256','freeze_sha256','holdout_marker_sha256','sensitivity_build_report_sha256','input_sha256','python'}
failures=[];omitted=[];counts={'numeric':0,'other':0};maxdelta=0
def compare(a,b,path):
 global maxdelta
 if isinstance(a,dict) and isinstance(b,dict):
  if a.keys()!=b.keys(): failures.append({'path':path,'reason':'keys differ'})
  for k in sorted(a.keys()&b.keys()):
   if k in provenance:
    omitted.append(path+'/'+k);continue
   compare(a[k],b[k],path+'/'+k)
 elif isinstance(a,list) and isinstance(b,list):
  if len(a)!=len(b): failures.append({'path':path,'reason':'length differs'})
  for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i))
 elif isinstance(a,(float,int)) and not isinstance(a,bool) and isinstance(b,(float,int)):
  counts['numeric']+=1;maxdelta=max(maxdelta,abs(a-b))
  equal=(a==b) if isinstance(a,int) and isinstance(b,int) else math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-8)
  if not equal:failures.append({'path':path,'expected':a,'actual':b})
 else:
  counts['other']+=1
  if a!=b:failures.append({'path':path,'expected':a,'actual':b})
for public,private in pairs.items():
 compare(json.loads((args.reference_dir/public).read_text(encoding='utf-8')),json.loads((run/private).read_text(encoding='utf-8')),public)
result=dict(status='passed' if not failures else 'differences_require_review',files_compared=len(pairs),values_checked=counts,integer_rule='exact',float_relative_tolerance=1e-8,float_absolute_tolerance=1e-8,max_absolute_numeric_difference=maxdelta,provenance_fields_excluded=omitted,differences=failures)
(run/'comparison.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='differences'},indent=2))
print(f'{len(failures)} differences; full details saved in {run / "comparison.json"}')
raise SystemExit(bool(failures))
