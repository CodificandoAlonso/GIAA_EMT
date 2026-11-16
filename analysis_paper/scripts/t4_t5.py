from common import *
from scipy import stats
out4=[]; out5=[]
def normal_days(df): return df[(df.DayType=="LA")&(df.FreeDay==0)]
def valid_bd(df): return (df.Board>=0)&(df.DropOff>=0)&(df.Board<80)&(df.DropOff<80)
raw={d:normal_days(load_dir(d)) for d in DIRN}
NS={d:len(STOPS[d]) for d in DIRN}
def complete_trips(df,d):
    n=df.groupby("TripId").size(); return n[n==NS[d]].index
# ----------- 4.1-4.3, 4.6
variants=[]
trip_rows=[]
for d in DIRN:
    df=raw[d]
    comp=set(complete_trips(df,d))
    ok_vis=valid_bd(df)&(df.Occupation>=0)&(df.Occupation<80)       # all conditions of clean_dataframe (<80) + clean_dataframe_advanced
    # trips whose every visit passes cleaning
    bad_trips=set(df.loc[~ok_vis,"TripId"])
    sets={
     "S0 raw, all normal-day visits":df,
     "S1 pipeline-cleaned visits (partial trips allowed)":df[ok_vis],
     "S2 complete trips, raw":df[df.TripId.isin(comp)],
     "S3 complete trips with no visit removed by cleaning":df[df.TripId.isin(comp-bad_trips)],
    }
    for name,x in sets.items():
        for term_lab,xx in [("with terminals",x),("without terminals",x[~x.Stop.isin([2646,5727])])]:
            B=xx.Board.sum(); D=xx.DropOff.sum()
            variants.append((d,name,term_lab,xx.TripId.nunique(),len(xx),int(B),int(D),100*(D/B-1)))
    for sub in ["S3 complete trips with no visit removed by cleaning"]:
      S3=sets[sub]
      for term_lab,xx in [("with terminals",S3),("without terminals",S3[~S3.Stop.isin([2646,5727])])]:
        g=xx.groupby("TripId").agg(boards=("Board","sum"),drops=("DropOff","sum"))
        g["diff"]=g.boards-g.drops; g["direction"]=d; g["terminals"]=term_lab; g["subset"]=sub[:3].strip()
        trip_rows.append(g.reset_index())
V=pd.DataFrame(variants,columns=["direction","subset","terminals","n_trips","n_visits","sum_boardings","sum_alightings","imbalance_%_(alightings/boardings-1)"])
# combined
comb=[]
for (name,t),g in V.groupby(["subset","terminals"]):
    B=g.sum_boardings.sum(); D=g.sum_alightings.sum(); comb.append(("both",name,t,g.n_trips.sum(),g.n_visits.sum(),B,D,100*(D/B-1)))
V=pd.concat([V,pd.DataFrame(comb,columns=V.columns)]).sort_values(["subset","terminals","direction"]).reset_index(drop=True)
save_table(V,"t4_imbalance_variants")
out4.append("### 4.2 / 4.6 Aggregate imbalance = sum(alightings)/sum(boardings) - 1 (paper: -4.4 %)\n\n"+md(V,"{:.2f}"))
TR=pd.concat(trip_rows); save_table(TR,"t4_per_trip_balance")
rows=[]
for (d,t,sb),g in TR.groupby(["direction","terminals","subset"]):
    rel=(g.drops/g.boards-1).replace([np.inf,-np.inf],np.nan).dropna()
    rows.append((d,sb,t,len(g),g["diff"].median(),g["diff"].quantile(.25),g["diff"].quantile(.75),g["diff"].mean(),100*(g["diff"]>0).mean(),100*(g["diff"]==0).mean(),100*(g["diff"]<0).mean(),100*rel.median(),100*rel.quantile(.25),100*rel.quantile(.75)))
dist=pd.DataFrame(rows,columns=["direction","subset","terminals","n_trips","diff_median","diff_q25","diff_q75","diff_mean","%trips boards>alightings","%trips equal","%trips boards<alightings","rel_imbalance_median_%","rel_q25_%","rel_q75_%"])
save_table(dist,"t4_trip_balance_distribution")
out4.append("\n### 4.1/4.3 Per-expedition balance (diff = boardings - alightings; subset S3)\n\n"+md(dist,"{:.2f}"))

# ----------- 4.4 last-stop occupation
rows=[]; neg=[]
for d in DIRN:
    df=raw[d]; comp=set(complete_trips(df,d))
    ok_vis=valid_bd(df)&(df.Occupation>=0)&(df.Occupation<80); bad=set(df.loc[~ok_vis,"TripId"])
    x=df[df.TripId.isin(comp)].sort_values(["TripId","order"]).copy()
    x["bd"]=x.Board-x.DropOff
    x["cum"]=x.groupby("TripId")["bd"].cumsum()
    last=x[x.order==NS[d]-1]
    clean_last=last[~last.TripId.isin(bad)]
    for lab,l in [("complete trips, raw",last),("complete trips, cleaned (S3)",clean_last)]:
        c=l["cum"]; rec=l["Occupation"]
        rows.append((d,lab,len(l),c.mean(),c.median(),c.quantile(.25),c.quantile(.75),c.abs().mean(),c.min(),c.max(),rec.median(),rec.quantile(.25),rec.quantile(.75)))
    # 4.5 negative cumulative before cleaning
    negcum=x.groupby("TripId")["cum"].min()<0
    # same with recorded Occupation <0 anywhere (raw)
    negrec=x.groupby("TripId")["Occupation"].min()<0
    # negative in cleaned trips
    xc=x[~x.TripId.isin(bad)]; negc=xc.groupby("TripId")["cum"].min()<0
    # all (incl. incomplete) normal-day trips, recorded
    allneg=df.groupby("TripId")["Occupation"].min()<0
    neg.append((d,len(negcum),100*negcum.mean(),100*negrec.mean(),len(allneg),100*allneg.mean(),len(negc),100*negc.mean()))
L=pd.DataFrame(rows,columns=["direction","subset","n_trips","computed_occ_last_mean","median","q25","q75","mean_abs","min","max","recorded_Occ_last_median","rec_q25","rec_q75"])
save_table(L,"t4_last_stop_occupation")
out4.append("\n### 4.4 Occupation computed at the last stop (cumulative Board-DropOff from 0); ideal value 0\n\n"+md(L,"{:.2f}"))
N=pd.DataFrame(neg,columns=["direction","n_complete_trips_raw","%trips cumulative occupancy <0 at some stop (raw, complete trips)","%trips recorded Occupation<0 at some stop (raw, complete trips)","n_all_normal_day_trips","%trips recorded Occupation<0 at some stop (all trips, raw)","n_trips_S3","%trips cumulative<0 after cleaning (S3)"])
save_table(N,"t4_negative_cumulative")
out4.append("\n### 4.5 Share of expeditions where occupancy turns negative at some stop\n\n"+md(N,"{:.2f}"))
# terminal concentration: per-stop boards/alightings imbalance S3
rows=[]
for d in DIRN:
    df=raw[d]; comp=set(complete_trips(df,d)); ok_vis=valid_bd(df)&(df.Occupation>=0)&(df.Occupation<80); bad=set(df.loc[~ok_vis,"TripId"])
    x=df[df.TripId.isin(comp-bad)]
    g=x.groupby("Stop").agg(boards=("Board","sum"),drops=("DropOff","sum"),n=("Board","size")).reindex(STOPS[d]).reset_index()
    g["net"]=g.boards-g.drops; g["direction"]=d; g["order"]=range(1,len(g)+1); rows.append(g)
PS=pd.concat(rows)[["direction","order","Stop","n","boards","drops","net"]]
save_table(PS,"t4_per_stop_net")
out4.append("\n### 4.6 Net boardings-alightings per stop (S3); terminals are the first and last row of each direction\n\n"+md(PS,"{:.0f}"))
write_section("t4_balance","\n".join(out4)); print("\n".join(out4))

# ============ TASK 5
visits=[]; rows=[]; fr=[]; tripcorr=[]
for d in DIRN:
    df=cleaned(d).sort_values(["TripId","order"]).copy()
    g=df.groupby("TripId")
    df["load"]=g["Occupation"].shift(1); df["prev_order"]=g["order"].shift(1)
    v=df[(df.prev_order.notna())&(df.order-df.prev_order==1)].copy()
    v["direction"]=d
    visits.append(v[["direction","TripId","Stop","order","TimeSlot","TimeSlot.1","load","Board","DropOff","Occupation"]])
    for (stop,s),x in v.groupby(["Stop","TimeSlot.1"]):
        n=len(x)
        if n>=3 and x.load.nunique()>1 and x.DropOff.nunique()>1:
            pr,pp=stats.pearsonr(x.load,x.DropOff); sr,sp=stats.spearmanr(x.load,x.DropOff)
        else: pr=pp=sr=sp=np.nan
        rows.append((d,stop,STOPS[d].index(stop)+1,s,n,pr,pp,sr,sp))
    # fraction alighting
    w=v[v["load"]>0].assign(frac=lambda t:t.DropOff/t["load"])
    for stop,x in w.groupby("Stop"):
        fr.append((d,stop,STOPS[d].index(stop)+1,len(x),x.frac.mean(),x.frac.quantile(.25),x.frac.median(),x.frac.quantile(.75)))
    w2=w; fr.append((d,"ALL",0,len(w2),w2.frac.mean(),w2.frac.quantile(.25),w2.frac.median(),w2.frac.quantile(.75)))
    # per trip cumulative correlation (complete trips)
    comp=df.groupby("TripId").size(); comp=comp[comp==NS[d]].index
    c=df[df.TripId.isin(comp)].copy()
    c["cB"]=c.groupby("TripId")["Board"].cumsum(); c["cD"]=c.groupby("TripId")["DropOff"].cumsum()
    def corr(x): 
        return np.corrcoef(x.cB,x.cD)[0,1] if x.cB.nunique()>1 and x.cD.nunique()>1 else np.nan
    tc=c.groupby("TripId").apply(corr,include_groups=False)
    tripcorr.append((d,len(tc),tc.notna().sum(),tc.median(),tc.quantile(.25),tc.quantile(.75),tc.mean()))
VIS=pd.concat(visits); VIS.rename(columns={"TimeSlot":"slot_departure","TimeSlot.1":"slot_service","load":"load_on_arrival","Board":"boardings","DropOff":"alightings","Occupation":"occupancy_after"}).to_csv("../tables/t5_visits.csv",index=False)
C=pd.DataFrame(rows,columns=["direction","stop","order","slot","n","pearson_r","pearson_p","spearman_r","spearman_p"]); save_table(C,"t5_corr_per_combination")
rows=[]
for d,x in C.groupby("direction"):
    x=x.dropna(subset=["pearson_r"])
    rows.append((d,len(x),x.pearson_r.median(),x.pearson_r.quantile(.25),x.pearson_r.quantile(.75),100*((x.pearson_p<.05)&(x.pearson_r>0)).mean(),100*((x.pearson_p<.05)&(x.pearson_r<0)).mean(),
                 x.spearman_r.median(),x.spearman_r.quantile(.25),x.spearman_r.quantile(.75),100*((x.spearman_p<.05)&(x.spearman_r>0)).mean(),100*((x.spearman_p<.05)&(x.spearman_r<0)).mean()))
CS=pd.DataFrame(rows,columns=["direction","n_combinations","pearson_median","q25","q75","%sig_positive","%sig_negative","spearman_median","q25 ","q75 ","%sig_positive ","%sig_negative "]); save_table(CS,"t5_corr_summary")
out5.append("### 5.2 Correlation between alightings and arrival load per (stop, service slot)\n\n"+md(CS,"{:.3f}"))
# split: excluding combos with small n
C30=C[C.n>=30]
rows=[(d,len(x),x.pearson_r.median(),100*((x.pearson_p<.05)&(x.pearson_r>0)).mean(),x.spearman_r.median(),100*((x.spearman_p<.05)&(x.spearman_r>0)).mean()) for d,x in C30.dropna(subset=["pearson_r"]).groupby("direction")]
out5.append("\nRestricted to combinations with n >= 30:\n\n"+md(pd.DataFrame(rows,columns=["direction","n_combinations","pearson_median","%sig_pos_pearson","spearman_median","%sig_pos_spearman"]),"{:.3f}"))
F=pd.DataFrame(fr,columns=["direction","stop","order","n_visits_(load>0)","frac_mean","frac_q25","frac_median","frac_q75"]); save_table(F,"t5_fraction_alighting")
out5.append("\n### 5.3 Fraction of the arriving load that alights (alightings/load)\n\n"+md(F,"{:.3f}"))
T=pd.DataFrame(tripcorr,columns=["direction","n_complete_trips","n_with_defined_corr","median","q25","q75","mean"]); save_table(T,"t5_trip_cumulative_corr")
out5.append("\n### 5.4 Per-expedition correlation of cumulative boardings and alightings along the route\n\n"+md(T,"{:.3f}"))
out5.append(f"\n### 5.5 Visit-level CSV: `tables/t5_visits.csv` ({len(VIS)} rows; first stop excluded, load = recorded Occupation of the previous stop of the same trip, only consecutive visits both surviving cleaning).")
write_section("t5_alighting_load","\n".join(out5)); print("\n".join(out5))
