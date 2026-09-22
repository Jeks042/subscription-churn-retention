# Reproduce milestone 4

This workflow reads the saved milestone 3 predictions and pre-scoring payment feature. It does not refit a model, recalibrate probabilities or repeat model selection. The [scenario contract](commercial_plan.md) and [assumptions JSON](commercial_assumptions.json) separate invented commercial inputs from observed source aggregates.

## Run locally

Use the existing Python environment and authorised private databases. The [model workflow](model_workflow.md) creates the frozen inputs.

```powershell
./.venv/Scripts/python.exe -m pip install -r requirements-lock.txt
./.venv/Scripts/python.exe -m unittest discover -s tests -v

./.venv/Scripts/python.exe src/build_commercial.py `
  --database data/analytics/analytics.duckdb `
  --model-dir data/models/v1 `
  --sensitivity-database data/models/sensitivity/source_sensitivity.duckdb `
  --output-dir data/commercial/v1

./.venv/Scripts/python.exe src/verify_commercial.py `
  --run-dir data/commercial/v1 `
  --output reports/commercial_verification.json
```

`--config` accepts an alternative assumptions JSON. Keep the published reference scenario intact and write exploratory variants to another directory with their own provenance. Changing assumptions produces a new scenario, not new empirical evidence. The common-cost reference experiment requires equal redemption assumptions across would-be churners/renewers; the core economics function also supports distinct group rates, but using them in experiment planning requires revising that plan explicitly.

## Outputs and data model

| File/object | Grain and meaning |
|---|---|
| commercial_evaluation.json / policy_profiles | 60 rows: source/risk basis × capacity × policy × value assumption; list totals and reference break-even economics |
| commercial_evaluation.json / scenarios | 360 rows: each policy profile × six named commercial scenarios |
| commercial_sensitivity_grid.json | 648 rows: two historical source cases × 324 cost/value/response combinations; common 10% risk-only list, uniform value |
| experiment_power.json | 24 binomial planning cases, two commercial-margin cases and six simulated verification cases |
| commercial_scenarios.svg | Shareable break-even and response-sensitivity chart |
| commercial_verification.json | Independent Decimal arithmetic and paired-source aggregate reconciliation |

`full_baseline` uses all 680,401 baseline customers. `common_baseline` and `common_full_union` use the same 679,309 customers, scores and contact lists with different labels. Do not sum or blend these source cases. `full_model_probability` and `common_model_probability` replace labels with summed frozen probabilities for a separate planning view; fractional churn units are expected counts, not observed people.

Risk-only ranks frozen probability; risk × value proxy ranks probability multiplied by the declared index. The latter is a post-holdout illustration and was not independently validated or chosen as a replacement. Value cases `uniform` and `payment_proxy` are competing assumptions, not extra populations. Choose one value case, one source/risk basis, one policy, one capacity and one scenario before aggregating totals.

The dimensionless payment index uses a positive-amount training median of 447 recorded source units, floor 0.5, ceiling 2.0 and neutral index 1 for nonpositive/unknown payment. No source-currency-to-CU conversion is performed. The reference 60 CU is invented retained contribution; proxy scaling assumes a relationship to past payment that the source does not verify. The financial benefit also assumes the additional retention persists for the full 90-day horizon.

## Validation and provenance

The builder checks the milestone 3 model freeze and fitted-bundle fingerprint, payment/score key ordering, unique holdout customers and exact reproduction of all existing risk-only contact/churn counts at each capacity and historical source. It records config, code, input and private-payment-array hashes. Public files contain aggregates only.

Twenty-eight tests cover the source/model pipeline plus conditional versus absolute effects, renewer incentive costs, zero/harm cases, heterogeneous value, impossible thresholds, index/tie behaviour, power inversion and binomial simulation. The independent verifier imports no economics functions from the builder: it recomputes 5,604 aggregate values with Decimal arithmetic and checks paired-source list statistics. All match within declared numerical tolerance.

The sample-size script implements an equal-arm normal approximation with pooled null and nonpooled alternative variance, consistent with the [statsmodels method](https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.power_proportions_2indep.html). Six 50,000-replicate binomial checks test actual pooled z-test rejection rates at null and alternative. The commercial-margin calculation uses a separate conservative Bernoulli variance bound; it does not assert power for the real net-contribution outcome or guardrails.

The scenario grid is not a probabilistic forecast, posterior, confidence interval or distribution of plausible company economics. Do not report the fraction of positive scenarios as a probability of success. Future campaign results would require actual random assignment and observation; see the [experiment proposal](retention_experiment.md).
