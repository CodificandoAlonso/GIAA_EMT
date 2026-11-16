from common import *
out6=[]; out8=[]; out9=[]
def states(d):
    df=load_dir(d); df=df[(df.DayType=="LA")&(df.FreeDay==0)]
    base=df[(df.Board>=0)&(df.DropOff>=0)&(df.Board<80)&(df.DropOff<80)&(df.Occupation>=0)]   # all pipeline conditions except the Occupation upper cut
    return {"A before upper cut":base,"B after Occupation<80":base[base.Occupation<80]}
# ---- 6.5: visits removed by the Occupation upper cut, per direction and slot (both slot definitions)
rows=[]
for d in DIRN:
    st=states(d); A=st["A before upper cut"]
    for sl_def in ["TimeSlot","TimeSlot.1"]:
        for s in SLOTS:
            x=A[A[sl_def]==s]
            rows.append((d,sl_def,s,len(x),int((x.Occupation>=80).sum()),int((x.Occupation==80).sum()),int((x.Occupation>80).sum()),100*(x.Occupation>=80).mean() if len(x) else np.nan))
R65=pd.DataFrame(rows,columns=["direction","slot_definition","slot","n_visits_before_cut","removed_by_Occ>=80","of_which_exactly_80","of_which_>80","pct_removed"])
save_table(R65,"t6_5_removed_by_occupation_cut")
tot=[]
for d in DIRN:
    A=states(d)["A before upper cut"]; tot.append((d,len(A),int((A.Occupation>=80).sum()),100*(A.Occupation>=80).mean(),int((A.Occupation==80).sum()),int((A.Occupation>80).sum())))
T65=pd.DataFrame(tot,columns=["direction","n_visits_before_cut","removed (Occ>=80)","pct","exactly 80","> 80"]); save_table(T65,"t6_5_removed_totals")
out6.append(md(T65,"{:.3f}")+"\n\nVisits removed by `Occupation >= 80`, with how many have exactly 80, per direction and slot (departure-slot definition; the service-slot version is in `tables/t6_5_removed_by_occupation_cut.csv`):\n\n"+md(R65[R65.slot_definition=="TimeSlot"].drop(columns=["slot_definition"]),"{:.2f}"))
# ---- 6.6: check slot definitions on the data
chk=[]
for d in DIRN:
    df=load_dir(d)
    h0=df.EventTime.str[:2].astype(int); h1=df["EventTime.1"].str[:2].astype(int)
    chk.append((d,100*(df.TimeSlot==h0).mean(),100*(df["TimeSlot.1"]==h1).mean(),len(df)))
C66=pd.DataFrame(chk,columns=["direction","% TimeSlot == hour(EventTime) (terminal departure)","% TimeSlot.1 == hour(EventTime.1) (stop arrival)","n_visits"]); save_table(C66,"t6_6_slot_definition_check")
out6.append("\nSlot definitions check on the data:\n\n"+md(C66,"{:.3f}"))
write_section("t6_computed","\n".join(out6))
# ---- Task 8
CAPS=[("occ>=80 (capacity)",80),("occ>=72 (90% of capacity)",72)]
rows_dir=[];rows_slot=[];rows_stop=[];rows_comb=[]
for d in DIRN:
    for stn,x in states(d).items():
        for lab,th in CAPS:
            f=(x.Occupation>=th)
            rows_dir.append((d,stn,lab,len(x),int(f.sum()),100*f.mean()))
            for s,g in x.groupby("TimeSlot"): rows_slot.append((d,stn,lab,s,len(g),int((g.Occupation>=th).sum()),100*(g.Occupation>=th).mean()))
            for stp,g in x.groupby("Stop"): rows_stop.append((d,stn,lab,stp,STOPS[d].index(stp)+1,len(g),int((g.Occupation>=th).sum()),100*(g.Occupation>=th).mean()))
            for (stp,s),g in x.groupby(["Stop","TimeSlot"]): rows_comb.append((d,stn,lab,stp,STOPS[d].index(stp)+1,s,len(g),int((g.Occupation>=th).sum()),100*(g.Occupation>=th).mean()))
H=["direction","state","threshold"]
D8=pd.DataFrame(rows_dir,columns=H+["n_visits","n_at_threshold","pct"]); S8=pd.DataFrame(rows_slot,columns=H+["slot","n_visits","n_at_threshold","pct"])
P8=pd.DataFrame(rows_stop,columns=H+["stop","order","n_visits","n_at_threshold","pct"]); C8=pd.DataFrame(rows_comb,columns=H+["stop","order","slot","n_visits","n_at_threshold","pct"])
for n,t in [("t8_by_direction",D8),("t8_by_slot",S8),("t8_by_stop",P8),("t8_by_stop_slot",C8)]: save_table(t,n)
out8.append("Slot = departure slot of the expedition (reference definition, `TimeSlot`). Occupation is the recorded occupancy after the stop.\n\n### By direction\n\n"+md(D8,"{:.3f}"))
piv=S8[S8.state.str.startswith("A")].pivot_table(index=["direction","slot"],columns="threshold",values="pct").reset_index()
out8.append("\n### By slot, state A, share of visits >=80 and >=72 (90% capacity). States B/C in `tables/t8_by_slot.csv`\n\n"+md(piv,"{:.2f}"))
out8.append("\n### By stop (state A, >=80 and >=72) \n\n"+md(P8[P8.state.str.startswith("A")].sort_values(["direction","order","threshold"]).drop(columns=["state"]),"{:.2f}"))
top=C8[(C8.state.str.startswith("A"))&(C8.threshold.str.startswith("occ>=80"))&(C8.n_visits>=30)].sort_values("pct",ascending=False).head(15).drop(columns=["state","threshold"])
out8.append("\n### 8.2 Stop-slot combinations with highest share of visits at capacity (state A, n>=30)\n\n"+md(top,"{:.2f}"))
top90=C8[(C8.state.str.startswith("A"))&(C8.threshold.str.startswith("occ>=72"))&(C8.n_visits>=30)].sort_values("pct",ascending=False).head(10).drop(columns=["state","threshold"])
out8.append("\n### >=90% of capacity, top combinations (state A, n>=30)\n\n"+md(top90,"{:.2f}"))
write_section("t8_capacity","\n".join(out8)); print("\n".join(out6)); print("\n".join(out8)[:6000])
# ---- Task 9
cl={d:cleaned(d) for d in DIRN}
rows=[];rows_s=[]
for d in DIRN:
    x=cl[d]; mism=(x.TimeSlot!=x["TimeSlot.1"])
    rows.append((d,len(x),int(mism.sum()),100*mism.mean()))
    for stp,g in x.groupby("Stop"):
        m=(g.TimeSlot!=g["TimeSlot.1"]); rows_s.append((d,stp,STOPS[d].index(stp)+1,len(g),int(m.sum()),100*m.mean()))
D9=pd.DataFrame(rows,columns=["direction","n_visits","n_mismatch","pct_mismatch"]); S9=pd.DataFrame(rows_s,columns=["direction","stop","order","n_visits","n_mismatch","pct_mismatch"]).sort_values(["direction","order"])
save_table(D9,"t9_mismatch_by_direction"); save_table(S9,"t9_mismatch_by_stop")
rho=[(d,np.corrcoef(g.order,g.pct_mismatch)[0,1]) for d,g in S9.groupby("direction")]
out9.append("Visit-level comparison of `TimeSlot` (terminal departure) vs `TimeSlot.1` (service/arrival), pipeline-cleaned normal-day visits.\n\n"+md(D9,"{:.2f}")+"\n\n"+md(S9,"{:.2f}")+"\n\nCorrelation of mismatch with stop order: "+", ".join(f"{d}: {r:.3f}" for d,r in rho))
# stop-slot level: share of mismatches by slot
rows=[]
for d in DIRN:
    x=cl[d]
    for s,g in x.groupby("TimeSlot"): rows.append((d,s,len(g),100*(g.TimeSlot!=g["TimeSlot.1"]).mean()))
M9=pd.DataFrame(rows,columns=["direction","departure_slot","n_visits","pct_mismatch"]); save_table(M9,"t9_mismatch_by_slot"); out9.append("\nBy departure slot:\n\n"+md(M9,"{:.2f}"))
# figure data for optional figure
S9.to_csv("../figures/fig_slot_mismatch_data.csv",index=False)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; style()
fig,ax=plt.subplots(figsize=(8.5*CM,5.2*CM))
for d,c,m in [("toA",OI["blue"],"o"),("toB",OI["orange"],"s")]:
    g=S9[S9.direction==d]; ax.plot(g.order,g.pct_mismatch,color=c,marker=m,ms=2.5,label={"toA":"Towards Cibeles","toB":"Towards La Peseta"}[d])
ax.set_xlabel("Stop order along the route"); ax.set_ylabel("Visits with different slots (%)"); ax.legend(frameon=False); fig.tight_layout(); figsave(fig,"fig_slot_mismatch")
write_section("t9_slots","\n".join(out9)); print("\n".join(out9)[:3500])
