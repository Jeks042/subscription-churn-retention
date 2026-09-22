# Milestone 5 dashboard and decision-memo handoff

Milestones 1–4 are complete. Build the executive report from published aggregates and traceable definitions, preserving the distinction between historical findings and hypothetical commercial results. No Power BI report has been built in milestone 4.

## Suggested stakeholder flow

1. **Decision:** historical risk targeting adds value; validate source, real economics and treatment response before considering a pilot. No rollout or realised-savings claim.
2. **Risk evidence:** February population, model comparison, capacity/precision/recall, calibration and weaker missing-record segments from milestone 3.
3. **Source sensitivity:** matched baseline versus full-union labels with fixed scores/lists; show the common denominator.
4. **Commercial scenarios:** assumed value, costs, redemption, conditional saves versus absolute effects, break-even and downside/zero-effect results.
5. **Experiment:** customer randomisation, fixed paid-renewal endpoint, 90-day contribution, sample-size assumptions, guardrails and launch-readiness conditions.

## Aggregate source tables

| Source | Suggested imported table | Key/filter requirements |
|---|---|---|
| reports/model_evaluation.json | Model metrics, capacity metrics, calibration bins, segments, source sensitivity | Separate full and common populations; separate raw and calibrated metrics |
| reports/commercial_evaluation.json / policy_profiles | Commercial policy profiles | source_case + capacity + policy + value_case is unique; 60 rows |
| reports/commercial_evaluation.json / scenarios | Named economic scenarios | Above profile key + scenario; 360 rows |
| reports/commercial_evaluation.json / config | Scenario dimension | Retain effect_type, effect, margin, contact/incentive/redemption assumptions and currency |
| reports/commercial_sensitivity_grid.json | Cost/value/response grid | Use columns array to name row-array fields; fixed common population/risk-only/10%/uniform-value scope; 648 rows |
| reports/experiment_power.json | Power planning | Distinguish zero-effect tests from commercial-margin planning; assumptions are not effects observed |

Maintain one-to-many dimension relationships, avoid fact-to-fact joins that multiply scenario rows and reconcile every KPI to the reference JSON. Scenarios, capacities and source cases are alternatives: totals across them are generally meaningless. Use single-select slicers or suppress totals where more than one alternative is selected.

The cases `full_model_probability` and `common_model_probability` use summed probabilities, so churn_units can be fractional expected counts. Historical source cases use observed reconstructed labels. Use different display wording and do not combine them. The CU values are generic assumed currency units; no money symbol or company currency should be invented.

## Reference reconciliation cards

- Full baseline February: 680,401 customers; 38,037 reconstructed churn; risk-only 10% contacts 68,040 and captures 25,155 (66.13%).
- Common population: 679,309 customers; 10% contacts 67,930 in either historical source case.
- Reference uniform economics: 60 CU contribution, 3.50 CU expected cost/contact, absolute break-even 5.833 percentage points.
- Common 10% conditional break-even: baseline 16.27%, full union 24.94%.
- 20% conditional saves at reference costs: +54,445 CU baseline versus −47,087 CU full union; label both hypothetical.
- Commercial experiment planning example: 23,564 enrolments at assumed 8-point effect, 90% planning power to clear the reference commercial margin, including 5% outcome allowance. This is not power for actual net contribution or guardrails.

The decision memo should explain why source choice and unmeasured effects prevent a rollout recommendation, why the value proxy is a sensitivity assumption, and which operational/finance evidence would allow a controlled pilot. Preserve the 22 unresolved label differences and unknown historical ingestion availability. Review screenshots, interactions, filter totals and all claims before final portfolio publication in milestone 6.
