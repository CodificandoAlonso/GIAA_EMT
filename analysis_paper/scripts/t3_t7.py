from common import *
from scipy import stats
R="/tmp/claude-1000/-home-hector-Desktop-CATEDRA-GIAA-EMT/c51b089e-2f79-4530-a3c4-ee0404e4a409/scratchpad/fits.pkl"
r=pd.read_pickle(R)
orig={"toA":2646,"toB":5727}; fin={"toA":5727,"toB":2646}
def in_set(x):
    term = orig[x.direction] if x.variable=="boardings" else fin[x.direction]
    return (x.stop not in (2646,5727)) or x.stop==term
r["in_notebook_set"]=r.apply(in_set,axis=1)
S=r[r.in_notebook_set].copy()
out=[]
# ---- Task 3
T=S[(S.n_clean>=2)&(S["mean"]>0)].copy()
T["stat"]=(T.n_clean-1)*T["var"]/T["mean"]
T["p_lo"]=stats.chi2.ppf(0.025,T.n_clean-1); T["p_hi"]=stats.chi2.ppf(0.975,T.n_clean-1)
T["over"]=T.stat>T.p_hi; T["under"]=T.stat<T.p_lo
save_table(T[["direction","variable","stop","order","slot","n_clean","mean","var","disp","stat","over","under","chosen"]],"t3_dispersion_per_combination")
g=T.groupby(["direction","variable"])
sm=g.agg(n_combinations=("slot","size"),pct_reject_overdisp=("over",lambda s:100*s.mean()),pct_reject_underdisp=("under",lambda s:100*s.mean()),
         disp_median=("disp","median"),disp_q25=("disp",lambda s:s.quantile(.25)),disp_q75=("disp",lambda s:s.quantile(.75)),pct_disp_gt1=("disp",lambda s:100*(s>1).mean())).reset_index()
sm["pct_reject_equidisp_total"]=sm.pct_reject_overdisp+sm.pct_reject_underdisp
save_table(sm,"t3_dispersion_summary")
excluded=S[~S.index.isin(T.index)].groupby(["direction","variable"]).size().reset_index(name="excluded_combos(n<2 or mean=0)")
out.append("### 3.1-3.3 Dispersion index (boardings per stop-hour, alightings per bus arrival; after MAD removal)\n\n"+md(sm,"{:.2f}")+"\n\nCombinations excluded (n<2 or mean=0, test undefined):\n\n"+md(excluded))
# also overall
allv=T.groupby("variable").agg(n=("slot","size"),pct_over=("over",lambda s:100*s.mean()),pct_under=("under",lambda s:100*s.mean()),disp_med=("disp","median")).reset_index()
out.append("\nBy variable (both directions pooled):\n\n"+md(allv,"{:.2f}"))
# 3.4 distribution shares
C=S[S.chosen.notna()]
rows=[]
for keys,gg_ in [(("all","all"),C)]+[((d,v),x) for (d,v),x in C.groupby(["direction","variable"])]+[(("all",v),x) for v,x in C.groupby("variable")]+[((d,"all"),x) for d,x in C.groupby("direction")]:
    vc=gg_.chosen.value_counts()
    n=len(gg_)
    rows.append((keys[0],keys[1],n,vc.get("NORMAL",0),vc.get("NEGATIVE BINOMIAL",0),vc.get("GEOMETRICAL",0),100*vc.get("NORMAL",0)/n,100*vc.get("NEGATIVE BINOMIAL",0)/n,100*vc.get("GEOMETRICAL",0)/n))
shares=pd.DataFrame(rows,columns=["direction","variable","n_cells","n_normal","n_negbin","n_geom","pct_normal","pct_negbin","pct_geom"])
save_table(shares,"t3_distribution_shares")
out.append("\n### 3.4 Selected distributions (paper: normal 62.4 %, NB 23.9 %, geometric 13.7 %)\n\n"+md(shares,"{:.1f}"))
# selection reason: how many cells had all three rejected (fallback)
fb=S.assign(fallback=~S.any_pass).groupby(["direction","variable"]).fallback.agg(["sum","size"]).reset_index()
out.append("\nCells where all three candidates were rejected (lowest-AIC fallback):\n\n"+md(fb))

# ---- Task 7
rows=[]
for (d,v),x in S.groupby(["direction","variable"]):
    nraw=x.n_raw.sum(); nrem=x.n_mad_removed.sum()
    rows.append((d,v,int(nraw),int(nrem),100*nrem/nraw if nraw else np.nan,int((x.n_mad_removed>0).sum()),len(x)))
for v,x in S.groupby("variable"):
    nraw=x.n_raw.sum(); nrem=x.n_mad_removed.sum(); rows.append(("all",v,int(nraw),int(nrem),100*nrem/nraw,int((x.n_mad_removed>0).sum()),len(x)))
x=S; rows.append(("all","all",int(x.n_raw.sum()),int(x.n_mad_removed.sum()),100*x.n_mad_removed.sum()/x.n_raw.sum(),int((x.n_mad_removed>0).sum()),len(x)))
t7a=pd.DataFrame(rows,columns=["direction","variable","n_obs_before","n_removed_by_MAD","pct_removed","cells_with_any_removal","n_cells"])
save_table(t7a,"t7_mad_removed")
out.append("\n### 7.1 Observations removed by the MAD rule (threshold 3, scaling 1.4826)\n\n"+md(t7a,"{:.3f}"))
rows=[]; det=[]
for (d,v),x in S.groupby(["direction","variable"]):
    for q in (90,95,99):
        b=x[f"p{q}_before"]; a=x[f"p{q}_after"]
        ok=(b>0)&a.notna()
        rel=((a-b)/b)[ok]
        rows.append((d,v,q,int(ok.sum()),100*rel.median(),100*rel.min(),100*(rel.abs()).max(),int(((a<b)[ok]).sum())))
t7b=pd.DataFrame(rows,columns=["direction","variable","percentile","n_cells_(before>0)","median_rel_diff_%","min_rel_diff_%","max_abs_rel_diff_%","cells_with_cut"])
save_table(t7b,"t7_tail_percentiles")
out.append("\n### 7.2 Relative change of tail percentiles after MAD removal ((after-before)/before)\n\n"+md(t7b,"{:.2f}"))
S2=S.copy()
for q in (90,95,99):
    S2[f"rel{q}"]=(S2[f"p{q}_after"]-S2[f"p{q}_before"])/S2[f"p{q}_before"].where(S2[f"p{q}_before"]>0)
top=S2.sort_values("rel99").groupby("variable").head(8)[["direction","variable","stop","slot","n_raw","n_mad_removed","p99_before","p99_after","rel99"]]
save_table(S2[["direction","variable","stop","slot","n_raw","n_mad_removed","p90_before","p90_after","p95_before","p95_after","p99_before","p99_after","rel90","rel95","rel99"]],"t7_tail_per_combination")
out.append("\n### 7.3 Combinations with the largest cut of the 99th percentile\n\n"+md(top,"{:.2f}"))
write_section("t3_t7","\n".join(out)); print("\n".join(out))
