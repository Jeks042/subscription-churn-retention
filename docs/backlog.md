# Delivery backlog

The linked GitHub issues are the current execution record. Complete each acceptance gate before its dependent work.

## 1. Validate data access, churn definition and temporal feasibility

[Issue #1](https://github.com/Jeks042/subscription-churn-retention/issues/1) · Depends on: None

Establish whether the KKBox source supports a defensible subscription decision.

Acceptance: A reviewer can reproduce the source inventory, follow a renewal/cancellation example and audit the time boundaries. No model fitting until the label and temporal design are defensible.

## 2. Build reproducible SQL cohort and feature tables

[Issue #2](https://github.com/Jeks042/subscription-churn-retention/issues/2) · Depends on: #1

Build the analytical foundation for retention diagnosis and prediction.

Acceptance: Features reproduce from the recorded source version; all feature events precede scoring; SQL joins reconcile to the eligible population. Historical ingestion availability cannot be verified in this source and must remain an explicit retrospective-study limitation.

Completed: transaction/listening staging and aggregation, cohort labels, renewal summaries, 7/30/90-day features, coverage/missingness analysis, assertions, training-only preprocessing and the final feature-table handoff. See [milestone 2 findings](../reports/milestone_2_findings.md).

## 3. Evaluate temporal baselines, calibration and capacity lift

[Issue #3](https://github.com/Jeks042/subscription-churn-retention/issues/3) · Depends on: #2

Assess whether risk scoring improves retention prioritisation on future observations.

Acceptance: A frozen model is evaluated once on the final holdout, with benchmark comparisons and uncertainty. Weak results are reported honestly and may justify retaining a simple rule.

Completed: frozen baseline selection and calibration, one-shot February evaluation, customer-bootstrap intervals, capacity/segment/drift diagnostics, duration ablation and fixed-score source-label sensitivity. All 21 tests and an independent 96-value metric check pass. See [milestone 3 findings](../reports/milestone_3_findings.md). Full alternative-source retraining and operational claims are outside this declared retrospective scope.

## 4. Assess retention capacity and commercial thresholds

[Issue #4](https://github.com/Jeks042/subscription-churn-retention/issues/4) · Depends on: #3

Translate risk estimates into transparent decision scenarios without claiming causal retention lift.

Acceptance: All commercial outputs are labelled scenarios. Predicted churn is never presented as persuadability, realised savings or measured intervention ROI.

Completed: risk-only versus payment-proxy policy scenarios, explicit 90-day CU economics, conditional/absolute break-even, 360 named scenarios, 648 sensitivity rows and a customer-randomised experiment proposal with 24 conventional power cases plus commercial-threshold planning. All 28 tests pass and 5,604 independently recalculated commercial values agree. Decision: further validation before a controlled pilot. See [milestone 4 findings](../reports/milestone_4_findings.md).

## 5. Build Power BI executive report and decision memo

[Issue #5](https://github.com/Jeks042/subscription-churn-retention/issues/5) · Depends on: #4

Create a stakeholder-ready account of risk, evidence and retention choices.

Acceptance: A stakeholder can understand what decision is supported, what remains uncertain and what evidence a retention intervention still needs. Dashboard numbers match source analysis tables.

Milestone 5 is complete: six-page portable Power BI report, 14 aggregate tables, 51 DAX measures, Desktop review and screenshots, plus executive decision memo. All 28 tests, 2,196 dashboard checks and 75 Microsoft schema checks pass. See [milestone 5 findings](../reports/milestone_5_findings.md).

## 6. Verify reproducibility and publish the portfolio case study

[Issue #6](https://github.com/Jeks042/subscription-churn-retention/issues/6) · Depends on: #5

Complete a defensible flagship case study with consistent public evidence.

Acceptance: Repository, case study and dashboard agree; another authorised analyst can reproduce and review the results.

Completed: fresh source-to-commercial reproduction with measured runtime/resources, output reconciliation, public-content and claims review, final README and live portfolio case study. See [milestone 6](../reports/milestone_6_findings.md).
