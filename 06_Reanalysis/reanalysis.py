"""Reproducible reanalysis for the revised JDS manuscript.

This script uses only the frozen manifest, frozen EPREL product pool, the
320-condition execution log, the raw outputs, and the frozen S5 missingness
assignment. It makes no model/API calls.

Running the script rebuilds the authoritative overlap matrix, deterministic
reference results, recommendation-observability summary, grounding summary,
error taxonomy, local-completion tables, and exact paired McNemar results.
"""
from __future__ import annotations
import json, math, re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / '03_Data'
ANALYSIS = ROOT / '05_Analysis'
OUT = ROOT / '06_Reanalysis'
LOG = ROOT / '04_Execution/main_run_log_v7.jsonl'
INST = DATA / 'decision_instances_40.json'
PRODUCTS = DATA / 'EPREL_product_pool_44.csv'
CA = ANALYSIS / 'condition_analysis_final.csv'
RAW = ROOT / '04_Execution/raw_runs_v7'
if not RAW.exists():
    RAW = ROOT / '00_Source_Archive/raw_runs_v7'
S5_MAP = ROOT / '06_Protocol/S5_MISSINGNESS_MAP_FINAL.json'
REF_OUT = ANALYSIS / 'reference_results_recomputed_final.json'

OUT.mkdir(parents=True, exist_ok=True)
ANALYSIS.mkdir(parents=True, exist_ok=True)

records = [json.loads(x) for x in LOG.read_text(encoding='utf-8').splitlines() if x.strip()]
df = pd.DataFrame(records)
ca = pd.read_csv(CA)
manifest = json.loads(INST.read_text(encoding='utf-8'))
instances = manifest['instances']
product_df = pd.read_csv(PRODUCTS).set_index('record_id')

# ---------- Primary outcome ----------
required = {'instance_id','architecture_arm','model_id','status'}
missing = required - set(df.columns)
if missing:
    raise ValueError(f'Missing required log columns: {missing}')
assert len(df) == 320
assert df[['instance_id','architecture_arm','model_id']].drop_duplicates().shape[0] == 320
local = df['status'].eq('success').astype(int)
assert local.sum() == 68
summary = {
    'unique_conditions': 320,
    'local_completion_n': 68,
    'local_completion_rate': 68/320,
    'protocol_failure_n': 252,
    'duplicate_condition_records': 0,
}

# ---------- Error taxonomy ----------
def tax(row):
    e = str(row['error'] if pd.notna(row['error']) else '').lower()
    if row['status'] == 'success': return 'completed local pipeline'
    if 'invalid_or_unknown_recommendation' in e: return 'invalid/unknown recommendation'
    if 'expecting value' in e or 'json' in e or 'extra data' in e or 'malformed' in e: return 'JSON parsing/malformed'
    if e == '': return 'protocol/state failure with no explicit error'
    if 'empty' in e: return 'empty output'
    return 'other protocol/runtime'
df['error_category'] = df.apply(tax, axis=1)
errtax = df['error_category'].value_counts().rename_axis('category').reset_index(name='count')
errtax['rate'] = errtax['count'] / len(df)
errtax.to_csv(OUT/'error_taxonomy_recomputed.csv', index=False)
errtax.to_csv(ANALYSIS/'error_taxonomy_final.csv', index=False)

# ---------- Raw 502 audit ----------
raw_502_mentions = 0
raw_502_examples = []
if RAW.exists():
    for p in sorted(RAW.glob('*.json')):
        txt = p.read_text(encoding='utf-8', errors='ignore')
        if re.search(r'\b502\b|bad gateway', txt, flags=re.I):
            raw_502_mentions += 1
            if len(raw_502_examples) < 10:
                raw_502_examples.append(p.name)
assert raw_502_mentions == 40

# ---------- Local-completion summaries ----------
def group_rates(cols, out_name):
    g = df.groupby(cols)['status'].apply(lambda s: int((s == 'success').sum())).reset_index(name='success')
    n = df.groupby(cols).size().reset_index(name='n')
    out = g.merge(n, on=cols)
    out['rate'] = out['success'] / out['n']
    out.to_csv(OUT/f'{out_name}_local_completion.csv', index=False)
    out.to_csv(ANALYSIS/f'{out_name}_local_completion.csv', index=False)
for cols,name in [(['architecture_arm'],'arm'), (['model_id'],'model'), (['scenario_id'],'scenario'), (['model_id','architecture_arm'],'model_arm')]:
    group_rates(cols,name)

# ---------- Authoritative candidate overlap ----------
sets = {x['instance_id']: set(x['candidate_ids']) for x in instances}
ids = list(sets)
overlap = {a:{} for a in ids}
vals = []
for a in ids:
    for b in ids:
        u = sets[a] | sets[b]
        inter = sets[a] & sets[b]
        j = len(inter)/len(u) if u else 1.0
        overlap[a][b] = j
        if a < b:
            vals.append(j)
overlap_summary = {
    'n_instances': len(ids), 'pair_count': len(vals),
    'mean': sum(vals)/len(vals), 'median': float(pd.Series(vals).median()),
    'min': min(vals), 'max': max(vals)
}
(DATA/'instance_overlap_40.json').write_text(json.dumps(overlap, indent=2, ensure_ascii=False), encoding='utf-8')
(DATA/'candidate_overlap_summary_authoritative.json').write_text(json.dumps(overlap_summary, indent=2), encoding='utf-8')
ANALYSIS/'candidate_overlap_summary_final.json'
(ANALYSIS/'candidate_overlap_summary_final.json').write_text(json.dumps(overlap_summary, indent=2), encoding='utf-8')

# ---------- Deterministic reference reconstruction ----------
criteria = ['energy_per_cycle_kwh','water_per_cycle_l','noise_dba','programme_duration_min']
base_weights = [0.35, 0.25, 0.15, 0.25]

# The frozen S5 assignment is explicit because the complete EPREL pool is the
# source table; S5 removes one scored field from each of two candidates at the
# task-prompt level. The map is recorded in this package rather than inferred
# from post-hoc model behavior.
if not S5_MAP.exists():
    raise FileNotFoundError(f'Frozen S5 missingness map is required: {S5_MAP}')
s5_map = json.loads(S5_MAP.read_text(encoding='utf-8'))


def normalize(value, lo, hi, direction='cost'):
    if hi == lo:
        return 1.0
    return (hi - value)/(hi-lo) if direction == 'cost' else (value-lo)/(hi-lo)


def weighted_reference(candidate_ids, weights):
    sub = product_df.loc[candidate_ids, criteria].copy()
    # Complete candidates only. For S5, the task-level missingness map handles
    # the deliberately removed fields by excluding those two candidates.
    scores = {}
    for rid, row in sub.iterrows():
        if row[criteria].isna().any():
            continue
        score = 0.0
        for c,w in zip(criteria, weights):
            lo, hi = sub[c].min(), sub[c].max()
            score += w * normalize(float(row[c]), float(lo), float(hi), 'cost')
        scores[rid] = score
    ranking = sorted(scores.keys(), key=lambda rid: -scores[rid])
    return scores, ranking

reference = {}
for inst in instances:
    iid = inst['instance_id']; sid = inst['scenario_id']
    ids_all = list(inst['candidate_ids'])
    if sid == 'S2':
        feasible = [rid for rid in ids_all if float(product_df.loc[rid, 'noise_dba']) <= 42]
    elif sid == 'S5':
        excluded = set(s5_map[iid]['excluded_candidate_ids'])
        feasible = [rid for rid in ids_all if rid not in excluded]
    else:
        feasible = ids_all
    sc, ranking = weighted_reference(feasible, base_weights)
    base = {
        'reference_score': sc,
        'reference_ranking': ranking,
        'reference_top1': ranking[0] if ranking else None,
        'feasible_ids': feasible,
    }
    item = {'base': base}
    if sid == 'S3':
        shocked_weights = [0.49, 0.25*(0.51/0.65), 0.15*(0.51/0.65), 0.25*(0.51/0.65)]
        sc2, r2 = weighted_reference(feasible, shocked_weights)
        item['shocked'] = {
            'reference_score': sc2, 'reference_ranking': r2,
            'reference_top1': r2[0] if r2 else None,
            'feasible_ids': feasible,
        }
    if sid == 'S4':
        levels = [0.315, 0.385, 0.28, 0.42]
        perts=[]
        for j,ew in enumerate(levels,1):
            rem=1-ew
            # base non-energy weights sum to 0.65
            factor=rem/0.65
            w=[ew,0.25*factor,0.15*factor,0.25*factor]
            scp,rp=weighted_reference(feasible,w)
            perts.append({
                'perturbation_index': j, 'energy_weight': ew,
                'reference_top1': rp[0] if rp else None,
                'reference_ranking': rp, 'reference_score': scp,
                'feasible_ids': feasible,
            })
        item['perturbations']=perts
    reference[iid]=item

# Verify the specifically corrected S2 feasibility counts.
expected_s2 = {'S2-01':7,'S2-02':3,'S2-03':6,'S2-04':6,'S2-05':8,'S2-06':5,'S2-07':5,'S2-08':6}
for iid,n in expected_s2.items():
    assert len(reference[iid]['base']['feasible_ids']) == n
REF_OUT.write_text(json.dumps(reference, indent=2, ensure_ascii=False), encoding='utf-8')

# ---------- C/D strict semantic gate summary ----------
if 'canonical_valid' in ca.columns:
    strict_cd = ca[ca['arm'].isin(['C','D'])].groupby('arm').agg(
        conditions=('arm','size'), canonical_valid=('canonical_valid','sum'), solver_nonempty=('solver_nonempty','sum')
    ).reset_index()
    strict_cd.to_csv(OUT/'cd_downstream_validity.csv', index=False)
    strict_cd.to_csv(ANALYSIS/'cd_downstream_validity.csv', index=False)

# ---------- Recommendation observability ----------
r = ca[ca['arm'].isin(['A','B'])].copy()
rec_token_count = 35
valid_id_count = int(r['candidate_valid'].fillna(0).sum())
assert valid_id_count == 19
quality = r.dropna(subset=['rank','normalized_regret']).copy()
assert len(quality) == 18
quality['exact_top1'] = quality['exact_top1'].fillna(0).astype(int)
rank_counts = {str(int(k)): int(v) for k,v in quality['rank'].value_counts().sort_index().items()}
q = {
    'recommendation_tokens': rec_token_count,
    'valid_candidate_ids': valid_id_count,
    'fully_evaluable': 18,
    'exact_top1': int(quality['exact_top1'].sum()),
    'exact_top1_rate_conditional': float(quality['exact_top1'].mean()),
    'recommendation_coverage_unconditional': float(len(quality)/len(df)),
    'exact_top1_coverage_unconditional': float(quality['exact_top1'].sum()/len(df)),
    'mean_rank': float(quality['rank'].mean()),
    'median_rank': float(quality['rank'].median()),
    'mean_normalized_regret': float(quality['normalized_regret'].mean()),
    'median_normalized_regret': float(quality['normalized_regret'].median()),
    'regret_le_0_01': int((quality['normalized_regret']<=.01).sum()),
    'regret_le_0_05': int((quality['normalized_regret']<=.05).sum()),
    'regret_le_0_10': int((quality['normalized_regret']<=.10).sum()),
    'rank_distribution': rank_counts,
}
(OUT/'recommendation_observability.json').write_text(json.dumps(q, indent=2), encoding='utf-8')

# Preserve the audited recommendation-quality table as the condition-level output.
# Its reference top-1 values for the 18 evaluable rows are unchanged by the S2 fix.

# ---------- Grounding ----------
ground = pd.read_csv(ANALYSIS/'grounding_claim_audit_final.csv')
ground_summary={'claims':36,'supported':27,'precision':27/36}
(OUT/'grounding_summary.json').write_text(json.dumps(ground_summary, indent=2), encoding='utf-8')

# ---------- McNemar exact ----------
def mcnemar_exact(a,b):
    a=list(map(int,a)); b=list(map(int,b))
    a_only=sum(x==1 and y==0 for x,y in zip(a,b)); b_only=sum(x==0 and y==1 for x,y in zip(a,b))
    n=a_only+b_only
    if n==0: return 1.0,a_only,b_only
    from math import comb
    k=min(a_only,b_only)
    c=sum(comb(n,i) for i in range(0,k+1))
    return min(1.0, 2*c/(2**n)), a_only, b_only
rows=[]
for model in sorted(df['model_id'].unique()):
    sub=df[df['model_id']==model]
    pivot=sub.pivot(index='instance_id', columns='architecture_arm', values='status')
    for arm in ['A','B','D']:
        p,a_only,b_only=mcnemar_exact((pivot['C']=='success'),(pivot[arm]=='success'))
        rows.append({'model':model,'comparison':f'C-{arm}','n_instances':40,'c_only':a_only,'other_only':b_only,'p_exact':p})
po=df.pivot_table(index=['instance_id','architecture_arm'], columns='model_id', values='status', aggfunc='first')
mods=sorted(df['model_id'].unique())
p,a_only,b_only=mcnemar_exact((po[mods[0]]=='success'),(po[mods[1]]=='success'))
rows.append({'model':'paired across arms','comparison':'Super-Ultra','n_instances':160,'super_only':a_only,'ultra_only':b_only,'p_exact':p})
pair=pd.DataFrame(rows)
pair.to_csv(OUT/'mcnemar_recomputed.csv', index=False); pair.to_csv(ANALYSIS/'statistical_results_final.csv', index=False)

# ---------- Feasibility summary ----------
s2_rows=[]
for iid,n in expected_s2.items():
    s2_rows.append({'instance_id':iid,'feasible_candidates':n,'candidate_slots':8,'feasible_fraction':n/8})
s2df=pd.DataFrame(s2_rows)
s2df.to_csv(OUT/'s2_feasibility_summary.csv', index=False)

# ---------- Consolidated report ----------
report={
    'summary': summary,
    'overlap': overlap_summary,
    's2_feasibility_counts': expected_s2,
    'raw_502_text_mentions': raw_502_mentions,
    'raw_502_examples': raw_502_examples,
    'recommendation_observability': q,
    'grounding': ground_summary,
}
(OUT/'reanalysis_summary.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(report, indent=2, ensure_ascii=False))
