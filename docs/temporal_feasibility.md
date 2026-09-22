# Temporal feasibility review

**Status: proposed calendar; not approved for model fitting.**

The transaction inventory covers event dates from January 2015 through March 2017. That supports investigation of earlier reconstructed expiry cohorts. It does not prove the supplied label releases can be treated as adjacent production training/test sets.

## Candidate historical evaluation

| Role | Scoring dates | Expiry cohorts | Latest conservative maturity |
|---|---|---|---|
| Training | 1 May, June, July and August 2016 | Corresponding calendar month | 30 September 2016 |
| Model selection | 1 October 2016 | October 2016 | 30 November 2016 |
| Calibration | 1 December 2016 | December 2016 | 30 January 2017 |
| Final holdout | 1 February 2017 | February 2017 | 30 March 2017 |

At each scoring date, features end on the previous day. Cohort eligibility uses the effective expiry known at that date. A label is conservatively mature only after the entire expiry-plus-30-day window has been observed. The preceding stage's labels mature before the next stage is scored.

This calendar is an analyst-proposed alternative, not the competition's supplied split. It depends on historical label reconstruction, sufficient behavioural coverage and adequate populations at each date. Exact cutoffs must be frozen before fitting.

## Conditions still to resolve

1. Complete the original listening-history inventory and validate date/key coverage.
2. Explain sample label mismatches, including release differences and cohort eligibility.
3. Review the 361,187 pre-March records in the refreshed transaction release. Event dates do not establish when these records became available operationally; no ingestion timestamps have been established.
4. Define handling of exact duplicates, same-day multiple events, zero/negative values and expiry anomalies without silently changing the source.
5. Set an intervention lead time. If requiring at least seven days before expiry, exclude early-month expiries or adopt a rolling scoring design and reassess the calendar.
6. Demonstrate sufficient counts, positive labels and full follow-up in every proposed cohort.

The current label sample is diagnostic. Accuracy on a mostly non-churn population is not enough to establish a correct label mapping. Report eligible coverage and disagreements alongside matches.
