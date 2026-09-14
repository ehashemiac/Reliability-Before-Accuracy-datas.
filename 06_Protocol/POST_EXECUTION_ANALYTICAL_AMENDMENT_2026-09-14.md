# Post-execution analytical amendment — revised manuscript

Date: 2026-09-14

The frozen empirical data and execution records are unchanged. This amendment documents the analytical revisions applied after an internal methodological audit of the manuscript.

1. The primary common endpoint is **local protocol completion**. The former use of a single universal six-gate success/product score was removed because the four architecture arms do not instantiate the same downstream stages.

2. Gates G1-G6 are retained as diagnostic, architecture-specific reliability states. A gate that is not instantiated by an architecture is treated as N/A, not as a failure.

3. The 49/80 C result is reported as local completion (61.3%), not final DSS reliability. Reanalysis of the exposed C/D decision objects found 0 strict semantic-valid states and 0 non-empty deterministic rankings.

4. Recommendation quality is reported conditionally: 35 A/B outputs contained recommendation tokens, 19 had valid candidate IDs, and 18 were fully evaluable; 9/18 matched the deterministic reference top choice. The 50.0% figure is not described as overall decision accuracy.

5. The authoritative candidate-overlap matrix is regenerated directly from the frozen 40-task manifest. Its 780 pairwise comparisons have mean Jaccard overlap 0.104049, median 0.066667, minimum 0, and maximum 0.333333.

6. The supplementary package now includes a transparent reanalysis script. PROMETHEE II remains documented as a possible future robustness analysis but is not reported as an executed result.

7. Historical protocol files and the original source archive are retained for traceability. The revised manuscript and current analysis files are the authoritative submission-facing artifacts.
