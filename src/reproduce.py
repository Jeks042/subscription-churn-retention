"""Run the published workflow in a new output directory; never reuse fitted runs."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--code-root', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--input-dir', type=Path, required=True)
    p.add_argument('--logs', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    a = p.parse_args()
    root, raw, logs, out = [x.resolve() for x in (a.code_root, a.input_dir, a.logs, a.output_dir)]
    out.mkdir(parents=True, exist_ok=False)
    val, aux, db, model, sens, commercial = [out/x for x in ('validation', 'logs', 'analytics', 'models', 'sensitivity', 'commercial')]
    val.mkdir()
    stages = [
        ('labels', ['src/audit_labels.py', '--input-dir', raw, '--output', val/'label_audit.json']),
        ('transactions', ['src/audit_transactions.py', '--input-dir', raw, '--output-dir', val]),
        ('listening_audit', ['src/audit_auxiliary.py', '--members', raw/'members_v3.csv', '--logs', logs, '--expected-log-bytes', '30514081415', '--output-dir', aux]),
        ('sql', ['src/build_sql.py', '--input-dir', raw, '--output-dir', db]),
        ('listening_features', ['src/build_listening.py', '--database', db/'analytics.duckdb', '--log-database', aux/'auxiliary.duckdb', '--audit-report', aux/'auxiliary_audit.json', '--output-dir', db]),
        ('label_check', ['src/verify_sql_reconstruction.py', '--database', db/'analytics.duckdb', '--output', out/'label_check.json']),
        ('listening_check', ['src/verify_listening_features.py', '--database', db/'analytics.duckdb', '--log-database', aux/'auxiliary.duckdb', '--output', out/'listening_check.json']),
        ('source_sensitivity', ['src/build_source_sensitivity.py', '--source-database', val/'validation.duckdb', '--output-dir', sens]),
        ('fit', ['src/evaluate_models.py', 'fit', '--database', db/'analytics.duckdb', '--output-dir', model]),
        ('evaluate', ['src/evaluate_models.py', 'evaluate', '--database', db/'analytics.duckdb', '--output-dir', model, '--sensitivity-database', sens/'source_sensitivity.duckdb', '--log-database', aux/'auxiliary.duckdb']),
        ('model_check', ['src/verify_model_metrics.py', '--run-dir', model, '--output', out/'model_metric_check.json']),
        ('commercial', ['src/build_commercial.py', '--database', db/'analytics.duckdb', '--model-dir', model, '--sensitivity-database', sens/'source_sensitivity.duckdb', '--output-dir', commercial]),
        ('commercial_check', ['src/verify_commercial.py', '--run-dir', commercial, '--output', out/'commercial_check.json']),
        ('tests', ['-m', 'unittest', 'discover', '-s', 'tests', '-v']),
        ('dashboard', ['-m', 'src.verify_dashboard', '--schemas']),
    ]
    # Windows peak working set covers the direct stage process, not the entire OS.
    class Counters(ctypes.Structure):
        _fields_ = [('cb', ctypes.c_ulong), ('PageFaultCount', ctypes.c_ulong)] + [(x, ctypes.c_size_t) for x in ('PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
    started = time.monotonic()
    report = dict(started_utc=datetime.now(timezone.utc).isoformat(), python=platform.python_version(), platform=platform.platform(), logical_cpus=os.cpu_count(), free_disk_before_bytes=shutil.disk_usage(out).free, status='running', stages=[])
    report['environment'] = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True).splitlines()
    def save():
        report['elapsed_seconds'] = round(time.monotonic()-started, 2)
        (out/'execution.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    for name, args in stages:
        print('START '+name, flush=True)
        t = time.monotonic()
        with (out/(name+'.log')).open('w', encoding='utf-8') as log:
            process = subprocess.Popen([sys.executable, '-u', *map(str, args)], cwd=root, stdout=log, stderr=subprocess.STDOUT)
            peak = 0
            while process.poll() is None:
                if os.name == 'nt':
                    counters = Counters(); counters.cb = ctypes.sizeof(counters)
                    if ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.c_void_p(int(process._handle)), ctypes.byref(counters), counters.cb):
                        peak = max(peak, counters.PeakWorkingSetSize)
                time.sleep(1)
        row = dict(stage=name, seconds=round(time.monotonic()-t,2), exit_code=process.returncode, peak_process_working_set_bytes=peak or None)
        report['stages'].append(row)
        if process.returncode:
            report['status']='failed'; save()
            raise SystemExit('Failed '+name+'; inspect the private stage log')
        save(); print('PASS '+name+' '+str(row['seconds'])+'s', flush=True)
    report['status']='passed'
    report['output_bytes']=sum(x.stat().st_size for x in out.rglob('*') if x.is_file())
    report['free_disk_after_bytes']=shutil.disk_usage(out).free
    save()


if __name__ == '__main__':
    main()
