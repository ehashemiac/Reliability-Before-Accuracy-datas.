# 40 Decision-Instance Protocol v4

## Frozen empirical pool
44 real EPREL dishwasher product/model records, all capacity = 14 place settings.

## Decision tasks
40 distinct decision tasks, each with 8 distinct candidates sampled from the 44-record frozen pool using seed `20260907`. Candidate sets are diversified; product reuse across tasks is allowed and explicitly accounted for.

Scenario allocation:
- S1 Balanced procurement: 10
- S2 Constraint-sensitive procurement: 8
- S3 Energy-importance shock: 8
- S4 Weight robustness: 7
- S5 Missing-information stress: 7

## Primary criteria
Energy/cycle, water/cycle, noise, programme duration; all are costs.
Base weights = 0.35, 0.25, 0.15, 0.25.

## S2 constraint
Hard constraint: noise <= 42 dB(A). Constraint is applied before scoring.

## S3 shock
Energy importance changes from 0.35 to 0.49; remaining criteria are proportionally renormalized. Uniform multiplication of all energy values is not used as the primary shock because it is invariant under min-max normalization.

## S4 robustness
Energy weight fixed perturbations: 0.315, 0.385, 0.28, 0.42 with proportional renormalization of the other three weights.

## S5 missingness
For two candidates, energy is removed from one and programme duration from another. Missing values are never imputed.

## Reference methods
Primary deterministic reference: min-max weighted sum. Secondary robustness reference: PROMETHEE II with linear preference. Neither is called ground truth.

## Experimental cells
40 tasks × 4 architecture arms × 2 Nemotron models = 320 conditions.
Arm D contains parser + deterministic computation + audit, so expected model API requests = 40 × 2 × (A+B+C+2D) = 400, before retries.
