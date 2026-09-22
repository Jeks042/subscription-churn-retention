# Reproduce the temporal model evaluation

The [evaluation plan](evaluation_plan.md) fixes the calendar, candidate families, selection criterion, calibration method, capacity fractions and sensitivity analyses. The [SQL workflow](sql_workflow.md) produces the private inputs. Obtain the competition data through your own authorised access; customer records and model artifacts are not distributed.

## Environment and execution

The recorded run uses Python 3.13. Install `requirements-lock.txt` for the exact recorded dependency environment, or `requirements.txt` for the direct dependency pins. Run from the repository root. The commands below use Windows PowerShell and the project virtual environment.

```powershell
./.venv/Scripts/python.exe -m pip install -r requirements-lock.txt
./.venv/Scripts/python.exe -m unittest discover -s tests -v

./.venv/Scripts/python.exe src/build_source_sensitivity.py `
  --source-database data/validation/validation.duckdb `
  --output-dir data/models/sensitivity

./.venv/Scripts/python.exe src/evaluate_models.py fit `
  --database data/analytics/analytics.duckdb `
  --output-dir data/models/v1

./.venv/Scripts/python.exe src/evaluate_models.py evaluate `
  --database data/analytics/analytics.duckdb `
  --output-dir data/models/v1 `
  --sensitivity-database data/models/sensitivity/source_sensitivity.duckdb `
  --log-database data/validation/original_complete/auxiliary.duckdb
```

The fitting stage reads training, October selection and December calibration data. It chooses a base model under the frozen rule and writes `model_freeze.json` before the final-evaluation command. The freeze records exact model parameters, scaler parameters, calibration coefficients, selection results, package versions and hashes. The fitted bundle remains private.

The evaluation stage verifies the freeze and feature evidence, then exclusively creates `holdout_started.json` before loading the final customer outcomes. It refuses to run again in that output directory. A failed downstream report retains the marker and private prediction/metric checkpoints; inspect and recover the report without retuning or deleting the holdout history. Independent reproduction in a new directory should reproduce the same frozen procedure and must not become a way to tune on the already-seen final test.

## What the metrics mean

- **Log loss and Brier score:** accuracy of probabilities, lower is better. Model selection uses October log loss.
- **Average precision:** the chosen summary of the precision–recall curve, labelled AP rather than trapezoidal PR area. Population prevalence is its no-skill reference.
- **ROC-AUC:** how often churn receives higher risk than non-churn, with tied scores handled explicitly.
- **Precision at capacity:** observed churn among the highest-scored contacted group.
- **Recall at capacity:** share of all observed churn captured in that group.
- **Lift at capacity:** precision divided by population churn rate. It describes targeting, not retention caused by an offer.
- **Calibration bins:** predicted versus observed risk, with row counts. December calibration-fit metrics are descriptive fitting diagnostics; February is the independent future assessment.

Capacity counts use floor(fraction × eligible customers). A SHA-256 customer-key ordering breaks score ties without looking at outcomes. The prevalence benchmark's realised targeting is one deterministic arbitrary ordering, so its realised lift can differ slightly from 1. The expectation under random ordering is 1.

The uncertainty code uses 200 seeded Poisson customer-bootstrap replicates and paired weights for the selected model versus the strongest simple benchmark by October log loss. Final-test customer IDs are unique; repeated training customers are reported separately and do not become duplicated final-test units. Intervals are conditional on fitted models and the observed month. They do not quantify model-training, future-period, source-truth or intervention-effect uncertainty.

## Sensitivity and interpretation

The duration ablation omits the three bounded-seconds totals and their three missing flags (32 remaining predictors). It keeps listening days, recency and quality flags. It assesses reliance on duration values, not whether a different cap is correct.

The source comparison reconstructs the full-union eligible cohort and evaluates the same frozen baseline predictions against both outcome definitions on the common eligible population. Cohort additions/removals are reported separately. It isolates target/population sensitivity and does not claim full alternative-source feature reconstruction or retraining. October results under a December-calibrated mapping are retrospective sensitivity diagnostics; December results use the calibrator's fitting population.

Member presence is a snapshot-quality diagnostic only, never a model input. Segment tables distinguish within-segment capacity metrics from the actual global policy's contact allocation. Seen/unseen training customers are reported to bound the generalisation claim. Feature drift compares holdout means against training means in units of training standard deviations; it is descriptive and does not establish causal change.

False positives are contacted customers who renew under the observed historical label; they are not proven wasted contacts. False negatives are observed churners outside the list; they are not proven preventable losses. Milestone 4 must state contact/offer costs, response assumptions, customer value and incremental treatment evidence before calculating commercial scenarios.

## Public evidence and private artifacts

Publish only reviewed aggregate JSON, documentation, source code, tests and SVG charts. `models.joblib`, `holdout_predictions.joblib`, source databases, customer IDs and row-level outputs remain under the ignored `data/` directory. The synthetic tests cross-check tied/weighted metrics against scikit-learn, verify budget accounting and deterministic ties, check the selection rule, and verify training-only scaling and monotone calibration.
