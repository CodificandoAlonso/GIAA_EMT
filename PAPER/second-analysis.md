# Evidence backs the design, not its labels

The literature supports what the two E01 models do (individual buses moved by fitted inter-stop times, demand driven by stop-level boarding and alighting counts, no estimated origin-destination matrix, non-deliberative agents coordinated by explicit protocols), but it does not support several of the terms and citations the draft uses to justify that design. Of the six steps of the intended argument, only step 2 (agent-based simulation is widely used in transport) stands as drafted, and it needs quantified sources. Steps 1 and 4 stand after narrowing. Step 3 contains a factual error (MATSim is not a BDI tool) and two unsupported generalisations ("normally", "microsimulations"). Step 5 mislabels the agents ("data-driven", "goal-oriented") and attributes to Brooks a claim about inter-agent communication that he never made. Step 6 cannot claim what Toledo et al. (2010) and Kieu et al. (2020) already published. The root defect is conceptual: the draft treats simulation granularity and agent cognitive architecture as one axis, and every source checked treats them as two. The most serious exposure is technical, not rhetorical: every located OD-free bus model that represents alighting ties it to the on-board load, and none samples alighting counts independently of it, as the first manuscript version does. What remains defensibly new is a protocol-specified (FIPA) multi-agent formulation of bus-line operations in GAMA, an absorption indicator defined on protocol outcomes, and a controlled comparison of demand resolution at fixed supply resolution on real operator counts, with the status "no precedent found in a time-limited search", not "first". Everything below derives from research notes dated 9 October 2026: short quotations were obtained through an automated page reader and must be checked against the PDFs, several Crossref and publisher pages were blocked, and DOIs not seen on a fetched page are omitted on purpose.

## One of six argument steps stands as drafted

Table 1 gives the verdict per step. The wording column is at claim level, as requested: it states what the sources allow the author to assert, not how to write it. The subsections that follow give the evidence and separate what the sources say from what the researchers inferred.

**Table 1. Verdict per step of the intended argument**

| Step | Draft claim | Verdict | Claim the sources support | Backing sources |
|---|---|---|---|---|
| 1 | Evaluating supply on observed data is slow and confounded, so operators rely on simulation | Supported in three components; two draft sentences have no source | Capacity-relevant extremes need many observations of the same trip pattern; supply and demand are jointly determined; simulation is the established tool for evaluating operational alternatives before field implementation | Furth et al. 2006 (TCRP 113); Taylor et al. 2009; Berrebi et al. (preprint); Toledo et al. 2010 |
| 2 | Agent-based / multi-agent simulation is widely used in transport | Supported; the draft's evidence is the weakest available | Growth and tool shares stated with counts | Divasson-J. et al. 2025; Bastarianto et al. 2023; Huang et al. 2022 |
| 3 | Some works use BDI agents, "normally for microsimulations"; MATSim is a BDI tool | MATSim claim is wrong; "normally", "microsimulations" and "passengers and buses" are unsupported; the purpose argument survives | Cognitive architectures are warranted when the individual decision process is the object of study or agents must react within the run; otherwise simpler agents suffice. BDI has been coupled to MATSim as an extension | Adam & Gaudou 2016, Sec. 3.4; Balke & Gilbert 2014, para. 2.2; Padgham et al. 2014 |
| 4 | A mesoscopic scope suffices; no OD behaviour, no exact speed, no OD matrix reconstructed | Substance supported; "scope" and any link to BDI must go; the OD claim holds only in a narrow form | Mesoscopic level of detail in the sense of Toledo et al.: individual buses, no second-by-second dynamics, inter-stop times from fitted distributions. Counts fix the load profile, not the OD matrix; none is estimated and no reported output depends on one | Toledo et al. 2010; Burghout 2004; Li & Cassidy 2007; Furth et al. 2006, ch. 8 |
| 5 | Agents are reactive and data-driven; "the intelligence emerges from the communication" | "Reactive" survives with a qualifier; "data-driven", "goal-oriented", "intelligence emerges" and the Brooks attribution do not | Non-deliberative agents (buses and stops keep internal state), empirically calibrated; system-level regularities arise from protocol-mediated local interactions | Wooldridge & Jennings 1995; Zhang et al. 2015; De Wolf & Holvoet 2005; Jennings 2000 |
| 6 | Positioning and contribution | Must be re-scoped | Novelty lies in the protocol-specified multi-agent formulation and the controlled comparison of demand resolution, not in OD-free, count-driven simulation | Toledo et al. 2010; Kieu et al. 2020; Balbo et al. 2024 |

### Step 1: three supportable components, two sentences without a source

What the sources say. TCRP Report 113 states that extreme values can only be estimated reliably from a large sample, recommends 85th and 95th percentile running times as a scheduling basis, and says that monitoring crowding on crowded routes requires a large sample ([Furth et al. 2006, TCRP 113](https://www.trb.org/publications/tcrp/tcrp_rpt_113.pdf)). Taylor et al. (2009) state that earlier studies had not addressed the simultaneous relationship between transit supply and consumption, and treat it with two-stage simultaneous equations over **265 US urbanised areas** ([Taylor et al. 2009, index record](https://www.worldtransitresearch.info/research/1872)). Berrebi, Joshi and Watkins, on weekday counts from four US agencies (2012-2018), find that ridership responds inelastically to frequency changes within a route segment, with low-frequency routes the most sensitive ([Berrebi et al., arXiv:2002.02493](https://arxiv.org/abs/2002.02493)). Toledo et al. (2010) state that simulation models are established as the primary tool for evaluation at the operational level and that tools for evaluation prior to field implementation are needed ([Toledo et al. 2010, working-paper reissue](https://www.transportportal.se/swopec/CTS2013-29.pdf)). Two keys already in the draft supply the remaining motive: Transit-Gym states that previously collected data do not cover all operational scenarios ([Sun et al. 2021](https://ar5iv.arxiv.org/html/2107.00105)), and Talusan et al. state that overage and disruption events are very sparse in real data ([Talusan et al. 2024](https://arxiv.org/html/2403.03339)).

What the sources do not say. The draft sentence that a "multiple month data window with same configuration is required" for statistical accuracy is contradicted for average counts by the same report: a typical **10% to 15% APC fleet penetration** suffices for most uses, and most uses of passenger counts require only moderate sample sizes ([TCRP 113, online reader](https://nap.nationalacademies.org/read/13907/chapter/2)). The sentence that "a small change in service supply configuration can shift the data results towards inconsistencies" has no source in the notes. No source was found stating that field experiments on bus supply are infeasible or too costly.

Researchers' inferences. The window-length sentence must either be narrowed to occupancy extremes or presented as a property of the E01 dataset and justified with the author's own cell counts per stop and time slot. Taylor et al. work at metropolitan level, so they back the confounding logic and not a line-level effect size. The three simulators the draft cites for "entities rely on simulation" are research prototypes; they are evidence of research practice, not of operator practice, and the general statement belongs to Toledo et al.

### Step 2: supported, but the draft cites the one review without numbers

What the sources say. The Cities systematic review (PRISMA; Scopus, SpringerLink and IEEE Xplore; 2013-2023) retains **154 publications yielding 258 ABM applications**, reports exponential growth over the last decade with momentum from 2015-2016, and finds that five tools account for 63% of applications: SUMO 26.13%, AnyLogic 12.61%, NetLogo 9.91%, **GAMA 7.21%** and MATSim 7.21% ([Divasson-J. et al. 2025](https://doi.org/10.1016/j.cities.2024.105697)). Bastarianto et al. (2023) review **309 Scopus documents (2006-2022)** and describe growth as exponential from 2015 ([Bastarianto et al. 2023](https://etrr.springeropen.com/articles/10.1186/s12544-023-00590-5)). Huang et al. (2022), the draft's only citation here, assert an increasing prevalence without counts or a trend figure ([Huang et al. 2022](https://downloads.hindawi.com/journals/jat/2022/1252534.pdf)). For public transport specifically, Balbo et al. (2024) review 38 papers (1990-2020) and report that public transport is about **14.7% of the MAS-in-ITS research papers** they collected, falling to 8.5% in 2016-2020, that most of this work handles real-time disturbances, and that few papers analyse the system instead of acting on it ([Balbo et al. 2024](https://link.springer.com/article/10.1007/s12469-023-00332-9)).

Researchers' inferences. "Widely used and growing" is safe for agent-based modelling in the broad sense. It is weaker for multi-agent systems with explicit communication: the Cities review counts SUMO as its most used ABM tool, while Nguyen et al. classify SUMO as microscopic and not agent-based ([Nguyen et al. 2021](https://ar5iv.labs.arxiv.org/html/2102.07505)), and Drogoul et al. state that multi-agent-based simulation is rarely built on computational agents in the MAS sense ([Drogoul et al. 2003](https://link.springer.com/chapter/10.1007/3-540-36483-8_1)). That gap between "ABM is everywhere" and "MAS with protocols is rare in public transport" is where the manuscript sits, and it is citable through Balbo et al.

### Step 3: MATSim is not BDI, and BDI is a minority approach in transport

What the sources say about MATSim. Each MATSim agent holds a memory of day plans with an associated score that is read as an econometric utility; a share of agents replans between iterations in a co-evolutionary process that stops when no agent can improve unilaterally; the mobility simulation is queue-based, not car-following ([MATSim book, ch. 1](https://openresearchlibrary.org/ext/api/media/27f59836-d5af-40ca-a7f4-8ea2033c958f/assets/external_content.pdf)). Bazzan and Klügl add that MATSim does not try to resemble the planning process and that its queue simulation has no active decision making while driving ([Bazzan & Klügl 2014](https://maxapress.com/data/article/ker/preview/pdf/S0269888913000118.pdf)). BDI exists for MATSim only as an external coupling: Chapter 31 of the MATSim book (Padgham and Singh) sits in the part titled "Extending MATSim" ([chapter page](https://www.ubiquitypress.com/site/chapters/e/10.5334/baw.31/); [book table of contents](https://library.oapen.org/bitstream/20.500.12657/32162/1/613715.pdf)), and the ECAI 2014 paper explains the motive: standard agents can only replan between iterations, and BDI is coupled in to obtain within-day replanning for a taxi prototype and a bushfire evacuation of a town of 444 inhabitants ([Padgham et al. 2014](https://ebooks.iospress.nl/pdf/doi/10.3233/978-1-61499-419-0-681)). The author's own project library classifies MATSim as "a mesoscopic simulation framework" ([Saval et al. 2023](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0281658)), and Huang et al. list MATSim in their toolkit table without calling it BDI ([Huang et al. 2022](https://downloads.hindawi.com/journals/jat/2022/1252534.pdf)).

What the sources say about BDI in transport. The located peer-reviewed BDI work covers car drivers and evacuees: Rossetti et al. (2002) and Dia (2002) on driver decisions, as characterised by Bazzan and Klügl ([Bazzan & Klügl 2014](https://maxapress.com/data/article/ker/preview/pdf/S0269888913000118.pdf)); Noroozian et al. (2014) on heterogeneous drivers coupled to a microscopic simulator ([Noroozian et al. 2014](https://scitepress.org/Papers/2014/48156/pdf/index.html)); the BDI-MATSim evacuation line ([Singh et al. 2016](https://link.springer.com/article/10.1007/s10458-016-9332-x)). The only bus-related item is BusAI, a 2025 workshop paper in which bus, stop and coordinator are Jason agents and passengers are not agents ([Lira et al. 2025](https://bsi.cefet-rj.br/~lazarin/publications/Lira%20et%20al.%20-%202025%20-%20BusAI%20An%20BDI-agent-based%20Urban%20Transport%20Information%20System.pdf)). On prevalence, Bazzan and Klügl report that the traffic works they review are mostly based on simple agent architectures ([Bazzan & Klügl 2014](https://maxapress.com/data/article/ker/preview/pdf/S0269888913000118.pdf)); the 2023 review of urban-transport ABMs does not contain the terms BDI, belief-desire-intention or cognitive ([Bastarianto et al. 2023](https://link.springer.com/article/10.1186/s12544-023-00590-5)); and the GAMA group's own BDI paper states that most social-simulation agents still use simple reactive models ([Taillandier et al. 2017](https://link.springer.com/chapter/10.1007/978-3-319-67477-3_1)).

What survives. Adam and Gaudou state the purpose argument almost literally in terms of the level of observation: simple agents suffice when the focus is global group behaviour, and BDI is more appropriate when individual agents become the focus; without data or theory about the decision process, BDI is not an appropriate choice; BDI agents are heavier and have to be used wisely ([Adam & Gaudou 2016, Secs. 3.4, 3.5.1, 3.5.2](https://maxapress.com/data/article/ker/preview/pdf/S0269888916000096.pdf)). Balke and Gilbert relay the same result from Carley et al.: simpler agents are adequate for macro-level prediction, more cognitively accurate agents for individual or small-group behaviour ([Balke & Gilbert 2014, para. 2.2](https://www.jasss.org/17/4/13.html)).

Researchers' inferences. The draft sentence fails in four ways, by severity: MATSim presented as a BDI tool is a factual error; "passengers and buses" has no located support, since no peer-reviewed BDI passenger model for bus, metro or rail was found; "normally" contradicts the surveys; and "microsimulations" conflates decision-model richness with traffic-flow resolution, because in transport the standard microscopic agent is reactive (IDM plus MOBIL in GAMA's driving skill, per Saval et al.). BDI-MATSim is itself a counter-example to "BDI implies microscopic": cognition was attached to a queue-based simulator that the GAMA group calls mesoscopic. On cost, the honest summary is "heavier, and the weight must be justified", not "does not scale": the BDI-MATSim authors report that only a very small portion of run time went to BDI reasoning ([Padgham et al. 2014](https://ebooks.iospress.nl/pdf/doi/10.3233/978-1-61499-419-0-681)). One point cuts against the author and must be faced: Adam and Gaudou consider BDI well suited to transport when travellers have many options (the page reader reported the word "ideal"; check it). The reply available is that a passenger on a single line with no path choice has no options to deliberate over. Two limits on this step: no survey located gives a quantitative breakdown of agent architectures in transport, so "minority" is a qualitative statement; and no peer-reviewed study was found that quantifies the calibration or identifiability burden of BDI parameters in a transport model, so that argument can be supported only indirectly, through Adam and Gaudou on data needs and Bastarianto et al. on calibration of agent-based models in general.

### Step 4: "mesoscopic" survives only with a definition, the OD claim only in its narrow form

What the sources say about granularity. The three labels classify the level of detail at which entities and their dynamics are represented. Burghout characterises mesoscopic models as describing individual vehicles but not their interactions ([Burghout 2004](https://kth.se/polopoly_fs/1.742065.1600688570!/hybrid%20mesoscopic.pdf)); FHWA defines microscopic models by car-following and lane-changing theories ([FHWA Traffic Analysis Toolbox Vol. I](https://ops.fhwa.dot.gov/trafficanalysistools/tat_vol1/sect4.htm)); Toledo et al. define mesoscopic transit models as representing individual vehicles while avoiding their second-by-second movement, and in their Tel Aviv case study draw running times between stops from lognormal distributions with no explicit background traffic ([Toledo et al. 2010, working-paper reissue](https://www.transportportal.se/swopec/CTS2013-29.pdf)). No definition found refers to the cognitive architecture of an agent.

The label has at least two conflicting meanings, and the author's reference list contains both. In simulation practice it means individual vehicles with simplified dynamics (Burghout, FHWA, Toledo). In traffic flow theory it means non-individual, probabilistic descriptions such as gas-kinetic models ([van Wageningen-Kessels et al., TU Delft repository](https://repository.tudelft.nl/file/File_09bae6e9-4f06-436a-aca6-e162b26560aa?preview=1)), and the PLOS ONE paper in the project files uses that second meaning when it says mesoscopic models "are not individual-based" ([Saval et al. 2023](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0281658)). A third usage sits in one of the author's existing keys: Huang et al. organise applications by time horizon, with "mesoscopic" meaning medium-term resolution of minutes or longer ([Huang et al. 2022](https://downloads.hindawi.com/journals/jat/2022/1252534.pdf)). Usage is not uniform beyond that: Cetin et al. call a queue model without car-following a "microsimulation" ([Cetin et al. 2003](https://svn.vsp.tu-berlin.de/repos/public-svn/publications/kn-old/strc03-queue/strc03-queue.pdf)), and MATSim is "a mesoscopic simulation framework" for Saval et al. but is said to manage agents "at the micro level" by Bastarianto et al. ([Bastarianto et al. 2023](https://etrr.springeropen.com/articles/10.1186/s12544-023-00590-5)).

Demand resolution is a separate choice from supply resolution. BusMezzo in 2010 had individual buses and aggregate passengers; by 2016 it is described as simulating individual passengers and individual vehicles with mesoscopic traffic dynamics, a FIFO boarding queue and capacity-based denied boarding ([Cats & Hartl 2016](https://pure.tudelft.nl/ws/files/11605597/JoAT_Cats_and_Hartl_2016.pdf); [Cats, West & Eliasson 2016](https://pure.tudelft.nl/ws/files/11510486/Cats_et_al_TR_B_2016b.pdf)). MATSim describes itself as a microscopic description of demand on a queue-based network model, and the book does not itself call the queue model mesoscopic in the chapters read ([MATSim book](https://library.oapen.org/bitstream/20.500.12657/32162/1/613715.pdf)). Individual-passenger simulation is called microscopic in recent transit assignment work ([Patzner & Müller-Hannemann 2024](https://arxiv.org/abs/2408.06308)).

What the sources say about OD. On-off counts do not determine the OD matrix: a given set of sums corresponds to many OD matrices ([Li & Cassidy 2007](https://escholarship.org/content/qt17m7k4vm/qt17m7k4vm.pdf)); the counts inform OD rates only through a highly indeterminate system of linear equations ([Hazelton 2010](https://informahealthcare.com/doi/abs/10.1198/TECH.2010.09021)); the feasible set is extraordinarily large ([Chen, Cheng & Sun 2025, arXiv v2](https://arxiv.org/html/2403.04742v2)). Load, by contrast, is computed as accumulated boardings minus accumulated alightings ([TCRP 113, ch. 8](https://nap.nationalacademies.org/read/13907/chapter/10)), and frequency setting has been done from load profiles alone since Ceder (1984) ([Ceder 1984, index record](https://trid.trb.org/View/269513)).

Researchers' inferences. "Mesoscopic in scope" is a category slip: the sources classify by level of detail, and scope denotes spatial and temporal extent. "Architecture 1 is still mesoscopic because the passenger is not BDI but a statistical count" does not survive either reviewer: one object per passenger is a disaggregate demand representation, which part of the literature calls microscopic, and BDI versus reactive is an architecture class unrelated to granularity. Counter-examples exist in both directions: car-following vehicles are reactive and microscopic; BusMezzo passengers take utility-based decisions inside a mesoscopic simulator. In the vocabulary a transport reviewer recognises, both architectures share mesoscopic supply dynamics and differ in demand resolution: disaggregate in Architecture 1 (the BusMezzo configuration of 2013-2016, minus passenger decisions), aggregate in Architecture 2 (the Toledo et al. 2010 configuration). No source states this two-axis view as a named taxonomy; the evidence is a set of consistent usages. A transport reviewer may also object that the model has no traffic-flow component at all, so that "discrete-event simulation of line operations" is the neutral description; "mesoscopic" then survives only through the explicit definition and the Toledo et al. precedent.

On OD, two derivations are the researchers' own and were not found in a source. For one direction of a route with n stops there are n(n-1)/2 feasible cells and 2n-3 independent marginal constraints, leaving (n-2)(n-3)/2 free dimensions (378 for n = 30). Every matrix in that feasible set produces the same load on every link, because load after stop k is cumulative boardings minus cumulative alightings. The second derivation is the cleanest formal basis for "occupancy does not need OD" and can be stated as the authors' own observation, with n for E01. The draft's phrasing "the model does not reconstruct an OD matrix" is true but incomplete: any rule that decides who alights implies one (see the reviewer risks below).

### Step 5: the agents are reactive, but not data-driven, goal-oriented or emergently intelligent

What the sources say about agent classes. Wooldridge and Jennings classify architectures as deliberative, reactive and hybrid, a reactive architecture being one without a central symbolic world model or complex symbolic reasoning ([Wooldridge & Jennings 1995](https://maxapress.com/data/article/ker/preview/pdf/S0269888900008122.pdf)). Wooldridge (1999) defines purely reactive agents as deciding entirely on the present, distinguishes agents with state, counts thermostats as agents but not as intelligent agents, and separates agents from objects by their deciding for themselves whether to act on a request ([Wooldridge 1999](https://web.mit.edu/marym/www/Wooldridge%A5IntellgntAgents.pdf)). In Franklin and Graesser's table, goal-oriented means the agent does not simply act in response to the environment ([Franklin & Graesser 1996](https://www.cs.memphis.edu/~franklin/AgentProg.html)); Russell and Norvig's goal-based class requires choosing actions to achieve a goal, a definition the notes obtained only from course slides ([UMD slides on AIMA ch. 2](https://www.cs.umd.edu/class/fall2003/cmsc421-0101/intelligent-agents.pdf)).

What the sources say about "data-driven". In Zhang et al., agent behaviour models are learned from individual-level data with cross-validation, so that the model has no additional behavioural parameters, and validation runs forward against held-out data; prior practice is criticised for ad hoc tuning and for validating on the calibration data ([Zhang et al., AAMAS 2015](https://ifmas.csc.liv.ac.uk/Proceedings/aamas2015/aamas/p513.pdf)). Kavak's dissertation has the same sense: attributes and behaviours derived from large-scale individual data by machine learning ([Kavak 2019](https://digitalcommons.odu.edu/msve_etds/49)). A broader usage exists, in which data shape design, initialisation and validation ([ESSA 2008 roadmap, repository record](https://docta.ucm.es/entities/publication/88c3f8ff-7f29-459b-9c05-55746d4a59e2)).

What the sources say about emergence and Brooks. Brooks's 1991 papers hold that intelligence emerges from the interaction of the components of a system and that coherence is imputed by an observer, but the interacting components are behaviours inside one robot, linked by fixed wiring with no dynamically established communication links; the paper does not analyse communication between separate agents and does not define "agent" ([Brooks 1991, AIJ](https://jmvidal.cse.sc.edu/library/brooks91b.pdf); [Brooks 1991, AI Memo 1293](https://jmvidal.cse.sc.edu/library/brooks91a.pdf)). Established and citable instead: a system exhibits emergence when coherent macro-level emergents arise dynamically from interactions between micro-level parts ([De Wolf & Holvoet 2005](https://pdodds.w3.uvm.edu/teaching/courses/2009-08UVM-300/docs/others/2005/dewolf2005a.pdf)); emergent phenomena result from the interactions of individual entities ([Bonabeau 2002](https://gsp.humboldt.edu/olm_2021/Courses/GSP_570/Articles/2002%20-%20Bonabeau%20-%20Agent-based%20modeling%20methods%20and%20techniques%20for%20simulating%20human%20systems.pdf)); and interaction is a first-class design object, with Jennings treating emergent behaviour as a risk as much as a feature ([Jennings 2000](https://jmvidal.cse.sc.edu/library/abse.pdf)). Singh notes that the mentalistic semantics of Arcol and the FIPA work presuppose that agents have beliefs and intentions ([Singh 1998](https://www.csc2.ncsu.edu/faculty/mpsingh/papers/mas/computer-acl-98.pdf)). The FIPA Request protocol itself is public sequencing: the Participant answers with refuse or agree, then failure, inform-done or inform-result ([FIPA SC00026H](http://www.fipa.org/specs/fipa00026/SC00026H.html)).

Researchers' inferences. The passenger agent of Architecture 1 is a simple reflex agent (reactive in Wooldridge and Jennings's terms; an agent, not an intelligent agent). Bus and stop agents keep counts, so "purely reactive" is inaccurate for them; "reactive (non-deliberative) agents with internal state" is accurate. "Goal-oriented" is not defensible for reflex agents; the supported form is "designed to meet objectives encoded in their rules". "Data-driven" with Zhang or Kavak as the reference invites the objection that the model is the "calibrated to aggregate data" case those papers define themselves against; "empirically calibrated" or "data-parameterised" is accurate, or "data-driven" defined in the broader sense with the ESSA roadmap. No publication was found that presents FIPA-ACL interaction protocols as the vehicle of emergent intelligence in a reactive multi-agent system, so that idea is the author's framing and must be presented as such. A scripted protocol is specified top-down; what can be claimed as emergent is a macro-level regularity no rule encodes (the load profile, the pattern of refused boardings, the absorbed fraction of waiting demand), and "intelligence" is the wrong noun for it. Finally, if the protocols use FIPA performatives with agents that hold no beliefs, the manuscript should say the protocols are used for their public sequencing and cite Singh for the position that a mentalistic semantics is neither necessary nor verifiable.

## BusMezzo and BusSim already own the OD-free claim

The closest precedent is not a multi-agent paper. BusMezzo generates passenger arrivals as a Poisson process with time-dependent rates per line and stop, draws alightings from a **Binomial on the arriving load** with a time-dependent alighting probability per line and stop, avoids explicit generation of individual passengers, has no passenger class among its six transit classes, and justifies the mesoscopic level on the grounds that microscopic models carry an unnecessary level of detail and computational effort for system-wide work ([Toledo et al. 2010, working-paper reissue](https://www.transportportal.se/swopec/CTS2013-29.pdf)). Its validation was thin by its authors' own account: headway distributions compared with video observations at two stops by Kolmogorov-Smirnov tests with n = 15 and n = 8 ([same source](https://www.transportportal.se/swopec/CTS2013-29.pdf)). The companion paper reports that the model reproduced bus bunching on the Tel Aviv line ([Cats et al. 2010, index record](https://www.worldtransitresearch.info/research/3986)).

In the agent-based literature, BusSim has exactly the agent set of Architecture 2: two agent classes, Bus and BusStop; passengers as stop-level aggregates; a per-stop arrival rate and a per-stop departure parameter defined as the percentage of on-board passengers alighting, set to 1 at the last stop; no OD matrix. All of its data are synthetic, and its purpose is parameter calibration plus particle-filter data assimilation for short-term prediction ([Kieu et al., arXiv version](https://ar5iv.labs.arxiv.org/html/1908.08288); [journal record](https://eprints.whiterose.ac.uk/id/eprint/154609/)). Khan et al. use the same structure (Poisson waiting passengers, Binomial alighting on load, boarding capped by residual capacity) ([Khan et al., arXiv:2202.06039](https://arxiv.org/pdf/2202.06039)), and Talusan et al., already in the draft, work from APC data without OD, with passengers as counts, stop-to-stop times sampled from an empirical distribution and capacity limits that leave passengers behind ([Talusan et al. 2024](https://arxiv.org/html/2403.03339)).

Three further precedents must be read before the positioning is written, because the notes could not open their full texts. Dimitrov et al. (2017) model one bus route in Auckland as a small multi-agent system, calibrated and validated, to test bus capacities and frequencies under current and projected demand; the platform and whether passengers carry destinations are unknown ([Dimitrov et al. 2017, index record](https://www.worldtransitresearch.info/research/6467)). Meignan et al. (2007) propose multi-agent simulation tools to analyse and evaluate bus networks, and Zhao et al. (2003) treat stops and buses as agents negotiating holding decisions; both are known only through the description in Balbo et al. ([Balbo et al. 2024](https://link.springer.com/article/10.1007/s12469-023-00332-9)). The Dimitrov paper shares the manuscript's object (one route), paradigm (multi-agent) and purpose (capacity and frequency); a positioning that ignores it is exposed. Whether any of the three, or Tlig and Bhouri (2011), runs on a FIPA-compliant platform is unverified.

The contrast class is equally useful. Once passengers are individual, a destination has to come from somewhere: an OD matrix supplied by a planning agency in Transit-Gym ([Sun et al. 2021](https://ar5iv.arxiv.org/html/2107.00105)), a randomly assigned destination in Quek et al. ([Quek et al. 2021, arXiv version](https://ar5iv.labs.arxiv.org/html/2004.13022)), smart-card-derived demand in Wang and Sun ([Wang & Sun 2021](https://www.ijcai.org/proceedings/2021/0060.pdf)).

### What the manuscript can no longer claim, and what remains

Researchers' inferences throughout this subsection. The manuscript cannot claim that sampling boardings and alightings from per-stop parameters without OD is new, that modelling a bus line with bus and stop agents and aggregate passengers is new, or that arguing for the mesoscopic level on grounds of detail and cost is new. What remains defensible, in descending order of strength, is the following. First, an explicit multi-agent formulation in which boarding and alighting are specified as FIPA interaction protocols: in everything the notes could read, bus-domain multi-agent papers specify interaction as contract net, negotiation, auctions, voting or unnamed "messages", and Balbo et al. mention neither FIPA nor JADE ([Balbo et al. 2024](https://link.springer.com/article/10.1007/s12469-023-00332-9)). Second, an indicator defined at the level of the interaction: demand absorption is the aggregate of agree and refuse outcomes of the boarding protocol, so the measured quantity lives in the protocol and not inside any agent (this reading comes from the brief's description of the model, not from a source). Third, a controlled comparison of demand resolution with supply resolution held fixed, including the measured cost of reifying the passenger; no located paper runs the same line under disaggregate and aggregate demand inside one protocol specification. Fourth, calibration and validation on real operator counts per stop and time slot, against BusSim's synthetic twin and BusMezzo's two-stop validation. Fifth, a system-analysis purpose (occupancy and absorption) on the side of the literature that Balbo et al. report as under-represented.

Each of these carries a limit. The first rests on "not found": no peer-reviewed GAMA model of bus-line operations and no bus model with FIPA-specified boarding and alighting appeared in four differently worded searches, which is weak evidence; the GAMA publications list and Scopus must be searched before any priority claim. The second depends on the bus being able to refuse, which the notes assumed from the phrase "demand absorption" and did not confirm in the code. The third can be turned against the paper (see the next section). No EAAI reviewer guidance or recent EAAI paper was examined to calibrate what that journal accepts as AI novelty.

## Load-independent alighting is the reviewer's first target

Table 2 ranks the risks. Rows 1, 2 and 6 concern the model the introduction announces; the others concern its wording. "Own analysis" marks arguments the researchers constructed themselves and found in no source.

**Table 2. Reviewer risks, by severity**

| Rank | Objection | Raised by | Basis | What defuses it |
|---|---|---|---|---|
| 1 | Alighting counts are sampled independently of the on-board load | Transit reviewer | Every located stochastic precedent conditions on load; consequences are own analysis | Binomial(load, p) with p from the same marginals, or reported diagnostics if the old layout stays |
| 2 | The model has an implied OD matrix, and under FIFO alighting it is an extreme one | Transit reviewer | Furth & Navick 1992 for random selection; FIFO case is own analysis | State that the matrix is implied, never estimated, and report no output that depends on it |
| 3 | "Mesoscopic" is used in a sense the paper's own references contradict | Transit reviewer | Burghout, FHWA, Toledo versus Delft genealogy, Saval, Huang | One definition, cited; "level of detail", not "scope" |
| 4 | Granularity is conflated with cognitive architecture | Both | All definitions checked | Two axes: supply dynamics and demand representation; architecture argued separately |
| 5 | "Data-driven", "goal-oriented" and the Brooks citation are misused | MAS reviewer | Zhang et al.; Franklin & Graesser; Brooks | "Empirically calibrated"; drop "goal-oriented"; cite Brooks only for what he says |
| 6 | If passengers have no destination and Architecture 2 gives the same outputs, they were never agents | MAS reviewer | Parunak et al.; Drogoul et al.; BusMezzo and BusSim omit them by design | Present the comparison first, as a finding on demand resolution; give a positive reason for passenger agents |
| 7 | The agents are objects exchanging method calls | MAS reviewer | Wooldridge 1999 | Show that the bus can refuse a boarding request |
| 8 | Simple rule agents are a known limitation of the field | Either | Huang et al. 2022, Sec. 4.4.2 | The data-identifiability argument (Grimm; O'Sullivan; Srikrishnan & Keller) |
| 9 | Boardings are not demand; per-bus over-dispersion may be headway variance | Transit reviewer | Own analysis; thin literature on count distributions | State the fitted unit; acknowledge censoring at capacity |
| 10 | APC counts are not balanced | Transit reviewer | TCRP 113, ch. 8 | State how boardings and alightings were balanced |
| 11 | Random arrivals and FIFO are assumptions too | Transit reviewer | Bowman & Turnquist; Ingvardson et al.; Schmöcker et al.; Trozzi et al. | One sentence each, with the alternative named |
| 12 | Without OD, short-turning, stop-skipping, express patterns and transfers are out of reach | Transit reviewer | Own analysis | Concede as a limit of scope |

### Risk 1: alighting sampled independently of the load

What the sources say. Every located model that treats alighting stochastically draws it conditional on the load: Binomial on the arriving load with a stop-specific probability in BusMezzo ([Toledo et al. 2010](https://www.transportportal.se/swopec/CTS2013-29.pdf)) and in Khan et al. ([arXiv:2202.06039](https://arxiv.org/pdf/2202.06039)); a percentage of on-board passengers in BusSim ([Kieu et al.](https://ar5iv.labs.arxiv.org/html/1908.08288)); a deterministic fraction of on-board passengers in Petit et al. ([Petit et al. 2018](https://par.nsf.gov/servlets/purl/10079018)). Li and Cassidy argue that alighting probabilities are what stays stable across trips ([Li & Cassidy 2007, index record](https://ideas.repec.org/a/eee/transb/v41y2007i1p114-125.html)). No published model was found that samples alighting counts independently of the load, after two targeted searches; that is absence of evidence, not proof of absence.

Researchers' own analysis, anchored in those facts and in the identity load = cumulative boardings minus cumulative alightings ([TCRP 113, ch. 8](https://nap.nationalacademies.org/read/13907/chapter/10)). An independent draw can exceed the load; truncating it biases realised alightings below the fitted mean and loads upward, most strongly for lightly loaded buses. With independent boardings and alightings the load is an unbounded random walk whose variance grows along the line, whereas real alightings co-vary with earlier boardings on the same trip; independent sampling therefore overstates load dispersion and with it the frequency of saturation and denied boarding, which is the absorption result. Boardings are an arrival process in time, so their total is invariant to the number of buses, but alightings drawn per bus arrival scale with the number of bus arrivals: the model is calibrated to the observed frequency and cannot answer supply what-ifs. This last point collides with step 1 of the argument, which motivates simulation by the need to evaluate supply alternatives. The terminal stop needs an override (everyone alights), which is an implicit admission that alighting depends on load. No empirical study quantifying the error of load-independent sampling was found.

The remedy the notes identify preserves the OD-free claim and needs no extra data: estimate, per stop and slot, the ratio of mean alightings to mean arriving load, and sample Binomial(load, p), or a beta-binomial if over-dispersion is needed. If the first manuscript version keeps the old layout, the notes' recommendation is to report the share of truncated draws and the gap between fitted and realised alighting means per stop as a diagnostic. Whether a later version changes the rule is the author's decision; the exposure of the first version is the same either way.

### Risk 2: the implied OD matrix under FIFO

What the sources say. Furth and Navick prove that Tsygalnitsky's recursive "fluid" method is the biproportional (IPF) method with a null seed, the solution in which every permissible OD pair is equally preferred ([Furth & Navick 1992](http://onlinepubs.trb.org/Onlinepubs/trr/1992/1338/1338-002.pdf)). The fluid assumption is that alighting passengers are drawn from the on-board load with equal probability whatever their boarding stop, which Li and Cassidy call often unrealistic ([Li & Cassidy 2007](https://escholarship.org/content/qt17m7k4vm/qt17m7k4vm.pdf)). Kingman (1962) proves that serving in order of arrival minimises waiting-time variance, the mean being independent of discipline under certain conditions ([Kingman 1962](https://www.cambridge.org/core/journals/mathematical-proceedings-of-the-cambridge-philosophical-society/article/abs/effect-of-queue-discipline-on-waiting-time-variance/D48362807F5674D679592E8BBA13C63C)).

Researchers' own analysis. A model that removes alighting passengers uniformly at random carries the null-seed IPF matrix implicitly. A model that removes them first-in-first-out carries a different one: the extreme assignment that makes ride lengths as equal as possible (mean ride length is fixed by the marginals; FIFO minimises its variance). That statement is reasoning by analogy with Kingman, whose theorem concerns a single-server queue and not a bulk server, and no transit source was found for it. The consequence is practical: any in-vehicle time, trip-length or itinerary statistic produced by Architecture 1 is an artefact of the alighting discipline and must not be reported. The defence against "you do have an OD matrix" is that it is implied, never estimated, and that no reported output is a function of it. FIFO at the stop is a different matter and has precedent: BusMezzo forms a boarding queue by arrival time ([Cats, West & Eliasson 2016](https://pure.tudelft.nl/ws/files/11510486/Cats_et_al_TR_B_2016b.pdf)), Trozzi et al. enforce FIFO queues ([Trozzi et al. 2013, index record](https://ideas.repec.org/a/eee/transb/v57y2013icp266-285.html)), and the alternative a reviewer will name is Schmöcker et al., where passengers mingle on the platform ([Schmöcker et al. 2008, index record](https://ideas.repec.org/a/eee/transb/v42y2008i10p925-945.html)).

### Risks 3 to 5: terminology

The mesoscopic conflict, the single-axis confusion and the three misused terms are documented under steps 3 to 5 above. Two additions. The reference list must not mix the two meanings of "mesoscopic" silently: if the PLOS ONE GAMA paper is cited near the mesoscopic claim, a reader can turn its "not individual-based" against Architecture 1. And the draft's Section 2 sentence that, per Brooks, emergent behaviour "guarantees an agency" is overstated: Brooks supports only that behaviour an observer reads as intelligent can arise from simple situated behaviours without central representation ([Brooks 1991](https://jmvidal.cse.sc.edu/library/brooks91b.pdf)); a definition of agency has to carry that claim, and the weak notion of agency in Wooldridge and Jennings (autonomy, social ability, reactivity, pro-activeness) is the standard one ([Wooldridge & Jennings 1995](https://www.cs.ox.ac.uk/people/michael.wooldridge/pubs/ker95/subsubsectionstar3_1_1_1.html)).

### Risks 6 to 8: are these agents, and are they too simple?

What the sources say. Parunak et al. find agent-based modelling most appropriate for domains with a high degree of localisation and distribution, dominated by discrete decisions, and call these tendencies and not hard rules ([Parunak et al. 1998](https://sites.pitt.edu/~cler/MSCMP3780/abm2.pdf)). O'Sullivan et al. state that where all agents face the same choice an aggregated statistical representation may be sufficient ([O'Sullivan et al. 2012](https://library.alnap.org/system/files/content/resource/files/main/OSullivan_etal_2012.pdf)). Grimm et al. hold that observed patterns decide which entities and resolution must be in the model ([Grimm et al. 2005](https://fenix.ciencias.ulisboa.pt/downloadFile/844562369089361/Pattern-oriented%20science.pdf)). Srikrishnan and Keller show in a perfect-model experiment that a limited data record may not constrain even a four-parameter agent-based model ([Srikrishnan & Keller 2021, institutional record](https://pure.psu.edu/en/publications/small-increases-in-agent-based-model-complexity-can-result-in-lar/)). Edmonds and Moss's KIDS approach starts from the descriptive model and simplifies only when model and evidence justify it ([Edmonds & Moss 2005, report page](http://cfpm.org/cpmrep132.html)). Huang et al. list as a limitation of the field that many systems still rest on simple threshold-based rules ([Huang et al. 2022](https://downloads.hindawi.com/journals/jat/2022/1252534.pdf)).

Researchers' inferences. Parunak's criteria support buses and stops as agents (distributed, discrete events) and cut against passenger agents that take no decision; Architecture 2 is the configuration those criteria favour, so Architecture 1 needs a positive justification that does not depend on a destination (queue position and individual waiting time at the stop, extensibility to behaviour, validation of the aggregate model). Under KIDS, Architecture 1 is the descriptive starting point and Architecture 2 the simplification the evidence justifies; if both give statistically indistinguishable occupancy and absorption, that equivalence is a result, and presenting it first answers "why agents for passengers at all" before it is asked. The absence of passenger cognition is justified by identifiability: no pattern in boarding and alighting counts can discriminate between passenger decision rules. This argument justifies the absence of cognition; it does not justify the mesoscopic label, and the two claims need separate sentences and separate citations. No source was found that states as a general rule that agent behaviour must not exceed what calibration data can identify; Srikrishnan and Keller is the nearest empirical statement, for one flood-risk model. On autonomy, the strongest evidence in the model is a capacity-dependent agree or refuse in the boarding protocol, which is Wooldridge's criterion for separating agents from objects. One further warning applies to Architecture 1: Sun et al. caution against "mid-level" models that mix stylised and empirical parts ([Sun et al. 2016, institutional record](https://tore.tuhh.de/handle/11420/5222)); Architecture 1 mixes fitted rates and travel times with a stylised FIFO alighting rule, so the manuscript must state what that rule can support (counts and loads) and what it cannot (individual in-vehicle times or itineraries).

### Risks 9 to 12: data and scope

Poisson arrivals are the modelling default in BusMezzo and Khan et al., and Chen et al. acknowledge that bus-journey data typically exhibit over-dispersion and zero inflation ([Chen, Cheng & Sun 2025, arXiv v2](https://arxiv.org/html/2403.04742v2)), but no verified source fits a negative binomial to per-stop, per-time-slot boarding counts of a bus line and tests it against Poisson; the nearest, Pulugurtha and Agurla, is cross-sectional between stops ([Pulugurtha & Agurla 2012](https://digitalcommons.usf.edu/jpt/vol15/iss1/3)). The author's own goodness-of-fit evidence has to carry that modelling choice. The researchers add two points of their own: with Poisson arrivals and variable headways, boardings per bus are a mixed Poisson, so over-dispersion per bus does not by itself show a non-Poisson arrival process, and the manuscript must say whether the fitted unit is arrivals per slot or boardings per bus; and observed boardings are censored demand when buses are full, which matters for an absorption result. On arrivals, Ingvardson et al. find that even at 5-minute headways **43% of passengers arrive in a timely manner** when timetables are available ([Ingvardson et al. 2018, index record](https://www.worldtransitresearch.info/research/6838)). On the balance of counts, TCRP 113 documents drift and negative loads in unbalanced APC counts ([TCRP 113, ch. 8](https://nap.nationalacademies.org/read/13907/chapter/10)).

## Seven keys are real, two are misused; two PDFs carry weight

All seven BibTeX keys match verifiable publications. Two are cited for claims their sources do not make (`horni2016matsim`, `brooks1991representation`), one is correct but weak (`huang2022overview`), and the three simulators are cited accurately but for a sentence that does not use what they offer.

**Table 3. The seven existing keys**

| Key | Matched publication | Use in the draft | Verdict and correct use |
|---|---|---|---|
| `manser2020designing` | Manser, Becker, Hörl & Axhausen, Transportation Research Part A 137, 1-15 (2020) | One of three "simulation techniques in public transport" | Keep. MATSim-based network design for Zurich with a co-evolutionary algorithm. Nothing in the abstract suggests BDI; full text not read |
| `sun2021transitgym` | Sun et al., IEEE SMARTCOMP 2021, pp. 69-76 | Same sentence | Keep, as the foil: SUMO microscopic simulation with person trips generated from an OD matrix; boardings and alightings are outputs. Also carries the motive that collected data do not cover all scenarios |
| `talusan2025dispatch` | Most probably Talusan et al., ACM TCPS 9(4), Article 43 (2025); the conference version is ICCPS 2024, pp. 157-168 | Same sentence | Keep, as the nearest precedent for the data constraint: APC only, no OD, counts, event-driven. Not agent-based in the MAS sense. Confirm which version the `.bib` entry holds: title, author list and venue differ |
| `huang2022overview` | Huang, Cui, Zhang, Tong, Shi & Liu, Journal of Advanced Transportation 2022, 1252534 | Growth of the multi-agent paradigm | Keep as the transport-wide overview; add the Cities review and Bastarianto et al. for numbers. Expect its Sec. 4.4.2 (simple rules as a limitation) to be used against step 5. The verified author list contains no "Kanezashi", a name that appeared in the research brief |
| `horni2016matsim` | Horni, Nagel & Axhausen (eds.), Ubiquity Press, 2016 | MATSim as a tool for building BDI multi-agent systems | Misused. Cite for what MATSim is, with chapter 1; cite Padgham et al. 2014 and chapter 31 for the BDI coupling |
| `brooks1991representation` | Brooks, Artificial Intelligence 47, 139-159 (1991) | Emergent behaviour "guarantees" agency; intelligence from communication | Misused. Supports only intelligence without central representation in a single situated robot. Keep for that narrow point or drop |
| `taillandier2019gama` | Taillandier et al., GeoInformatica 23(2), 299-322 (2019) | Platform reference | Keep. The article text was not read: whether it documents the FIPA skill and headless batch mode, the draft's two reasons for choosing GAMA, is unchecked; the GAMA documentation page is the verified source for the FIPA skill |

Sources for Table 3: Manser ([Crossref](https://api.crossref.org/works/10.1016/j.tra.2020.04.011); [RePEc](https://ideas.repec.org/a/eee/transa/v137y2020icp1-15.html)); Transit-Gym ([Penn State record](https://pure.psu.edu/en/publications/transit-gym-a-simulation-and-evaluation-engine-for-analysis-of-bu/); [full text](https://ar5iv.arxiv.org/html/2107.00105)); Talusan ([TCPS record](https://pure.psu.edu/en/publications/an-end-to-end-solution-for-public-transit-stationing-and-dispatch/); [ICCPS record](https://pure.psu.edu/en/publications/an-online-approach-to-solving-public-transit-stationing-and-dispa/)); Huang ([publisher PDF](https://downloads.hindawi.com/journals/jat/2022/1252534.pdf)); MATSim ([Ubiquity Press](https://www.ubiquitypress.com/site/books/e/10.5334/baw/)); Brooks ([paper PDF](https://jmvidal.cse.sc.edu/library/brooks91b.pdf)); GAMA ([IRD record](https://www.documentation.ird.fr/hor/fdi:010075739); [FIPA skill documentation](https://gama-platform.org/wiki/UsingFIPAACL)).

**Table 4. The six project PDFs**

| File | Publication | Verdict | Use for | Do not use for |
|---|---|---|---|---|
| `1s2.0S0264275124009119main.pdf` | Divasson-J., Macarulla, Garcia & Borges, Cities 158, 105697 (2025) | Cite | Step 2 with numbers; GAMA among the five dominant tools; data origins (company data 7.79%) | Steps 3 and 4: it contains no discussion of BDI, reactive versus cognitive agents, or granularity |
| `journal.pone.0281658.pdf` | Saval et al., PLOS ONE 18(3), e0281658 (2023) | Cite, with care | GAMA as an extensible generic platform; MATSim labelled mesoscopic; calibrate on one site and validate on another | The mesoscopic label of the E01 model: its definition ("not individual-based") is the opposite meaning |
| `LNBIPPaperNabilMorri.pdf` | Morri, Hadouaj & Ben Said, LNBIP 417, pp. 242-267 (2021) | Cite briefly | Design precedent for Architecture 2's agent set: vehicle and station agents exchanging messages, station holding boarding and alighting flows, no passenger agent | Any claim of FIPA, BDI or statistical validation: AnyLogic, expert-set thresholds, no statistical test |
| `ICEIS_2020NabilMorri.pdf` | Morri, Hadouaj & Ben Said, ICEIS 2020, pp. 416-427 | Do not cite alongside the LNBIP chapter | Nothing the extended chapter does not cover | A second, self-overlapping citation |
| `sustainability1608907.pdf` | Chambers, Di Marzo Serugendo & Cruz, Sustainability 16(20), 8907 (2024) | Optional, one clause | GAMA plus public transport at the strategic level; emergence from agent-agent and agent-environment interaction | Operations modelling: no vehicles, no passengers, visual validation |
| `28.TrafficSimulationusingAgentBasedModelling2021.pdf` | Shaharuddin & Misro, AIP Conference Proceedings 2423, 020035 (2021) | Drop | Nothing that Saval et al. and the Cities review do not support better | An EAAI reference list: no calibration, no validation, five runs per setting, campus scope, which the Cities review's own exclusion criteria reject |

Sources for Table 4: [Cities review](https://doi.org/10.1016/j.cities.2024.105697); [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0281658); [LNBIP chapter](https://doi.org/10.1007/978-3-030-75418-1_12); [ICEIS paper](https://www.scitepress.org/Link.aspx?doi=10.5220/0009416104160427); [Sustainability](https://www.mdpi.com/2071-1050/16/20/8907); [AIP proceedings](https://doi.org/10.1063/5.0075719). None of the six uses FIPA or ACL, none uses BDI, and none simulates boarding and alighting on a bus line; step 3 therefore cannot be sourced from this set at all. Indexing status and quartiles of the six venues were not verified.

## Seven paragraphs, one claim each: the evidence map

The map gives, per paragraph, the single claim, the verified support and the statements to avoid. It deliberately stops short of prose. Each entry ends with the decision that is the author's to make. Keys refer to Appendix A.

### Paragraph 1. Why simulate

**Claim.** Judging a supply configuration from observed operation is limited by sample size at the extremes and by the joint determination of supply and demand; operational alternatives are therefore evaluated by simulation before deployment. **Support.** `furth2006using` (large samples for extremes and crowding); `taylor2009nature` (simultaneity, metropolitan level); `berrebi2020ridership` (ridership responds to frequency within a route segment; preprint); `toledo2010mesoscopic` (simulation as the primary tool at operational level); `cats2011impacts` (holding strategies evaluated by simulation on a Stockholm trunk line); `sun2021transitgym` and `talusan2025dispatch` (scenarios of interest are absent or sparse in collected data). **Do not say.** That a multi-month window with a fixed configuration is "required" (TCRP 113 says moderate samples suffice for most count uses); that a small supply change makes results "inconsistent"; that operators rely on simulation on the strength of three research prototypes; that field experiments are infeasible. **Left to the author.** Whether the eight-month window is argued from the literature (extremes only) or from the dataset's own cell counts.

### Paragraph 2. Agent-based simulation in transport

**Claim.** Agent-based simulation is an established and growing approach in urban mobility, GAMA is among its most used platforms, and multi-agent work on public transport is a small share concentrated on real-time control. **Support.** `divassonj2025abm` (154 publications, 258 applications, tool shares); `bastarianto2023agent` (309 documents, growth from 2015); `huang2022overview` (overview without counts); `balbo2024extended` (14.7% share, falling; few papers analyse the system); `bazzan2014review` (public transport named as a topic the review does not cover in depth). **Do not say.** "Increasing" with Huang et al. alone; that the three transit simulators are multi-agent systems (Talusan et al. is not agent-based in the MAS sense; Transit-Gym is SUMO); anything resting on `shaharuddin2021traffic`. **Left to the author.** How much of the ABM-versus-MAS distinction to expose here; it strengthens the gap statement but invites the "are these agents" question early.

### Paragraph 3. Architecture follows the level of observation

**Claim.** Cognitive architectures are chosen when individual deliberation or within-run reaction is the object of study; in transport simulation they are a minority, applied to drivers and evacuees and coupled to MATSim as an extension, while the usual agent is utility-based at the demand level and reactive at the vehicle level. **Support.** `adam2016bdi` (Secs. 3.4, 2.1.6, 3.5.1, 3.5.2); `balke2014agents` (paras. 1.1, 2.2); `bazzan2014review` (Sec. 3.4.3); `horni2016introducing` (what MATSim agents are); `padgham2014integrating`, `padgham2016bdi`, `singh2016integrating` (the coupling and its applications); `rossetti2002bdi`, `dia2002agent`, `noroozian2014heterogeneous` (drivers); `taillandier2017bdi`, `bourgais2020ben` (BDI in GAMA; cost and sensitivity). **Do not say.** That MATSim is a BDI tool or that `manser2020designing` uses BDI; "normally"; "microsimulations" or "microscopic level"; "passengers and buses"; that BDI "does not scale" (the evidence is mixed); that Balke and Gilbert's "one of the most popular models" describes simulation practice (it describes the agent-programming community). **Left to the author.** How to answer Adam and Gaudou's view that BDI suits transport when travellers have many options, and whether the single-line, no-choice setting is the answer.

### Paragraph 4. Level of detail, on two axes

**Claim.** Level of detail is set separately for supply dynamics and for demand representation; this work fixes supply at the mesoscopic level in the sense of Toledo et al. and varies demand between disaggregate and aggregate. **Support.** `burghout2004hybrid`, `fhwa_tat_vol1` (definitions); `toledo2010mesoscopic` (transit definition, fitted running times, rationale against microscopic detail); `cats2016modelling`, `cats2016dynamic` (individual passengers on mesoscopic dynamics, FIFO boarding, denied boarding); `horni2016introducing` (microscopic demand on a queue model); `nguyen2021overview` (granularity and agent orientation as separate axes); `hadi2022mrm` (demand representation as a separate element). **Do not say.** "Mesoscopic in scope"; mesoscopic "because the passenger is not BDI"; "just a statistical count" for Architecture 1; that the two-axis view is an established taxonomy; anything that places `saval2023gama` next to the mesoscopic claim without disambiguation. **Left to the author.** Whether to keep "mesoscopic" at all, given that the model has no traffic-flow component, or to use the neutral "discrete-event simulation of line operations" and cite Toledo et al. for the precedent only.

### Paragraph 5. Counts, load and the OD matrix

**Claim.** Stop-level boarding and alighting counts determine the load profile but not the OD matrix; occupancy and absorption are functions of the former; established operations models run on arrival rates and alighting fractions without an OD matrix. **Support.** `li2007generalized`, `hazelton2010statistical`, `li2009markov`, `chen2025bayesian` (non-identifiability); `furth1992bus`, `mccord2010iterative`, `ji2014estimating` (what null-seed IPF is and how it performs); `furth2006using` (load as cumulative boardings minus alightings); `ceder1984bus` (frequency from load profiles); `toledo2010mesoscopic`, `kieu2020dealing`, `khan2022modular` (OD-free precedents); `sun2021estimating` (loads and alighting flows identified better than OD flows, from dwell times); `sun2021transitgym`, `quek2021analysis`, `wang2021reducing` (the contrast class that needs destinations). **Do not say.** That the model "has no OD matrix" (it implies one); that IPF is "seed-dependent" without qualification (the null base is an accepted default that performs "surprisingly well" in McCord et al., and Ji et al. 2014 converge regardless of the initial base); that reconstruction is a "harder problem" (null-seed IPF is a single pass); that OD "cannot" be estimated from eight months of counts (it could; the argument is that it is not needed); any in-vehicle time or trip-length result; "maximum entropy" as if it were the transit literature's term for the null-seed solution (no fetched transit source uses the phrase; the chain is Furth and Navick's equal preference, Li and Cassidy's minimum information relative to the seed, and general IPF theory). Do not cite the Changzhou tap-in preprint (unreviewed, no ground truth, a different data regime) or describe the Canadian Journal of Civil Engineering paper (content unverified). **Left to the author.** Whether to state the load-invariance and degrees-of-freedom arguments as the paper's own observations with n for E01, and how this paragraph will read once the alighting rule is settled.

### Paragraph 6. The agents and their interactions

**Claim.** The agents are non-deliberative and empirically calibrated; the behaviour of interest is produced by local interactions specified as FIPA interaction protocols, and the key indicator is defined on protocol outcomes. **Support.** `wooldridge1995intelligent`, `wooldridge1999intelligent` (architecture classes, agents with state, the refuse criterion); `parunak1998agent` (when agents are warranted; relations between observables as output, not input); `grimm2005pattern`, `osullivan2012agent`, `srikrishnan2021small`, `edmonds2005kiss` (resolution follows purpose and data); `jennings2000agent`, `kubera2010everything`, `kubera2011ioda` (interaction as the design object, simple entities as agents); `odell2001representing`, `fipa00026`, `gama_fipa`, `taillandier2019gama` (specification formalism and platform); `dewolf2005emergence`, `bonabeau2002agent` (emergence of macro-level regularities); `singh1998agent` (protocols without mentalistic semantics). **Do not say.** "Data-driven" with `zhang2016data` or `kavak2018big`; "goal-oriented"; "intelligence emerges from communication"; Brooks for inter-agent communication or for a guarantee of agency; "purely reactive" for buses and stops; that GAMA conforms to the FIPA specifications or relates to JADE (its documentation states neither); "Medawar zone" attributed to O'Sullivan et al. (the term is in Grimm et al.). **Left to the author.** Which macro-level result no rule encodes will be shown as the emergent regularity, and whether an out-of-sample check (fit on some days, test on others) will be reported to earn the broader sense of "data-driven".

### Paragraph 7. Gap and contribution

**Claim.** OD-free bus-line models exist either as non-agent mesoscopic simulators or as agent-based models on synthetic data, and multi-agent work on buses targets control; this work contributes a protocol-specified multi-agent model of one line, calibrated on operator counts, with a controlled comparison of demand resolution. **Support.** `toledo2010mesoscopic`, `cats2010mesoscopic` (BusMezzo); `kieu2020dealing` (BusSim); `talusan2025dispatch` (count-driven, not agent-based); `balbo2024extended` (the gap; protocols used in the field); `morri2021approach` (vehicle and station agents, no passenger agent, AnyLogic); `dimitrov2017modeling`, `meignan2007simulation`, `zhao2003distributed` (to be read first). **Do not say.** "First" for OD-free simulation, for bus and stop agents, for a GAMA bus model or for FIPA in public transport; that the novelty is the sampling scheme; "intelligence". **Left to the author.** Which of the five candidate contributions leads, given that EAAI asks for an AI novelty as well as an engineering application.

## What was not verified, and why it matters

The verdicts above are only as good as the access the researchers had, and the limits are specific. Crossref and OpenAlex API calls were rate-limited after the first requests; the doi.org resolver, ScienceDirect, Taylor & Francis, Wiley, IEEE pages, cdnsciencepub.com, Project Euclid, HAL, PubMed Central, SWOV, the ETH Research Collection, several link.springer.com pages, the AAMAS 2011 PDF, the Ubiquity Press chapter PDFs, the TCQSM chapter on onlinepubs.trb.org and FIPA documents SC00029H and SC00037J could not be read. One DOI recalled from memory for Toledo et al. turned out to be wrong when checked, which is why no DOI appears in Appendix A unless it was seen on a fetched page.

Four consequences bear directly on Section 1. First, every quoted phrase in this report was returned by an automated page reader and is a pointer, not a transcription; none should enter the manuscript verbatim before it is checked against the PDF. Second, several key sources were read in a version other than the one to be cited: Toledo et al. in the CTS Working Paper 2013:29 reissue (section numbers and pagination differ from the journal), Kieu et al. and Khan et al. on arXiv, Zhang et al. in the AAMAS 2015 version, Talusan et al. in the ICCPS 2024 version, Parunak et al. in a course-hosted copy. Third, some characterisations are second-hand: Rossetti et al. (2002) and Dia (2002) as BDI rest on Bazzan and Klügl's description; Russell and Norvig's taxonomy on course slides; Ferber's reactive/cognitive wording on a book review; the body of MATSim chapter 31 was not read, so its motivation and architecture are reported from the ECAI 2014 paper by the same authors; Meignan et al. and Zhao et al. are known through Balbo et al. Fourth, surveys were read incompletely: Adam and Gaudou's preview was truncated in Sec. 3.5.3 and gave no page numbers within 207-238; Balke and Gilbert's Section 8 was read only up to the first comparison tables; TCRP 113 page numbers are approximate and its sample-size chapter was not returned; the FHWA page returned only the one-sentence definitions; the approach of Kavak et al. (2018) is inferred from the first author's dissertation abstract.

Three absences are search-limited and must be worded as such: no peer-reviewed BDI passenger model for bus, metro or rail; no peer-reviewed GAMA model of bus-line operations; no bus model with FIPA-specified boarding and alighting. A Scopus or Web of Science query is needed before any of the three is asserted. The terminology assessment (granularity, agent classes, emergence) was made from the brief's description of the manuscript and not from the draft; the assessment of the existing citations was made from the draft `.tex`. Bazzan and Klügl's review dates from 2014, and no equivalent AI-oriented review of agent technology in traffic from 2018 onwards was found.

## Conclusion

The argument the sources support is narrower and stronger than the one drafted. It does not run "BDI is for microsimulation, we are mesoscopic, so we are reactive"; it runs "the data identify loads and not itineraries, so demand needs no destination and passengers need no cognition; supply needs no vehicle dynamics; what remains to be modelled is who asks whom for what, and that is an interaction-protocol problem". That reformulation moves the AI contribution from a property the agents do not have (intelligence, goals, learning from data) to a property the model does have (a protocol specification whose outcomes define the indicator, and a controlled change of agent resolution), which is the only version of the contribution that can be defended line by line with verified sources.

The introduction cannot be finalised independently of the alighting rule. A paragraph that motivates simulation by the need to test supply alternatives, followed by a model whose alighting draw is tied to the observed frequency, hands the reviewer the objection. Before the prose is written, three items need a decision or a check that no literature search can supply: whether the bus can refuse a boarding request in the implemented protocol, whether the first manuscript version keeps load-independent alighting and with what diagnostics, and what Dimitrov et al. (2017) actually did on a single Auckland route.

## Appendix A. Consolidated BibTeX (entries verified in the notes)

Reading rules. An entry is included when its bibliographic details were confirmed on a page actually fetched: [P] the publisher page, the publication's own PDF or an author-hosted full text; [R] an institutional repository or university record; [I] a bibliographic index (Crossref, DBLP, OpenAlex, DOAJ, RePEc, TRID, World Transit Research). The comment above each entry states the level and what was not confirmed. A missing `doi`, `pages` or `number` field means the value was not seen on a fetched page, not that none exists. The seven existing keys are kept. Two duplicates in the notes were merged: `saval2023mixed` into `saval2023gama`, and `kieu2019dealing` into `kieu2020dealing`.

```bibtex
% ---------------------------------------------------------------------------
% Keys already used in the draft (kept unchanged)
% ---------------------------------------------------------------------------

% [I] Crossref record; abstract on RePEc. Full text not read.
@article{manser2020designing,
  author  = {Manser, Patrick and Becker, Henrik and H{\"o}rl, Sebastian and Axhausen, Kay W.},
  title   = {Designing a large-scale public transport network using agent-based microsimulation},
  journal = {Transportation Research Part A: Policy and Practice},
  volume  = {137},
  pages   = {1--15},
  year    = {2020},
  doi     = {10.1016/j.tra.2020.04.011}
}

% [R] Pages and DOI from one institutional record (Penn State Pure). Authors and title also on
%  arXiv:2107.00105, the version whose text was read.
@inproceedings{sun2021transitgym,
  author    = {Sun, Ruixiao and Gui, Rongze and Neema, Himanshu and Chen, Yuche and Ugirumurera, Juliette and Severino, Joseph and Pugliese, Philip and Laszka, Aron and Dubey, Abhishek},
  title     = {{Transit-Gym}: A Simulation and Evaluation Engine for Analysis of Bus Transit Systems},
  booktitle = {Proceedings of the 2021 IEEE International Conference on Smart Computing (SMARTCOMP)},
  pages     = {69--76},
  year      = {2021},
  publisher = {IEEE},
  doi       = {10.1109/SMARTCOMP52413.2021.00030}
}

% [R] Single source (Penn State Pure); confirm on the ACM Digital Library. Full text not read. If
%  the draft's entry is the ICCPS 2024 paper, use talusan2024online instead.
@article{talusan2025dispatch,
  author  = {Talusan, Jose Paolo and Han, Chaeeun and Rogers, David and Mukhopadhyay, Ayan and Laszka, Aron and Freudberg, Dan and Dubey, Abhishek},
  title   = {An End-to-End Solution for Public Transit Stationing and Dispatch Problem},
  journal = {ACM Transactions on Cyber-Physical Systems},
  volume  = {9},
  number  = {4},
  pages   = {43},
  note    = {Article 43},
  year    = {2025},
  doi     = {10.1145/3754454}
}

% [P] Publisher PDF read; DOAJ record.
@article{huang2022overview,
  author  = {Huang, Jiangyan and Cui, Youkai and Zhang, Lele and Tong, Weiping and Shi, Yunyang and Liu, Zhiyuan},
  title   = {An Overview of Agent-Based Models for Transport Simulation and Analysis},
  journal = {Journal of Advanced Transportation},
  volume  = {2022},
  pages   = {1252534},
  note    = {Article ID 1252534, 17 pages},
  year    = {2022},
  doi     = {10.1155/2022/1252534}
}

% [P] Open-access book PDF.
@book{horni2016matsim,
  editor    = {Horni, Andreas and Nagel, Kai and Axhausen, Kay W.},
  title     = {The Multi-Agent Transport Simulation {MATSim}},
  publisher = {Ubiquity Press},
  address   = {London},
  year      = {2016},
  isbn      = {978-1-909188-75-4},
  doi       = {10.5334/baw}
}

% [P] Paper PDF read; volume, issue and pages from a university bibliography entry. DOI not seen on
%  a fetched page, omitted.
@article{brooks1991representation,
  author  = {Brooks, Rodney A.},
  title   = {Intelligence without representation},
  journal = {Artificial Intelligence},
  volume  = {47},
  number  = {1--3},
  pages   = {139--159},
  year    = {1991}
}

% [R] IRD record (citation and abstract). Article text not read.
@article{taillandier2019gama,
  author  = {Taillandier, Patrick and Gaudou, Benoit and Grignard, Arnaud and Huynh, Quang-Nghi and Marilleau, Nicolas and Caillou, Philippe and Philippon, Damien and Drogoul, Alexis},
  title   = {Building, composing and experimenting complex spatial models with the {GAMA} platform},
  journal = {GeoInformatica},
  volume  = {23},
  number  = {2},
  pages   = {299--322},
  year    = {2019},
  doi     = {10.1007/s10707-018-00339-6}
}

% ---------------------------------------------------------------------------
% The six project PDFs
% ---------------------------------------------------------------------------

% [P] PDF on disk; title, authors, journal and volume confirmed on OpenAlex.
@article{divassonj2025abm,
  author  = {Divasson-J., A. and Macarulla, Ana M. and Garcia, J. Ignacio and Borges, Cruz E.},
  title   = {Agent-based modeling in urban human mobility: A systematic review},
  journal = {Cities},
  volume  = {158},
  pages   = {105697},
  year    = {2025},
  doi     = {10.1016/j.cities.2024.105697}
}

% [P] PDF on disk and publisher page. Second author as printed in the article's own citation ("Minh
%  DP"); another note set writes "Pham Minh, Duc". Replaces the duplicate key saval2023mixed.
@article{saval2023gama,
  author  = {Saval, Arnaud and Minh, Duc Pham and Chapuis, Kevin and Tranouez, Pierrick and Caron, Cl{\'e}ment and Daud{\'e}, {\'E}ric and Taillandier, Patrick},
  title   = {Dealing with mixed and non-normative traffic. An agent-based simulation with the {GAMA} platform},
  journal = {PLoS ONE},
  volume  = {18},
  number  = {3},
  pages   = {e0281658},
  year    = {2023},
  doi     = {10.1371/journal.pone.0281658}
}

% [P] PDF on disk; confirmed on OpenAlex (Springer page blocked). Only the first editor is printed;
%  complete the list from the front matter.
@incollection{morri2021approach,
  author    = {Morri, Nabil and Hadouaj, Sameh and Ben Said, Lamjed},
  title     = {An Approach to Intelligent Control Public Transportation System Using a Multi-agent System},
  booktitle = {Enterprise Information Systems. ICEIS 2020},
  editor    = {Filipe, J. and others},
  series    = {Lecture Notes in Business Information Processing},
  volume    = {417},
  pages     = {242--267},
  publisher = {Springer},
  year      = {2021},
  doi       = {10.1007/978-3-030-75418-1_12}
}

% [P] PDF on disk; SCITEPRESS record. Superseded by morri2021approach: cite one of the two, not
%  both.
@inproceedings{morri2020intelligent,
  author    = {Morri, Nabil and Hadouaj, Sameh and Ben Said, Lamjed},
  title     = {Intelligent Regulation System to Optimize the Service Performance of the Public Transport},
  booktitle = {Proceedings of the 22nd International Conference on Enterprise Information Systems (ICEIS 2020) -- Volume 1},
  pages     = {416--427},
  publisher = {SCITEPRESS},
  year      = {2020},
  isbn      = {978-989-758-423-7},
  doi       = {10.5220/0009416104160427}
}

% [P] PDF on disk; MDPI page.
@article{chambers2024autonomous,
  author  = {Chambers, Flann and Di Marzo Serugendo, Giovanna and Cruz, Christophe},
  title   = {Autonomous Generation of a Public Transportation Network by an Agent-Based Model: Mutual Enrichment with Knowledge Graphs for Sustainable Urban Mobility},
  journal = {Sustainability},
  volume  = {16},
  number  = {20},
  pages   = {8907},
  year    = {2024},
  doi     = {10.3390/su16208907}
}

% [P] PDF on disk; OpenAlex. Not recommended for an EAAI reference list.
@inproceedings{shaharuddin2021traffic,
  author    = {Shaharuddin, Raihanah Adawiyah and Misro, Md Yushalify},
  title     = {Traffic simulation using agent based modelling},
  booktitle = {Proceedings of the International Conference on Mathematical Sciences and Technology 2020 (MathTech 2020)},
  series    = {AIP Conference Proceedings},
  volume    = {2423},
  pages     = {020035},
  year      = {2021},
  publisher = {AIP Publishing},
  doi       = {10.1063/5.0075719}
}

% ---------------------------------------------------------------------------
% Motivation: observed data versus simulation
% ---------------------------------------------------------------------------

% [P] Report PDF and National Academies record. Page numbers used in the notes are approximate; the
%  sample-size chapter (ch. 9) was not read.
@techreport{furth2006using,
  author      = {Furth, Peter G. and Hemily, Brendon and Muller, Theo H. J. and Strathman, James G.},
  title       = {Using Archived {AVL-APC} Data to Improve Transit Performance and Management},
  type        = {TCRP Report},
  number      = {113},
  institution = {Transportation Research Board},
  address     = {Washington, DC},
  year        = {2006},
  isbn        = {0-309-09861-0},
  doi         = {10.17226/13907}
}

% [I] World Transit Research record. DOI not shown, omitted.
@article{taylor2009nature,
  author  = {Taylor, Brian D. and Miller, Douglas and Iseki, Hiroyuki and Fink, Camille},
  title   = {Nature and/or nurture? Analyzing the determinants of transit ridership across {US} urbanized areas},
  journal = {Transportation Research Part A: Policy and Practice},
  volume  = {43},
  number  = {1},
  pages   = {60--77},
  year    = {2009}
}

% [P] arXiv record only. Preprint; journal version not verified.
@misc{berrebi2020ridership,
  author        = {Berrebi, Simon and Joshi, Sanskruti and Watkins, Kari E.},
  title         = {On Ridership and Frequency},
  year          = {2020},
  eprint        = {2002.02493},
  archivePrefix = {arXiv}
}

% [I] RePEc record of the working-paper version; single source for DOI and pages.
@article{cats2011impacts,
  author  = {Cats, Oded and Larijani, Anahid Nabavi and Koutsopoulos, Haris N. and Burghout, Wilco},
  title   = {Impacts of holding control strategies on transit performance: a bus simulation model analysis},
  journal = {Transportation Research Record},
  volume  = {2216},
  pages   = {51--58},
  year    = {2011},
  doi     = {10.3141/2216-06}
}

% [R] Penn State Pure; text read as arXiv:2403.03339. Single source for DOI and pages.
@inproceedings{talusan2024online,
  author    = {Talusan, Jose Paolo and Han, Chaeeun and Mukhopadhyay, Ayan and Laszka, Aron and Freudberg, Dan and Dubey, Abhishek},
  title     = {An Online Approach to Solving Public Transit Stationing and Dispatch Problem},
  booktitle = {Proceedings of the 15th ACM/IEEE International Conference on Cyber-Physical Systems (ICCPS)},
  pages     = {157--168},
  year      = {2024},
  publisher = {IEEE},
  doi       = {10.1109/ICCPS61052.2024.00021}
}

% ---------------------------------------------------------------------------
% Reviews of agent-based and multi-agent work in transport
% ---------------------------------------------------------------------------

% [R] White Rose record (four authors, initials only); content read on the Springer page, where one
%  reader saw three authors plus "et al.". Confirm the author list and first names.
@article{bastarianto2023agent,
  author  = {Bastarianto, F. F. and Hancock, T. O. and Choudhury, C. F. and Manley, E.},
  title   = {Agent-Based Models in Urban Transportation: Review, Challenges, and Opportunities},
  journal = {European Transport Research Review},
  volume  = {15},
  pages   = {19},
  year    = {2023},
  doi     = {10.1186/s12544-023-00590-5}
}

% [I] OpenAlex (journal, volume, pages, DOI). DBLP lists the venue as ANT/EDI40 2020 and did not
%  confirm the volume. Abstract only.
@article{kagho2020agent,
  author  = {Kagho, Grace O. and Bala{\'c}, Milo{\v{s}} and Axhausen, Kay W.},
  title   = {Agent-Based Models in Transport Planning: Current State, Issues, and Expectations},
  journal = {Procedia Computer Science},
  volume  = {170},
  pages   = {726--732},
  year    = {2020},
  doi     = {10.1016/j.procs.2020.03.164}
}

% [I] Crossref; content read in the KER preview PDF. Crossref gives the online date 3 May 2013; 2014
%  is the conventional issue year for 29(3) and was not separately confirmed.
@article{bazzan2014review,
  author  = {Bazzan, Ana L. C. and Kl{\"u}gl, Franziska},
  title   = {A Review on Agent-Based Technology for Traffic and Transportation},
  journal = {The Knowledge Engineering Review},
  volume  = {29},
  number  = {3},
  pages   = {375--403},
  year    = {2014},
  doi     = {10.1017/S0269888913000118}
}

% [P] arXiv version read; journal record from DOAJ. DOI not shown, omitted.
@article{nguyen2021overview,
  author  = {Nguyen, Johannes and Powers, Simon T. and Urquhart, Neil and Farrenkopf, Thomas and Guckert, Michael},
  title   = {An overview of agent-based traffic simulators},
  journal = {Transportation Research Interdisciplinary Perspectives},
  volume  = {12},
  pages   = {100486},
  year    = {2021},
  eprint  = {2102.07505},
  archiveprefix = {arXiv}
}

% [P] Springer open-access page read.
@article{balbo2024extended,
  author  = {Balbo, Flavien and Mandiau, Ren{\'e} and Zargayouna, Mahdi},
  title   = {Extended review of multi-agent solutions to Advanced Public Transportation Systems challenges},
  journal = {Public Transport},
  volume  = {16},
  number  = {1},
  pages   = {159--186},
  year    = {2024},
  doi     = {10.1007/s12469-023-00332-9}
}

% ---------------------------------------------------------------------------
% MATSim and the BDI coupling
% ---------------------------------------------------------------------------

% [P] Book table of contents; DOI suffix via the Ubiquity reader. Starts p. 3; end page not verified
%  (chapter 2 starts p. 9).
@incollection{horni2016introducing,
  author    = {Horni, Andreas and Nagel, Kai and Axhausen, Kay W.},
  title     = {Introducing {MATSim}},
  booktitle = {The Multi-Agent Transport Simulation {MATSim}},
  editor    = {Horni, Andreas and Nagel, Kai and Axhausen, Kay W.},
  chapter   = {1},
  publisher = {Ubiquity Press},
  address   = {London},
  year      = {2016},
  doi       = {10.5334/baw.1}
}

% [P] Book table of contents. Starts p. 187; end page not verified. Body not read.
@incollection{dobler2016withinday,
  author    = {Dobler, Christoph and Nagel, Kai},
  title     = {Within-Day Replanning},
  booktitle = {The Multi-Agent Transport Simulation {MATSim}},
  editor    = {Horni, Andreas and Nagel, Kai and Axhausen, Kay W.},
  chapter   = {30},
  publisher = {Ubiquity Press},
  address   = {London},
  year      = {2016},
  doi       = {10.5334/baw.30}
}

% [P] Ubiquity chapter page and book table of contents. Starts p. 201; 201--210 inferred from the
%  next divider, not verified. Body not read.
@incollection{padgham2016bdi,
  author    = {Padgham, Lin and Singh, Dhirendra},
  title     = {Making {MATSim} Agents Smarter with the Belief-Desire-Intention Framework},
  booktitle = {The Multi-Agent Transport Simulation {MATSim}},
  editor    = {Horni, Andreas and Nagel, Kai and Axhausen, Kay W.},
  chapter   = {31},
  publisher = {Ubiquity Press},
  address   = {London},
  year      = {2016},
  doi       = {10.5334/baw.31}
}

% [P] IOS Press PDF read; [R] DepositOnce record. FAIA volume 263 taken from the repository file
%  name, not from a printed series statement.
@inproceedings{padgham2014integrating,
  author    = {Padgham, Lin and Nagel, Kai and Singh, Dhirendra and Chen, Qingyu},
  title     = {Integrating {BDI} Agents into a {MATSim} Simulation},
  booktitle = {ECAI 2014: 21st European Conference on Artificial Intelligence},
  editor    = {Schaub, Torsten and Friedrich, Gerhard and O'Sullivan, Barry},
  series    = {Frontiers in Artificial Intelligence and Applications},
  volume    = {263},
  pages     = {681--686},
  publisher = {IOS Press},
  address   = {Amsterdam},
  year      = {2014},
  doi       = {10.3233/978-1-61499-419-0-681}
}

% [P] AAMAS 2014 proceedings PDF. No DOI found.
@inproceedings{chen2014adding,
  author    = {Chen, Qingyu and Wilsher, Arie and Singh, Dhirendra and Padgham, Lin},
  title     = {Adding {BDI} Agents to {MATSim} Traffic Simulator (Demonstration)},
  booktitle = {Proceedings of the 13th International Conference on Autonomous Agents and Multiagent Systems (AAMAS 2014)},
  editor    = {Lomuscio, Alessio and Scerri, Paul and Bazzan, Ana and Huhns, Michael},
  pages     = {1637--1638},
  address   = {Paris, France},
  year      = {2014},
  url       = {https://aamas.csc.liv.ac.uk/Proceedings/aamas2014/aamas/p1637.pdf}
}

% [P] Springer page.
@article{singh2016integrating,
  author  = {Singh, Dhirendra and Padgham, Lin and Logan, Brian},
  title   = {Integrating {BDI} Agents with Agent-Based Simulation Platforms},
  journal = {Autonomous Agents and Multi-Agent Systems},
  volume  = {30},
  number  = {6},
  pages   = {1050--1071},
  year    = {2016},
  doi     = {10.1007/s10458-016-9332-x}
}

% [P] IJCAI proceedings page.
@inproceedings{singh2017ees,
  author    = {Singh, Dhirendra and Padgham, Lin},
  title     = {Emergency Evacuation Simulator ({EES}) -- a Tool for Planning Community Evacuations in {Australia}},
  booktitle = {Proceedings of the Twenty-Sixth International Joint Conference on Artificial Intelligence (IJCAI 2017)},
  pages     = {5249--5251},
  year      = {2017},
  doi       = {10.24963/ijcai.2017/780}
}

% [P] Springer chapter page. Page range not shown, omitted.
@incollection{singh2020matsim,
  author    = {Singh, Dhirendra and Padgham, Lin and Nagel, Kai},
  title     = {Using {MATSim} as a Component in Dynamic Agent-Based Micro-Simulations},
  booktitle = {Engineering Multi-Agent Systems (EMAS 2019)},
  editor    = {Dennis, Louise and Bordini, Rafael and Lesp{\'e}rance, Yves},
  series    = {Lecture Notes in Computer Science},
  volume    = {12058},
  publisher = {Springer},
  address   = {Cham},
  year      = {2020},
  doi       = {10.1007/978-3-030-51417-4_5}
}

% ---------------------------------------------------------------------------
% BDI and cognitive agents: surveys, transport applications, GAMA
% ---------------------------------------------------------------------------

% [I] Crossref; content read in the KER preview PDF (truncated in Sec. 3.5.3; section numbers only,
%  no page numbers).
@article{adam2016bdi,
  author  = {Adam, Carole and Gaudou, Benoit},
  title   = {{BDI} Agents in Social Simulations: A Survey},
  journal = {The Knowledge Engineering Review},
  volume  = {31},
  number  = {3},
  pages   = {207--238},
  year    = {2016},
  doi     = {10.1017/S0269888916000096}
}

% [P] JASSS page (Section 8 read only in part).
@article{balke2014agents,
  author  = {Balke, Tina and Gilbert, Nigel},
  title   = {How Do Agents Make Decisions? {A} Survey},
  journal = {Journal of Artificial Societies and Social Simulation},
  volume  = {17},
  number  = {4},
  pages   = {13},
  year    = {2014},
  doi     = {10.18564/jasss.2687}
}

% [I] DOAJ. Abstract only.
@article{larsen2019beyond,
  author  = {Larsen, John Bruntse},
  title   = {Going Beyond {BDI} for Agent-Based Simulation},
  journal = {Journal of Information and Telecommunication},
  volume  = {3},
  number  = {4},
  pages   = {446--464},
  year    = {2019},
  doi     = {10.1080/24751839.2019.1620024}
}

% [P] Springer chapter page.
@incollection{taillandier2017bdi,
  author    = {Taillandier, Patrick and Bourgais, Mathieu and Caillou, Philippe and Adam, Carole and Gaudou, Benoit},
  title     = {A {BDI} Agent Architecture for the {GAMA} Modeling and Simulation Platform},
  booktitle = {Multi-Agent Based Simulation XVII (MABS 2016)},
  editor    = {Nardin, Luis Gustavo and Antunes, Luis},
  series    = {Lecture Notes in Computer Science},
  volume    = {10399},
  pages     = {3--23},
  publisher = {Springer},
  address   = {Cham},
  year      = {2017},
  doi       = {10.1007/978-3-319-67477-3_1}
}

% [P] JASSS page.
@article{bourgais2020ben,
  author  = {Bourgais, Mathieu and Taillandier, Patrick and Vercouter, Laurent},
  title   = {{BEN}: An Architecture for the Behavior of Social Agents},
  journal = {Journal of Artificial Societies and Social Simulation},
  volume  = {23},
  number  = {4},
  pages   = {12},
  year    = {2020},
  doi     = {10.18564/jasss.4437}
}

% [R] UT Capitole repository record. DOI not shown, omitted.
@article{adam2017bdifsm,
  author  = {Adam, Carole and Taillandier, Patrick and Dugdale, Julie and Gaudou, Benoit},
  title   = {{BDI} Versus {FSM} Agents in Social Simulations for Raising Awareness in Disasters: A Case Study in {Melbourne} Bushfires},
  journal = {International Journal of Information Systems for Crisis Response and Management},
  volume  = {9},
  number  = {1},
  pages   = {27--44},
  year    = {2017}
}

% [I] OpenAlex only. Paper not read; its characterisation as BDI rests on Bazzan and Klugl (2014).
@article{rossetti2002bdi,
  author  = {Rossetti, Rosaldo J. F. and Bordini, Rafael H. and Bazzan, Ana L. C. and Bampi, S{\'e}rgio and Liu, Ronghui and Van Vliet, Dirck},
  title   = {Using {BDI} Agents to Improve Driver Modelling in a Commuter Scenario},
  journal = {Transportation Research Part C: Emerging Technologies},
  volume  = {10},
  number  = {5--6},
  pages   = {373--398},
  year    = {2002},
  doi     = {10.1016/S0968-090X(02)00027-X}
}

% [I] OpenAlex only. Paper not read; its characterisation as BDI rests on Bazzan and Klugl (2014).
@article{dia2002agent,
  author  = {Dia, Hussein},
  title   = {An Agent-Based Approach to Modelling Driver Route Choice Behaviour Under the Influence of Real-Time Information},
  journal = {Transportation Research Part C: Emerging Technologies},
  volume  = {10},
  number  = {5--6},
  pages   = {331--349},
  year    = {2002},
  doi     = {10.1016/S0968-090X(02)00025-6}
}

% [R] White Rose record, which spells the second author "R. Lui"; "Liu" assumed from the 2002
%  co-authorship. Confirm on the publisher page.
@article{rossetti2005pretrip,
  author  = {Rossetti, R. and Liu, R.},
  title   = {An Agent-Based Approach to Assess Drivers' Interaction with Pre-Trip Information Systems},
  journal = {Journal of Intelligent Transportation Systems},
  volume  = {9},
  number  = {1},
  pages   = {1--10},
  year    = {2005},
  doi     = {10.1080/15472450590912529}
}

% [P] SciTePress paper page. Proceedings volume number not confirmed.
@inproceedings{noroozian2014heterogeneous,
  author    = {Noroozian, Arman and Hindriks, Koen V. and Jonker, Catholijn M.},
  title     = {Towards Simulating Heterogeneous Drivers with Cognitive Agents},
  booktitle = {Proceedings of the 6th International Conference on Agents and Artificial Intelligence (ICAART 2014)},
  pages     = {147--155},
  publisher = {SciTePress},
  year      = {2014},
  isbn      = {978-989-758-016-1},
  doi       = {10.5220/0004815601470155}
}

% [R] Authors' institutional publication page. No DOI found; proceedings PDF not opened.
@inproceedings{lutzenberger2011bdi,
  author    = {L{\"u}tzenberger, Marco and Masuch, Nils and Hirsch, Benjamin and Ahrndt, Sebastian and He{\ss}ler, Axel and Albayrak, Sahin},
  title     = {The {BDI} Driver in a Service City (Extended Abstract)},
  booktitle = {Proceedings of the 10th International Conference on Autonomous Agents and Multiagent Systems (AAMAS 2011)},
  pages     = {1257--1258},
  address   = {Taipei, Taiwan},
  year      = {2011}
}

% [I] DBLP only (venue "SpringSim", pp. 63--70, no DOI). Full proceedings title not verified; paper
%  not read (known through Adam and Gaudou).
@inproceedings{wolfe2008bdi,
  author    = {Wolfe, Shawn R. and Sierhuis, Maarten and Jarvis, Peter A.},
  title     = {To {BDI}, or Not to {BDI}: Design Choices in an Agent-Based Traffic Flow Management Simulation},
  booktitle = {SpringSim},
  pages     = {63--70},
  year      = {2008}
}

% [P] Springer chapter page.
@incollection{sadeghigarjan2023agamas,
  author    = {Sadeghi Garjan, Mahyar and Chaanine, Tommy and Pasquale, Cecilia and Pastore, Vito Paolo and Ferrando, Angelo},
  title     = {{AGAMAS}: A New Agent-Oriented Traffic Simulation Framework for {SUMO}},
  booktitle = {Multi-Agent Systems (EUMAS 2023)},
  editor    = {Malvone, Vadim and Murano, Aniello},
  series    = {Lecture Notes in Computer Science},
  volume    = {14282},
  pages     = {396--405},
  publisher = {Springer},
  address   = {Cham},
  year      = {2023},
  doi       = {10.1007/978-3-031-43264-4_25}
}

% [P] Author-hosted PDF. Workshop paper; no DOI printed.
@inproceedings{lira2025busai,
  author    = {Lira, Lucas and Serafim, Andrei and Lazarin, Nilson and Freitas, Bruno and Pantoja, Carlos},
  title     = {{BusAI}: An {BDI}-Agent-Based Urban Transport Information System},
  booktitle = {19th Workshop-School on Agents, Environments, and Applications (WESAAC 2025)},
  pages     = {137--144},
  year      = {2025}
}

% ---------------------------------------------------------------------------
% Granularity: microscopic, mesoscopic, macroscopic
% ---------------------------------------------------------------------------

% [P] Thesis PDF read; record from the VTI library.
@phdthesis{burghout2004hybrid,
  author  = {Burghout, Wilco},
  title   = {Hybrid microscopic-mesoscopic traffic simulation},
  school  = {Royal Institute of Technology (KTH)},
  address = {Stockholm, Sweden},
  year    = {2004},
  number  = {TRITA-INFRA 04-035},
  isbn    = {91-7323-099-5},
  url     = {https://kth.se/polopoly_fs/1.742065.1600688570!/hybrid%20mesoscopic.pdf}
}

% [I] Crossref. Body not read.
@article{burghout2005hybrid,
  author  = {Burghout, Wilco and Koutsopoulos, Haris N. and Andr{\'e}asson, Ingmar},
  title   = {Hybrid Mesoscopic--Microscopic Traffic Simulation},
  journal = {Transportation Research Record: Journal of the Transportation Research Board},
  volume  = {1934},
  number  = {1},
  pages   = {218--225},
  year    = {2005},
  doi     = {10.1177/0361198105193400123}
}

% [P] SAGE record (citation and abstract). Body not read.
@article{hoogendoorn2001state,
  author  = {Hoogendoorn, S. P. and Bovy, P. H. L.},
  title   = {State-of-the-art of vehicular traffic flow modelling},
  journal = {Proceedings of the Institution of Mechanical Engineers, Part I: Journal of Systems and Control Engineering},
  volume  = {215},
  number  = {4},
  pages   = {283--303},
  year    = {2001},
  doi     = {10.1177/095965180121500402}
}

% [I] RePEc record (citation and abstract). Body not read.
@incollection{barcelo2010models,
  author    = {Barcel{\'o}, Jaume},
  title     = {Models, Traffic Models, Simulation, and Traffic Simulation},
  booktitle = {Fundamentals of Traffic Simulation},
  editor    = {Barcel{\'o}, Jaume},
  series    = {International Series in Operations Research \& Management Science},
  publisher = {Springer},
  pages     = {1--62},
  year      = {2010},
  doi       = {10.1007/978-1-4419-6142-6_1}
}

% [I] RePEc record (citation and abstract). Body not read.
@incollection{benakiva2010dynamit,
  author    = {Ben-Akiva, Moshe and Koutsopoulos, Haris N. and Antoniou, Constantinos and Balakrishna, Ramachandran},
  title     = {Traffic Simulation with {DynaMIT}},
  booktitle = {Fundamentals of Traffic Simulation},
  editor    = {Barcel{\'o}, Jaume},
  series    = {International Series in Operations Research \& Management Science},
  publisher = {Springer},
  pages     = {363--398},
  year      = {2010},
  doi       = {10.1007/978-1-4419-6142-6_10}
}

% [P] Web page read. Report number, authors and date not shown on the page.
@misc{fhwa_tat_vol1,
  author       = {{Federal Highway Administration}},
  title        = {Traffic Analysis Toolbox Volume {I}: Traffic Analysis Tools Primer, Section 4.0 Categories of Traffic Analysis Tools},
  howpublished = {U.S. Department of Transportation},
  url          = {https://ops.fhwa.dot.gov/trafficanalysistools/tat_vol1/sect4.htm}
}

% [P] Report PDF read (Caltrans-hosted copy).
@techreport{hadi2022mrm,
  author      = {Hadi, Mohammed and Zhou, Xuesong and Hale, David},
  title       = {Multiresolution Modeling for Traffic Analysis: Guidebook},
  institution = {Federal Highway Administration, Turner-Fairbank Highway Research Center},
  number      = {FHWA-HRT-22-055},
  year        = {2022},
  month       = feb
}

% [P] Article PDF read.
@article{jeihani2007review,
  author  = {Jeihani, Mansoureh},
  title   = {A Review of Dynamic Traffic Assignment Computer Packages},
  journal = {Journal of the Transportation Research Forum},
  volume  = {46},
  number  = {2},
  pages   = {35--46},
  year    = {2007}
}

% [P] Paper PDF read.
@inproceedings{cetin2003large,
  author    = {Cetin, Nurhan and Burri, Adrian and Nagel, Kai},
  title     = {A Large-Scale Agent-Based Traffic Microsimulation Based On Queue Model},
  booktitle = {Swiss Transport Research Conference (STRC 03)},
  address   = {Monte Verit{\`a}, Ascona},
  year      = {2003},
  url       = {https://svn.vsp.tu-berlin.de/repos/public-svn/publications/kn-old/strc03-queue/strc03-queue.pdf}
}

% [R] Institutional record (citation and abstract).
@article{fernandez2010modelling,
  author  = {Fern{\'a}ndez, R.},
  title   = {Modelling public transport stops by microscopic simulation},
  journal = {Transportation Research Part C: Emerging Technologies},
  volume  = {18},
  number  = {6},
  pages   = {856--868},
  year    = {2010},
  doi     = {10.1016/j.trc.2010.02.002}
}

% [I] TRID record (citation and abstract).
@inproceedings{adnan2016simmobility,
  author    = {Adnan, Muhammad and Pereira, Francisco C. and Azevedo, Carlos Lima and Basak, Kakali and Lovric, Milan and Raveau, Sebasti{\'a}n and Zhu, Yi and Ferreira, Joseph and Zegras, Christopher and Ben-Akiva, Moshe},
  title     = {{SimMobility}: A Multi-scale Integrated Agent-Based Simulation Platform},
  booktitle = {Transportation Research Board 95th Annual Meeting},
  address   = {Washington, DC},
  year      = {2016},
  note      = {Paper 16-2691}
}

% ---------------------------------------------------------------------------
% Transit operations simulators and multi-agent bus models
% ---------------------------------------------------------------------------

% [I] Crossref and World Transit Research. Body read in the reissue CTS Working Paper 2013:29;
%  section numbers and pagination differ from the journal.
@article{toledo2010mesoscopic,
  author  = {Toledo, Tomer and Cats, Oded and Burghout, Wilco and Koutsopoulos, Haris N.},
  title   = {Mesoscopic simulation for transit operations},
  journal = {Transportation Research Part C: Emerging Technologies},
  volume  = {18},
  number  = {6},
  pages   = {896--908},
  year    = {2010},
  doi     = {10.1016/j.trc.2010.02.008}
}

% [I] Crossref and World Transit Research. Abstract only.
@article{cats2010mesoscopic,
  author  = {Cats, Oded and Burghout, Wilco and Toledo, Tomer and Koutsopoulos, Haris N.},
  title   = {Mesoscopic Modeling of Bus Public Transportation},
  journal = {Transportation Research Record: Journal of the Transportation Research Board},
  volume  = {2188},
  number  = {1},
  pages   = {9--18},
  year    = {2010},
  doi     = {10.3141/2188-02}
}

% [P] Working paper PDF read. Stated there as published in Procedia Computer Science (ABMTRANS);
%  volume and pages not confirmed.
@techreport{cats2013multiagent,
  author      = {Cats, Oded},
  title       = {Multi-Agent Transit Operations and Assignment Model},
  institution = {Centre for Transport Studies, KTH Royal Institute of Technology},
  type        = {CTS Working Paper},
  number      = {2013:24},
  year        = {2013},
  url         = {https://www.transportportal.se/swopec/CTS2013-24.pdf}
}

% [P] Author manuscript read.
@article{cats2016modelling,
  author  = {Cats, Oded and Hartl, M.},
  title   = {Modelling public transport on-board congestion: comparing schedule-based and agent-based assignment approaches and their implications},
  journal = {Journal of Advanced Transportation},
  volume  = {50},
  number  = {6},
  pages   = {1209--1224},
  year    = {2016},
  doi     = {10.1002/atr.1398}
}

% [P] Author manuscript read.
@article{cats2016dynamic,
  author  = {Cats, Oded and West, J. and Eliasson, J.},
  title   = {A dynamic stochastic model for evaluating congestion and crowding effects in transit systems},
  journal = {Transportation Research Part B: Methodological},
  volume  = {89},
  pages   = {43--57},
  year    = {2016},
  doi     = {10.1016/j.trb.2016.04.001}
}

% [R] White Rose record (journal, volume, article number, DOI); given names abbreviated as on the
%  record. Model details read in arXiv:1908.08288. Replaces the duplicate key kieu2019dealing.
@article{kieu2020dealing,
  author  = {Kieu, L.-M. and Malleson, N. and Heppenstall, A.},
  title   = {Dealing with uncertainty in agent-based models for short-term predictions},
  journal = {Royal Society Open Science},
  volume  = {7},
  number  = {1},
  pages   = {191074},
  year    = {2020},
  doi     = {10.1098/rsos.191074}
}

% [I] RePEc; text read in arXiv:2004.13022. RePEc lists a fifth name (Tingqiang Chen), probably the
%  academic editor; check the published PDF.
@article{quek2021analysis,
  author  = {Quek, Wei Liang and Chung, Ning Ning and Saw, Vee-Liem and Chew, Lock Yue},
  title   = {Analysis and Simulation of Intervention Strategies against Bus Bunching by means of an Empirical Agent-Based Model},
  journal = {Complexity},
  volume  = {2021},
  pages   = {2606191},
  note    = {Article ID 2606191},
  year    = {2021},
  doi     = {10.1155/2021/2606191}
}

% [I] OpenAlex. Paper not read; described through Balbo et al. (2024).
@article{zhao2003distributed,
  author  = {Zhao, Jiamin and Bukkapatnam, Satish and Dessouky, Maged M.},
  title   = {Distributed architecture for real-time coordination of bus holding in transit networks},
  journal = {IEEE Transactions on Intelligent Transportation Systems},
  volume  = {4},
  number  = {1},
  pages   = {43--51},
  year    = {2003},
  doi     = {10.1109/TITS.2003.809769}
}

% [I] OpenAlex. Paper not read; described through Balbo et al. (2024).
@article{meignan2007simulation,
  author  = {Meignan, David and Simonin, Olivier and Koukam, Abderrafi{\^a}a},
  title   = {Simulation and evaluation of urban bus-networks using a multiagent approach},
  journal = {Simulation Modelling Practice and Theory},
  volume  = {15},
  number  = {6},
  pages   = {659--671},
  year    = {2007},
  doi     = {10.1016/j.simpat.2007.02.005}
}

% [I] World Transit Research and RePEc. Abstract only; platform and passenger representation
%  unknown.
@article{dimitrov2017modeling,
  author  = {Dimitrov, S. and Ceder, A. and Chowdhury, S. and Monot, M.},
  title   = {Modeling the interaction between buses, passengers and cars on a bus route using a multi-agent system},
  journal = {Transportation Planning and Technology},
  volume  = {40},
  number  = {5},
  pages   = {592--610},
  year    = {2017},
  doi     = {10.1080/03081060.2017.1314504}
}

% [I] World Transit Research. Single source.
@article{tlig2011multiagent,
  author  = {Tlig, M. and Bhouri, N.},
  title   = {A multi-agent system for urban traffic and buses regularity control},
  journal = {Procedia - Social and Behavioral Sciences},
  volume  = {20},
  pages   = {896--905},
  year    = {2011},
  doi     = {10.1016/j.sbspro.2011.08.098}
}

% [P] Springer chapter page.
@inproceedings{cubillos2007performance,
  author    = {Cubillos, C. and Guidi-Polanco, F. and Soto, R.},
  title     = {Performance Analysis of a Multiagent Architecture for Passenger Transportation},
  booktitle = {SOFSEM 2007: Theory and Practice of Computer Science},
  series    = {Lecture Notes in Computer Science},
  volume    = {4362},
  pages     = {591--600},
  publisher = {Springer},
  year      = {2007},
  doi       = {10.1007/978-3-540-69507-3_51}
}

% [P] arXiv abstract only (the notes also list OASIcs ATMOS 2024, not verified).
@misc{patzner2024dynamic,
  author        = {Patzner, Julian and M{\"u}ller-Hannemann, Matthias},
  title         = {Dynamic Traffic Assignment for Public Transport with Vehicle Capacities},
  year          = {2024},
  eprint        = {2408.06308},
  archiveprefix = {arXiv}
}

% [P] arXiv abstract only. Preprint.
@misc{leffler2022adaptive,
  author        = {Leffler, David and Burghout, Wilco and Cats, Oded and Jenelius, Erik},
  title         = {An adaptive route choice model for integrated fixed and flexible transit systems},
  year          = {2022},
  eprint        = {2211.10802},
  archiveprefix = {arXiv}
}

% ---------------------------------------------------------------------------
% OD estimation from boarding and alighting counts
% ---------------------------------------------------------------------------

% [P] TRID record and TRB PDF. No DOI.
@article{benakiva1985alternative,
  author  = {Ben-Akiva, Moshe and Macke, Peter P. and Hsu, Poh Ser},
  title   = {Alternative Methods to Estimate Route-Level Trip Tables and Expand On-Board Surveys},
  journal = {Transportation Research Record},
  number  = {1037},
  pages   = {1--11},
  year    = {1985},
  url     = {http://onlinepubs.trb.org/Onlinepubs/trr/1985/1037/1037-001.pdf}
}

% [I] TRID record. ASCE landing page not fetched.
@article{simon1985generating,
  author  = {Simon, J. and Furth, Peter G.},
  title   = {Generating a Bus Route {O-D} Matrix from On-Off Data},
  journal = {Journal of Transportation Engineering},
  volume  = {111},
  number  = {6},
  pages   = {583--593},
  year    = {1985},
  url     = {https://trid.trb.org/View/271052}
}

% [P] TRID record and full text. No DOI.
@article{furth1992bus,
  author  = {Furth, Peter G. and Navick, David S.},
  title   = {Bus Route {O-D} Matrix Generation: Relationship Between Biproportional and Recursive Methods},
  journal = {Transportation Research Record},
  number  = {1338},
  pages   = {14--21},
  year    = {1992},
  url     = {http://onlinepubs.trb.org/Onlinepubs/trr/1992/1338/1338-002.pdf}
}

% [I] RePEc (abstract). DOI not shown, omitted.
@article{lamond1981bregman,
  author  = {Lamond, B. and Stewart, N. F.},
  title   = {Bregman's balancing method},
  journal = {Transportation Research Part B: Methodological},
  volume  = {15},
  number  = {4},
  pages   = {239--248},
  year    = {1981},
  url     = {https://ideas.repec.org/a/eee/transb/v15y1981i4p239-248.html}
}

% [I] RePEc; text read in the UCTC working-paper version (eScholarship). DOI not shown, omitted.
@article{li2007generalized,
  author  = {Li, Yuwei and Cassidy, Michael J.},
  title   = {A generalized and efficient algorithm for estimating transit route {ODs} from passenger counts},
  journal = {Transportation Research Part B: Methodological},
  volume  = {41},
  number  = {1},
  pages   = {114--125},
  year    = {2007},
  url     = {https://ideas.repec.org/a/eee/transb/v41y2007i1p114-125.html}
}

% [R] Loughborough repository record and World Transit Research (abstract). Full text not read. DOI
%  not shown, omitted.
@article{li2009markov,
  author  = {Li, Baibing},
  title   = {Markov models for {B}ayesian analysis about transit route origin-destination matrices},
  journal = {Transportation Research Part B: Methodological},
  volume  = {43},
  number  = {3},
  pages   = {301--310},
  year    = {2009},
  url     = {https://www.worldtransitresearch.info/research/1862}
}

% [P] Publisher abstract page (title, DOI). Volume and pages seen only in a reference list. Full
%  text not read.
@article{hazelton2010statistical,
  author  = {Hazelton, Martin L.},
  title   = {Statistical Inference for Transit System Origin-Destination Matrices},
  journal = {Technometrics},
  volume  = {52},
  number  = {2},
  pages   = {221--230},
  year    = {2010},
  doi     = {10.1198/TECH.2010.09021}
}

% [P] SAGE page; World Transit Research.
@article{mccord2010iterative,
  author  = {McCord, Mark R. and Mishalani, Rabi G. and Goel, Prem and Strohl, Brandon},
  title   = {Iterative Proportional Fitting Procedure to Determine Bus Route Passenger Origin--Destination Flows},
  journal = {Transportation Research Record},
  volume  = {2145},
  number  = {1},
  pages   = {59--65},
  year    = {2010},
  doi     = {10.3141/2145-07}
}

% [I] TRID record; ASCE page.
@article{ji2014estimating,
  author  = {Ji, Yuxiong and Mishalani, Rabi G. and McCord, Mark R.},
  title   = {Estimating Transit Route {OD} Flow Matrices from {APC} Data on Multiple Bus Trips Using the {IPF} Method with an Iteratively Improved Base: Method and Empirical Evaluation},
  journal = {Journal of Transportation Engineering},
  volume  = {140},
  number  = {5},
  pages   = {04014008},
  year    = {2014},
  doi     = {10.1061/(ASCE)TE.1943-5436.0000647}
}

% [I] World Transit Research.
@article{ji2015transit,
  author  = {Ji, Yuxiong and Mishalani, Rabi G. and McCord, Mark R.},
  title   = {Transit passenger origin--destination flow estimation: Efficiently combining onboard survey and large automatic passenger count datasets},
  journal = {Transportation Research Part C: Emerging Technologies},
  volume  = {58},
  pages   = {178--192},
  year    = {2015},
  doi     = {10.1016/j.trc.2015.04.021}
}

% [I] RePEc for the journal record; text read as arXiv:2403.04742v2. Article number not confirmed.
@article{chen2025bayesian,
  author  = {Chen, Xiaoxu and Cheng, Zhanhong and Sun, Lijun},
  title   = {Bayesian inference of time-varying origin--destination matrices from boarding and alighting counts for transit services},
  journal = {Transportation Research Part B: Methodological},
  volume  = {199},
  year    = {2025},
  doi     = {10.1016/j.trb.2025.103278},
  note    = {Preprint arXiv:2403.04742 (2024). Article number not confirmed}
}

% [R] PolyPublie record only. Abstract not read.
@article{chen2025statistical,
  author  = {Chen, Xiaoxu and Thibault, Marc-Olivier and Tr{\'e}panier, Martin and Sun, Lijun},
  title   = {Statistical inference of boarding and alighting counts in transit systems with incomplete data},
  journal = {Transportation Research Part C: Emerging Technologies},
  volume  = {183},
  pages   = {105484},
  year    = {2025},
  doi     = {10.1016/j.trc.2025.105484}
}

% [I] World Transit Research.
@article{sun2021estimating,
  author  = {Sun, Wenzhe and Schm{\"o}cker, Jan-Dirk and Fukuda, Koji},
  title   = {Estimating the route-level passenger demand profile from bus dwell times},
  journal = {Transportation Research Part C: Emerging Technologies},
  volume  = {130},
  pages   = {103273},
  year    = {2021},
  doi     = {10.1016/j.trc.2021.103273}
}

% [I] World Transit Research. Trip-chaining; a different data regime (card-level).
@article{barry2002origin,
  author  = {Barry, James J. and Newhouser, Robert and Rahbee, Adam and Sayeda, Shermeen},
  title   = {Origin and Destination Estimation in {N}ew {Y}ork {C}ity with Automated Fare System Data},
  journal = {Transportation Research Record},
  volume  = {1817},
  pages   = {183--187},
  year    = {2002},
  doi     = {10.3141/1817-24}
}

% [I] TRID. DOI not shown, omitted.
@article{trepanier2007individual,
  author  = {Tr{\'e}panier, Martin and Tranchant, Nicolas and Chapleau, Robert},
  title   = {Individual Trip Destination Estimation in a Transit Smart Card Automated Fare Collection System},
  journal = {Journal of Intelligent Transportation Systems},
  volume  = {11},
  number  = {1},
  pages   = {1--14},
  year    = {2007},
  url     = {https://trid.trb.org/View/804750}
}

% [I] World Transit Research.
@article{munizaga2012estimation,
  author  = {Munizaga, Marcela A. and Palma, Carolina},
  title   = {Estimation of a disaggregate multimodal public transport Origin--Destination matrix from passive smartcard data from {S}antiago, {C}hile},
  journal = {Transportation Research Part C: Emerging Technologies},
  volume  = {24},
  pages   = {9--18},
  year    = {2012},
  doi     = {10.1016/j.trc.2012.01.007}
}

% [P] arXiv. Publication venue not identified.
@misc{loukas2022categorical,
  author        = {Loukas, Orestis and Chung, Ho Ryun},
  title         = {Categorical Distributions of Maximum Entropy under Marginal Constraints},
  year          = {2022},
  eprint        = {2204.03406},
  archivePrefix = {arXiv},
  note          = {Publication venue not identified}
}

% ---------------------------------------------------------------------------
% OD-free operations models, bunching and holding
% ---------------------------------------------------------------------------

% [P] arXiv text read. DOI as listed on the arXiv record; journal volume and pages not confirmed.
@misc{khan2022modular,
  author        = {Khan, Zaid Saeed and He, Weili and Men{\'e}ndez, M{\'o}nica},
  title         = {Application of Modular Vehicle Technology to Mitigate Bus Bunching},
  year          = {2022},
  eprint        = {2202.06039},
  archivePrefix = {arXiv},
  doi           = {10.1016/j.trc.2022.103953},
  note          = {DOI as listed on the arXiv record; journal volume and pages not confirmed}
}

% [P] Full text (NSF PAR).
@article{petit2018dynamic,
  author  = {Petit, Antoine and Ouyang, Yanfeng and Lei, Chao},
  title   = {Dynamic bus substitution strategy for bunching intervention},
  journal = {Transportation Research Part B: Methodological},
  volume  = {115},
  pages   = {1--16},
  year    = {2018},
  doi     = {10.1016/j.trb.2018.06.001}
}

% [P] Working paper read (eScholarship).
@techreport{daganzo2009reducing,
  author      = {Daganzo, Carlos F. and Pilachowski, Josh},
  title       = {Reducing bunching with bus-to-bus cooperation},
  institution = {University of California, Berkeley},
  type        = {Working Paper},
  number      = {UCB-ITS-VWP-2009-12},
  year        = {2009},
  url         = {https://escholarship.org/content/qt0551g0zw/qt0551g0zw.pdf}
}

% [P] Citation and abstract (ITS Berkeley). Alighting treatment not verified.
@article{daganzo2009headway,
  author  = {Daganzo, Carlos F.},
  title   = {A headway-based approach to eliminate bus bunching: Systematic analysis and comparisons},
  journal = {Transportation Research Part B: Methodological},
  volume  = {43},
  number  = {10},
  pages   = {913--921},
  year    = {2009},
  doi     = {10.1016/j.trb.2009.04.002}
}

% [I] RePEc. Alighting treatment not verified.
@article{xuan2011dynamic,
  author  = {Xuan, Yiguang and Argote, Juan and Daganzo, Carlos F.},
  title   = {Dynamic bus holding strategies for schedule reliability: Optimal linear control and performance analysis},
  journal = {Transportation Research Part B: Methodological},
  volume  = {45},
  number  = {10},
  pages   = {1831--1845},
  year    = {2011},
  doi     = {10.1016/j.trb.2011.07.009}
}

% [P] Full-text copy read; pages from RePEc.
@article{bartholdi2012self,
  author  = {Bartholdi, John J. and Eisenstein, Donald D.},
  title   = {A self-co{\"o}rdinating bus route to resist bus bunching},
  journal = {Transportation Research Part B: Methodological},
  volume  = {46},
  number  = {4},
  pages   = {481--491},
  year    = {2012},
  doi     = {10.1016/j.trb.2011.11.001}
}

% [P] Citation and abstract (INFORMS, RePEc). Alighting distribution NOT verified; do not state it
%  without the PDF.
@article{hickman2001analytic,
  author  = {Hickman, Mark D.},
  title   = {An Analytic Stochastic Model for the Transit Vehicle Holding Problem},
  journal = {Transportation Science},
  volume  = {35},
  number  = {3},
  pages   = {215--237},
  year    = {2001},
  doi     = {10.1287/trsc.35.3.215.10150}
}

% [I] RePEc. DOI not shown, omitted.
@article{andersson1981mathematical,
  author  = {Andersson, Per-{\AA}ke and Scalia-Tomba, Gian-Paolo},
  title   = {A mathematical model of an urban bus route},
  journal = {Transportation Research Part B: Methodological},
  volume  = {15},
  number  = {4},
  pages   = {249--266},
  year    = {1981},
  url     = {https://ideas.repec.org/a/eee/transb/v15y1981i4p249-266.html}
}

% [I] RePEc. Alighting treatment not verified.
@article{delgado2012how,
  author  = {Delgado, Felipe and Mu{\~n}oz, Juan Carlos and Giesen, Ricardo},
  title   = {How much can holding and/or limiting boarding improve transit performance?},
  journal = {Transportation Research Part B: Methodological},
  volume  = {46},
  number  = {9},
  pages   = {1202--1217},
  year    = {2012},
  doi     = {10.1016/j.trb.2012.04.005}
}

% [I] World Transit Research. Demand representation not verified.
@article{sanchezmartinez2016realtime,
  author  = {S{\'a}nchez-Mart{\'i}nez, Gabriel E. and Koutsopoulos, Haris N. and Wilson, Nigel H. M.},
  title   = {Real-time holding control for high-frequency transit with dynamics},
  journal = {Transportation Research Part B: Methodological},
  volume  = {83},
  pages   = {1--19},
  year    = {2016},
  doi     = {10.1016/j.trb.2015.11.013}
}

% [I] World Transit Research. Alighting treatment not verified.
@article{wang2020dynamic,
  author  = {Wang, Jiawei and Sun, Lijun},
  title   = {Dynamic holding control to avoid bus bunching: A multi-agent deep reinforcement learning framework},
  journal = {Transportation Research Part C: Emerging Technologies},
  volume  = {116},
  pages   = {102661},
  year    = {2020},
  doi     = {10.1016/j.trc.2020.102661}
}

% [P] IJCAI proceedings PDF.
@inproceedings{wang2021reducing,
  author    = {Wang, Jiawei and Sun, Lijun},
  title     = {Reducing Bus Bunching with Asynchronous Multi-Agent Reinforcement Learning},
  booktitle = {Proceedings of the Thirtieth International Joint Conference on Artificial Intelligence (IJCAI-21)},
  pages     = {426--433},
  year      = {2021},
  url       = {https://www.ijcai.org/proceedings/2021/0060.pdf}
}

% [I] TRID.
@article{ceder1984bus,
  author  = {Ceder, Avi},
  title   = {Bus frequency determination using passenger count data},
  journal = {Transportation Research Part A},
  volume  = {18},
  number  = {5--6},
  pages   = {439--453},
  year    = {1984},
  url     = {https://trid.trb.org/View/269513}
}

% ---------------------------------------------------------------------------
% Count data, dwell time, arrival process, queue discipline
% ---------------------------------------------------------------------------

% [P] Author copy read.
@article{sun2014models,
  author  = {Sun, Lijun and Tirachini, Alejandro and Axhausen, Kay W. and Erath, Alexander and Lee, Der-Horng},
  title   = {Models of bus boarding and alighting dynamics},
  journal = {Transportation Research Part A: Policy and Practice},
  volume  = {69},
  pages   = {447--460},
  year    = {2014},
  doi     = {10.1016/j.tra.2014.09.007}
}

% [P] Author-hosted copy. Used in the notes only as the secondary source for the TCQSM dwell-time
%  variables.
@article{fletcher2013effects,
  author  = {Fletcher, Grant and El-Geneidy, Ahmed},
  title   = {Effects of Fare Payment Types and Crowding on Dwell Time: Fine-Grained Analysis},
  journal = {Transportation Research Record},
  number  = {2351},
  pages   = {124--132},
  year    = {2013},
  doi     = {10.3141/2351-14}
}

% [P] USF Digital Commons. Cross-sectional (between stops), not within stop and time slot.
@article{pulugurtha2012assessment,
  author  = {Pulugurtha, Srinivas S. and Agurla, Mahesh},
  title   = {Assessment of Models to Estimate Bus-Stop Level Transit Ridership using Spatial Modeling Methods},
  journal = {Journal of Public Transportation},
  volume  = {15},
  number  = {1},
  pages   = {33--52},
  year    = {2012},
  doi     = {10.5038/2375-0901.15.1.3}
}

% [P] Springer page.
@article{marques2023transit,
  author  = {Marques, Samuel de Fran{\c{c}}a and Pitombo, Cira Souza},
  title   = {Transit Ridership Modeling at the Bus Stop Level: Comparison of Approaches Focusing on Count and Spatially Dependent Data},
  journal = {Applied Spatial Analysis and Policy},
  volume  = {16},
  number  = {1},
  pages   = {277--313},
  year    = {2023},
  doi     = {10.1007/s12061-022-09482-y}
}

% [I] TRID.
@article{bowman1981service,
  author  = {Bowman, L. A. and Turnquist, M. A.},
  title   = {Service frequency, schedule reliability and passenger wait times at transit stops},
  journal = {Transportation Research Part A},
  volume  = {15},
  number  = {6},
  pages   = {465--471},
  year    = {1981},
  url     = {https://trid.trb.org/View/180496}
}

% [I] World Transit Research.
@article{ingvardson2018passenger,
  author  = {Ingvardson, Jesper Bl{\'a}foss and Nielsen, Otto Anker and Raveau, Sebasti{\'a}n and Nielsen, Bo Friis},
  title   = {Passenger arrival and waiting time distributions dependent on train service frequency and station characteristics: A smart card data analysis},
  journal = {Transportation Research Part C: Emerging Technologies},
  volume  = {90},
  pages   = {292--306},
  year    = {2018},
  doi     = {10.1016/j.trc.2018.03.006}
}

% [P] City Research Online full text.
@inproceedings{kaparias2015analysing,
  author    = {Kaparias, Ioannis and Rossetti, C. and Trozzi, Valentina},
  title     = {Analysing passenger arrivals rates and waiting times at bus stops},
  booktitle = {94th Annual Meeting of the Transportation Research Board},
  address   = {Washington, DC},
  year      = {2015},
  url       = {https://openaccess.city.ac.uk/id/eprint/6257/}
}

% [I] RePEc (abstract). DOI not shown, omitted.
@article{schmocker2008quasi,
  author  = {Schm{\"o}cker, Jan-Dirk and Bell, Michael G. H. and Kurauchi, Fumitaka},
  title   = {A quasi-dynamic capacity constrained frequency-based transit assignment model},
  journal = {Transportation Research Part B: Methodological},
  volume  = {42},
  number  = {10},
  pages   = {925--945},
  year    = {2008},
  url     = {https://ideas.repec.org/a/eee/transb/v42y2008i10p925-945.html}
}

% [I] RePEc (abstract).
@article{trozzi2013dynamic,
  author  = {Trozzi, Valentina and Gentile, Guido and Bell, Michael G. H. and Kaparias, Ioannis},
  title   = {Dynamic user equilibrium in public transport networks with passenger congestion and hyperpaths},
  journal = {Transportation Research Part B: Methodological},
  volume  = {57},
  pages   = {266--285},
  year    = {2013},
  doi     = {10.1016/j.trb.2013.06.011}
}

% [P] Cambridge Core abstract page. Exact class of disciplines covered by the theorem not confirmed.
@article{kingman1962effect,
  author  = {Kingman, J. F. C.},
  title   = {The effect of queue discipline on waiting time variance},
  journal = {Mathematical Proceedings of the Cambridge Philosophical Society},
  volume  = {58},
  number  = {1},
  pages   = {163--164},
  year    = {1962},
  doi     = {10.1017/S0305004100036331}
}

% [P] arXiv.
@misc{eschenfeldt2011bound,
  author        = {Eschenfeldt, Patrick and Gross, Ben and Pippenger, Nicholas},
  title         = {A Bound on the Variance of the Waiting Time in a Queueing System},
  year          = {2011},
  eprint        = {1106.0074},
  archivePrefix = {arXiv}
}

% ---------------------------------------------------------------------------
% Agent theory, interaction protocols, FIPA
% ---------------------------------------------------------------------------

% [I] Crossref; paper read (KER preview PDF and the author's HTML version).
@article{wooldridge1995intelligent,
  author  = {Wooldridge, Michael and Jennings, Nicholas R.},
  title   = {Intelligent agents: theory and practice},
  journal = {The Knowledge Engineering Review},
  volume  = {10},
  number  = {2},
  pages   = {115--152},
  year    = {1995},
  doi     = {10.1017/S0269888900008122}
}

% [P] Chapter text read in an author-hosted copy; book record confirmed. Page range in the printed
%  volume not confirmed, omitted.
@incollection{wooldridge1999intelligent,
  author    = {Wooldridge, Michael},
  title     = {Intelligent Agents},
  booktitle = {Multiagent Systems: A Modern Approach to Distributed Artificial Intelligence},
  editor    = {Weiss, Gerhard},
  publisher = {MIT Press},
  year      = {1999},
  isbn      = {0262232030}
}

% [P] Authors' site (bibliographic). Chapter 2 content seen only through course slides; quote the
%  book directly.
@book{russell2020artificial,
  author    = {Russell, Stuart and Norvig, Peter},
  title     = {Artificial Intelligence: A Modern Approach},
  edition   = {4},
  publisher = {Pearson},
  year      = {2020},
  isbn      = {978-0134610993}
}

% [P] Author-hosted full text read; volume, pages and DOI from index records (LNCS 1193 is indexed
%  under 1997; the author's page gives 1996). Volume editors not confirmed.
@incollection{franklin1997agent,
  author    = {Franklin, Stan and Graesser, Art},
  title     = {Is it an Agent, or just a Program?: A Taxonomy for Autonomous Agents},
  booktitle = {Proceedings of the Third International Workshop on Agent Theories, Architectures, and Languages (ATAL-96)},
  series    = {Lecture Notes in Computer Science},
  volume    = {1193},
  publisher = {Springer},
  pages     = {21--35},
  year      = {1997},
  doi       = {10.1007/BFb0013570}
}

% [I] DBLP. Body not read; DOI not verified, omitted.
@article{maes1990situated,
  author  = {Maes, Pattie},
  title   = {Situated agents can have goals},
  journal = {Robotics and Autonomous Systems},
  volume  = {6},
  number  = {1--2},
  pages   = {49--70},
  year    = {1990}
}

% [I] Crossref. Body not read.
@article{brooks1986robust,
  author  = {Brooks, Rodney A.},
  title   = {A robust layered control system for a mobile robot},
  journal = {IEEE Journal on Robotics and Automation},
  volume  = {2},
  number  = {1},
  pages   = {14--23},
  year    = {1986},
  doi     = {10.1109/JRA.1986.1087032}
}

% [P] Read as MIT AI Memo 1293; proceedings pages from the IJCAI anthology record.
@inproceedings{brooks1991reason,
  author    = {Brooks, Rodney A.},
  title     = {Intelligence Without Reason},
  booktitle = {Proceedings of the International Joint Conference on Artificial Intelligence (IJCAI-91)},
  pages     = {569--595},
  year      = {1991}
}

% [P] Springer chapter page (citation and abstract).
@incollection{drogoul2003multi,
  author    = {Drogoul, Alexis and Vanbergue, Diane and Meurisse, Thomas},
  title     = {Multi-agent Based Simulation: Where Are the Agents?},
  booktitle = {Multi-Agent-Based Simulation II (MABS 2002)},
  editor    = {Sichman, Jaime Sim{\~a}o and Bousquet, Fran{\c{c}}ois and Davidsson, Paul},
  series    = {Lecture Notes in Computer Science},
  volume    = {2581},
  publisher = {Springer},
  pages     = {1--15},
  year      = {2003},
  doi       = {10.1007/3-540-36483-8_1}
}

% [P] Extended abstract PDF read.
@inproceedings{kubera2010everything,
  author    = {Kubera, Yoann and Mathieu, Philippe and Picault, S{\'e}bastien},
  title     = {Everything can be Agent!},
  booktitle = {Proceedings of the 9th International Conference on Autonomous Agents and Multiagent Systems (AAMAS 2010)},
  address   = {Toronto, Canada},
  pages     = {1547--1548},
  year      = {2010}
}

% [I] Authors' BibTeX file. Body not read.
@article{kubera2011ioda,
  author  = {Kubera, Yoann and Mathieu, Philippe and Picault, S{\'e}bastien},
  title   = {{IODA}: an interaction-oriented approach for multi-agent based simulations},
  journal = {Autonomous Agents and Multi-Agent Systems},
  volume  = {23},
  number  = {3},
  pages   = {303--343},
  year    = {2011},
  doi     = {10.1007/s10458-010-9164-z}
}

% [P] Paper PDF read. Issue number and DOI not seen, omitted.
@article{jennings2000agent,
  author  = {Jennings, Nicholas R.},
  title   = {On agent-based software engineering},
  journal = {Artificial Intelligence},
  volume  = {117},
  pages   = {277--296},
  year    = {2000}
}

% [P] Author-hosted PDF read (Computer, December 1998, pp. 40--47). Volume and issue as given in the
%  research brief; DOI omitted.
@article{singh1998agent,
  author  = {Singh, Munindar P.},
  title   = {Agent Communication Languages: Rethinking the Principles},
  journal = {Computer},
  volume  = {31},
  number  = {12},
  pages   = {40--47},
  year    = {1998}
}

% [I] DBLP. Body not read.
@article{smith1980contract,
  author  = {Smith, Reid G.},
  title   = {The Contract Net Protocol: High-Level Communication and Control in a Distributed Problem Solver},
  journal = {IEEE Transactions on Computers},
  volume  = {C-29},
  number  = {12},
  pages   = {1104--1113},
  year    = {1980},
  doi     = {10.1109/TC.1980.1675516}
}

% [R] University of Augsburg record and a library entry. Body not read.
@incollection{odell2001representing,
  author    = {Odell, James J. and Parunak, H. Van Dyke and Bauer, Bernhard},
  title     = {Representing Agent Interaction Protocols in {UML}},
  booktitle = {Agent-Oriented Software Engineering},
  editor    = {Ciancarini, Paolo and Wooldridge, Michael},
  series    = {Lecture Notes in Computer Science},
  volume    = {1957},
  publisher = {Springer},
  pages     = {121--140},
  year      = {2001},
  doi       = {10.1007/3-540-44564-1_8}
}

% [I] Catalogue record only.
@book{bellifemine2007developing,
  author    = {Bellifemine, Fabio Luigi and Caire, Giovanni and Greenwood, Dominic},
  title     = {Developing Multi-Agent Systems with {JADE}},
  publisher = {Wiley},
  year      = {2007},
  isbn      = {978-0-470-05747-6}
}

% [P] Specification page read.
@misc{fipa00026,
  author       = {{Foundation for Intelligent Physical Agents}},
  title        = {{FIPA} Request Interaction Protocol Specification},
  howpublished = {Document SC00026H, Standard},
  year         = {2002},
  url          = {http://www.fipa.org/specs/fipa00026/SC00026H.html}
}

% [P] Documentation page read. It does not state conformance to the FIPA specifications and does not
%  name JADE.
@misc{gama_fipa,
  author       = {{GAMA Platform}},
  title        = {Using {FIPA} {ACL}},
  howpublished = {GAMA platform documentation},
  url          = {https://gama-platform.org/wiki/UsingFIPAACL},
  note         = {Accessed 9 October 2026}
}

% [P] Paper PDF read; header reads "S. Brueckner et al. (Eds.): ESOA 2004, LNCS 3464". Full volume
%  title, editor list and DOI not confirmed.
@incollection{dewolf2005emergence,
  author    = {De Wolf, Tom and Holvoet, Tom},
  title     = {Emergence Versus Self-Organisation: Different Concepts but Promising When Combined},
  booktitle = {ESOA 2004},
  editor    = {Brueckner, S. and others},
  series    = {Lecture Notes in Computer Science},
  volume    = {3464},
  publisher = {Springer},
  pages     = {1--15},
  year      = {2005}
}

% [P] Paper PDF read.
@article{bonabeau2002agent,
  author  = {Bonabeau, Eric},
  title   = {Agent-based modeling: methods and techniques for simulating human systems},
  journal = {Proceedings of the National Academy of Sciences},
  volume  = {99},
  number  = {suppl. 3},
  pages   = {7280--7287},
  year    = {2002},
  doi     = {10.1073/pnas.082080899}
}

% ---------------------------------------------------------------------------
% ABM methodology: level of detail, purpose, data
% ---------------------------------------------------------------------------

% [P] Springer chapter page; pages from the LNCS index; body read in a course-hosted copy (section
%  numbers are those of that copy).
@incollection{parunak1998agent,
  author    = {Parunak, H. Van Dyke and Savit, Robert and Riolo, Rick L.},
  title     = {Agent-Based Modeling vs. Equation-Based Modeling: A Case Study and Users' Guide},
  booktitle = {Multi-Agent Systems and Agent-Based Simulation (MABS 1998)},
  editor    = {Sichman, Jaime Sim{\~a}o and Conte, Rosaria and Gilbert, Nigel},
  series    = {Lecture Notes in Computer Science},
  volume    = {1534},
  publisher = {Springer},
  address   = {Berlin, Heidelberg},
  pages     = {10--25},
  year      = {1998},
  doi       = {10.1007/10692956_2}
}

% [P] Authors' report page CPM-04-132 (citation and summary). DOI not verified, omitted; editor list
%  incomplete.
@incollection{edmonds2005kiss,
  author    = {Edmonds, Bruce and Moss, Scott},
  title     = {From {KISS} to {KIDS} -- An `Anti-simplistic' Modelling Approach},
  booktitle = {Multi-Agent and Multi-Agent-Based Simulation (MABS 2004)},
  editor    = {Davidsson, Paul and others},
  series    = {Lecture Notes in Artificial Intelligence},
  volume    = {3415},
  publisher = {Springer},
  pages     = {130--144},
  year      = {2005}
}

% [I] USGS record; paper PDF read.
@article{grimm2005pattern,
  author  = {Grimm, Volker and Revilla, Eloy and Berger, Uta and Jeltsch, Florian and Mooij, Wolf M. and Railsback, Steven F. and Thulke, Hans-Hermann and Weiner, Jacob and Wiegand, Thorsten and DeAngelis, Donald L.},
  title   = {Pattern-oriented modeling of agent-based complex systems: lessons from ecology},
  journal = {Science},
  volume  = {310},
  number  = {5750},
  pages   = {987--991},
  year    = {2005},
  doi     = {10.1126/science.1116681}
}

% [R] TUHH record (citation and abstract).
@article{sun2016simple,
  author  = {Sun, Z. and Lorscheid, I. and Millington, J. D. and Lauf, S. and Magliocca, N. R. and Groeneveld, J. and Balbi, S. and Nolzen, H. and M{\"u}ller, B. and Schulze, J. and Buchmann, C. M.},
  title   = {Simple or complicated agent-based models? A complicated issue},
  journal = {Environmental Modelling \& Software},
  volume  = {86},
  pages   = {56--67},
  year    = {2016},
  doi     = {10.1016/j.envsoft.2016.09.006}
}

% [P] Chapter PDF read. Only the first editor was shown.
@incollection{osullivan2012agent,
  author    = {O'Sullivan, David and Millington, James and Perry, George and Wainwright, John},
  title     = {Agent-Based Models -- Because They're Worth It?},
  booktitle = {Agent-Based Models of Geographical Systems},
  editor    = {Heppenstall, A. J. and others},
  publisher = {Springer},
  address   = {Dordrecht},
  pages     = {109--123},
  year      = {2012},
  doi       = {10.1007/978-90-481-8927-4_6}
}

% [R] Penn State record (citation and abstract).
@article{srikrishnan2021small,
  author  = {Srikrishnan, Vivek and Keller, Klaus},
  title   = {Small increases in agent-based model complexity can result in large increases in required calibration data},
  journal = {Environmental Modelling \& Software},
  volume  = {138},
  pages   = {104978},
  year    = {2021},
  doi     = {10.1016/j.envsoft.2021.104978}
}

% [R] University of Birmingham record. Body not read.
@article{saltelli2020five,
  author  = {Saltelli, A. and Bammer, G. and Bruno, I. and Charters, E. and Di Fiore, M. and Didier, E. and Nelson Espeland, W. and Kay, J. and Lo Piano, S. and Mayo, D. and Pielke, R. and Portaluri, T. and Porter, T. M. and Puy, A. and Rafols, I. and Ravetz, J. R. and Reinert, E. and Sarewitz, D. and Stark, P. B. and Stirling, A. and van der Sluijs, J. and Vineis, P.},
  title   = {Five ways to ensure that models serve society: a manifesto},
  journal = {Nature},
  volume  = {582},
  number  = {7813},
  pages   = {482--484},
  year    = {2020},
  doi     = {10.1038/d41586-020-01812-9}
}

% [P] arXiv (v7, 2013). No journal venue found.
@misc{morvan2012multi,
  author        = {Morvan, Gildas},
  title         = {Multi-level agent-based modeling -- A literature survey},
  year          = {2012},
  eprint        = {1205.0561},
  archiveprefix = {arXiv},
  note          = {v7, 2013}
}

% [I] Co-author's publication list. Body not read; DOI not verified, omitted.
@incollection{gilquijano2012biological,
  author    = {Gil-Quijano, Javier and Louail, Thomas and Hutzler, Guillaume},
  title     = {From Biological to Urban Cells: Lessons from Three Multilevel Agent-Based Models},
  booktitle = {Principles and Practice of Multi-Agent Systems (PRIMA 2010)},
  editor    = {Desai, N. and Liu, A. and Winikoff, M.},
  series    = {Lecture Notes in Computer Science},
  volume    = {7057},
  publisher = {Springer},
  address   = {Berlin},
  pages     = {620--635},
  year      = {2012}
}

% [I] DBLP (volume, issue, pages) and CoMSES (DOI). Content read only in the AAMAS 2015 version.
@article{zhang2016data,
  author  = {Zhang, Haifeng and Vorobeychik, Yevgeniy and Letchford, Joshua and Lakkaraju, Kiran},
  title   = {Data-driven agent-based modeling, with application to rooftop solar adoption},
  journal = {Autonomous Agents and Multi-Agent Systems},
  volume  = {30},
  number  = {6},
  pages   = {1023--1049},
  year    = {2016},
  doi     = {10.1007/s10458-016-9326-8}
}

% [P] AAMAS 2015 PDF read; pages from DBLP.
@inproceedings{zhang2015data,
  author    = {Zhang, Haifeng and Vorobeychik, Yevgeniy and Letchford, Joshua and Lakkaraju, Kiran},
  title     = {Data-Driven Agent-Based Modeling, with Application to Rooftop Solar Adoption},
  booktitle = {Proceedings of the 14th International Conference on Autonomous Agents and Multiagent Systems (AAMAS 2015)},
  address   = {Istanbul, Turkey},
  pages     = {513--521},
  year      = {2015}
}

% [I] DBLP. Body not read; no DOI shown.
@inproceedings{kavak2018big,
  author    = {Kavak, Hamdi and Padilla, Jose J. and Lynch, Christopher J. and Diallo, Saikou Y.},
  title     = {Big data, agents, and machine learning: towards a data-driven agent-based modeling approach},
  booktitle = {Proceedings of the Annual Simulation Symposium (ANSS), SpringSim 2018},
  pages     = {12:1--12:12},
  year      = {2018}
}

% [R] ODU Digital Commons (abstract read).
@phdthesis{kavak2019data,
  author = {Kavak, Hamdi},
  title  = {A Data-Driven Approach for Modeling Agents},
  school = {Old Dominion University},
  year   = {2019},
  doi    = {10.25777/6b7c-9a95}
}

% [R] UCM repository record. AUTHOR ORDER as listed there (Gilbert first); the paper is usually
%  cited with Hassan first. Check the first page.
@inproceedings{gilbert2008stepping,
  author    = {Gilbert, Nigel and Hassan, Samer and Antunes, Luis and Pav{\'o}n, Juan},
  title     = {Stepping on earth: A roadmap for data-driven agent-based modelling},
  booktitle = {Proceedings of the European Social Simulation Association Annual Conference},
  address   = {Brescia, Italy},
  year      = {2008},
  url       = {https://hdl.handle.net/20.500.14352/54074}
}

% [I] RePEc (citation and abstract). Definitions not read.
@article{macal2016everything,
  author  = {Macal, C. M.},
  title   = {Everything you need to know about agent-based modelling and simulation},
  journal = {Journal of Simulation},
  volume  = {10},
  number  = {2},
  pages   = {144--156},
  year    = {2016},
  doi     = {10.1057/jos.2016.7}
}

% ---------------------------------------------------------------------------
% Preprints (not peer-reviewed when read on 9 October 2026)
% ---------------------------------------------------------------------------

% [P] arXiv. Preprint, no venue listed.
@misc{vu2025generative,
  author        = {Vu, Trung-Dung and Gaudou, Benoit and Oberoi, Kamaldeep Singh},
  title         = {Modeling Realistic Human Behavior Using Generative Agents in a Multimodal Transport System: Software Architecture and Application to {Toulouse}},
  year          = {2025},
  eprint        = {2510.19497},
  archivePrefix = {arXiv},
  note          = {Preprint}
}

% [P] arXiv. Preprint.
@misc{liu2024llm,
  author        = {Liu, Tianming and Yang, Jirong and Yin, Yafeng},
  title         = {Toward {LLM}-Agent-Based Modeling of Transportation Systems: A Conceptual Framework},
  year          = {2024},
  eprint        = {2412.06681},
  archivePrefix = {arXiv},
  note          = {Preprint}
}

% [P] arXiv abstract. Unreviewed; no ground truth for destinations; card-level data, not an
%  OD-from-counts method. The abstract page was reported as "submitted 23 July 2026" while the
%  identifier prefix suggests August 2026; check the date.
@misc{zhao2026transit,
  author        = {Zhao, Gefei and Ling, Jiahe and Su, Yuelong},
  title         = {Transit Destination Inference from Tap-In-Only Bus Smart-Card Data: A Hierarchical {B}ayesian Approach},
  year          = {2026},
  eprint        = {2608.11223},
  archivePrefix = {arXiv},
  doi           = {10.48550/arXiv.2608.11223},
  note          = {Preprint, not peer reviewed}
}
```

## Appendix B. References to check before submission

**Table B1. Entries in Appendix A with a field or content still to confirm**

| What to confirm | Keys |
|---|---|
| Index-only verification, paper not read | `rossetti2002bdi`, `dia2002agent` (BDI characterisation rests on Bazzan & Klügl), `kagho2020agent` (DBLP did not confirm the Procedia volume), `larsen2019beyond`, `wolfe2008bdi` (full proceedings title missing), `zhao2003distributed`, `meignan2007simulation` (content known only through Balbo et al.), `smith1980contract`, `maes1990situated`, `kavak2018big`, `brooks1986robust`, `burghout2005hybrid` |
| DOI or page range from a single institutional or index record | `sun2021transitgym`, `talusan2025dispatch` (confirm on the ACM Digital Library), `talusan2024online`, `dimitrov2017modeling`, `tlig2011multiagent`, `cats2011impacts`, `kieu2020dealing` |
| Page range missing | `horni2016introducing` (starts p. 3), `dobler2016withinday` (starts p. 187), `padgham2016bdi` (starts p. 201; 201-210 inferred from the table of contents), `singh2020matsim`, `wooldridge1999intelligent` |
| DOI omitted because not seen on a fetched page | `brooks1991representation`, `jennings2000agent`, `singh1998agent`, `maes1990situated`, `edmonds2005kiss`, `dewolf2005emergence`, `gilquijano2012biological`, `nguyen2021overview`, `chen2014adding`, `lutzenberger2011bdi`, `adam2017bdifsm`, `lira2025busai`, `kavak2018big`, `wolfe2008bdi`, `taylor2009nature`, `li2007generalized`, `li2009markov`, `lamond1981bregman`, `trepanier2007individual`, `simon1985generating`, `schmocker2008quasi`, `andersson1981mathematical`, `ceder1984bus`, `bowman1981service` |
| Author names | `rossetti2005pretrip` (repository spells the second author "Lui"), `bastarianto2023agent` (initials only; one reader saw three authors plus "et al."), `gilbert2008stepping` (author order: repository lists Gilbert first, the paper is usually cited with Hassan first), `quek2021analysis` (RePEc lists a fifth name, probably the editor), `saval2023gama` ("Minh, Duc Pham" as printed versus "Pham Minh, Duc"), `kieu2020dealing`, `dimitrov2017modeling`, `tlig2011multiagent`, `cubillos2007performance` (initials only) |
| Year, volume, venue or editors | `bazzan2014review` (Crossref gives online date 3 May 2013; 2014 is the conventional issue year), `padgham2014integrating` (FAIA volume 263 taken from a file name), `franklin1997agent` (1996 on the author's page, 1997 in the index; volume editors), `noroozian2014heterogeneous` (proceedings volume number), `chen2025bayesian` (article number), `hazelton2010statistical` (volume and pages seen only in a reference list), `khan2022modular` (journal volume and pages), `fhwa_tat_vol1` (report number, authors, date), `cats2013multiagent` (stated as published in Procedia Computer Science; volume and pages not confirmed), `zhao2026transit` (submission date inconsistent with the identifier), `singh1998agent` (volume and issue as given in the brief), `brooks1991reason` (pages from the anthology record), `osullivan2012agent`, `edmonds2005kiss`, `dewolf2005emergence`, `morri2021approach` (editor lists incomplete), `loukas2022categorical`, `morvan2012multi` (no venue identified) |
| Content read in another version than the one cited | `toledo2010mesoscopic` (CTS Working Paper 2013:29), `zhang2016data` (AAMAS 2015 version), `kieu2020dealing`, `khan2022modular`, `nguyen2021overview`, `chen2025bayesian`, `sun2021transitgym` (arXiv), `talusan2025dispatch` (ICCPS 2024 text), `li2007generalized` (UCTC working paper), `parunak1998agent` (course-hosted copy), `brooks1991reason` (AI Memo 1293), `cats2016modelling`, `cats2016dynamic` (author manuscripts), `cats2011impacts` (working-paper record) |
| Abstract or record only; attribute no specific claim without reading | `cats2010mesoscopic`, `hoogendoorn2001state`, `barcelo2010models`, `benakiva2010dynamit`, `fernandez2010modelling`, `adnan2016simmobility`, `drogoul2003multi`, `kubera2011ioda`, `odell2001representing`, `bellifemine2007developing`, `sun2016simple`, `srikrishnan2021small`, `saltelli2020five`, `gilquijano2012biological`, `macal2016everything`, `kavak2019data`, `taillandier2019gama`, `manser2020designing`, `chen2025statistical`, `hazelton2010statistical`, `li2009markov`, `ji2015transit`, `sun2021estimating`, `trozzi2013dynamic`, `schmocker2008quasi`, `padgham2016bdi`, `dobler2016withinday`, `patzner2024dynamic`, `leffler2022adaptive`, `dimitrov2017modeling`, `tlig2011multiagent` |
| Alighting or demand treatment not verified at full text | `hickman2001analytic`, `daganzo2009headway`, `xuan2011dynamic`, `delgado2012how`, `sanchezmartinez2016realtime`, `wang2020dynamic` |
| Content known through a secondary source | `russell2020artificial` (chapter 2 taxonomy taken from course slides) |
| Preprints, not peer-reviewed when read | `vu2025generative`, `liu2024llm`, `zhao2026transit`, `berrebi2020ridership`, `patzner2024dynamic`, `leffler2022adaptive`, `morvan2012multi`, `eschenfeldt2011bound`, `loukas2022categorical` |
| Class of disciplines in the theorem not confirmed | `kingman1962effect` (verify against the two-page note before using "non-anticipating, service-time-independent") |

**Table B2. References excluded from Appendix A (secondary-only, discrepant or unconfirmed)**

| Reference | What the notes have | Why it is excluded |
|---|---|---|
| Tsygalnitsky (1977), M.S. thesis, MIT | Cited in the transit literature as S. Tsygalnitsky, "Simplified Methods for Transportation Planning"; MIT DSpace (hdl 1721.1/16282) lists "Tsygalnitzky, Serge Michel", "Simplified methods in transportation analysis" | Title and spelling discrepancy; thesis text not opened to confirm it contains the recursive method |
| Deming & Stephan (1940), Annals of Mathematical Statistics 11(4), 427-444 | Seen in a Wikipedia reference list | Secondary only; DOI not confirmed |
| Milkovits (2008), Transportation Research Record 2072, 125-130 | Consistent in two reference lists | Secondary only |
| Blume, Corman & Sansavini (2022), Transportation Research Part B 161, 60-94 | Text read as arXiv:2105.12798 | Journal details from a reference list only; network-level, not single-route |
| Saeidi, Abolfazli & Mehran, Canadian Journal of Civil Engineering, DOI 10.1139/cjce-2024-0276 | Title, authors and DOI from a publication list and a search result | Year, volume, issue and pages unconfirmed; abstract not read; the description "Regina, gravity model, cluster symmetry" is unverified |
| Berrebi, Hans, Chiabaut, Laval, Leclercq & Watkins, "Comparing bus holding methods with and without real-time predictions", Transportation Research Part C, DOI 10.1016/j.trc.2017.07.012 | Index record lists it as in press (online 24 August 2017) | Year of issue, volume and pages unconfirmed; alighting treatment not verified |
| Ferber (1999), Multi-Agent Systems, Addison Wesley Longman, ISBN 0-201-36048-9 | Known through a JASSS book review | Secondary only; the book was not opened |
| van Wageningen-Kessels, Hoogendoorn, Vuik & van Lint, "Traffic Flow Modeling: a Genealogy" | Repository PDF read | Venue and year not stated in the file; the journal version (EURO Journal on Transportation and Logistics, 2015) was not confirmed |
| Furness (1965), "Time function iteration", Traffic Engineering and Control | Method attribution confirmed in the Lamond & Stewart abstract | Volume and pages unconfirmed |
| Luethi, Weidmann & Nash, "Passenger arrival rates at public transport stations" | Printed as an ETH Zurich report, 2006, in another paper's reference list | Year and venue unresolved (ETH report 2006 versus TRB 2007) |
| Jolliffe & Hutchinson, Transportation Science 9, 248-282 | Printed with year 1974 in one reference list; commonly cited as 1975 | Year unresolved |
| TCQSM, 3rd edition (TCRP Report 165) | Dwell-time variables reported second-hand from a paper citing the 2nd edition | Bibliographic details and equation number not verified |
| Ireland & Kullback (1968); Csiszár (1975); Bishop & Fienberg (1969) | Seen in the reference list of Loukas & Chung | Secondary only; the closed form for triangular tables in Bishop & Fienberg is plausible but unverified |
| Hussain, Bhaskar & Chung (2021), Transportation Research Part C 125, 103044 | Seen in a reference list | Secondary only |
| Bazzan, Wahle & Klügl (1999); Fernandes & Nunes (2008) | Known through two surveys | Not verified |
| Carley et al. (1998) | Cited via Gilbert inside Balke & Gilbert | Not verified |
| Hindriks et al. (2010); Cho et al. (2008); Novák et al. (2013) | Known through Adam & Gaudou | Not verified |
| Adam, Taillandier & Dugdale, "Comparing Agent Architectures in Social Simulation: BDI Agents versus Finite-state Machines" (HICSS-50) | Exists in a repository | Year, pages and DOI not shown |
| Robertson, "Modelling Bushfire Evacuation Behaviours", arXiv:1909.00991 | Preprint | No venue |
| Demazeau (1995), "From interactions to collective behaviour in agent-based systems" | Not confirmed on any retrievable page | Details must be checked independently |
| FIPA SC00029H (Contract Net) and SC00037J (Communicative Act Library) | Fetch errors | Not read; the statement that FIPA ACL semantics rest on mental attitudes comes from Singh (1998) |
| Balbo & Pinson (2010) | Reported inside Balbo et al. (2024) | Reference not verified |
| Maerivoet & De Moor, arXiv physics/0507127 | Has a section on the different meanings of "mesoscopic" | Text truncated; not read, worth reading directly |
| Journal version of Berrebi, Joshi & Watkins, "On Ridership and Frequency" | Only the arXiv record was read | Journal version not verified |
| A source for "do not solve a more general problem as an intermediate step" (Vapnik's principle) | None | Not verified; do not cite without checking |
| Ceder, Public Transit Planning and Operation; Vuchic's texts | Not accessible | No statement from either was checked |