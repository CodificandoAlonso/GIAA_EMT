from common import *
import json
from scipy import stats
nan_nb=nan_g=mad0=tot=0
for d in DIRN:
    cl=cleaned(d)
    for dd in [stop_slot_boards(cl,d),stop_slot_dropoffs(cl)]:
        for k,v in dd.items():
            if len(v)<2: continue
            tot+=1; x=np.array(v,float)
            if np.median(np.abs(x-np.median(x)))==0: mad0+=1
            c,_=remove_outliers_mad(v)
            nb=test_negative_binomial(c); g=test_geometric(c)
            if nb.get("statistic",0)!=nb.get("statistic",0): nan_nb+=1
            if g["p_value"]!=g["p_value"]: nan_g+=1
sm=pd.read_csv("../tables/t3_dispersion_summary.csv"); T=pd.read_csv("../tables/t3_dispersion_per_combination.csv")
v=T.groupby("variable").agg(over=("over","mean"),med=("disp","median"))
o=pd.read_csv("../tables/t10_occupation_combinations.csv"); o["ok"]=o.is_normal.astype(str)=="True"; r=o[~o.ok]
J=dict(tot=tot,nan_nb=nan_nb,nan_g=nan_g,mad0=mad0,over_b=100*v.loc["boardings","over"],over_a=100*v.loc["alightings","over"],med_b=v.loc["boardings","med"],med_a=v.loc["alightings","med"],
 n_rej=len(r),n_term=int(r.stop.isin([2646,5727]).sum()),n23=int((r.slot==23).sum()),n23_nt=int(((r.slot==23)&~r.stop.isin([2646,5727])).sum()))
json.dump(J,open("../sections/stats80.json","w")); print(J)
