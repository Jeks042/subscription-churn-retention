# Milestone 4 scenario contract

Declared before calculating the value-proxy policy results on 22 September 2026. February outcomes have already been seen in milestone 3: these policy comparisons are retrospective scenario illustrations, not a new independent validation. No model, probability calibration, source policy or capacity is retuned.

## Units and assumptions

All money is **generic scenario currency units (CU)**, not KKBox prices, GBP, TWD or an FX conversion. The reference subscription fee is assumed to be 40 CU per 30-day month. A 90-day retained-service horizon and 50% contribution margin imply 60 CU of incremental contribution per additional retained subscriber **before intervention cost**. Sensitivity margins of 30% and 70% imply 36 and 84 CU. This assumes the extra retention persists through that horizon; it is not measured lifetime value.

Reference outreach cost is 0.50 CU per assigned contact, incentive cost 10 CU per redemption and redemption probability 30% across contacted customers. Both would-be churners and would-be renewers can redeem. Expected cost is therefore 3.50 CU per contact, including incentives for customers who would stay anyway. Fixed setup cost is excluded from the reference and must be entered separately if present. Scenario financial values are incremental to no additional outreach; tax, financing and FX are outside scope.

The treatment concept is one reminder plus an optional retention offer. Response and redemption assumptions are not estimates and are not inferred from model scores. A reminder can affect behaviour without redemption; for an offer-only mechanism, conditional saves exceeding would-be-churner redemption would require a different coherent assumption set.

## Policy and value definitions

- Risk-only: frozen combined-model probability, with the existing SHA-256 tie breaker.
- Risk × value proxy: that probability multiplied by a dimensionless past-payment index. Divide positive pre-scoring 90-day recorded subscription amounts by the median positive training amount; clip the ratio to [0.5, 2]. Nonpositive/no-payment amounts receive neutral index 1 and an explicit unknown-value flag. No outcome enters the index or its training median.
- Compare both policies under uniform value and proxy-scaled value. The proxy scenario assumes future contribution is proportional to past recorded payments; uniform value checks what happens when that assumption is discarded. Report displacement, overlap, unknown-value allocation and capped-index counts. Do not call the proxy measured margin or LTV.
- Keep 5%, 10%, 20% list sizes and deterministic ties. Use the full baseline population and paired baseline/full-union labels on the common eligible population. The common-population contact lists must be identical across source-label cases.

## Equations

For a chosen list, let q_i denote a source-specific churn scenario (historical labels for retrospective illustrations or the frozen probability for a model-based planning case), V_i assumed retained contribution, c contact cost, d cost per redeemed offer, r_C/r_R redemption probabilities for would-be churners/renewers, and F fixed cost.

Expected incremental cost = N c + d sum[q_i r_C + (1-q_i) r_R] + F.

Under a **conditional save fraction s among would-be churners**, assuming no retention effect on would-be renewers and no harm: additional retained = s sum(q_i); benefit = s sum(q_i V_i). Break-even s = total cost / sum(q_i V_i).

Under a **uniform absolute retention change delta per contacted customer**: additional retained = N delta; benefit = delta sum(V_i). Do not multiply this absolute effect by churn risk again. Break-even delta = total cost / sum(V_i). A uniform positive delta cannot exceed the selected group's available churn probability, and a negative delta cannot exceed its baseline renewal probability. Per-customer feasibility is not established by group averages.

The conditional and absolute break-even calculations have different value-weighting assumptions when V varies. Their simple conversion delta=q s is valid for uniform V; heterogeneous effects/value can invalidate equivalence. Negative-effect stress tests use the absolute formulation. No value is assigned to a save beyond the declared horizon.

## Prespecified outputs

Six scenarios: a one-percentage-point adverse absolute effect; a low-response/high-cost downside; zero effect; 10% conditional saves at reference costs; 20% conditional saves at reference costs; and optimistic value/cost/response assumptions. Show both historical-label and model-probability planning cases explicitly.

The detailed sensitivity grid varies contribution margin {30%,50%,70%}, contact cost {0.25,0.50,1}, incentive cost {0,5,10}, redemption {10%,30%,60%}, and conditional save fraction {0,5%,10%,20%}, for the common-population risk-only 10% list under uniform value and each source. There are 324 parameter combinations per source (648 rows). These are alternatives, not a probability distribution or confidence interval.

Publish only aggregate policy/scenario tables, a break-even plot, inputs and validation evidence. Private saved scores and customer-level value indexes remain under data/. Preserve the previous frozen model artifacts.

## Experiment planning

Propose a customer-randomised 1:1 reminder-plus-offer versus business-as-usual experiment within a prospectively fixed eligible risk list. Use a paid-renewal endpoint with a deadline based on preassignment expiry, intention-to-treat analysis, one enrollment per customer, fixed analysis time, financial and customer-experience guardrails. Costs and operational outcomes must be validated before launching.

Report two-sided 5% significance, 80%/90% power and absolute retention effects of 1, 2, 3 and 6 percentage points under both historical risk proxies plus a conservative 50% control rate. Also size a conservative commercial-margin test: true absolute effect assumed 8 points, minimum worthwhile effect 3.50/60 = 5.833 points, using a 95% lower confidence bound and worst-case Bernoulli variance. Include 5% missing-outcome capacity allowance without treating incomplete outcomes as permission to exclude randomised customers. No experiment or real outreach is executed.
