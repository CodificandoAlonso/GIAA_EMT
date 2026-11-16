from common import *
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
style()
out=[]
cl={d:cleaned(d) for d in DIRN}
ND=158
# hourly profile
prof=[]
for d in DIRN:
    g=cl[d].groupby("TimeSlot.1")["Board"].sum().reindex(SLOTS,fill_value=0)
    nd=cl[d].EventDate.nunique()
    for s in SLOTS: prof.append((d,s,g[s]/nd,g[s],nd))
prof=pd.DataFrame(prof,columns=["direction","slot","mean_total_boardings_per_day","total_boardings","n_days"])
save_table(prof,"t2_hourly_profile"); prof.to_csv("../figures/fig_hourly_profile_data.csv",index=False)
peak={d:int(prof[prof.direction==d].sort_values("mean_total_boardings_per_day").iloc[-1].slot) for d in DIRN}
top3={d:prof[prof.direction==d].sort_values("mean_total_boardings_per_day",ascending=False).head(4)[["slot","mean_total_boardings_per_day"]] for d in DIRN}
out.append(f"Peak hour (slot = hour of service, TimeSlot.1) by mean total boardings per normal day: toA **{peak['toA']}**, toB **{peak['toB']}**.\n")
for d in DIRN: out.append(f"Top-4 hours {d}:\n\n"+md(top3[d].assign(direction=d)[["direction","slot","mean_total_boardings_per_day"]],"{:.1f}")+"\n")
out.append(f"Paper claim: 7-9 h towards Cibeles, after 17 h towards La Peseta -> matches: toA {'yes' if peak['toA'] in (7,8) else 'NO'}, toB {'yes' if peak['toB']>=17 else 'NO'}.\n")
# per stop profile at peak
rows=[]
for d in DIRN:
    df=cl[d]; pk=df[df["TimeSlot.1"]==peak[d]]
    for stop in STOPS[d]:
        g=pk[pk.Stop==stop]
        r=[d,peak[d],stop,STOPS[d].index(stop)+1,len(g)]
        for col in ["Board","DropOff","Occupation"]:
            r+= [g[col].mean(), g[col].quantile(.25), g[col].quantile(.75)]
        rows.append(r)
cols=["direction","slot","stop","order","n_visits"]+[f"{c}_{k}" for c in ["board","dropoff","occ"] for k in ["mean","q25","q75"]]
peakdf=pd.DataFrame(rows,columns=cols)
save_table(peakdf,"t2_peak_stop_profile"); peakdf.to_csv("../figures/fig_load_profile_data.csv",index=False)
out.append(md(peakdf,"{:.1f}"))
# figure 1 full page
fig,axes=plt.subplots(1,2,figsize=(17*CM,6.0*CM),sharey=False)
names={"toA":"Towards Cibeles (toA)","toB":"Towards La Peseta (toB)"}
for ax,d in zip(axes,DIRN):
    p=peakdf[peakdf.direction==d]; x=np.arange(len(p))
    w=0.38
    ax.bar(x-w/2,p.board_mean,w,color=OI["blue"],label="Boardings")
    ax.bar(x+w/2,p.dropoff_mean,w,color=OI["orange"],label="Alightings")
    ax.set_ylabel("Passengers per bus arrival")
    ax.set_xticks(x); ax.set_xticklabels(p.stop.astype(str),rotation=90)
    ax.set_xlabel("Stop code, in route order")
    ax2=ax.twinx(); ax2.spines["right"].set_visible(True)
    ax2.plot(x,p.occ_mean,color=OI["verm"],marker="o",ms=2.5,label="Occupancy after stop")
    ax2.fill_between(x,p.occ_q25,p.occ_q75,color=OI["verm"],alpha=0.2,lw=0,label="Occupancy IQR")
    ax2.set_ylabel("Occupancy (passengers)")
    ax2.set_ylim(0,max(60,p.occ_q75.max()*1.1)); ax.set_ylim(0,max(p.board_mean.max(),p.dropoff_mean.max())*1.25)
    ax.set_title(f"{names[d]}, hour {peak[d]}",fontsize=8)
h1,l1=axes[0].get_legend_handles_labels(); a2=fig.axes[2]; h2,l2=a2.get_legend_handles_labels()
fig.legend(h1+h2,l1+l2,loc="lower center",ncol=4,frameon=False,bbox_to_anchor=(0.5,-0.08))
fig.tight_layout(); figsave(fig,"fig_load_profile")
# figure 2
fig,ax=plt.subplots(figsize=(8.5*CM,5.2*CM))
for d,c,m in [("toA",OI["blue"],"o"),("toB",OI["orange"],"s")]:
    p=prof[prof.direction==d]; ax.plot(p.slot,p.mean_total_boardings_per_day,color=c,marker=m,ms=2.5,label=names[d])
ax.set_xlabel("Hour of day (time slot)"); ax.set_ylabel("Boardings per normal day"); ax.set_xticks(range(5,24,2)); ax.legend(frameon=False)
fig.tight_layout(); figsave(fig,"fig_hourly_profile")
write_section("t2_profile","\n".join(out)); print("\n".join(out))
