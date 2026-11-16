from common import *
INP=f"{ROOT}/GAMA/src/TEST_MOBILITY/includes/INPUTS"
fits={80:pd.read_csv("../tables/fits_per_combination.csv"),75:pd.read_csv("../tables/fits_per_combination_cut75.csv")}
tts={80:pd.read_csv("../tables/t10_traveltime_combinations.csv"),75:pd.read_csv("../tables/t10_traveltime_combinations_cut75.csv")}
rows=[]; det=[]
for d in DIRN:
    old=pd.read_csv(f"{ROOT}/BASE_DATA/old_input_data_E01_{d}.csv")
    for dtype,var in [("Board","boardings"),("DropOff","alightings")]:
        o=old[old.DataType==dtype]
        for cut,F in fits.items():
            x=F[(F.direction==d)&(F.variable==var)][["stop","slot","chosen","param1","param2"]]
            m=o.merge(x,left_on=["Stop","Timeslot"],right_on=["stop","slot"],how="left")
            t=(m.chosen==m.DistributionType)
            p=t&np.isclose(m.Param1,m.param1,rtol=1e-6,atol=1e-9)&np.isclose(m.Param2.fillna(0),m.param2.fillna(0),rtol=1e-6,atol=1e-9)
            rows.append((var,d,cut,len(o),int(t.sum()),int(p.sum())))
            m["match_type"]=t; m["match_exact"]=p; m["cut"]=cut; m["variable"]=var; m["direction"]=d; det.append(m)
    # travel times
    T=pd.read_csv(f"{INP}/input_times_stops_{d}.csv")
    for cut,tt in tts.items():
        t=tt[tt.direction==d]; n=ok=0
        for _,r in T.iterrows():
            for s in SLOTS:
                n+=1
                q=t[(t.segment==r.StopsCodes)&(t.slot==s)]
                if len(q)==1 and np.isclose(q["mean"].iloc[0],r[f"Mean_{s}"],rtol=1e-6) and np.isclose(q["std"].iloc[0],r[f"Std_{s}"],rtol=1e-6): ok+=1
        rows.append(("travel times",d,cut,n,ok,ok))
R=pd.DataFrame(rows,columns=["variable","direction","cut","n_combinations_in_file","same_distribution_type","same_type_and_params"])
save_table(R,"t_old_input_comparison"); pd.concat(det).to_csv("../tables/t_old_input_comparison_detail.csv",index=False)
print(R.to_string())
D=pd.concat(det); print(D[(D.cut==80)&(D.variable=="boardings")&(~D.match_type)][["direction","Stop","Timeslot","DistributionType","chosen"]].head(8))
