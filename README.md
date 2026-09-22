# Subscription Churn & Retention Decision System

**Status: Milestones 1–4 complete for the scoped retrospective study. SQL features, frozen model evaluation, commercial scenarios and an experiment proposal are published. Next: Power BI executive reporting and a decision memo.**

Start with the [milestone 4 findings](reports/milestone_4_findings.md) or [current progress page](reports/progress.md). With assumed 60 CU retained contribution and 3.50 CU contact/offer cost, the matched 10% list requires conditional saves of 16.27% under baseline labels versus 24.94% under refreshed labels. A 20% save assumption changes from surplus to loss across sources. The decision is further validation before a controlled pilot; no campaign or savings has been measured.

The [frozen model evaluation](reports/milestone_3_findings.md) captures 66.13% of reconstructed churn at 10% capacity on 680,401 final-test customers (36.97% precision; 6.61× lift). Source sensitivity and missing-record segments constrain interpretation.

The SQL foundation has 4,384,573 customer/date rows and 38 input features. All 28 tests pass; independent checks agree on 7,000 sampled labels, 16,100 listening values, 96 model metrics and 5,604 commercial values. See the [SQL dictionary](docs/sql_workflow.md), [model workflow](docs/model_workflow.md) and [commercial workflow](docs/commercial_workflow.md).

## Business decision

Which subscribers should a retention team prioritise under limited contact capacity, and what evidence is needed before funding an intervention?

This independent analytical case study uses the KKBox/WSDM subscription dataset to connect cohort behaviour, time-valid risk estimates, model calibration and commercial thresholds. Predicting who will leave does not establish who can be persuaded to stay.

## Analytical scope

- SQL cohort analysis and customer snapshots built from strictly pre-scoring event dates, with historical ingestion availability explicitly unproven.
- Temporal evaluation with explicit label-maturity and intervention lead-time checks.
- Simple benchmarks, calibrated probabilities and lift at realistic capacity scenarios.
- Retention economics expressed as assumptions and break-even thresholds.
- Power BI executive reporting and a controlled-intervention proposal.

## Delivery milestones

1. [Validate data access, churn definition and temporal feasibility](https://github.com/Jeks042/subscription-churn-retention/issues/1)
2. [Build reproducible SQL cohort and feature tables](https://github.com/Jeks042/subscription-churn-retention/issues/2)
3. [Evaluate temporal baselines, calibration and capacity lift](https://github.com/Jeks042/subscription-churn-retention/issues/3)
4. [Assess retention capacity and commercial thresholds](https://github.com/Jeks042/subscription-churn-retention/issues/4)
5. [Build Power BI executive report and decision memo](https://github.com/Jeks042/subscription-churn-retention/issues/5)
6. [Verify reproducibility and publish the portfolio case study](https://github.com/Jeks042/subscription-churn-retention/issues/6)

[Milestone 4](https://github.com/Jeks042/subscription-churn-retention/issues/4) is complete. The [dashboard handoff](docs/dashboard_handoff.md) carries the validated evidence and scenario definitions into milestone 5. Supplied competition labels remain diagnostic rather than interchangeable with reconstructed historical outcomes.

## Documentation

- [Validation findings and outstanding gates](reports/validation_findings.md)
- [Current progress](reports/progress.md)
- [Milestone 4 findings and break-even chart](reports/milestone_4_findings.md)
- [Commercial assumptions and workflow](docs/commercial_workflow.md)
- [Proposed retention experiment](docs/retention_experiment.md)
- [Dashboard handoff](docs/dashboard_handoff.md)
- [Milestone 3 findings and charts](reports/milestone_3_findings.md)
- [Frozen evaluation plan](docs/evaluation_plan.md)
- [Model reproduction workflow](docs/model_workflow.md)
- [Commercial handoff](docs/commercial_handoff.md)
- [Milestone 2 findings](reports/milestone_2_findings.md)
- [Model handoff](docs/model_handoff.md)
- [SQL workflow and feature dictionary](docs/sql_workflow.md)
- [Label and cutoff examples](docs/label_examples.md)
- [Reproducible validation workflow](docs/validation_workflow.md)
- [Temporal feasibility review](docs/temporal_feasibility.md)
- [Source review](docs/source_review.md)
- [Business brief](docs/business_brief.md)
- [Analytical design](docs/analytical_design.md)
- [Data access and handling](data/README.md)
- [Decision log](docs/decision_log.md)
- [Delivery backlog](docs/backlog.md)

## Repository structure

| Location | Purpose |
|---|---|
| docs/ | Business context, design and decisions |
| data/ | Access documentation; source data stays outside version control |
| sql/ | Reproducible cohort and feature queries |
| src/ | Analysis and evaluation modules |
| tests/ | Temporal, join and reconciliation checks |
| reports/ | Validated aggregate findings and decision records |
| dashboard/ | Power BI specification and public screenshots |

Tools: Python 3.13, DuckDB 1.5.5, NumPy 2.3.3, scikit-learn 1.7.2 and Matplotlib 3.10.6; Power BI reporting remains planned. Direct dependencies are pinned in requirements.txt and the recorded environment in requirements-lock.txt. Workflows run locally against authorised source files.

## Data source

[WSDM - KKBox's Churn Prediction Challenge](https://www.kaggle.com/competitions/kkbox-churn-prediction-challenge) is subject to [competition rules](https://www.kaggle.com/c/kkbox-churn-prediction-challenge/rules). Source data and customer-level derivatives are not distributed here.

## Author

Chukwujekwu Joseph Ezema · [Portfolio](https://jeks042.github.io/) · [GitHub](https://github.com/Jeks042)

Companion project: [A/B Testing & Incremental Revenue](https://github.com/Jeks042/ab-testing-incremental-revenue).
