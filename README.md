# Subscription Churn & Retention Decision System

**Decision: validate operational data and economics before funding a controlled retention pilot.**

This independent KKBox portfolio study connects reproducible SQL, temporal risk evaluation, retention economics and Power BI reporting. All six delivery milestones are complete for the scoped retrospective study.

[Read the portfolio case study](https://jeks042.github.io/subscription-churn-retention.html) · [View the dashboard](reports/milestone_5_findings.md) · [Read the decision memo](reports/decision_memo.md) · [Reproduce the analysis](docs/reproduction_workflow.md)

## Validated result

- **4,384,573 customer/date rows and 38 predictors**, built from past events across seven scoring dates.
- **680,401 final-test customers:** the selected model captures **66.13%** of reconstructed churn at 10% capacity, with **36.97% precision** and **6.61× lift**.
- **Source-sensitive economics:** on the matched population, the required conditional save rate rises from **16.27% to 24.94%** under alternative labels, assuming 60 CU retained contribution and 3.50 CU contact/offer cost. A 20% save scenario changes from +54,445 CU to −47,087 CU.
- **Fresh reproduction completed with documented numerical variation:** 28 tests, 2,196 dashboard checks and 75 Microsoft schema validations, with independent checks and a review of refit differences. See the [measured milestone 6 record](reports/milestone_6_findings.md).

The model's full-cohort list has 68,040 contacts; commercial source comparisons use 67,930 contacts among common customers. Commercial amounts are illustrative generic currency units. No retention campaign, realised savings or causal treatment effect has been measured.

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

All six milestones are complete within the declared retrospective scope. Supplied competition labels remain diagnostic rather than interchangeable with reconstructed historical outcomes. Historical ingestion availability and treatment responsiveness remain unverified.

## Documentation

- [Final reproduction and publication record](reports/milestone_6_findings.md)
- [Full reproduction workflow](docs/reproduction_workflow.md)
- [CV/project wording and LinkedIn draft](docs/portfolio_wording.md)

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

Tools: Python 3.13, DuckDB 1.5.5, NumPy 2.3.3, scikit-learn 1.7.2, Matplotlib 3.10.6 and Power BI Desktop 2.157.1354.0. Direct dependencies are pinned in requirements.txt, optional report validation in requirements-dashboard.txt, and the analysis environment in requirements-lock.txt. Workflows run locally against authorised source files; the dashboard uses public aggregates only.

## Data source

[WSDM - KKBox's Churn Prediction Challenge](https://www.kaggle.com/competitions/kkbox-churn-prediction-challenge) is subject to [competition rules](https://www.kaggle.com/c/kkbox-churn-prediction-challenge/rules). Source data and customer-level derivatives are not distributed here.

## Author

Chukwujekwu Joseph Ezema · [Portfolio](https://jeks042.github.io/) · [GitHub](https://github.com/Jeks042)

Companion project: [A/B Testing & Incremental Revenue](https://github.com/Jeks042/ab-testing-incremental-revenue).
