from common import *
from scipy import stats
import json
np.set_printoptions(linewidth=200)
out=[]
def P(*a):
    t=" ".join(str(x) for x in a); out.append(t); print(t)

def nb_detail(x, corrected=False, untestable_rejects=False):
    a=np.array(x,float); n=len(a); m=a.mean(); v=a.var(ddof=1)
    if not v>m: return dict(status="var<=mean",ok=False)
    p=m/v; r=m*p/(1-p)
    vals,obs=np.unique(a.astype(int),return_counts=True)
    exp=np.array([n*stats.nbinom.pmf(k,r,p) for k in vals])
    mask=exp>=5
    if mask.sum()<2: return dict(status="too few bins",ok=False,vals=vals,obs=obs,exp=exp)
    if corrected and mask.all(): op,ep=obs,exp
    else: op=np.append(obs[mask],obs[~mask].sum()); ep=np.append(exp[mask],exp[~mask].sum())
    df=len(op)-1-2
    if corrected and df<1: return dict(status="untestable",ok=(not untestable_rejects),vals=vals,obs=obs,exp=exp,op=op,ep=ep,df=df)
    if not corrected and df<1: df=1
    with np.errstate(all="ignore"): st=np.sum((op-ep)**2/ep)
    pv=1-stats.chi2.cdf(st,df)
    return dict(status="ok",ok=bool(pv>0.05),vals=vals,obs=obs,exp=exp,op=op,ep=ep,df=df,stat=st,p=pv,r=r,pp=p)

def geom_detail(x, corrected=False, untestable_rejects=False):
    a=np.array(x,float); n=len(a); p=1/(a.mean()+1)
    vals,obs=np.unique(a,return_counts=True)
    exp=np.array([n*(1-p)**k*p for k in vals]); mask=exp>=5
    if not mask.all(): op=np.append(obs[mask],obs[~mask].sum()); ep=np.append(exp[mask],exp[~mask].sum())
    else: op,ep=obs,exp
    df=len(op)-1-1
    if corrected and df<1: return dict(status="untestable",ok=(not untestable_rejects),vals=vals,obs=obs,exp=exp,op=op,ep=ep,df=df)
    with np.errstate(all="ignore"): st=np.sum((op-ep)**2/ep)
    pv=1-stats.chi2.cdf(st,df) if df>0 else np.nan
    return dict(status="ok",ok=bool(pv>0.05) if pv==pv else False,vals=vals,obs=obs,exp=exp,op=op,ep=ep,df=df,stat=st,p=pv,pp=p)

# ---- collect all cells
cells=[]
for d in DIRN:
    cl=cleaned(d)
    for var,dd in [("boardings",stop_slot_boards(cl,d)),("alightings",stop_slot_dropoffs(cl))]:
        for (stop,s),v in dd.items():
            if len(v)<2: continue
            x,_=remove_outliers_mad(v); cells.append((d,var,stop,s,x))
# sanity: my detail replicas agree with the pipeline functions
bad=0
for d,var,stop,s,x in cells:
    nb=test_negative_binomial(x); g=test_geometric(x)
    a=nb_detail(x); b=geom_detail(x)
    if bool(nb['is_negbin'])!=a["ok"] or bool(g['is_geometric'])!=b["ok"]: bad+=1
P(f"Replica check: {bad} of {len(cells)} cells differ between the printed-detail replica and the pipeline functions.\n")

def show(title,det,x):
    P(f"**{title}**"); P(f"- n = {len(x)} (after MAD); mean = {np.mean(x):.3f}; var = {np.var(x,ddof=1):.3f}")
    P(f"- observed values (sorted, first 40): {sorted(x)[:40]}{' ...' if len(x)>40 else ''}")
    P(f"- classes (unique values): {det['vals'].tolist()}")
    P(f"- observed frequencies:    {det['obs'].tolist()}")
    P(f"- expected frequencies:    {np.round(det['exp'],2).tolist()}")
    P(f"- pooled observed / expected (as built by the function): {det['op'].tolist()} / {np.round(det['ep'],2).tolist()}")
    P(f"- degrees of freedom = {det['df']}; statistic = {det['stat']}; p-value = {det['p']}")
    P(f"- `p_value > alpha` -> {det['p']>0.05}  => candidate treated as REJECTED\n")
P("### 2.a Negative binomial: NaN p-value (all expected >= 5 -> empty final class, 0/0)\n")
nbn=[c for c in cells if nb_detail(c[4]).get("p",0)!=nb_detail(c[4]).get("p",0) and nb_detail(c[4])["status"]=="ok"]
seen=set(); pick=[]
for c in nbn:
    if (c[0],c[1]) not in seen: seen.add((c[0],c[1])); pick.append(c)
    if len(pick)==3: break
for d,var,stop,s,x in pick: show(f"NB, {d}, {var}, stop {stop}, slot {s}",nb_detail(x),x)
P("### 2.b Geometric: NaN p-value (df <= 0)\n")
gn=[c for c in cells if (lambda g:g.get("p",0)!=g.get("p",0))(geom_detail(c[4]))]
seen=set(); pick=[]
for c in gn:
    if (c[0],c[1]) not in seen: seen.add((c[0],c[1])); pick.append(c)
    if len(pick)==3: break
for d,var,stop,s,x in pick: show(f"Geometric, {d}, {var}, stop {stop}, slot {s}",geom_detail(x),x)

# ---- effect on selection
S_term={("toA","boardings"):2646,("toB","boardings"):5727,("toA","alightings"):5727,("toB","alightings"):2646}
def in_set(d,var,stop): return stop not in (2646,5727) or stop==S_term[(d,var)]
rows=[]
for pol,rej in [("untestable -> not rejected",False),("untestable -> rejected",True)]:
    for d,var,stop,s,x in cells:
        if not in_set(d,var,stop): continue
        isn,_,_,_=is_normal_simplified(x)
        nb0=test_negative_binomial(x)['is_negbin']; g0=test_geometric(x)['is_geometric']
        nb1=nb_detail(x,True,rej)["ok"]; g1=geom_detail(x,True,rej)["ok"]
        t=pd.DataFrame(columns=["Stop","Timeslot","DistributionType","Param1","Param2"])
        c0=select_by_aic(x,{'NORMAL':bool(isn),'NEGATIVE BINOMIAL':bool(nb0),'GEOMETRICAL':bool(g0)},stop,s,t)
        c1=select_by_aic(x,{'NORMAL':bool(isn),'NEGATIVE BINOMIAL':bool(nb1),'GEOMETRICAL':bool(g1)},stop,s,t)
        rows.append((pol,d,var,stop,s,c0,c1,c0!=c1,bool(isn or nb0 or g0),bool(isn or nb1 or g1),bool(nb0!=nb1),bool(g0!=g1)))
R=pd.DataFrame(rows,columns=["policy","direction","variable","stop","slot","chosen_original","chosen_corrected","selection_changes","any_pass_original","any_pass_corrected","nb_verdict_changes","geom_verdict_changes"])
save_table(R,"t6_1_nan_correction_effect")
sm=R.groupby(["policy","direction","variable"]).agg(cells=("slot","size"),selection_changes=("selection_changes","sum"),nb_verdict_changes=("nb_verdict_changes","sum"),geom_verdict_changes=("geom_verdict_changes","sum"),any_pass_changes=("any_pass_original",lambda s:0)).reset_index()
sm["any_pass_changes"]=R.groupby(["policy","direction","variable"]).apply(lambda g:(g.any_pass_original!=g.any_pass_corrected).sum(),include_groups=False).values
tot=R.groupby("policy").agg(cells=("slot","size"),selection_changes=("selection_changes","sum"),nb_verdict_changes=("nb_verdict_changes","sum"),geom_verdict_changes=("geom_verdict_changes","sum")).reset_index(); tot["pct_selection_changes"]=100*tot.selection_changes/tot.cells
P("### 2.c Effect of correcting the two tests on the distribution selection (cells of the notebook stop set)\n")
P("Correction: no empty final class (the pooled class is added only if some expected < 5); at least 1 degree of freedom is required, otherwise the test is not applicable and the candidate is either kept or discarded (two policies).\n")
P(md(tot,"{:.2f}")); P(""); P(md(sm,"{:.0f}"))
tr=R[R.policy=="untestable -> not rejected"].groupby(["chosen_original","chosen_corrected"]).size().reset_index(name="n"); tr=tr[tr.chosen_original!=tr.chosen_corrected]
P("\nTransitions (policy 'not rejected'):\n"); P(md(tr,"{:.0f}"))
tr=R[R.policy=="untestable -> rejected"].groupby(["chosen_original","chosen_corrected"]).size().reset_index(name="n"); tr=tr[tr.chosen_original!=tr.chosen_corrected]
P("\nTransitions (policy 'rejected'):\n"); P(md(tr,"{:.0f}"))
write_section("t6_nan_correction","\n".join(out))

# ---- bug cell
nb_cells=json.load(open(f"{SRC}/final_analysis_board_dropoff.ipynb"))["cells"]
P("\n\n==== final_analysis_board_dropoff.ipynb, cell 6 (toA, stop 2646) ====")
src="".join(nb_cells[6]["source"]); out2=[src]
print(src)
P("\n==== same pattern in cell 8 (toB, stop 5727) ====")
print("".join(nb_cells[8]["source"])[-1700:-900])
# evaluate on a terminal combination
d="toA"; cl=cleaned(d); b=stop_slot_boards(cl,d)
for slot in (5,8):
    x,_=remove_outliers_mad(b[(2646,slot)])
    is_normal,_,mean,std=is_normal_simplified(x)
    neg_bin=test_negative_binomial(x); geom=test_geometric(x)
    P(f"\nstop 2646 toA, slot {slot}: n={len(x)}")
    P(f"  is_normal = {is_normal!r}  (type {type(is_normal).__name__})")
    P(f"  neg_bin   = {neg_bin!r}")
    P(f"  type(neg_bin) = {type(neg_bin).__name__}, bool(neg_bin) = {bool(neg_bin)}")
    P(f"  geom      = {geom!r}")
    P(f"  type(geom) = {type(geom).__name__}, bool(geom) = {bool(geom)}")
    P(f"  (is_normal or neg_bin or geom) = {(is_normal or neg_bin or geom)!r} -> bool {bool(is_normal or neg_bin or geom)}")
    P(f"  real verdicts: neg_bin['is_negbin'] = {neg_bin['is_negbin']}, geom['is_geometric'] = {geom['is_geometric']}")
write_section("t10_bug_cell","\n".join(out2)+"\n"+"\n".join(out[-17:]))
