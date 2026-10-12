#!/usr/bin/env python3
r"""
validacion_completa.py — validacion de ocupacion a partir de bhatt_detalle.csv.

Cubre los cuatro diagnosticos:
  1. Descomposicion de BC en termino de NIVEL (medias) y de DISPERSION (sigmas),
     tambien en D_B = -ln BC (aditiva), con el contrafactual de cada termino.
  2. Regresion sim = a + b*esp con errores estandar e IC95, cota de la pendiente
     por la regresion inversa (la pendiente real queda entre b y 1/b_inv, porque
     mean_esp tambien tiene error), sesgo por cuartiles de ocupacion y Theil.
  3. Conservacion de masa (opcional, requiere --masa).
  4. Ruido entre replicas: variabilidad de cada metrica entre semillas y
     distribucion nula de BC entre replicas del MISMO modelo (techo alcanzable
     de % equivalentes y umbral calibrado empiricamente).
Si se pasan varios modelos, los compara celda a celda (McNemar).

Uso:
  python3 validacion_completa.py \
      --modelo M1_indep  r1/bhatt_detalle.csv r2/bhatt_detalle.csv ... \
      --modelo M2_binom  s1/bhatt_detalle.csv s2/bhatt_detalle.csv ... \
      [--masa masa_M2_binom.csv] [--masa-modelo M2_binom] \
      --umbral 0.97 --outdir validacion

  Un modelo con UN solo fichero funciona, pero entonces el diagnostico 4 no
  se puede calcular (se necesitan >= 2 replicas con semillas distintas).

  --masa: CSV con medias por celda, columnas
      direccion,franja,elemento,subidas_sim,subidas_esp,bajadas_sim,bajadas_esp
"""

import argparse
import itertools
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

KEYS = ["tipo", "direccion", "franja", "elemento"]
COLS = ["mean_sim", "std_sim", "mean_esp", "std_esp"]


# ------------------------------------------------------------------ nucleo
def bc_terminos(m1, s1, m2, s2):
    """(BC, termino_dispersion, termino_nivel) para dos normales."""
    m1, s1, m2, s2 = (np.asarray(v, float) for v in (m1, s1, m2, s2))
    with np.errstate(divide="ignore", invalid="ignore"):
        v = s1**2 + s2**2
        disp = np.sqrt(2.0 * s1 * s2 / v)
        niv = np.exp(-((m1 - m2) ** 2) / (4.0 * v))
    return disp * niv, disp, niv


def cargar(path, tipo):
    df = pd.read_csv(path)
    d = df[(df["tipo"] == tipo) & (df["estado"] == "evaluada")].copy()
    d = d.dropna(subset=COLS)
    d = d[(d.std_sim > 0) & (d.std_esp > 0)].copy()
    d["elemento"] = d["elemento"].astype(int)
    bc, disp, niv = bc_terminos(d.mean_sim, d.std_sim, d.mean_esp, d.std_esp)
    d["bc_calc"], d["bc_dispersion"], d["bc_nivel"] = bc, disp, niv
    d["ratio_sigma"] = d.std_sim / d.std_esp
    d["err"] = d.mean_sim - d.mean_esp
    return d


def theil(sim, obs):
    sim, obs = np.asarray(sim, float), np.asarray(obs, float)
    mse = np.mean((sim - obs) ** 2)
    u = np.sqrt(mse) / (np.sqrt(np.mean(sim**2)) + np.sqrt(np.mean(obs**2)))
    ss, so = sim.std(), obs.std()
    r = np.corrcoef(sim, obs)[0, 1]
    return {"U": u, "Um": (sim.mean() - obs.mean()) ** 2 / mse,
            "Us": (ss - so) ** 2 / mse, "Uc": 2 * (1 - r) * ss * so / mse,
            "r": r, "rmse": np.sqrt(mse), "mae": np.mean(np.abs(sim - obs))}


def metricas(d, umbral):
    """Un diccionario plano de metricas para una replica o un agregado."""
    reg = stats.linregress(d.mean_esp, d.mean_sim)
    inv = stats.linregress(d.mean_sim, d.mean_esp)
    th = theil(d.mean_sim, d.mean_esp)
    db_niv, db_disp = -np.log(d.bc_nivel), -np.log(d.bc_dispersion)
    return {
        "n_celdas": len(d),
        "pct_equiv": 100 * (d.bc_calc >= umbral).mean(),
        "bc_medio": d.bc_calc.mean(),
        "nivel_medio": d.bc_nivel.mean(),
        "disp_medio": d.bc_dispersion.mean(),
        "frac_DB_nivel": db_niv.sum() / (db_niv.sum() + db_disp.sum()),
        "sesgo_medio_pax": d.err.mean(),
        "sesgo_medio_sigmas": (d.err / d.std_esp).mean(),
        "mediana_ratio_sigma": d.ratio_sigma.median(),
        "pend_b": reg.slope, "pend_b_se": reg.stderr,
        "orden_a": reg.intercept, "orden_a_se": reg.intercept_stderr,
        "pend_b_cota_sup": 1 / inv.slope,
        "R2": reg.rvalue**2,
        "rmse": th["rmse"], "mae": th["mae"], "theil_U": th["U"],
        "Um": th["Um"], "Us": th["Us"], "Uc": th["Uc"],
    }


def agregar_replicas(reps):
    """Promedia las replicas por celda (varianzas promediadas, no sigmas)."""
    c = pd.concat(reps, ignore_index=True)
    g = c.groupby(KEYS)
    a = g.agg(mean_sim=("mean_sim", "mean"), mean_esp=("mean_esp", "first"),
              std_esp=("std_esp", "first")).reset_index()
    a["std_sim"] = np.sqrt(g["std_sim"].apply(lambda s: np.mean(s**2)).values)
    bc, disp, niv = bc_terminos(a.mean_sim, a.std_sim, a.mean_esp, a.std_esp)
    a["bc_calc"], a["bc_dispersion"], a["bc_nivel"] = bc, disp, niv
    a["ratio_sigma"] = a.std_sim / a.std_esp
    a["err"] = a.mean_sim - a.mean_esp
    return a


# ------------------------------------------------- 1 y 2: un modelo
def informe_modelo(nombre, d, umbral, outdir, tipo):
    m = metricas(d, umbral)
    print(f"\n{'='*70}\nMODELO {nombre}: {m['n_celdas']} celdas\n{'='*70}")

    print("\n[1] De donde viene la perdida de BC")
    print(f"  % equivalentes (BC>={umbral}) : {m['pct_equiv']:.1f}%")
    print(f"  BC medio {m['bc_medio']:.4f} = nivel {m['nivel_medio']:.4f} "
          f"x dispersion {m['disp_medio']:.4f} (aprox.)")
    print(f"  fraccion de D_B atribuible al nivel: {100*m['frac_DB_nivel']:.1f}% "
          f"(resto, dispersion)")
    print(f"  celdas donde limita la dispersion: "
          f"{100*(d.bc_dispersion < d.bc_nivel).mean():.1f}%")
    q = d.ratio_sigma.quantile([.05, .25, .5, .75, .95])
    print(f"  sigma_sim/sigma_esp: p05={q[.05]:.2f} p25={q[.25]:.2f} "
          f"med={q[.5]:.2f} p75={q[.75]:.2f} p95={q[.95]:.2f}; "
          f"sobredispersas {100*(d.ratio_sigma>1).mean():.1f}%")
    print(f"  contrafactual: dispersion perfecta -> "
          f"{100*(d.bc_nivel>=umbral).mean():.1f}% pasan | "
          f"nivel perfecto -> {100*(d.bc_dispersion>=umbral).mean():.1f}% pasan")

    print("\n[2] Regresion sim = a + b*esp")
    zb = (m["pend_b"] - 1) / m["pend_b_se"]
    za = m["orden_a"] / m["orden_a_se"]
    print(f"  b = {m['pend_b']:.4f} +- {1.96*m['pend_b_se']:.4f} (IC95)   "
          f"b-1=0: z={zb:+.1f}")
    print(f"  a = {m['orden_a']:+.3f} +- {1.96*m['orden_a_se']:.3f} (IC95)   "
          f"a=0: z={za:+.1f}   R2={m['R2']:.4f}")
    print(f"  cota por regresion inversa: la pendiente real esta entre "
          f"{m['pend_b']:.3f} y {m['pend_b_cota_sup']:.3f} "
          f"(mean_esp tambien tiene error)")
    sig_b, sig_a = abs(zb) > 1.96, abs(za) > 1.96
    if sig_b and not sig_a:
        diag = "MULTIPLICATIVO (proporcional a la ocupacion)"
    elif sig_a and not sig_b:
        diag = "ADITIVO (desplazamiento constante)"
    elif sig_a and sig_b:
        diag = "MIXTO (aditivo y proporcional)"
    else:
        diag = "ni a ni b distinguibles de (0, 1): sin sesgo sistematico lineal"
    print(f"  diagnostico: {diag}")
    cuart = pd.qcut(d.mean_esp, 4, labels=["Q1", "Q2", "Q3", "Q4"])
    t = d.groupby(cuart, observed=True).agg(
        esp=("mean_esp", "mean"), err=("err", "mean"),
        err_sigmas=("err", lambda s: (s / d.loc[s.index, "std_esp"]).mean()),
        pct_eq=("bc_calc", lambda s: 100 * (s >= umbral).mean()))
    print("  sesgo por cuartil de ocupacion esperada:")
    print("    " + t.round(2).to_string().replace("\n", "\n    "))
    print(f"  RMSE={m['rmse']:.3f}  MAE={m['mae']:.3f}  Theil U={m['theil_U']:.4f}  "
          f"Um={m['Um']:.3f} Us={m['Us']:.3f} Uc={m['Uc']:.3f}")

    print("\n  sensibilidad al umbral:")
    print("   " + "  ".join(f"{u:.2f}:{100*(d.bc_calc>=u).mean():.0f}%"
                            for u in (0.99, 0.98, 0.97, 0.95, 0.90, 0.85)))

    # figuras
    fig, ax = plt.subplots(1, 3, figsize=(18, 5.5))
    ok = d.bc_calc >= umbral
    lim = float(max(d.mean_esp.max(), d.mean_sim.max())) * 1.05
    xs = np.linspace(0, lim, 10)
    ax[0].scatter(d.mean_esp[~ok], d.mean_sim[~ok], s=14, alpha=.5, c="#d62728",
                  label=f"No equivalentes (n={int((~ok).sum())})")
    ax[0].scatter(d.mean_esp[ok], d.mean_sim[ok], s=14, alpha=.8, c="#2ca02c",
                  label=f"Equivalentes (n={int(ok.sum())})")
    ax[0].plot(xs, xs, "k--", lw=1.2, label="identidad")
    ax[0].plot(xs, m["orden_a"] + m["pend_b"] * xs, c="#1f77b4", lw=1.8,
               label=f"y={m['orden_a']:+.2f}+{m['pend_b']:.3f}x")
    ax[0].set(xlim=(0, lim), ylim=(0, lim), xlabel="Media esperada (EMT)",
              ylabel="Media simulada", title=f"{nombre}: simulado vs esperado")
    ax[0].legend(fontsize=8, loc="upper left")
    sc = ax[1].scatter(d.bc_nivel, d.bc_dispersion, c=d.bc_calc, s=14,
                       cmap="RdYlGn", vmin=0.7, vmax=1.0)
    ax[1].axhline(umbral, ls="--", c="grey", lw=1)
    ax[1].axvline(umbral, ls="--", c="grey", lw=1)
    ax[1].set(xlabel="Termino de nivel", ylabel="Termino de dispersion",
              title="Que factor limita cada celda")
    plt.colorbar(sc, ax=ax[1], label="BC")
    ax[2].scatter(d.mean_esp, d.err, s=14, alpha=.5, c="#1f77b4")
    ax[2].axhline(0, c="k", ls="--", lw=1)
    ax[2].plot(xs, m["orden_a"] + (m["pend_b"] - 1) * xs, c="#d62728", lw=1.8)
    ax[2].set(xlabel="Media esperada", ylabel="Error (sim - esp)",
              title="Sesgo vs nivel (aditivo: plano; proporcional: pendiente)")
    for a_ in ax:
        a_.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(outdir / f"validacion_{nombre}_{tipo}.png", dpi=200)
    plt.close(fig)
    return m


# ------------------------------------------------- 4: ruido entre replicas
def ruido_replicas(nombre, reps, umbral, outdir, maxpares=45, seed=0):
    print(f"\n[4] Ruido entre replicas — {nombre} ({len(reps)} replicas)")
    filas = [metricas(r, umbral) for r in reps]
    tab = pd.DataFrame(filas)
    tab.to_csv(outdir / f"metricas_replicas_{nombre}.csv", index=False)
    claves = ["pct_equiv", "bc_medio", "nivel_medio", "disp_medio",
              "sesgo_medio_pax", "sesgo_medio_sigmas", "pend_b", "orden_a", "R2"]
    res = tab[claves].agg(["mean", "std", "min", "max"]).T
    print("    " + res.round(4).to_string().replace("\n", "\n    "))

    rng = np.random.default_rng(seed)
    pares = list(itertools.combinations(range(len(reps)), 2))
    if len(pares) > maxpares:
        pares = [pares[i] for i in rng.choice(len(pares), maxpares, replace=False)]
    nulo = []
    for i, j in pares:
        m = reps[i][KEYS + ["mean_sim", "std_sim"]].merge(
            reps[j][KEYS + ["mean_sim", "std_sim"]], on=KEYS, suffixes=("_i", "_j"))
        bc, _, _ = bc_terminos(m.mean_sim_i, m.std_sim_i, m.mean_sim_j, m.std_sim_j)
        nulo.append(bc[np.isfinite(bc)])
    nulo = np.concatenate(nulo)
    q = np.quantile(nulo, [.01, .05, .5])
    print(f"  BC entre replicas del mismo modelo (n={len(nulo)} comparaciones):")
    print(f"    p01={q[0]:.4f}  p05={q[1]:.4f}  mediana={q[2]:.4f}")
    print(f"    TECHO: un modelo perfecto pasaria el umbral {umbral} en "
          f"{100*(nulo>=umbral).mean():.1f}% de las celdas")
    print(f"    umbral calibrado (p05 del nulo): {q[1]:.4f}  "
          f"(umbral con 95% de aceptacion de un modelo identico)")
    print("    (nota: compara dos estimaciones ruidosas, asi que el nulo es "
          "algo mas conservador que sim-vs-datos)")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(nulo, bins=50, color="#1f77b4", alpha=.8)
    ax.axvline(umbral, c="k", ls="--", label=f"umbral {umbral}")
    ax.axvline(q[1], c="#d62728", ls=":", label=f"p05 nulo = {q[1]:.3f}")
    ax.set(xlabel="BC entre replicas", ylabel="celdas",
           title=f"{nombre}: distribucion nula de BC")
    ax.legend()
    fig.tight_layout()
    fig.savefig(outdir / f"nulo_replicas_{nombre}.png", dpi=200)
    plt.close(fig)
    return q[1], 100 * (nulo >= umbral).mean()


# ------------------------------------------------- 3: conservacion de masa
def conservacion_masa(nombre, d, masa_csv):
    print(f"\n[3] Conservacion de masa — {nombre}")
    ms = pd.read_csv(masa_csv)
    req = ["direccion", "franja", "elemento", "subidas_sim", "subidas_esp",
           "bajadas_sim", "bajadas_esp"]
    faltan = [c for c in req if c not in ms.columns]
    if faltan:
        print(f"  columnas ausentes en {masa_csv}: {faltan}; no se ejecuta")
        return
    ms["elemento"] = ms["elemento"].astype(int)
    for k in ("subidas", "bajadas"):
        tot_s, tot_e = ms[f"{k}_sim"].sum(), ms[f"{k}_esp"].sum()
        dif = ms[f"{k}_sim"] - ms[f"{k}_esp"]
        t, p = stats.ttest_1samp(dif, 0.0)
        print(f"  {k:8}: sim={tot_s:.1f} esp={tot_e:.1f} ratio={tot_s/tot_e:.4f}  "
              f"dif/celda={dif.mean():+.3f} (t={t:+.2f}, p={p:.2g})")
    g = ms.groupby(["direccion", "franja"]).agg(
        sub_s=("subidas_sim", "sum"), sub_e=("subidas_esp", "sum"),
        baj_s=("bajadas_sim", "sum"), baj_e=("bajadas_esp", "sum"))
    g["balance_sim"] = g.sub_s - g.baj_s
    g["balance_esp"] = g.sub_e - g.baj_e
    g["ratio_baj"] = g.baj_s / g.baj_e
    g["ratio_sub"] = g.sub_s / g.sub_e
    print("  balance subidas-bajadas por sentido y franja (debe ser ~0 al final "
          "de la ruta):")
    print("    " + g[["ratio_sub", "ratio_baj", "balance_sim", "balance_esp"]]
          .round(3).to_string().replace("\n", "\n    "))
    j = d.merge(ms, on=["direccion", "franja", "elemento"], how="inner")
    if len(j) > 10:
        j["err_baj"] = j.bajadas_sim - j.bajadas_esp
        j["err_sub"] = j.subidas_sim - j.subidas_esp
        for c, et in (("err_baj", "error de bajadas"), ("err_sub", "error de subidas")):
            rho, p = stats.spearmanr(j[c], j.err)
            print(f"  Spearman({et}, error de ocupacion) = {rho:+.3f} (p={p:.2g})")
        print("  (error de ocupacion = sim-esp; bajadas de mas -> rho negativo; "
              "subidas de menos -> rho positivo)")


# ------------------------------------------------- comparacion de modelos
def comparar(modelos, umbral):
    nombres = list(modelos)
    print(f"\n{'='*70}\nCOMPARACION ENTRE MODELOS (por celda, replicas promediadas)\n{'='*70}")
    for a, b in itertools.combinations(nombres, 2):
        m = modelos[a][KEYS + ["bc_calc"]].merge(
            modelos[b][KEYS + ["bc_calc"]], on=KEYS, suffixes=("_a", "_b"))
        pa, pb = m.bc_calc_a >= umbral, m.bc_calc_b >= umbral
        n10, n01 = int((pa & ~pb).sum()), int((~pa & pb).sum())
        p = stats.binomtest(min(n10, n01), n10 + n01, 0.5).pvalue if n10 + n01 else np.nan
        print(f"  {a} vs {b}: {len(m)} celdas comunes | pasan solo {a}: {n10} | "
              f"pasan solo {b}: {n01} | McNemar p={p:.2g}")
        print(f"    BC medio: {a}={m.bc_calc_a.mean():.4f}  {b}={m.bc_calc_b.mean():.4f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modelo", nargs="+", action="append", required=True,
                    metavar=("NOMBRE", "CSV"),
                    help="NOMBRE seguido de uno o mas bhatt_detalle.csv (replicas)")
    ap.add_argument("--tipo", default="ocupacion", choices=["ocupacion", "tiempo"])
    ap.add_argument("--umbral", type=float, default=0.97)
    ap.add_argument("--masa", type=Path)
    ap.add_argument("--masa-modelo", help="a que modelo corresponde --masa")
    ap.add_argument("--outdir", type=Path, default=Path("validacion"))
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    modelos, replicas = {}, {}
    for spec in args.modelo:
        if len(spec) < 2:
            raise SystemExit("--modelo necesita NOMBRE y al menos un CSV")
        nombre, ficheros = spec[0], spec[1:]
        reps = [cargar(f, args.tipo) for f in ficheros]
        if not all(len(r) for r in reps):
            raise SystemExit(f"{nombre}: algun CSV no tiene celdas evaluadas con "
                             "mean_sim/std_sim/mean_esp/std_esp")
        replicas[nombre] = reps
        modelos[nombre] = reps[0] if len(reps) == 1 else agregar_replicas(reps)

    resumen = {}
    for nombre, d in modelos.items():
        resumen[nombre] = informe_modelo(nombre, d, args.umbral, args.outdir, args.tipo)
        if len(replicas[nombre]) >= 2:
            ruido_replicas(nombre, replicas[nombre], args.umbral, args.outdir)
        else:
            print(f"\n[4] {nombre}: una sola replica; ruido entre replicas NO calculable")
        if args.masa and args.masa_modelo == nombre:
            conservacion_masa(nombre, d, args.masa)
    if args.masa and args.masa_modelo not in modelos:
        print("\n[3] --masa ignorado: indica --masa-modelo con el nombre de un modelo")

    if len(modelos) > 1:
        comparar(modelos, args.umbral)
    pd.DataFrame(resumen).T.to_csv(args.outdir / "resumen_modelos.csv")
    print(f"\nSalidas en {args.outdir}/")


if __name__ == "__main__":
    main()