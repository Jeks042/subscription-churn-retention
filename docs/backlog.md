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

Transaction staging, cohort labels, renewal summaries, 7/30/90-day payment features and assertions are implemented. Listening features, missingness/coverage analysis and the final feature-table handoff remain in progress.

## 3. Evaluate temporal baselines, calibration and capacity lift

[Issue #3](https://github.com/Jeks042/subscription-churn-retention/issues/3) · Depends on: #2

Assess whether risk scoring improves retention prioritisation on future observations.

Acceptance: A frozen model is evaluated once on the final holdout, with benchmark comparisons and uncertainty. Weak results are reported honestly and may justify retaining a simple rule.

## 4. Assess retention capacity and commercial thresholds

[Issue #4](https://github.com/Jeks042/subscription-churn-retention/issues/4) · Depends on: #3

Translate risk estimates into transparent decision scenarios without claiming causal retention lift.

Acceptance: All commercial outputs are labelled scenarios. Predicted churn is never presented as persuadability, realised savings or measured intervention ROI.

## 5. Build Power BI executive report and decision memo

[Issue #5](https://github.com/Jeks042/subscription-churn-retention/issues/5) · Depends on: #4

Create a stakeholder-ready account of risk, evidence and retention choices.

Acceptance: A stakeholder can understand what decision is supported, what remains uncertain and what evidence a retention intervention still needs. Dashboard numbers match source analysis tables.

## 6. Verify reproducibility and publish the portfolio case study

[Issue #6](https://github.com/Jeks042/subscription-churn-retention/issues/6) · Depends on: #5

Complete a defensible flagship case study with consistent public evidence.

Acceptance: Repository, portfolio, dashboard and CV agree; another authorised analyst can reproduce the results. No LinkedIn posting or CV claims before final review.
