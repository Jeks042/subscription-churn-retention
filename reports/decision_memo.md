# Decision memo — subscription retention

**22 September 2026 · Independent retrospective case study · Recommendation: validate the remaining launch gates before a controlled pilot.**

The analysis supports prioritising subscribers for a test of retention intervention. It does not establish that intervention will save customers or earn incremental contribution. No campaign has been executed.

## Evidence supporting the next decision

The frozen combined model captures 25,155 of 38,037 reconstructed churn outcomes by selecting 68,040 of 680,401 eligible February 2017 customers: 66.13% recall and 36.97% precision. The conditional 95% bootstrap interval for recall is 65.78–66.59%. Average precision is 0.508, compared with 0.275 for the renewal rule. These are historical ranking results, not treatment effects. [Model findings](milestone_3_findings.md).

Coverage matters. Customers without listening or member records have weaker ranking performance. About 77.20% of holdout customers also appear in training. This is a later-month validation, not evidence of equally strong performance for every new customer or segment.

Source versions materially affect the decision. On the same 679,309 customers and fixed 67,930-contact list, observed list precision changes from 35.85% under baseline labels to 23.39% under full-union labels. Event dates do not establish historical ingestion availability, and 22 supplied-label disagreements remain unexplained.

## Economics remain assumptions

With an assumed 60 generic currency units (CU) of 90-day retained contribution and 3.50 CU of expected variable cost per contact, absolute break-even is 5.83 percentage points. Conditional break-even is 16.27% of would-be churners under matched baseline labels and 24.94% under matched full-union labels.

At an assumed 20% conditional save rate, the matched risk-only 10% list produces **+54,445 CU** under baseline labels and **−47,087 CU** under full-union labels. At zero effect both cases lose **237,755 CU**. These are alternative scenarios; they must never be summed or described as realised savings. Prices, margins, redemption and zero fixed setup cost are assumptions. [Commercial findings](milestone_4_findings.md).

Do not promote the payment-value policy from these results. Its value index is unverified, 23.05% of the matched 10% list has unknown payment value, and its apparent gains depend on the proxy assumption. The comparison was performed after holdout evaluation and is not independent validation of a new policy.

## Evidence required before committing funds

| Proposed owner | Required evidence |
|---|---|
| Data engineering / analytics | Resolve source-history policy, verify operational timing and reconstruct a prospectively available eligible population. |
| Finance | Actual contribution horizon, fees, margins, incentive/redemption costs, fixed costs and variance of customer contribution. |
| CRM / operations | Valid contact eligibility and consent, suppression rules, assignment integrity and complete offer/cost tracking. |
| Experiment owner | Pre-registered randomisation, paid-renewal endpoint, intention-to-treat analysis, missing-outcome bounds, stopping rules and approved guardrails. |

The proposed experiment randomises customers 1:1 in a frozen eligible risk pool. Paid renewal is measured after randomisation by frozen expiry + 30 days; commercial contribution uses a separate 90-day window. A planning example requires 23,564 enrolments for 90% power to clear the reference 5.83-point commercial margin **if the true absolute effect is 8 points**. This strong effect is an assumption, not a forecast. Binary endpoint sizing does not establish power for actual contribution, complaints or opt-outs. [Experiment proposal](../docs/retention_experiment.md).

## Report and methods

The [Power BI project](../dashboard/README.md) presents the overview, cohort/segment checks, model reliability, commercial comparison, guarded scenario explorer and experiment gates. All imported records are published aggregates. The model, preprocessing and calibration remain frozen; this reporting milestone fits no new model.

For detailed definitions and reproducibility see the [analytical design](../docs/analytical_design.md), [SQL workflow](../docs/sql_workflow.md), [model workflow](../docs/model_workflow.md), [commercial workflow](../docs/commercial_workflow.md), and [dashboard workflow](../docs/dashboard_workflow.md).
