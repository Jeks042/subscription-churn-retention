# Portfolio, CV and LinkedIn wording

Prepared 23 September 2026. These are evidence-based drafts for an independent portfolio project, not employment or client-delivery claims. No LinkedIn post has been published and no personal CV has been changed.

## CV project entry

**Subscription Churn & Retention Decision System — Independent portfolio project**  
SQL (DuckDB), Python, Power BI | September 2026

- Built a reproducible subscription analytics workflow with 4.38 million customer/date rows, 38 past-event predictors and independent checks of cohort labels, listening features and commercial outputs.
- Evaluated temporally separated churn models on 680,401 final-test customers; the selected model captured 66.13% of reconstructed churn at 10% contact capacity, with 36.97% precision and 6.61× lift.
- Translated risk ranking into a six-page Power BI decision report, source-sensitive break-even economics and a proposed randomised retention experiment; identified a 16.27–24.94% conditional save threshold under explicit illustrative assumptions.

Portfolio: https://jeks042.github.io/subscription-churn-retention.html  
Repository: https://github.com/Jeks042/subscription-churn-retention

## Concise LinkedIn draft

My latest portfolio project asks two connected questions: who is at risk of leaving, and what evidence would justify spending money to retain them?

Using the historical KKBox subscription dataset, I built SQL cohorts and past-event features, evaluated models across time, and created a Power BI decision report.

On 680,401 final-test customers, the selected model captured 66.13% of reconstructed churn within a 10% contact list. But the commercial review was just as important: changing the source definition raised the illustrative break-even save rate from 16.27% to 24.94%.

My recommendation is to validate operational data and unit economics before a controlled retention pilot. This is an independent retrospective case study; no campaign, savings or incremental retention has been measured.

Case study: https://jeks042.github.io/subscription-churn-retention.html

#DataAnalytics #SQL #PowerBI #CustomerAnalytics

## Claims review

The 66.13% capture result uses the full final cohort and 68,040 contacts. Commercial source comparisons use 679,309 common customers and 67,930 contacts. The two denominators must not be combined.

The save-rate range is a break-even requirement among would-be churners under 60 CU contribution and 3.50 CU contact/offer cost; it is not an observed improvement or an absolute renewal-rate uplift. Risk ranking does not estimate the causal effect of an offer. Project wording should not claim deployed retention, realised savings, an approved pilot or validated customer lifetime value.
