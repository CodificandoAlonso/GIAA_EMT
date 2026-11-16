"""Shared loaders for the paper analysis. Reuses the pipeline functions; nothing is reimplemented
except where explicitly noted in RESULTS.md."""
import sys, os, glob, json, io, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
ROOT = "/home/hector/Desktop/CATEDRA/GIAA_EMT"
SRC = f"{ROOT}/DATOS/src"
sys.path.insert(0, SRC)
# pipeline functions (DATOS/src/*.py)
from generate_gaussian import clean_dataframe_advanced                      # generate_gaussian.py:483
OCC_CUT = int(os.environ.get('OCC_CUT', 80))   # 80 by default; 75 only for the provenance comparison (compare_old_input.py)
SUF = '' if OCC_CUT == 80 else f'_cut{OCC_CUT}'
def clean_dataframe(data: pd.DataFrame, direction: int):
    """original pipeline cleaning with the Occupation < 80 cut (the repo's generate_gaussian.py:477 has < 75; not modified)"""
    data = data[data["Occupation"] >= 0]
    data = data[data["Occupation"] < OCC_CUT]
    data = data[data["Direction"] == direction]
    return data
from fussion_gauss import is_normal_simplified                              # fussion_gauss.py:40

# --- functions that live only inside the notebook final_analysis_board_dropoff.ipynb (cell 4): load their source verbatim
def _load_nb_cell(nbname, idx):
    nb = json.load(open(f"{SRC}/{nbname}"))
    return "".join(nb["cells"][idx]["source"])
_ns = {}
exec("import numpy as np\nimport pandas as pd\nfrom scipy import stats\n"
     + _load_nb_cell("final_analysis_board_dropoff.ipynb", 4), _ns)
test_geometric = _ns["test_geometric"]; test_negative_binomial = _ns["test_negative_binomial"]
test_normal_chi2 = _ns["test_normal_chi2"]; remove_outliers_mad = _ns["remove_outliers_mad"]
select_by_aic = _ns["select_by_aic"]

# stop order of the route (GAMA/.../mobility_performance.gaml, load_401)
STOPS = {"toA": [2646, 562, 4090, 4188, 5939, 3995, 3991, 3903, 2539, 2535, 1929, 4032, 5360, 82, 5727],
         "toB": [5727, 81, 1167, 2538, 3929, 3990, 3994, 5938, 4187, 2964, 649, 2646]}
DIRN = {"toA": 2, "toB": 1}
DIRS = {"toA": f"{ROOT}/DATOS/data/E01_toA/NEW", "toB": f"{ROOT}/DATOS/data/E01_toB"}
SLOTS = list(range(5, 24))
CAP = 80

def load_raw(d):
    fs = sorted(glob.glob(DIRS[d] + "/*.csv"))
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)

def load_dir(d):
    """all visits of direction d (Direction filter only), with stop order index"""
    df = load_raw(d)
    df = df[df["Direction"] == DIRN[d]].copy()
    order = {s: i for i, s in enumerate(STOPS[d])}
    df["order"] = df["Stop"].map(order)
    return df

def cleaned(d, occ_cut=None):
    """pipeline cleaning: clean_dataframe (Direction + Occupation range) then clean_dataframe_advanced('LA')"""
    df = load_dir(d)
    x = clean_dataframe(df, DIRN[d])
    return clean_dataframe_advanced(x, "LA")

def save_table(df, name, index=False):
    df.to_csv(f"{ROOT}/analysis_paper/tables/{name}.csv", index=index)

def write_section(name, text):
    os.makedirs(f"{ROOT}/analysis_paper/sections", exist_ok=True)
    open(f"{ROOT}/analysis_paper/sections/{name}.md", "w").write(text)

def md(df, floatfmt="{:.2f}"):
    def f(v):
        if isinstance(v, (float, np.floating)):
            return "" if np.isnan(v) else floatfmt.format(v)
        return str(v)
    cols = list(df.columns)
    rows = ["| " + " | ".join(map(str, cols)) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        rows.append("| " + " | ".join(f(r[c]) for c in cols) + " |")
    return "\n".join(rows)

def stop_slot_boards(cl, d):
    """boardings aggregated per stop, per day and arrival slot (TimeSlot.1), as in final_analysis_board_dropoff cell 3/7:
    for every unique day of the stop's cleaned data, sum(Board) in that slot (days without buses give 0)."""
    out = {}
    for stop, g in cl.groupby("Stop"):
        days = g["EventDate"].unique()
        piv = g.groupby(["EventDate", "TimeSlot.1"])["Board"].sum().unstack(fill_value=0).reindex(index=days, columns=SLOTS, fill_value=0)
        for s in SLOTS:
            out[(stop, s)] = piv[s].tolist()
    return out

def stop_slot_dropoffs(cl):
    out = {}
    for stop, g in cl.groupby("Stop"):
        for s in SLOTS:
            out[(stop, s)] = g.loc[g["TimeSlot.1"] == s, "DropOff"].tolist()
    return out

# ---- figure style
OI = {"blue":"#0072B2","orange":"#E69F00","verm":"#D55E00","green":"#009E73","sky":"#56B4E9","purple":"#CC79A7","black":"#000000","yellow":"#F0E442"}
CM = 1/2.54
def style():
    import matplotlib as mpl
    mpl.rcParams.update({"font.family":"serif","font.serif":["DejaVu Serif","Times New Roman","Liberation Serif"],
        "font.size":8,"axes.labelsize":8,"xtick.labelsize":7,"ytick.labelsize":7,"legend.fontsize":7,
        "axes.linewidth":0.6,"lines.linewidth":1.0,"pdf.fonttype":42,"savefig.bbox":"tight","savefig.pad_inches":0.02,
        "axes.spines.top":False,"axes.spines.right":False})
def figsave(fig, name):
    fig.savefig(f"{ROOT}/analysis_paper/figures/{name}.pdf")
