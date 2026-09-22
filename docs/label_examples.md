# Label and cutoff examples

These examples are synthetic and public. They illustrate the implemented contract without redistributing customer histories. Real-source comparisons are aggregate only and are reported separately.

Scoring is 1 February 2017. Features end on 31 January. The latest known expiry must fall in February and be at least seven days after scoring. Full observation through the original expiry plus 30 days is required for every labelled case.

| Example | Known expiry | Subsequent activity | Result |
|---|---|---|---|
| Timely renewal | 8 February | Renew on 9 March (29 days later) | Non-churn |
| Boundary renewal | 8 February | Renew on 10 March (exactly 30 days later) | Churn |
| Cancellation then renewal | 8 February | Cancel on 9 February, shortening expiry to 1 February; renew 3 March | Churn: 30-day gap from shortened expiry |
| Plan change | 8 February | Same-plan subscription and cancellation on 10 February | Subscription sorts first; cancellation alone is not churn |
| Insufficient follow-up | 28 February | Observation stops 20 March | NULL label, not included in a mature denominator |
| Too little contact lead | 7 February | Any future history | Excluded from outreach-eligible features: only six days of lead |
| Future-only customer | No pre-scoring events | First transaction on 2 February | Not a scoring candidate |
| Event after maturity | 8 February | Cancellation on 11 March after the 10 March maturity date | Outside outcome window; does not rewrite this cohort's label |

Same-day source ordering uses event date, then descending lexical concatenation of plan price, plan days and payment method, then subscription before cancellation; identical-plan renewals extend expiry and cancellations shorten it. SQL and Python preserve this unusual source ordering rather than substituting numeric price sorting. Ties remaining after this order have the same expiry/cancellation outcome; feature counts use all non-identical events.

Tests check these boundaries, duplicate amounts, exact 7/30/90-day feature cutoffs and invariance to changing post-scoring amounts/expiry. A separate real-data check compares SQL to the independent Python reconstruction for 1,000 lead-eligible customers per scoring date. Agreement proves implementation consistency, not equality with undisclosed source histories or supplied competition labels.
