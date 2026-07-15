"""
Figura ilustrativa: comparacion entre el metodo escalonado y el metodo con
tendencia (rotacion sobre el punto medio de cada franja hacia el valor de la
franja siguiente).

Valores SINTETICOS, unicamente ilustrativos (no proceden de datos EMT).
La rampa de la ultima franja mostrada rota hacia un valor sintetico tau_{h+3};
la politica real de contorno (rotacion hacia cero al fin de servicio) se
documenta por separado.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "legend.fontsize": 9.5,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

ITER_POR_HORA = 1800                       # p.ej. paso de 2 s -> 3600/2
tasas = np.array([36.0, 126.0, 54.0])      # pasajeros/parada/hora (franjas mostradas)
tasa_siguiente = 72.0                      # tau_{h+3}, solo para la rampa de la 3a franja
horas = ["h", "h+1", "h+2"]
inc = tasas / ITER_POR_HORA                # incremento por iteracion (escalon)
inc_next = np.append(inc[1:], tasa_siguiente / ITER_POR_HORA)

t_total = 3 * ITER_POR_HORA
t = np.arange(t_total + 1)
bordes = [0, ITER_POR_HORA, 2 * ITER_POR_HORA, 3 * ITER_POR_HORA]

# --- Metodo escalonado ---
esc = np.repeat(inc, ITER_POR_HORA)
esc = np.append(esc, esc[-1])

# --- Metodo con tendencia: recta que pivota en (punto medio, tau_h) y
#     alcanza tau_{h+1} al final de la franja ---
tend = np.empty(t_total + 1)
for i in range(3):
    ini, fin = bordes[i], bordes[i + 1]
    y_ini = 2 * inc[i] - inc_next[i]       # ordenada al inicio de la franja
    y_fin = inc_next[i]                    # ordenada al final de la franja
    tt = np.arange(ini, fin + 1)
    tend[ini:fin + 1] = y_ini + (y_fin - y_ini) * (tt - ini) / (fin - ini)
# (la asignacion sucesiva sobreescribe el punto de frontera con el valor
#  inicial de la franja siguiente, lo que dibuja el salto residual)

fig, ax = plt.subplots(figsize=(6.4, 4.2))

ax.axhline(0, color="0.6", linewidth=0.8)
for b in bordes[1:3]:
    ax.axvline(b, color="gray", linestyle=":", linewidth=1.0)

ax.step(t, esc, where="post", color="black", linewidth=1.5,
        label="método escalonado")
# Dibujar cada rampa con sus propios valores extremos y el salto residual
# como conector discontinuo
for i in range(3):
    ini, fin = bordes[i], bordes[i + 1]
    y_ini = 2 * inc[i] - inc_next[i]
    y_fin = inc_next[i]
    tt = np.arange(ini, fin + 1)
    ax.plot(tt, y_ini + (y_fin - y_ini) * (tt - ini) / (fin - ini),
            color="tab:blue", linewidth=1.8,
            label="método con tendencia" if i == 0 else None)
    if i > 0:
        y_fin_prev = inc_next[i - 1]
        ax.plot([ini, ini], [y_fin_prev, y_ini], color="tab:blue",
                linestyle=(0, (2, 2)), linewidth=1.3)

# Anotaciones
"""ax.annotate("salto residual",
            xy=(bordes[1], (inc_next[0] + (2 * inc[1] - inc_next[1])) / 2),
            xytext=(bordes[1] + 350, 0.095), fontsize=9.5, color="tab:blue",
            arrowprops=dict(arrowstyle="->", color="tab:blue", linewidth=0.9))
ax.annotate("tramo negativo\n(deuda del contador)",
            xy=(int(ITER_POR_HORA * 0.10), tend[int(ITER_POR_HORA * 0.10)]),
            xytext=(int(ITER_POR_HORA * 0.28), -0.033), fontsize=9.5,
            color="tab:blue",
            arrowprops=dict(arrowstyle="->", color="tab:blue", linewidth=0.9))"""
# Pivotes en el punto medio
medios = [(bordes[i] + bordes[i + 1]) // 2 for i in range(3)]
ax.plot(medios, inc, linestyle="None", marker="o", markersize=4.5,
        markerfacecolor="white", markeredgecolor="tab:blue",
        label="pivote (punto medio, $\\tau_h$)")

ax.set_xticks(bordes)
ax.set_xticklabels([horas[0], horas[1], horas[2], "h+3"])
ax.set_xlabel("Tiempo (franjas horarias)")
ax.set_ylabel("Valor agregado por iteración")
ax.legend(loc="upper right", frameon=False)
ax.set_ylim(min(tend) * 1.25, max(2 * inc[1] - inc_next[1], max(esc)) * 1.32)

fig.tight_layout()
fig.savefig("/home/claude/comparativa_tendencia.pdf", bbox_inches="tight")
fig.savefig("/home/claude/comparativa_tendencia.png", dpi=200, bbox_inches="tight")
print("OK")