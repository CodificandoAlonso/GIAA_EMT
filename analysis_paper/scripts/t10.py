from common import *
from scipy import stats
r=pd.read_pickle("/tmp/claude-1000/-home-hector-Desktop-CATEDRA-GIAA-EMT/c51b089e-2f79-4530-a3c4-ee0404e4a409/scratchpad/fits"+SUF+".pkl")
occ=pd.read_csv("../tables/t10_occupation_combinations"+SUF+".csv"); tt=pd.read_csv("../tables/t10_traveltime_combinations"+SUF+".csv")
occ["ok"]=occ.is_normal.astype(str)=="True"; tt["ok"]=tt.is_normal.astype(str)=="True"
orig={"toA":2646,"toB":5727}; fin={"toA":5727,"toB":2646}
rows=[]
def row(var,d,variant,k,n,note=""):
    bt=stats.binomtest(int(k),int(n),0.95); ci=bt.proportion_ci(confidence_level=0.95,method="wilson")
    rows.append((var,d,variant,int(k),int(n),100*k/n,100*ci.low,100*ci.high,bt.pvalue,note))
for var,term in [("boardings",orig),("alightings",fin)]:
    for d in DIRN:
        x=r[(r.direction==d)&(r.variable==var)]
        main=x[~x.stop.isin([2646,5727])]; t=x[x.stop==term[d]]
        k_main=main.any_pass.sum(); n_main=len(main)
        row(var,d,"as published (terminal counted as always non-rejected)",k_main+19,n_main+19,"reproduces paper")
        row(var,d,"corrected (terminal with its real test result)",k_main+t.any_pass.sum(),n_main+len(t))
        row(var,d,"main-loop stops only (terminals excluded)",k_main,n_main)
for d in DIRN:
    o=occ[occ.direction==d]; row("occupation",d,"all stops incl. terminals (as published)",o.ok.sum(),len(o),"reproduces paper")
    o2=o[~o.stop.isin([2646,5727])]; row("occupation",d,"terminals excluded (as the text states)",o2.ok.sum(),len(o2))
    t=tt[tt.direction==d]; row("travel times",d,"as published",t.ok.sum(),len(t),"reproduces paper")
    t2=t[t.n>0]; row("travel times",d,"combinations with n>0 only",t2.ok.sum(),len(t2))
T=pd.DataFrame(rows,columns=["variable","direction","variant","n_not_rejected","N","pct_not_rejected","wilson95_low","wilson95_high","binom_test_p_vs_0.95","note"])
save_table(T,"t10_nonrejection_table"+SUF)
paper={("boardings","toA"):90.60,("boardings","toB"):87.56,("alightings","toA"):93.61,("alightings","toB"):90.91,("travel times","toA"):95.49,("travel times","toB"):90.43,("occupation","toA"):94.39,("occupation","toB"):88.60}
chk=[]
for (v,d),p in paper.items():
    x=T[(T.variable==v)&(T.direction==d)&(T.note=="reproduces paper")].iloc[0]; chk.append((v,d,p,round(x.pct_not_rejected,2),x.n_not_rejected,x.N,abs(round(x.pct_not_rejected,2)-p)<0.006))
CK=pd.DataFrame(chk,columns=["variable","direction","paper_%","recomputed_%","k","N","match"]); save_table(CK,"t10_check_vs_paper"+SUF)
out=["### 10.1/10.2 Recomputed table vs paper\n\n"+md(CK,"{:.2f}"),"\n### 10.3 Binomial test against 0.95 and Wilson 95 % CI (all variants)\n\n"+md(T,"{:.3f}")]
# 10.4 occupation by slot
o=occ.copy()
by=o.groupby("slot").agg(N=("ok","size"),n_not_rejected=("ok","sum")).reset_index(); by["pct"]=100*by.n_not_rejected/by.N
by_d=o.groupby(["direction","slot"]).agg(N=("ok","size"),n_not_rejected=("ok","sum")).reset_index(); by_d["pct"]=100*by_d.n_not_rejected/by_d.N
rej=o[~o.ok].groupby("slot").size().reindex(SLOTS,fill_value=0)
byj=by.merge(rej.rename("n_rejected").reset_index(),on="slot")
by_d.to_csv("../tables/t10_occupation_by_slot_direction"+SUF+".csv",index=False); save_table(byj,"t10_occupation_by_slot"+SUF); by_d.to_csv("../figures/fig_occupation_nonrejection_by_slot_data"+SUF+".csv",index=False)
out.append("\n### 10.4 Occupation, non-rejection by slot (both directions)\n\n"+md(byj,"{:.1f}")+"\n\nBy direction and slot (only slots with any rejection):\n\n"+md(by_d[by_d.pct<100],"{:.1f}"))
rj=o[~o.ok][["direction","stop","slot","n"]].sort_values(["direction","slot"])
out.append("\nAll rejected occupation combinations:\n\n"+md(rj))
save_table(rj,"t10_occupation_rejected_combinations"+SUF)
last=by_d[by_d.slot==23]; share_last=(o[~o.ok].slot==23).mean()
out.append(f"\nShare of all occupation rejections falling in slot 23: **{100*share_last:.1f}%** ({int((o[~o.ok].slot==23).sum())} of {int((~o.ok).sum())}); slot 23 holds {100*(o.slot==23).mean():.1f}% of the combinations.")
write_section("t10_nonrejection"+SUF,"\n".join(out)); print("\n".join(out))
