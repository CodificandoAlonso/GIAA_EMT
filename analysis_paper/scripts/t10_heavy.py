"""Occupation (analisis_ALL_OCCUPATION.ipynb cell 2 function, verbatim) and travel-time (analysis_time_between_stops.ipynb cell 14 logic)
non-rejection recomputation. Uses generate_gaussian.estimate_outliers (ESD) and fussion_gauss.is_normal_simplified."""
from common import *
import generate_gaussian as gg
from multiprocessing import Pool
import pickle
nbsrc = json.load(open(f"{SRC}/analisis_ALL_OCCUPATION.ipynb"))["cells"]
src = None
for c in nbsrc:
    s = "".join(c["source"])
    if "def generate_gaussian_per_slot_all_days" in s: src = s; break
ns = dict(vars(gg)); exec(src, ns)
occ_fn = ns["generate_gaussian_per_slot_all_days"]
estimate_outliers = gg.estimate_outliers

def occ_job(args):
    d, f = args
    df = pd.read_csv(f)
    df = clean_dataframe(df, DIRN[d])
    res = occ_fn(df, "Occupation")
    rows = []
    if res.empty: return rows
    r = res.iloc[0]; stop = int(r["Stop"])
    for s in SLOTS:
        n_inst = r[f"instances_{s}"]
        rows.append(dict(direction=d, stop=stop, slot=s, is_normal=r[f"IsNormal_{s}"], n=(len(n_inst) if isinstance(n_inst, list) else 0)))
    return rows

def tt_job(args):
    d, i = args
    st = STOPS[d]
    cl = get_cl(d)
    a = cl[cl.Stop == st[i]]; b = cl[cl.Stop == st[i+1]]
    rows = []
    for s in SLOTS:
        aa = a[a["TimeSlot.1"] == s][["TripId","EventTime.1"]]; bb = b[b["TimeSlot.1"] == s][["TripId","EventTime.1"]]
        m = aa.merge(bb, on="TripId", suffixes=("_a","_b"))
        ta = pd.to_timedelta(m["EventTime.1_a"].str[:15]); tb = pd.to_timedelta(m["EventTime.1_b"].str[:15])
        data = sorted((tb - ta).dt.total_seconds().tolist())
        n0 = len(data)
        isn, _, mean, std = is_normal_simplified(data)
        out_removed = 0
        if not isn:
            out_list = estimate_outliers(data.copy(), 20, False)
            for it in out_list: data.remove(it)
            out_removed = len(out_list)
            isn, _, mean, std = is_normal_simplified(data)
        rows.append(dict(direction=d, segment=f"{st[i]}-{st[i+1]}", seg_order=i, slot=s, n=n0, esd_removed=out_removed, is_normal=bool(isn), mean=mean, std=std))
    return rows

from functools import lru_cache
@lru_cache(None)
def get_cl(d): return cleaned(d)
if __name__ == "__main__":
    jobs_o = [(d, f) for d in DIRN for f in sorted(glob.glob(DIRS[d] + "/*.csv"))]
    jobs_t = [(d, i) for d in DIRN for i in range(len(STOPS[d]) - 1)]
    with Pool(16) as p:
        o = p.map(occ_job, jobs_o, chunksize=1)
        t = p.map(tt_job, jobs_t, chunksize=1)
    occ = pd.DataFrame([r for x in o for r in x]); tt = pd.DataFrame([r for x in t for r in x])
    occ.to_csv("../tables/t10_occupation_combinations"+SUF+".csv", index=False); tt.to_csv("../tables/t10_traveltime_combinations"+SUF+".csv", index=False)
    print(occ.groupby("direction").is_normal.agg(["size", "sum", "mean"])); print(tt.groupby("direction").is_normal.agg(["size", "sum", "mean"]))
