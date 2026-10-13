"""Regenerates every table, log and figure of the IA vs AG comparison (about 10 min; first run builds the cache)."""

import time

import a_integrity
import b_ia_vs_ag
import c_empirical
import d_risk
import e_cost
import f_robust
import load

if __name__ == "__main__":
    for m in ("AG", "IA"):
        load.load_model(m)
    for name, mod in (("A", a_integrity), ("B", b_ia_vs_ag), ("C", c_empirical), ("D", d_risk), ("E", e_cost), ("F", f_robust)):
        t = time.time()
        mod.main()
        print(f"Analysis {name}: {time.time() - t:.0f}s")
