#!/usr/bin/env python3
r"""
relacion_oferta_error.py — contraste estadistico de los mecanismos propuestos.

No basta con que un mecanismo sea "compatible" con el resultado: hay que
derivar de el una prediccion direccional sobre DONDE debe concentrarse el
error y comprobar si los datos la cumplen. Se contrastan dos hipotesis que
predicen cosas distintas.

  H1  SOBREOFERTA.  La ocupacion acumulada en la parada j vale
          occ_j = (1/n) * sum_{i<j} subidas_i  -  sum_{i<j} bajadas_i
      Las subidas se reparten entre n autobuses; las bajadas se muestrean por
      llegada y NO se dividen. Si n_sim > n_real por un factor k, el deficit
      absoluto es  (1 - 1/k) * (1/n) * sum subidas_i , es decir PROPORCIONAL
      a las subidas acumuladas aguas arriba, no a la ocupacion.
      -> Prediccion: |sesgo| crece con las subidas acumuladas por autobus.

  H2  MUESTREO INDEPENDIENTE DE BAJADAS.  Sin matriz origen-destino, las
      bajadas de cada parada se sortean por separado. En la realidad estan
      negativamente correlacionadas (quien baja en j ya no puede bajar en
      j+1). Al sortearlas independientes las varianzas se SUMAN en lugar de
      cancelarse parcialmente, y la ocupacion es una magnitud acumulada.
      -> Prediccion: sigma_sim/sigma_esp crece con la posicion en la ruta.

  H1 y H2 son mecanismos distintos: si ambos operan, sus errores deben ser
  aproximadamente INDEPENDIENTES entre si. Una correlacion alta indicaria
  que en realidad hay una sola causa.

Uso:
  python3 relacion_oferta_error.py bhatt_detalle.csv \
      --inputs-toa input_data_E01_toA.csv \
      --inputs-tob input_data_E01_toB.csv \
      --horario final_input.json \
      [--llegadas-reales llegadas_por_franja.csv] \
      --outdir .

  llegadas_por_franja.csv (opcional, para el contraste directo de H1):
      direccion,franja,llegadas_reales
      to_A,6,2.8
      ...
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ORDEN = {
    "to_A": [2646, 562, 4090, 4188, 5939, 3995, 3991, 3903,
             2539, 2535, 1929, 4032, 5360, 82, 5727],
    "to_B": [5727, 81, 1167, 2538, 3929, 3990, 3994, 5938,
             4187, 2964, 649, 2646],
}


def media_ajuste(kind, a, b):
    if kind == "NORMAL":
        return a
    if kind == "GEOMETRICAL":
        return (1 - a) / a if a > 0 else np.nan
    if kind == "NEGATIVE BINOMIAL":
        return a * (1 - b) / b if b > 0 else np.nan
    return np.nan


def corr(x, y, etiqueta, prediccion):
    """Pearson y Spearman con su p-valor, y veredicto frente a la prediccion."""
    m = np.isfinite(x) & np.isfinite(y)
    x, y = np.asarray(x)[m], np.asarray(y)[m]
    if len(x) < 4:
        print(f"  {etiqueta:52} n<4, sin contraste")
        return None
    r, pr = stats.pearsonr(x, y)
    rho, ps = stats.spearmanr(x, y)
    signo = "+" if rho > 0 else "-"
    if prediccion == "0":
        # prediccion de independencia: se "cumple" si la correlacion es debil
        ok = abs(rho) < 0.30
    else:
        ok = (signo == prediccion) and (ps < 0.05)
    print(f"  {etiqueta:52} n={len(x):4}  r={r:+.3f} (p={pr:.2g})  "
          f"rho={rho:+.3f} (p={ps:.2g})  "
          f"{'CUMPLE' if ok else 'no cumple'} (se predijo {prediccion})")
    return {"n": len(x), "pearson_r": r, "pearson_p": pr,
            "spearman_rho": rho, "spearman_p": ps, "cumple": bool(ok)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("detalle", type=Path)
    ap.add_argument("--inputs-toa", type=Path, required=True)
    ap.add_argument("--inputs-tob", type=Path, required=True)
    ap.add_argument("--horario", type=Path, required=True)
    ap.add_argument("--llegadas-reales", type=Path)
    ap.add_argument("--outdir", type=Path, default=Path("."))
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    d = pd.read_csv(args.detalle)
    d = d[(d.tipo == "ocupacion") & (d.estado == "evaluada")].copy()
    d = d.dropna(subset=["mean_sim", "std_sim", "mean_esp", "std_esp"])
    d["elemento"] = d["elemento"].astype(int)
    d["ratio_sigma"] = d.std_sim / d.std_esp
    d["sesgo_rel"] = (d.mean_sim - d.mean_esp) / d.mean_esp
    d["abs_sesgo_sigmas"] = (d.mean_sim - d.mean_esp).abs() / d.std_esp

    # --- posicion en la ruta y subidas acumuladas aguas arriba -------------
    inp = {}
    for dirc, f in (("to_A", args.inputs_toa), ("to_B", args.inputs_tob)):
        t = pd.read_csv(f)
        t["mean"] = [media_ajuste(k, a, b) for k, a, b
                     in zip(t.DistributionType, t.Param1, t.Param2)]
        inp[dirc] = t

    salidas = {}
    J = json.load(open(args.horario))
    for bus, deps in J.items():
        for stop, hhmm in deps:
            dirc = "to_A" if stop == "2646" else "to_B"
            fr = int(hhmm.split(":")[0])
            salidas[(dirc, fr)] = salidas.get((dirc, fr), 0) + 1

    pos, acum, nbus = [], [], []
    for _, r in d.iterrows():
        orden = ORDEN[r.direccion]
        try:
            j = orden.index(int(r.elemento))
        except ValueError:
            pos.append(np.nan); acum.append(np.nan); nbus.append(np.nan); continue
        pos.append(j)
        t = inp[r.direccion]
        up = t[(t.Stop.isin(orden[:j])) & (t.Timeslot == r.franja) &
               (t.DataType == "Board")]["mean"].sum()
        n = salidas.get((r.direccion, int(r.franja)), np.nan)
        acum.append(up); nbus.append(n)
    d["pos_ruta"] = pos
    d["subidas_acum"] = acum
    d["n_salidas"] = nbus
    d["subidas_acum_por_bus"] = d.subidas_acum / d.n_salidas
    d["deficit_abs"] = d.mean_esp - d.mean_sim

    print(f"=== Contrastes sobre {len(d)} celdas de ocupacion ===\n")

    print("--- H1  Sobreoferta: el deficit debe escalar con las subidas "
          "acumuladas por autobus ---")
    r1 = corr(d.subidas_acum_por_bus, d.deficit_abs,
              "deficit absoluto  vs  subidas acumuladas/bus", "+")
    corr(d.mean_esp, d.deficit_abs,
         "deficit absoluto  vs  ocupacion esperada (control)", "+")
    # discriminante: si manda la oferta, el deficit sigue a las subidas
    # incluso controlando por el nivel de ocupacion
    m = d.dropna(subset=["subidas_acum_por_bus", "deficit_abs", "mean_esp"])
    if len(m) > 10:
        X = np.column_stack([np.ones(len(m)), m.subidas_acum_por_bus, m.mean_esp])
        beta, *_ = np.linalg.lstsq(X, m.deficit_abs.values, rcond=None)
        yhat = X @ beta
        r2 = 1 - ((m.deficit_abs - yhat)**2).sum() / \
                 ((m.deficit_abs - m.deficit_abs.mean())**2).sum()
        print(f"  regresion multiple  deficit ~ subidas/bus + ocupacion_esp:")
        print(f"      b_subidas={beta[1]:+.4f}   b_ocup={beta[2]:+.4f}   "
              f"R2={r2:.3f}")
        print("      (si b_subidas sigue siendo positivo y significativo con "
              "la ocupacion controlada,\n       el deficit NO es un simple "
              "porcentaje del nivel: apunta a la oferta)")

    print("\n--- H2  Muestreo independiente de bajadas: la sobredispersion "
          "debe crecer con la posicion ---")
    r2t = corr(d.pos_ruta, d.ratio_sigma,
               "sigma_sim/sigma_esp  vs  posicion en la ruta", "+")
    corr(d.pos_ruta, d.abs_sesgo_sigmas,
         "|sesgo| en sigmas  vs  posicion en la ruta (control)", "+")

    print("\n--- Independencia de los dos errores ---")
    r3 = corr(d.abs_sesgo_sigmas, d.ratio_sigma,
              "|sesgo| en sigmas  vs  sigma_sim/sigma_esp", "0")
    if r3:
        print(f"      |rho| = {abs(r3['spearman_rho']):.3f}: "
              f"{'independientes, mecanismos separables' if abs(r3['spearman_rho'])<0.3 else 'ACOPLADOS, probablemente una sola causa'}")

    print("\n--- Cuanto explica cada agrupacion (eta cuadrado sobre el BC) ---")
    d["bc"] = d.coeff.astype(float)
    for g in ("direccion", "franja", "elemento", "pos_ruta"):
        gr = d.groupby(g)["bc"]
        ss_b = (gr.count() * (gr.mean() - d.bc.mean())**2).sum()
        ss_t = ((d.bc - d.bc.mean())**2).sum()
        print(f"  {g:12} eta2 = {ss_b/ss_t:.3f}   ({d[g].nunique()} niveles)")

    if args.llegadas_reales and args.llegadas_reales.exists():
        print("\n--- H1 directo: atenuacion frente a sobreoferta por franja ---")
        lr = pd.read_csv(args.llegadas_reales)
        agg = (d.groupby(["direccion", "franja"])
                 .agg(sim=("mean_sim", "mean"), esp=("mean_esp", "mean"))
                 .reset_index())
        agg = agg.merge(lr, on=["direccion", "franja"], how="inner")
        agg["n_sim"] = [salidas.get((r.direccion, int(r.franja)), np.nan)
                        for _, r in agg.iterrows()]
        agg["k_oferta"] = agg.n_sim / agg.llegadas_reales
        agg["atenuacion"] = agg.sim / agg.esp
        corr(agg.k_oferta, agg.atenuacion,
             "atenuacion (sim/esp)  vs  k = n_sim/n_real", "-")
        agg.to_csv(args.outdir / "relacion_oferta_por_franja.csv", index=False)
    else:
        print("\n--- H1 directo: NO EJECUTADO ---")
        print("  Falta --llegadas-reales. Es el contraste decisivo de H1:")
        print("  sin el, solo se comprueba que el deficit escala con las")
        print("  subidas, que es condicion necesaria pero no suficiente.")
        print("  Para obtenerlo, sobre los datos crudos de EMT y por sentido:")
        print("      arr = df[df.TimeSlot==f].groupby('EventDate').size()")
        print("      llegadas_reales = arr.mean()")

    # ---------------- figura ----------------
    fig, ax = plt.subplots(1, 3, figsize=(16, 5))
    ax[0].scatter(d.subidas_acum_por_bus, d.deficit_abs, s=14, alpha=.5,
                  color="#1f77b4")
    ax[0].axhline(0, ls="--", lw=1, color="grey")
    ax[0].set_xlabel("Subidas acumuladas por autobus")
    ax[0].set_ylabel("Deficit absoluto (esp - sim)")
    ax[0].set_title("H1: deficit frente a subidas acumuladas")

    bx = d.dropna(subset=["pos_ruta"]).groupby("pos_ruta")["ratio_sigma"]
    ax[1].errorbar(bx.mean().index, bx.mean().values,
                   yerr=bx.std().values, fmt="o-", color="#d62728", capsize=3)
    ax[1].axhline(1.0, ls="--", lw=1, color="grey")
    ax[1].set_xlabel("Posicion en la ruta")
    ax[1].set_ylabel("sigma_sim / sigma_esp")
    ax[1].set_title("H2: sobredispersion frente a posicion")

    ax[2].scatter(d.abs_sesgo_sigmas, d.ratio_sigma, s=14, alpha=.5,
                  color="#2ca02c")
    ax[2].axhline(1.0, ls="--", lw=1, color="grey")
    ax[2].set_xlabel("|sesgo| (sigmas)")
    ax[2].set_ylabel("sigma_sim / sigma_esp")
    ax[2].set_title("Independencia de los dos errores")
    for a in ax:
        a.grid(alpha=.25)
    fig.tight_layout()
    out = args.outdir / "relacion_oferta_error.png"
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print(f"\n  -> {out}")
    d.to_csv(args.outdir / "relacion_oferta_error_detalle.csv", index=False)
    print(f"  -> {args.outdir}/relacion_oferta_error_detalle.csv")


if __name__ == "__main__":
    main()