# Subscription Churn & Retention Decision System

**Status: source validation in progress. Access confirmed; initial audits complete. Model fitting remains on hold pending label and temporal reconciliation.**

## Business decision

Which subscribers should a retention team prioritise under limited contact capacity, and what evidence is needed before funding an intervention?

This independent analytical case study uses the KKBox/WSDM subscription dataset to connect cohort behaviour, time-valid risk estimates, model calibration and commercial thresholds. Predicting who will leave does not establish who can be persuaded to stay.

## Analytical scope

- SQL cohort analysis and customer snapshots built only from information available at scoring.
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

Start with [Milestone 1](https://github.com/Jeks042/subscription-churn-retention/issues/1). Data access, file coverage and label reconstruction must be established before fitting models.

## Documentation

- [Validation findings and outstanding gates](reports/validation_findings.md)
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

Tools: Python 3.13 and DuckDB 1.5.5 for source validation; Power BI planned for reporting. Dependencies are pinned in requirements.txt. The validation workflow runs locally against authorised source files; modelling and dashboards are not yet implemented.

## Data source

[WSDM - KKBox's Churn Prediction Challenge](https://www.kaggle.com/competitions/kkbox-churn-prediction-challenge) is subject to [competition rules](https://www.kaggle.com/c/kkbox-churn-prediction-challenge/rules). Source data and customer-level derivatives are not distributed here.

## Author

Chukwujekwu Joseph Ezema · [Portfolio](https://jeks042.github.io/) · [GitHub](https://github.com/Jeks042)

Companion project: [A/B Testing & Incremental Revenue](https://github.com/Jeks042/ab-testing-incremental-revenue).
