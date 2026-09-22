# Business brief

## Decision and stakeholders

A subscription retention lead has limited outreach capacity. Customer analytics must establish which groups show elevated churn risk, how reliable the estimates are, and what commercial assumptions would justify a controlled retention pilot. Finance needs transparent contribution economics; operations needs contact volumes; product needs actionable hypotheses.

This is an independent historical-data case study, not work commissioned by KKBox or evidence of an intervention delivered for that business.

## Questions

1. Where does renewal behaviour deteriorate across cohorts and eligible subscriber groups?
2. Do behavioural features improve future risk ranking over simple renewal/recency rules?
3. Are probabilities calibrated well enough for planning at constrained capacity?
4. What incremental retention effect would be required to cover intervention cost?
5. What experiment could establish whether an offer produces that effect?

## Decision measures

Use cohort retention/renewal with explicit denominators, log loss and Brier score for probability quality, and precision/recall/lift at 5%, 10% and 20% capacity as initial planning scenarios. Report uncertainty and prevalence alongside comparisons.

Commercial value is a scenario until intervention evidence exists. In the simplest formulation:

Expected incremental contribution per contacted subscriber = assumed absolute incremental retention probability × retained contribution over a stated horizon − expected incremental intervention cost.

Do not multiply an absolute treatment effect by churn probability again. If using a conditional save-rate assumption among would-be churners, document the additional assumptions required to translate it into an absolute effect. Costs must include outreach and expected offer redemption, including customers who would have remained anyway.

## Outputs and completion

Deliver a reproducible SQL/Python analysis, Power BI executive report, decision memo, limitations and a randomised pilot proposal. A no-go conclusion or preference for a simple baseline is a valid outcome. Completion requires evidence reconciliation, reproducibility and defensible public claims.

## Scope boundary

No production customer contact, measured causal uplift claim, invented financial results or synthetic replacement presented as observed KKBox data. Historical results cannot establish present-day subscriber behaviour.
