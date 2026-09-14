# EPREL Primary Pool Audit v4

Frozen: 2026-09-09

## Scope
Primary empirical pool for the JDS DSS benchmark: household dishwashers under Commission Delegated Regulation (EU) 2019/2017.

## Frozen pool
**44 distinct real product/model records, all rated capacity = 14 place settings.**

- 24 records are backed by individual official EPREL product pages.
- 20 additional records are backed by the official EPREL public dishwasher category index.
- No third-party mirror is used in the frozen primary pool.

The official EPREL category page itself displays the model-level fields used in this benchmark (rated capacity, energy consumption, water consumption, programme duration and airborne acoustical noise).

## Capacity control
A previous amendment found that mixing mini/compact and full-size dishwashers can confound per-cycle energy/water consumption with product capacity. The frozen primary pool therefore fixes capacity to 14 place settings.

## Primary criteria
- energy_per_cycle_kwh: cost
- water_per_cycle_l: cost
- noise_dba: cost
- programme_duration_min: cost

Price, repairability and warranty are not primary scoring variables. They remain outside the primary estimand because the selected public category does not provide a consistently complete, comparable set across all 44 frozen records.

## Provenance tiers
### Tier 1 — individual product page
Registration number and product page URL are retained.

### Tier 2 — official category index
The EPREL public category index displays the product/model and the four primary attributes but the extracted public-page text used in this workflow does not expose a registration number for every listed row. Stable internal IDs are therefore assigned as `IDX-<supplier>-<model>`. These are explicitly marked as index-backed, not presented as registration numbers.

## No imputation
All 44 records contain all four primary fields. No value was imputed.

## Reproducibility note
The public EPREL UI is client-side rendered in places, while the category page is directly searchable in the research environment. The frozen dataset is therefore an archived structured representation of values observed on official EPREL pages, with source URLs and provenance tier retained.
