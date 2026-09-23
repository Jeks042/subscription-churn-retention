# Full local reproduction

Use authorised KKBox files under the competition agreement. The repository distributes code and aggregate evidence; it does not distribute source files, customer extracts or fitted model bundles.

## Environment and inputs

Use Python 3.13 and a fresh checkout. `.gitattributes` preserves committed bytes because the evidence manifests hash code, SQL and JSON files; automatic line-ending conversion would invalidate those hashes.

Required input directory: `train.csv`, `train_v2.csv`, `transactions.csv`, `transactions_v2.csv` and `members_v3.csv`. Supply the complete original `user_logs.csv` separately; its uncompressed size must be 30,514,081,415 bytes. The source hashes in the published audits identify the expected versions. The refreshed listening file is a diagnostic source from milestone 1 and is not used in the baseline feature pipeline.

PowerShell, from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt -r requirements-dashboard.txt
.\.venv\Scripts\python.exe src/reproduce.py --input-dir data/raw --logs data/raw/original_logs_complete/user_logs.csv --output-dir data/reproduction/new_run
.\.venv\Scripts\python.exe src/verify_reproduction.py --run-dir data/reproduction/new_run
```

The output directory must not already exist. Each run retains private logs and new databases/model artifacts under that directory. Do not point it at the original frozen model run. Do not upload the output directory to GitHub.

On other platforms use the environment's Python executable in place of the Windows path. The measured milestone 6 run is Windows-specific; this is not a claim that other operating systems have been tested.

## What the runner does

1. Audit supplied labels, transactions, members and the complete original listening history.
2. Rebuild transaction staging, seven historical cohorts, past-event listening features and the 38-predictor table.
3. Independently verify 7,000 sampled labels and 16,100 listening-feature values.
4. Reconstruct alternative-source labels on selection, calibration and holdout dates.
5. Repeat the already-frozen fitting procedure in a new directory, then evaluate it once. No choices are changed in response to the final-test result.
6. Independently verify model metrics, rebuild commercial scenarios and check their arithmetic.
7. Run the synthetic tests and validate the published Power BI aggregates, bindings and Microsoft schemas.

The runner supports `--code-root` for testing a separate published checkout. It records each stage's exit status, wall time, installed packages and, on Windows, the sampled peak working set of the direct stage process. A Windows virtual environment may launch a child interpreter, so that direct-process counter can measure only the launcher; it must not be used for capacity planning. Milestone 6 used a separate process-tree monitor for its reported memory observation. Output bytes exclude raw inputs, the environment and temporary spill files.

The dashboard check validates the committed report. It deliberately does not regenerate or replace the author's final report layout or screenshots. Power BI Desktop refresh and slicer behaviour were checked separately in [milestone 5](../reports/milestone_5_findings.md). The Microsoft schema check requires internet access.

## Reading the results

`execution.json` is the stage record; a nonzero stage exits the runner immediately. Inspect the corresponding private log before retrying. The one-shot model evaluator refuses to overwrite an evaluated run. Use a fresh run directory for a new complete attempt.

The second command writes `comparison.json` in the private run directory and exits nonzero if the rebuilt evidence differs. It compares 13 reports: integer counts exactly, floating-point values with absolute and relative tolerance `1e-8`, and other retained values exactly. Timestamps, database file hashes and newly serialized model-bundle hashes can differ between independent runs; excluded provenance fields are listed explicitly. These are not reasons to relax output checks. Keep the original published freeze and final evaluation as the historical decision record.

In the measured milestone 6 run, all pipeline checks passed but this strict comparison returned nonzero. Tiny differences in three duration sums were accompanied by a slightly different optimiser stopping point, small score changes and individual records crossing some diagnostic boundaries. The detailed review confirmed unchanged headline capacity counts, all 12 matched 10% risk-only/uniform scenario dictionaries and every scenario profit sign. That run is accepted as analytical reproduction with documented numerical variation, not bit-for-bit model or customer-list reproduction. Do not automatically waive differences in a future run: review the generated report against the published bounds and preserve any new discrepancy.

See the [milestone 6 record](../reports/milestone_6_findings.md) for the actual measured run and its limits. Detailed stage contracts remain in the [SQL](sql_workflow.md), [model](model_workflow.md), [commercial](commercial_workflow.md) and [dashboard](dashboard_workflow.md) workflows.
