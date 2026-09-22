# Milestone 4 commercial handoff

Milestone 3 is complete. Its [findings](../reports/milestone_3_findings.md) and [aggregate evaluation](../reports/model_evaluation.json) are the starting evidence. The selected combined logistic regression was frozen before final-test evaluation; do not retune on February outcomes.

## Capacity evidence

| Scenario | Contacts | Baseline observed churn captured | Contacted observed renewers |
|---|---:|---:|---:|
| 5% | 34,020 | 19,557 | 14,463 |
| 10% | 68,040 | 25,155 | 42,885 |
| 20% | 136,080 | 30,031 | 106,049 |

These are historical classifications, not saves or treatment-response predictions. Contact fractions are scenarios, not approved budgets. Costs can apply to everyone contacted, including customers who would renew anyway.

## Carry uncertainty into economics

- Baseline final-test mean predicted risk is 5.16% versus 5.59% observed churn. Do not assume perfect calibration.
- On 679,309 common eligible customers, changing source labels lowers 10%-capacity precision from 35.85% to 23.39%, while the contact list remains fixed. Show separate source cases rather than blending their outcomes or selecting the more profitable version.
- The source-sensitivity evaluation holds baseline features and scores fixed; alternative-source feature reconstruction/retraining has not been done. Neither release is verified operational truth.
- No-listening-record and missing-member segments have weak discrimination relative to the overall model. Preserve the populations and show exposure differences; absence of records is not established inactivity.
- Customer-bootstrap intervals condition on the fitted model and one month. Source uncertainty and future-period variation are not inside those intervals.

## Decisions to make in milestone 4

Define a contribution-value horizon, margin, contact cost, incentive/redemption assumptions and consistent currency units. Distinguish a conditional save rate among would-be churners from an absolute incremental retention probability. Use downside, zero-effect and optimistic assumptions; derive break-even conditions rather than declaring realised ROI.

Assess whether a risk-plus-value policy is supportable by historically available value information. Recorded payments are not automatically future contribution margin or lifetime value. If adequate value evidence is absent, use explicit scenarios and state the limitation.

Design a randomised treatment/control retention study with customer-level assignment, eligibility, capacity, primary outcome, follow-up, guardrails and power assumptions. Risk identifies observed historical churn propensity; only incremental evidence can establish whether contacting a customer changes the outcome. The 22 unresolved supplied-label differences and missing ingestion timestamps remain explicit study limits.

No commercial costs, treatment effects, actual campaign outcomes or savings have been established by milestone 3.
