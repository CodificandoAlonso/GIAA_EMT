"""Fit boardings (per stop-hour) and alightings (per arrival) with the pipeline functions; save per-combination results."""
from common import *
import pickle
rows=[]; 
NOTEBOOK_EXCL = {"toA": {2646, 5727}, "toB": {2646, 5727}}   # excluded from the main loop of final_analysis_board_dropoff cells 5/8
for d in DIRN:
    cl = cleaned(d)
    data = {"boardings": stop_slot_boards(cl, d), "alightings": stop_slot_dropoffs(cl)}
    for var, dd in data.items():
        for (stop, s), vals in dd.items():
            vals=list(vals); n_raw=len(vals)
            cleaned_vals, outl = remove_outliers_mad(vals)         # threshold=3, 1.4826 (final notebook cell 4)
            n=len(cleaned_vals)
            r = dict(direction=d, variable=var, stop=stop, order=STOPS[d].index(stop), slot=s, n_raw=n_raw, n_clean=n, n_mad_removed=len(outl))
            if n>=2:
                a=np.array(cleaned_vals,float); m=a.mean(); v=a.var(ddof=1)
                r.update(mean=m, var=v, disp=(v/m if m>0 else np.nan))
                is_normal,_,_,_ = is_normal_simplified(cleaned_vals)
                nb = test_negative_binomial(cleaned_vals); ge = test_geometric(cleaned_vals)
                r.update(is_normal=bool(is_normal), is_nb=bool(nb['is_negbin']), is_geom=bool(ge['is_geometric']))
                df_tmp = pd.DataFrame(columns=["Stop","Timeslot","DistributionType","Param1","Param2"])
                chosen = select_by_aic(cleaned_vals, {'NORMAL':bool(is_normal),'NEGATIVE BINOMIAL':bool(nb['is_negbin']),'GEOMETRICAL':bool(ge['is_geometric'])}, stop, s, df_tmp)
                r.update(chosen=chosen, param1=(df_tmp.Param1.iloc[-1] if len(df_tmp) else np.nan), param2=(df_tmp.Param2.iloc[-1] if len(df_tmp) else np.nan))
            else:
                r.update(mean=np.nan,var=np.nan,disp=np.nan,is_normal=False,is_nb=False,is_geom=False,chosen=None)
            r["any_pass"]=bool(r["is_normal"] or r["is_nb"] or r["is_geom"])
            # tail percentiles before / after
            for q in (90,95,99):
                r[f"p{q}_before"]=np.percentile(vals,q) if n_raw else np.nan
                r[f"p{q}_after"]=np.percentile(cleaned_vals,q) if n else np.nan
            rows.append(r)
res=pd.DataFrame(rows); res.to_pickle("/tmp/claude-1000/-home-hector-Desktop-CATEDRA-GIAA-EMT/c51b089e-2f79-4530-a3c4-ee0404e4a409/scratchpad/fits"+SUF+".pkl")
res.to_csv("../tables/fits_per_combination"+SUF+".csv",index=False)
print(res.groupby(["direction","variable"]).agg(n=("slot","size"),any_pass=("any_pass","mean")))
