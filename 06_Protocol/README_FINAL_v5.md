# JDS Agentic DSS — Final Option-B Package v8

## Research framing
The empirical study is now framed as **sustainable and resilient procurement decision support**, not as a direct circularity measurement study. This avoids over-claiming circularity because the frozen EPREL dishwasher category does not provide a complete primary circularity/repairability field set. DPP/ESPR remain the digital-product-information and regulatory framing layers.

## Frozen pool
44 real EPREL dishwasher product/model records, all rated capacity = 14 place settings. 24 are backed by individual official EPREL product pages; 20 are backed by the official EPREL category index. No third-party mirror is in the frozen primary pool.

## Experiment
40 decision tasks × 4 architecture arms × 2 Nemotron models = 320 experimental conditions. Arm D uses parser + deterministic solver + audit, so expected API requests = 400 before retries.

## Models
- nvidia/nemotron-3-ultra-550b-a55b:free
- nvidia/nemotron-3-super-120b-a12b:free

## Primary criteria
Energy per eco cycle, water per eco cycle, noise, programme duration.

## Important
This package contains no fabricated benchmark results. Run the model benchmark locally, then score and analyze the raw output.
