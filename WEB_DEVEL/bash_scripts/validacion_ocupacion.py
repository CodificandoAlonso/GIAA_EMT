#!/usr/bin/env python3
r"""
validacion_ocupacion.py — analisis de validacion a partir de bhatt_detalle.csv.

El porcentaje de celdas "fusionables" es un criterio de paso/no-paso sobre un
umbral que MEZCLA dos errores distintos: el desplazamiento de la media y el
desajuste de la dispersion. Una celda con la media perfecta y el doble de
desviacion falla; una celda con media desplazada media sigma y la dispersion
correcta pasa. Reportar solo el porcentaje oculta cual de los dos domina.

Este script descompone el coeficiente en sus dos factores

    BC = sqrt( 2 s1 s2 / (s1^2 + s2^2) )  *  exp( -(m1-m2)^2 / (4 (s1^2+s2^2)) )
         \______ termino de DISPERSION __/     \______ termino de NIVEL ______/

y anade las metricas de validacion habituales en simulacion: regresion de lo
simulado frente a lo observado (pendiente, ordenada, R2), RMSE, MAE y el
coeficiente de desigualdad de Theil con su descomposicion en sesgo, varianza
y covarianza.

Uso:
  python3 validacion_ocupacion.py /ruta/PLOTS/general/bhatt_detalle.csv \
                                  --tipo ocupacion --outdir /ruta/PLOTS/general
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def bc_terminos(m1, s1, m2, s2):
    """Devuelve (BC_total, termino_dispersion, termino_nivel)."""
    v = s1**2 + s2**2
    disp = np.sqrt(2.0 * s1 * s2 / v)
    niv = np.exp(-((m1 - m2) ** 2) / (4.0 * v))
    return disp * niv, disp, niv


def theil(sim, obs):
    """Coeficiente de desigualdad de Theil y su descomposicion.

    U cercano a 0 indica buen ajuste. La descomposicion reparte el error
    cuadratico medio entre sesgo (Um), varianza (Us) y covarianza (Uc).
    Un error concentrado en Uc es error no sistematico, el menos grave;
    en Um o Us indica error sistematico de nivel o de dispersion.
    """
    sim, obs = np.asarray(sim, float), np.asarray(obs, float)
    n = len(sim)
    mse = np.mean((sim - obs) ** 2)
    u = np.sqrt(mse) / (np.sqrt(np.mean(sim**2)) + np.sqrt(np.mean(obs**2)))
    ms, mo = sim.mean(), obs.mean()
    ss = sim.std(ddof=0)
    so = obs.std(ddof=0)
    r = np.corrcoef(sim, obs)[0, 1] if n > 1 else np.nan
    um = (ms - mo) ** 2 / mse
    us = (ss - so) ** 2 / mse
    uc = 2 * (1 - r) * ss * so / mse
    return {"U": u, "Um_sesgo": um, "Us_varianza": us, "Uc_covarianza": uc,
            "r": r, "rmse": np.sqrt(mse),
            "mae": float(np.mean(np.abs(sim - obs)))}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("detalle", type=Path, help="bhatt_detalle.csv")
    ap.add_argument("--tipo", default="ocupacion", choices=["ocupacion", "tiempo"])
    ap.add_argument("--umbral", type=float, default=0.97)
    ap.add_argument("--outdir", type=Path, default=Path("."))
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.detalle)
    d = df[(df["tipo"] == args.tipo) & (df["estado"] == "evaluada")].copy()
    d = d.dropna(subset=["mean_sim", "std_sim", "mean_esp", "std_esp"])
    if not len(d):
        raise SystemExit("sin celdas evaluadas con medias registradas; "
                         "vuelve a lanzar data_extractor.py con la version "
                         "que guarda mean_sim/std_sim/mean_esp/std_esp")

    bc, disp, niv = bc_terminos(d.mean_sim.values, d.std_sim.values,
                                d.mean_esp.values, d.std_esp.values)
    d["bc_calc"], d["bc_dispersion"], d["bc_nivel"] = bc, disp, niv
    d["ratio_sigma"] = d.std_sim / d.std_esp

    print(f"=== Validacion de {args.tipo}: {len(d)} celdas evaluadas ===\n")

    print("--- 1. De donde viene la perdida de coeficiente ---")
    print(f"  BC medio                      : {d.bc_calc.mean():.4f}")
    print(f"  termino de NIVEL medio        : {d.bc_nivel.mean():.4f}"
          f"   (perdida {100*(1-d.bc_nivel.mean()):.1f}%)")
    print(f"  termino de DISPERSION medio   : {d.bc_dispersion.mean():.4f}"
          f"   (perdida {100*(1-d.bc_dispersion.mean()):.1f}%)")
    dom = (d.bc_dispersion < d.bc_nivel).mean()
    print(f"  celdas donde manda la dispersion: {100*dom:.1f}%")

    print("\n--- 2. Ratio de desviaciones sigma_sim / sigma_esp ---")
    q = d.ratio_sigma.quantile([.05, .25, .5, .75, .95])
    print(f"  p05={q[.05]:.2f}  p25={q[.25]:.2f}  mediana={q[.5]:.2f}  "
          f"p75={q[.75]:.2f}  p95={q[.95]:.2f}")
    print(f"  celdas SOBREdispersas (ratio>1): {100*(d.ratio_sigma>1).mean():.1f}%")

    print("\n--- 3. Regresion simulado = a + b * esperado ---")
    b, a = np.polyfit(d.mean_esp, d.mean_sim, 1)
    pred = a + b * d.mean_esp
    r2 = 1 - np.sum((d.mean_sim - pred)**2) / np.sum((d.mean_sim - d.mean_sim.mean())**2)
    print(f"  pendiente b = {b:.4f}   (1.0 = sin sesgo proporcional)")
    print(f"  ordenada  a = {a:+.4f}")
    print(f"  R2          = {r2:.4f}   <- cuanto del patron espacio-temporal se reproduce")

    print("\n--- 4. Metricas de error y desigualdad de Theil ---")
    t = theil(d.mean_sim.values, d.mean_esp.values)
    print(f"  RMSE = {t['rmse']:.3f} pax   MAE = {t['mae']:.3f} pax   r = {t['r']:.4f}")
    print(f"  U de Theil = {t['U']:.4f}")
    print(f"    Um (sesgo)      = {t['Um_sesgo']:.3f}")
    print(f"    Us (varianza)   = {t['Us_varianza']:.3f}")
    print(f"    Uc (covarianza) = {t['Uc_covarianza']:.3f}")
    print("    (idealmente Um y Us proximos a 0 y Uc proximo a 1: el error "
          "seria no sistematico)")

    print("\n--- 5. Sensibilidad al umbral ---")
    for u in (0.99, 0.98, 0.97, 0.95, 0.90, 0.85):
        print(f"  umbral {u:.2f} -> {100*(d.bc_calc>=u).mean():5.1f}% de celdas equivalentes")

    print("\n--- 6. Contrafactual: si solo existiera el error de nivel ---")
    bc_solo_nivel = d.bc_nivel.values
    bc_solo_disp = d.bc_dispersion.values
    print(f"  con dispersion perfecta: {100*(bc_solo_nivel>=args.umbral).mean():5.1f}% pasarian")
    print(f"  con nivel perfecto     : {100*(bc_solo_disp>=args.umbral).mean():5.1f}% pasarian")
    print(f"  situacion real         : {100*(d.bc_calc>=args.umbral).mean():5.1f}%")

    # ---------------- figuras ----------------
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.5))

    sc = ax[0].scatter(d.bc_nivel, d.bc_dispersion, c=d.bc_calc, s=16,
                       cmap="RdYlGn", vmin=0.7, vmax=1.0)
    ax[0].axhline(args.umbral, ls="--", lw=1, color="grey")
    ax[0].axvline(args.umbral, ls="--", lw=1, color="grey")
    ax[0].set_xlabel("Termino de nivel (medias)")
    ax[0].set_ylabel("Termino de dispersion (desviaciones)")
    ax[0].set_title("Que factor limita cada celda")
    plt.colorbar(sc, ax=ax[0], label="BC total")

    ax[1].hist(d.ratio_sigma, bins=40, color="#1f77b4", alpha=0.75)
    ax[1].axvline(1.0, ls="--", lw=1.5, color="black", label="sigma_sim = sigma_esp")
    ax[1].axvline(d.ratio_sigma.median(), ls=":", lw=1.5, color="#d62728",
                  label=f"mediana = {d.ratio_sigma.median():.2f}")
    ax[1].set_xlabel("sigma simulada / sigma esperada")
    ax[1].set_ylabel("Numero de celdas")
    ax[1].set_title("Desajuste de dispersion")
    ax[1].legend()

    fig.suptitle(f"Descomposicion de la validacion — {args.tipo}")
    fig.tight_layout()
    out = args.outdir / f"validacion_descomposicion_{args.tipo}.png"
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print(f"\n  -> {out}")

    # regresion con banda
    fig, ax = plt.subplots(figsize=(7, 7))
    lim = float(max(d.mean_esp.max(), d.mean_sim.max())) * 1.05
    ok = d.bc_calc >= args.umbral
    ax.scatter(d.mean_esp[~ok], d.mean_sim[~ok], s=16, alpha=.5, color="#d62728",
               label=f"No equivalentes (n={int((~ok).sum())})")
    ax.scatter(d.mean_esp[ok], d.mean_sim[ok], s=16, alpha=.8, color="#2ca02c",
               label=f"Equivalentes (n={int(ok.sum())})")
    xs = np.linspace(0, lim, 10)
    ax.plot(xs, xs, ls="--", lw=1.2, color="black", label="identidad")
    ax.plot(xs, a + b * xs, lw=1.8, color="#1f77b4",
            label=f"ajuste: y = {a:+.2f} + {b:.3f}x  (R2={r2:.3f})")
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.set_xlabel("Media esperada (datos EMT)")
    ax.set_ylabel("Media simulada")
    ax.set_title(f"Simulado frente a esperado — {args.tipo}")
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    out = args.outdir / f"validacion_regresion_{args.tipo}.png"
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print(f"  -> {out}")

    d.to_csv(args.outdir / f"validacion_detalle_{args.tipo}.csv", index=False)
    print(f"  -> {args.outdir}/validacion_detalle_{args.tipo}.csv")


if __name__ == "__main__":
    main()