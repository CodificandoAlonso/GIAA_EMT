from common import *
import re
out0, out1 = [], []
raw = {d: load_raw(d) for d in DIRN}
dfs = {d: load_dir(d) for d in DIRN}

# ---------------- TASK 0
rows=[]
for d in DIRN:
    fs = sorted(glob.glob(DIRS[d]+"/*.csv"))
    schemas = {tuple(pd.read_csv(f, nrows=0).columns) for f in fs}
    rows.append((d, len(fs), len(schemas), ", ".join(pd.read_csv(fs[0], nrows=0).columns)))
t0_schema = pd.DataFrame(rows, columns=["direction","n_csv","n_distinct_schemas","columns"])
save_table(t0_schema, "t0_schema")
out0.append(md(t0_schema))

# trip id equality, ordering check
chk=[]
for d in DIRN:
    df = dfs[d]
    same = (df.TripId == df["TripId.1"]).mean()
    # arrival-time monotonic along stop order (use departure date + EventTime.1; crossing midnight -> add 1 day if date.1 > date)
    t = pd.to_datetime(df["EventDate.1"] + " " + df["EventTime.1"].str[:15])
    df = df.assign(t=t).sort_values(["TripId","order"])
    mono = df.groupby("TripId")["t"].apply(lambda s: s.is_monotonic_increasing)
    chk.append((d, same, mono.mean(), mono.size))
t0_chk = pd.DataFrame(chk, columns=["direction","share_TripId==TripId.1","share_trips_with_arrival_time_increasing_in_stop_order","n_trips"])
save_table(t0_chk, "t0_order_check"); out0.append(md(t0_chk, "{:.4f}"))

# Occupation recorded? identity check
idrows=[]
for d in DIRN:
    for label, df in [("raw (all visits of direction)", dfs[d]), ("cleaned (pipeline, normal days)", cleaned(d))]:
        df = df.sort_values(["TripId","order"]).copy()
        g = df.groupby("TripId")
        df["prev_occ"] = g["Occupation"].shift(1); df["prev_order"] = g["order"].shift(1)
        cons = df[(df.prev_order.notna()) & (df.order - df.prev_order == 1)]
        calc = cons.prev_occ + cons.Board - cons.DropOff
        ok = (calc == cons.Occupation)
        ok_clip = (calc.clip(lower=0) == cons.Occupation)
        first = df[df.order == 0]
        okf = ((first.Board - first.DropOff) == first.Occupation).mean() if len(first) else np.nan
        idrows.append((d, label, len(cons), ok.mean()*100, ok_clip.mean()*100, len(first), okf*100))
t0_id = pd.DataFrame(idrows, columns=["direction","subset","n_consecutive_pairs","% Occ == prevOcc+Board-DropOff","% same, calc clipped at 0","n_first_stop_visits","% first stop: Occ == Board-DropOff"])
save_table(t0_id, "t0_occupation_identity"); out0.append(md(t0_id))

# windows
w=[]
for d in DIRN:
    ds=sorted(dfs[d].EventDate.unique()); w.append((d, ds[0], ds[-1], len(ds)))
t0_w=pd.DataFrame(w,columns=["direction","first_date","last_date","n_distinct_dates"]); save_table(t0_w,"t0_window"); out0.append(md(t0_w))
same_dates = set(dfs["toA"].EventDate)==set(dfs["toB"].EventDate)
out0.append(f"\nSet of dates identical in both folders: **{same_dates}**")
write_section("t0_data", "\n\n".join(out0))

# ---------------- TASK 1
alld = pd.concat([dfs["toA"], dfs["toB"]])
day = alld.groupby("EventDate").agg(DayType=("DayType","first"), FreeDay=("FreeDay","max"), Weekday=("Weekday","first")).reset_index()
def reason(r):
    if r.DayType=="LA" and r.FreeDay==0: return "normal"
    if r.Weekday in ("S","D"): return "weekend (Sat/Sun)"
    if r.DayType=="FE": return "public holiday (Mon-Fri)"
    if r.DayType=="LA" and r.FreeDay==1: return "free-fare working day"
    return "other"
day["reason"]=day.apply(reason,axis=1)
cnt = day.reason.value_counts().rename_axis("category").reset_index(name="n_days")
cnt.loc[len(cnt)] = ["TOTAL", cnt.n_days.sum()]
save_table(cnt,"t1_days"); 
out1.append(f"First date: **{day.EventDate.min()}**, last date: **{day.EventDate.max()}**. (n days = {len(day)})\n")
out1.append(md(cnt))
# weekend on FE? holidays on weekend counted as weekend (precedence). check FE saturday?
out1.append("\nPrecedence: weekend > holiday > free fare. Note: all Sundays carry DayType FE; Saturdays DayType SA; holidays falling Mon-Fri are FE; FreeDay=1 occurs only in LA days.\n")
n_normal = int((day.reason=="normal").sum())
day_ndays = {d: dfs[d][(dfs[d].DayType=="LA")&(dfs[d].FreeDay==0)].EventDate.nunique() for d in DIRN}
out1.append(f"Normal days (DayType=LA & FreeDay=0): **{n_normal}** (toA: {day_ndays['toA']}, toB: {day_ndays['toB']}).\n")

# sample sizes
rows=[]
for d in DIRN:
    df = dfs[d]; nd = df[(df.DayType=="LA")&(df.FreeDay==0)]
    cl = cleaned(d)
    rows.append((d, nd.TripId.nunique(), len(nd), cl.TripId.nunique(), len(cl), df.TripId.nunique(), len(df), nd.Stop.nunique()))
t1_n = pd.DataFrame(rows, columns=["direction","trips_normal_days","visits_normal_days","trips_after_cleaning","visits_after_cleaning","trips_all_days","visits_all_days","n_stops"])
save_table(t1_n,"t1_sample_sizes"); out1.append("\n"+md(t1_n))

# removal by condition
conds = {
 "Occupation < 0": lambda x: x.Occupation<0,
 "Occupation >= 80": lambda x: x.Occupation>=80,
 "Board < 0": lambda x: x.Board<0,
 "DropOff < 0": lambda x: x.DropOff<0,
 "Board >= 80": lambda x: x.Board>=80,
 "DropOff >= 80": lambda x: x.DropOff>=80,
}
rows=[]; uni=[]
for d in DIRN:
    for scope, df in [("all records of direction", dfs[d]), ("normal-day records", dfs[d][(dfs[d].DayType=="LA")&(dfs[d].FreeDay==0)])]:
        n=len(df)
        for k,f in conds.items():
            m=f(df).sum(); rows.append((d,scope,k,int(m),100*m/n,n))
        u80 = ((df.Occupation<0)|(df.Occupation>=80)|(df.Board<0)|(df.DropOff<0)|(df.Board>=80)|(df.DropOff>=80))
        uni.append((d,scope,n,int(u80.sum()),100*u80.mean()))
t1_c=pd.DataFrame(rows,columns=["direction","scope","condition","n_records","pct","N_total"]); save_table(t1_c,"t1_removed_by_condition")
t1_u=pd.DataFrame(uni,columns=["direction","scope","N_total","unique_removed","pct"]); save_table(t1_u,"t1_removed_unique")
out1.append("\n"+md(t1_c,"{:.4f}")+"\n\n"+md(t1_u,"{:.4f}"))

# one record every two days
rows=[]
for d in DIRN:
    df=dfs[d]; nd=df[(df.DayType=="LA")&(df.FreeDay==0)]
    D=nd.EventDate.nunique(); S=nd.Stop.nunique()
    for lab,u in [("Occ<80",((nd.Occupation<0)|(nd.Occupation>=80)|(nd.Board<0)|(nd.DropOff<0)|(nd.Board>=80)|(nd.DropOff>=80))),
]:
        r=int(u.sum()); rows.append((d,lab,r,D,S,r/(D*S),(D*S)/r if r else np.nan))
for lab in ["Occ<80"]:
    sub=[r for r in rows if r[1]==lab]; r=sum(x[2] for x in sub); D=sub[0][3]
    S=sum(x[4] for x in sub); rows.append(("both",lab,r,D,S,r/(D*S),(D*S)/r))
t1_r=pd.DataFrame(rows,columns=["direction","cleaning","removed_records","normal_days","stops","removed/(days*stops)","inverse (days per removed record)"])
save_table(t1_r,"t1_removed_per_day_stop"); out1.append("\n"+md(t1_r,"{:.4f}"))

# n obs per combination
sumrows=[]; detail=[]
for d in DIRN:
    cl=cleaned(d)
    b=stop_slot_boards(cl,d); dr=stop_slot_dropoffs(cl)
    for (stop,s),v in b.items(): detail.append((d,"boardings (per stop-hour, day sums)",stop,s,len(v)))
    for (stop,s),v in dr.items(): detail.append((d,"alightings (per bus arrival)",stop,s,len(v)))
    # occupation per visit by departure slot
    for (stop,s),g in cl.groupby(["Stop","TimeSlot"]): detail.append((d,"occupation (per visit, departure slot)",stop,s,len(g)))
    # travel times per segment: trips in both consecutive stops, same arrival slot
    st=STOPS[d]
    for i in range(len(st)-1):
        a=cl[cl.Stop==st[i]][["TripId","TimeSlot.1"]]; bb=cl[cl.Stop==st[i+1]][["TripId","TimeSlot.1"]]
        for s in SLOTS:
            n=len(set(a[a["TimeSlot.1"]==s].TripId)&set(bb[bb["TimeSlot.1"]==s].TripId))
            detail.append((d,"travel times (per segment, both arrivals in slot)",f"{st[i]}-{st[i+1]}",s,n))
det=pd.DataFrame(detail,columns=["direction","variable","stop_or_segment","slot","n_obs"]); save_table(det,"t1_nobs_per_combination")
agg=det.groupby(["direction","variable"]).n_obs.agg(["count","min","median","max"]).reset_index()
agg.columns=["direction","variable","n_combinations","min","median","max"]
save_table(agg,"t1_nobs_summary"); out1.append("\n"+md(agg,"{:.1f}"))
low=det[det.n_obs>0].sort_values("n_obs").groupby(["direction","variable"]).head(0)
sl=det.groupby(["direction","variable","slot"]).n_obs.median().reset_index()
lows=[]
for (d,v),g in sl.groupby(["direction","variable"]):
    g=g.sort_values("n_obs").head(3); lows.append((d,v,", ".join(f"slot {int(r.slot)} (median n={r.n_obs:.0f})" for r in g.itertuples())))
tl=pd.DataFrame(lows,columns=["direction","variable","slots_with_fewest_obs"]); save_table(tl,"t1_lowest_slots"); out1.append("\n"+md(tl))
zero=det[det.n_obs==0].groupby(["direction","variable"]).size().reset_index(name="combinations_with_0_obs")
out1.append("\nCombinations with zero observations:\n\n"+(md(zero) if len(zero) else "none"))
write_section("t1_sizes","\n".join(out1))
print("\n\n".join(out0)); print("\n".join(out1))
