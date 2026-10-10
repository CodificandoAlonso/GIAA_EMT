# Passenger-as-Agent vs. Mesoscopic Data-Driven Agents in Bus-Line Simulation: An Annotated Literature Review for an EAAI Related-Work Section

The literature supports the paper's positioning, but only narrowly. Passenger-as-agent transit simulation is a mature field (MATSim, BusMezzo, MILATRAS, SimMobility, Leng & Corman). Bus/stop agent models with stochastic, data-calibrated aggregate demand also exist (Kieu et al. 2020; Quek et al. 2021; Zhao et al. 2003; MARL holding-control work). Taken together, these leave no novelty in "agents without individual passengers" as such. The defensible contribution is narrower: a controlled, same-line comparison of two agent architectures (explicit passenger agents vs. aggregate stop/bus agents calibrated with Binomial/Beta/Beta-Binomial models from operator boarding/alighting counts), implemented with FIPA interaction protocols in GAMA. I found no verified peer-reviewed paper that combines all of these.

## TL;DR

- **Strand 1 is well established.** Individual passengers with origin–destination, path choice, learning and reaction to information or crowding are standard in MATSim (Horni, Nagel & Axhausen 2016), BusMezzo (Cats et al. 2010, 2011; Cats & West 2020), MILATRAS (Wahba & Shalaby 2014), SimMobility (Adnan et al. 2016) and Leng & Corman (2020). BusMezzo is mesoscopic for vehicles and agent-based for passengers.
- **Strand 2 exists, but it is scattered and rarely framed in agent-theory terms.** The closest precedents are Kieu, Malleson & Heppenstall (2020), a bus-route ABM with bus and stop agents, occupancy as a state variable and GPS data assimilation; Quek et al. (2021), an "empirical" agent-based bus model with GPS-derived speed distributions and exponential passenger arrivals; and Zhao, Bukkapatnam & Dessouky (2003), distributed bus/stop agents negotiating holding. "Reactive goal-oriented data-driven agent" is **not** an established term of art. The article must define it, anchored in Wooldridge & Jennings (1995), Russell & Norvig's agent taxonomy and data-driven ABM (Zhang et al. 2016; Kavak et al. 2018).
- **The novelty claim is defensible for EAAI only if framed as an agent-engineering contribution.** That means a dual-architecture design on one real line (EMT Madrid E01), FIPA-based bus/stop/passenger interaction in GAMA, and an explicit comparison of fidelity, data requirements and computational cost between the micro and meso agent designs. The authors' own group already published GAMA+FIPA agent simulations (Carbó & Molina 2023; Carbo, Zubelzu & Molina 2026), so methodological novelty must come from the transit domain and the architecture comparison, not from the toolchain.

## 1. Strand 1 — Passenger-as-agent (microscopic/disaggregate) models

### 1.1 Activity-based / agent-based simulators with transit modules

**Horni, A., Nagel, K., Axhausen, K.W. (eds.) (2016). *The Multi-Agent Transport Simulation MATSim*. Ubiquity Press, London. DOI 10.5334/baw.** This is the standard open-access reference for MATSim.
- *Granularity:* micro for travellers. Every traveller is an agent with a daily plan of activities, and plans are scored with a utility function.
- *Architecture:* utility-based agents in a co-evolutionary plan-improvement loop.
- *Data and scale:* synthetic populations from surveys, census or smart card data; city or region networks.
- *Analysis:* mode, route and departure-time choice, and policy scenarios.
- *Public transport:* simulated as vehicles following schedules, with passenger agents boarding and alighting. The transit chapter is by Rieser; I did not verify its chapter number or DOI suffix.
- *Use in the paper:* cite as the canonical "passengers as fully deliberative/utility-based agents" pole.

**Rieser, M., Grether, D., Nagel, K. (2009). Adding mode choice to a multiagent transport simulation. *Transportation Research Record* 2132, 50–58. DOI 10.3141/2132-06.** This is MATSim's early multimodal extension and part of the line of work leading to MATSim's transit module.
- *Verification:* confirmed only via secondary reference lists, not the publisher page.
- *Correction:* the often-cited "Agent-oriented coupling of activity-based demand generation with multiagent traffic simulation" (Rieser et al.) is *TRR* 2021 (2007), 10–17, and is not a public-transport paper. Its DOI was not verified from a primary source.

**Adnan, M., Pereira, F.C., Lima Azevedo, C.M., Basak, K., Lovric, M., Raveau, S., Zhu, Y., Ferreira, J., Zegras, C., Ben-Akiva, M. (2016). SimMobility: A multi-scale integrated agent-based simulation platform. TRB 95th Annual Meeting Compendium of Papers, Washington, DC (TRID record 1393000; no DOI).**
- *Granularity:* multi-scale, with long-term, mid-term (day-to-day) and short-term (within-day) modules. All are activity-based with individual agents.
- *Architecture:* agents' choices are tied to the goal of performing activities. The authors call this activity-based; reading it as goal-driven is my interpretation.
- *Platform, data, scale:* SimMobility on Singapore data, at network scale.
- *Relevance:* an explicitly multi-level agent platform. It is useful to show that granularity choice is a design decision even within passenger-agent frameworks.

**Erath, A., Fourie, P.J., van Eggermond, M., Ordóñez Medina, S.A., Chakirov, A., Axhausen, K.W. (2012). Large-scale agent-based transport demand model for Singapore. Paper presented at the 13th International Conference on Travel Behaviour Research (IATBR), Toronto; ETH IVT Arbeitsbericht 790.**
- *Model:* a MATSim scenario for Singapore. Public transport smart card data are used to detect activities and build agent demand.
- *Verification:* the author list beyond Erath, Fourie, Ordóñez and Chakirov, and the exact venue, come from the ETH report and are only partially verified.

**Fourie, P.J., Erath, A., Ordóñez Medina, S.A., Chakirov, A., Axhausen, K.W. (2016). Using smartcard data for agent-based transport simulation. Book chapter (2016); the book title, editors and pages were not verified.**
- *Model:* a full day of Singapore smart card transactions is turned into both transit supply and passenger demand for a simplified MATSim transit simulation. Bus speeds and dwell times are stochastic, which avoids simulating car–bus interaction (per secondary summaries).
- *Relevance:* a direct precedent for AFC data driving passenger-agent demand. It also shows a "meso-like" simplification of vehicle movement inside a micro passenger model.

### 1.2 Agent-based transit assignment and passenger behaviour

**Toledo, T., Cats, O., Burghout, W., Koutsopoulos, H.N. (2010). Mesoscopic simulation for transit operations. *Transportation Research Part C* 18(6), 896–908. DOI 10.1016/j.trc.2010.02.008.** This is the founding BusMezzo paper.
- *Model:* a transit simulator built on the Mezzo mesoscopic traffic model. Vehicles move mesoscopically on links, and the model represents bus operations at stops (dwell times, schedule and control strategies) for evaluating Advanced Public Transportation Systems (APTS) such as frequency setting and real-time holding.
- *Precise classification:* BusMezzo is **mesoscopic for vehicles/traffic**. In later versions (Cats et al. 2011; Cats 2011 PhD, KTH) it is **agent-based for passengers**, who make adaptive path choices.
- *Caveat:* whether the 2010 paper's passenger demand is fully individual or arrival-rate based should be checked in the full text before asserting it. My working understanding is that the individual-passenger path-choice layer came in the 2011 papers.

**Cats, O., Burghout, W., Toledo, T., Koutsopoulos, H.N. (2010). Mesoscopic modeling of bus public transportation. *Transportation Research Record* 2188, 9–18. DOI 10.3141/2188-02.**
- *Granularity:* meso vehicles; a bus-operations focus (dwell, holding, service reliability).
- *Relevance:* closest "meso transit operations" anchor from the transportation side.

**Cats, O., Koutsopoulos, H.N., Burghout, W., Toledo, T. (2011). Effect of real-time transit information on dynamic path choice of passengers. *Transportation Research Record* 2217, 46–54. DOI 10.3141/2217-06.**
- *Model:* passengers are individual agents making within-day dynamic path-choice decisions (boarding, alighting, walking) that respond to real-time information.
- *Architecture:* probabilistic discrete-choice (utility-based) agents.
- *Platform, scale:* BusMezzo, network scale.
- *Analysis:* the effect of information provision on passenger decisions and the system.
- *Note:* Toledo's own publication list spells the title "path choices"; the DOI-linked copies say "path choice".

**Cats, O., West, J. (2020). Learning and adaptation in dynamic transit assignment models for congested networks. *Transportation Research Record* 2674(1), 113–124. DOI 10.1177/0361198119900138.**
- *Model:* a day-to-day learning mechanism inside a dynamic agent-based transit assignment model (BusMezzo). Passengers adapt to service uncertainty, on-board crowding and information.
- *Granularity, architecture:* micro passengers; learning, utility-based agents.
- *Application:* Stockholm rapid transit network.
- *Relevance:* a recent, authoritative example of passengers' decisions (crowding, information, learning) being the object of analysis.

**Wahba, M., Shalaby, A. (2014). Learning-based framework for transit assignment modeling under information provision. *Transportation* 41(2), 397–417. DOI 10.1007/s11116-013-9510-5.** This is the core MILATRAS paper.
- *Model:* departure-time and path choices are modelled as a Markov decision process with reinforcement-learning passengers.
- *Granularity:* micro, agent-based travellers; aggregate patterns emerge from individual choices.
- *Scale:* network (the thesis applies it to Toronto).
- *Supporting items:* Wahba & Shalaby (2005), "Multiagent learning-based approach to transit assignment problem: a prototype", *TRR* 1926, 96–105 (DOI not verified); Wahba's 2008/2009 University of Toronto PhD thesis, *MILATRAS*.
- *Relevance:* one secondary source (arXiv 2408.06308) calls MILATRAS the first agent-based public-transport simulation with a learning process. That characterisation is that source's, not mine.

**Leng, N., Corman, F. (2020). The role of information availability to passengers in public transport disruptions: An agent-based simulation approach. *Transportation Research Part A* 133, 214–236. DOI 10.1016/j.tra.2020.01.007.**
- *Model:* MATSim-based agent micro-simulation of large-scale passenger behaviour during disruptions, under different information availability.
- *Granularity:* micro passengers.
- *Analysis:* travel time, line changes and line usage.
- *Relevance:* a recent passenger-decision-centred study (Strand 1 exemplar).

**Cong, C., Li, X., Yang, S., Zhang, Q., Lu, L., Shi, Y. (2022). Impact estimation of unplanned urban rail disruptions on public transport passengers: A multi-agent based simulation approach. *International Journal of Environmental Research and Public Health* 19(15), 9052 (published 25 July 2022). DOI 10.3390/ijerph19159052; PMC9330580.**
- *Model:* passenger agents choose responses through a rule-based logit model with Monte Carlo sampling, and they interact with vehicle and station agents. Ningbo network.
- *Verification:* the author list (Cong, Li, Yang, Zhang, Lu & Shi) comes from the PMC record.
- *Relevance:* a three-agent-type decomposition (passenger/vehicle/station) almost identical to the article's bus/stop/passenger, with individual passengers.

### 1.3 Bus-network multi-agent simulations with passenger agents, and GAMA transit work

**Meignan, D., Simonin, O., Koukam, A. (2007). Simulation and evaluation of urban bus-networks using a multiagent approach. *Simulation Modelling Practice and Theory* 15(6), 659–671. DOI 10.1016/j.simpat.2007.02.005.**
- *Model:* a multi-agent bus-network simulation with buses, passengers and traffic. Passengers determine routes across pedestrian and bus networks.
- *Use:* evaluating a redesigned bus network for Belfort (France), integrated into a decision-support tool.
- *Granularity:* micro passengers plus bus agents; reactive/situated agents (the Simonin/Koukam school). The architecture label is my interpretation.
- *Relevance:* probably the closest classic MAS-community precedent for a bus/passenger agent decomposition. Cite it prominently.

**McDonnell, S., Zellner, M. (2011). Exploring the effectiveness of bus rapid transit: a prototype agent-based model of commuting behavior. *Transport Policy* 18(6), 825–835.**
- *Model:* commuter agents choosing between car and BRT. Prototype, stylised scale.
- *Verification:* DOI and platform not verified here; the citation comes from the Balbo et al. (2024) reference list.

**Vu, T.-D., Gaudou, B., Oberoi, K.S. (2025). Modeling realistic human behavior using generative agents in a multimodal transport system: software architecture and application to Toulouse. arXiv:2510.19497 (IRIT, Université Toulouse Capitole; CESI LINEACT).**
- *Model:* combines the **GAMA** platform with an LLM-based generative agent, GTFS data and OpenTripPlanner. *Inhabitant* (passenger) agents are driven by the generative agents, and *Public Vehicle* agents follow GTFS schedules. Over a simulated month the agents form travel habits.
- *Relevance:* a very recent GAMA transit model with explicit passenger agents. It is the nearest GAMA analogue to the article's passenger-agent architecture.
- *Verification:* preprint; not peer-reviewed.

### 1.4 Reviews

**Balbo, F., Mandiau, R., Zargayouna, M. (2024). Extended review of multi-agent solutions to Advanced Public Transportation Systems challenges. *Public Transport* 16(1), 159–186. DOI 10.1007/s12469-023-00332-9.**
- *Method:* a systematic review restricted to journal papers; the authors analysed 38 papers from 19 journals over 1990–2020, using the Vowels (Agents–Environment–Interaction–Organisation) grid.
- *Findings:* MAS suit real-time disturbance management because of delegation, pro-activeness and autonomy. It cites Zhao et al. (2003), Meignan et al. (2007), McDonnell & Zellner (2011) and Ingvardson et al. (2017).
- *Use:* the single best review to cite for "MAS in public transport". Its Interaction (I) dimension is the natural hook for the paper's FIPA protocols.

**Klügl, F., Bazzan, A.L.C., Ossowski, S. (2010). Agents in traffic and transportation. *Transportation Research Part C* 18(1), 69–70.** A short editorial giving the rationale for agents in transport: systems are naturally distributed, and bottom-up modelling handles their complexity. DOI not verified here.

**Rezazada, M., Nassir, N., Tanin, E., Ceder, A. (2024). Bus bunching: a comprehensive review from demand, supply, and decision-making perspectives. *Transport Reviews* 44(4), 766–790. DOI 10.1080/01441647.2024.2313969.**
- *Content:* covers holding (Daganzo 2009), boarding limits and multi-agent DRL (Wang & Sun 2020).
- *Verification:* authors, volume and pages from Crossref.

## 2. Strand 2 — Reactive, goal-oriented, data-driven agents at mesoscopic level

### 2.1 Bus/stop agent models with aggregate or stochastic passenger demand (closest precedents)

**Kieu, L.-M., Malleson, N., Heppenstall, A. (2020). Dealing with uncertainty in agent-based models for short-term predictions. *Royal Society Open Science* 7(1), 191074. DOI 10.1098/rsos.191074 (preprint arXiv:1908.08288; code on Zenodo, record 3548255).** This is the **most directly relevant Strand 2 precedent.**
- *Agents:* bus agents with states idle/moving/dwelling/finished, acceleration, dwell-time parameters and **occupancy (Occ)** as a state variable, plus bus-stop agents with geofences.
- *Passengers:* represented as counts and rates at stops and on buses. No individually tracked passengers is how I read the published parameter tables.
- *Data:* calibrated on synthetic "historical" GPS data, with particle-filter data assimilation of synthetic "real-time" GPS. Observed trajectories of Brisbane Route 555 motivate the model.
- *Scale, platform:* a single bus route; Python.
- *Analysis:* short-term prediction of bus locations and bunching under low and high demand.
- *Architecture:* rule-based reactive agents (my classification). The authors use "agent-based model" and "data assimilation", not "reactive".
- *Positioning:* the article differs in using real operator boarding/alighting counts, explicit FIPA interaction, GAMA, and a passenger-agent counterpart architecture.

**Quek, W.L., Chung, N.N., Saw, V.-L., Chew, L.Y. (2021). Analysis and simulation of intervention strategies against bus bunching by means of an empirical agent-based model. *Complexity* 2021, 2606191. DOI 10.1155/2021/2606191 (preprint arXiv:2004.13022).**
- *Model:* the "Empirically-based Monte Carlo Bus-network (EMB)" model. Bus agents move with empirical GPS-derived velocity distributions, and passengers arrive at stops with exponential inter-arrival times.
- *Data, validation:* validated on the NTU (Singapore) campus shuttle loop.
- *Analysis:* holding, no-boarding and centralised pulsing strategies.
- *Granularity:* meso-like. Passengers are a stochastic process at stops, and the empirical distributions are calibrated from data.
- *Relevance:* a close precedent for "data-driven, distribution-sampled demand in a bus-line ABM". The authors' term "empirical agent-based model" is a useful established near-synonym for the article's "data-driven".

**Zhao, J., Bukkapatnam, S., Dessouky, M.M. (2003). Distributed architecture for real-time coordination of bus holding in transit networks. *IEEE Transactions on Intelligent Transportation Systems* 4(1), 43–51. DOI 10.1109/TITS.2003.809769.**
- *Model:* a distributed multi-agent architecture in which bus and stop agents negotiate holding decisions in real time.
- *Granularity:* operations-level; passengers enter as demand rates, not agents (my reading via the Balbo et al. 2024 review; confirm in the full text).
- *Relevance:* an early precedent for **infrastructure/vehicle agents with interaction protocols** in bus control. Its reference list includes Sandholm's implementation of the contract net protocol, which supports citing it against any claim that stop-agent negotiation is new.

**Wang, J., Sun, L. (2020). Dynamic holding control to avoid bus bunching: A multi-agent deep reinforcement learning framework. *Transportation Research Part C* 116, 102661. DOI 10.1016/j.trc.2020.102661.**
- *Model:* each bus is a learning agent. Multi-agent PPO with a joint-action tracker learns holding policies.
- *Passengers:* demand is stochastic or aggregate; passengers are not agents.
- *Relevance:* illustrates "agents without individual passengers" in high-impact transit work. The architecture is learned, contrasting with the article's rule-based, data-calibrated agents.
- *Follow-up:* Wang & Sun's asynchronous MARL work (IJCAI 2021) extends this line; its citation was not verified here.

**Daganzo, C.F. (2009). A headway-based approach to eliminate bus bunching: Systematic analysis and comparisons. *Transportation Research Part B* 43(10), 913–921. DOI 10.1016/j.trb.2009.04.002.**
- *Model:* an analytical, macro/meso headway dynamics model with aggregate passenger arrival rates, plus adaptive holding.
- *Status:* not an ABM.
- *Use:* cite as the operations-research foundation for aggregate passenger representation in bus-line dynamics.
- *Verification:* the issue number is consistent with the December date, but Crossref did not return it.

**Bartholdi, J.J. III, Eisenstein, D.D. (2012). A self-coördinating bus route to resist bus bunching. *Transportation Research Part B* 46(4), 481–491. DOI 10.1016/j.trb.2011.11.001.**
- *Model:* a decentralised headway rule that lets buses self-equalise without a schedule. Each bus follows a simple local rule, so it is reactive and decentralised (my framing).
- *Relevance:* conceptually close to reactive bus agents in Brooks' sense of emergent coordination.

**Ingvardson, J.B., Jensen, J.K., Nielsen, O.A. (2017). Analysing improvements to on-street public transport systems: a mesoscopic model approach. *Public Transport* 9(1), 385–409. DOI 10.1007/s12469-016-0151-x.**
- *Model:* a mesoscopic model evaluating segregated infrastructure and APTS elements (including holding) via a reliability measure combining headway regularity and running-time variability.
- *Relevance:* supports the "mesoscopic is the appropriate granularity for operations evaluation" argument.

### 2.2 Micro/meso trade-off and multi-level modelling

**Burghout, W., Koutsopoulos, H.N., Andréasson, I. (2005). Hybrid mesoscopic–microscopic traffic simulation. *Transportation Research Record* 1934, 218–225. DOI 10.1177/0361198105193400123.**
- *Content:* the canonical hybrid-resolution traffic paper. It combines microscopic detail in areas of interest with mesoscopic representation elsewhere, to manage computational and calibration cost.
- *Corrections:* use pages 218–225; some papers mis-cite 218–255. Older references use a 10.3141 DOI form.

**Morvan, G. (2012, rev. 2013). Multi-level agent-based modeling — A literature survey. arXiv:1205.0561 [cs.MA].**
- *Content:* defines multi-level ABM (heterogeneous agent models at different levels) and reviews applications, including flow models. It notes that GAMA has native multi-level capabilities (macro-/micro-species).
- *Use:* the theoretical justification for treating "stop with aggregate passenger flow" as a legitimate higher-level agent.
- *Status:* not peer-reviewed in this form; widely cited.

### 2.3 Data-driven ABM methodology

**Zhang, H., Vorobeychik, Y., Letchford, J., Lakkaraju, K. (2016). Data-driven agent-based modeling, with application to rooftop solar adoption. *Autonomous Agents and Multi-Agent Systems* 30(6), 1023–1049. DOI 10.1007/s10458-016-9326-8 (conference version: AAMAS 2015, pp. 513–521).**
- *Content:* introduces the term **DDABM**. Individual behaviour models are learned with machine learning from data, deployed in the multi-agent system, and validated on a holdout sequence of collective outcomes. The authors stress that the resulting model has no additional hand-tuned behavioural parameters.
- *Relevance:* the best citation for "data-driven agents". Note the difference: DDABM learns *individual* behaviour from individual-level data, whereas the article calibrates *aggregate stop-level* distributions. The article should say it adopts the DDABM principle at the meso level.

**Kavak, H., Padilla, J.J., Lynch, C.J., Diallo, S.Y. (2018). Big data, agents, and machine learning: towards a data-driven agent-based modeling approach. In *Proceedings of the Annual Simulation Symposium (ANSS '18)*, SpringSim 2018, pp. 1–12.**
- *Content:* argues for the DDABM approach using big data and machine learning to derive agent behaviour.
- *Correction:* the title the request attributes to Kavak et al. ("Big data, agents, and the city") is a **different** work: Crooks, A., Malleson, N., Wise, S., Heppenstall, A. (2018), "Big data, agents and the city", in Schintler, L.A., Chen, Z. (eds.), *Big Data for Regional Science*, Routledge. That chapter discusses using big data to inform, calibrate and validate urban ABMs, and notes that the individual-level data needed are often only available in aggregate form. That point directly supports a meso design. Pages and DOI for both items were not verified.

### 2.4 Agent-theory framing

- **Wooldridge, M., Jennings, N.R. (1995). Intelligent agents: theory and practice. *Knowledge Engineering Review* 10(2), 115–152. DOI 10.1017/S0269888900008122.** Defines the weak notion of agency (autonomy, social ability, reactivity, pro-activeness) and the deliberative/reactive/hybrid architecture distinction. This is the anchor for calling stop/bus agents "reactive" yet "pro-active/goal-directed".
- **Rao, A.S., Georgeff, M.P. (1995). BDI agents: from theory to practice. *Proc. 1st International Conference on Multi-Agent Systems (ICMAS-95)*, San Francisco, AAAI Press, pp. 312–319 (no DOI).** The BDI contrast pole. The article's agents are deliberately *not* BDI.
- **Russell, S., Norvig, P., *Artificial Intelligence: A Modern Approach*** (4th ed., Pearson, 2020/2021). Taxonomy: simple reflex, model-based reflex, goal-based, utility-based and learning agents. Edition and year were not tool-verified here.
- **Brooks, R.A. (1986). A robust layered control system for a mobile robot. *IEEE Journal of Robotics and Automation* 2(1), 14–23. DOI 10.1109/JRA.1986.1087032.** Subsumption and the reactive paradigm. Cited from domain knowledge; not tool-verified in this search.
- **Ferber, J. (1999). *Multi-Agent Systems: An Introduction to Distributed Artificial Intelligence*. Addison-Wesley.** Reactive vs. cognitive agents. The title is confirmed in secondary reference lists.

### 2.5 GAMA platform and the authors' group (GIAA, UC3M)

**Taillandier, P., Gaudou, B., Grignard, A., Huynh, Q.-N., Marilleau, N., Caillou, P., Philippon, D., Drogoul, A. (2019). Building, composing and experimenting complex spatial models with the GAMA platform. *GeoInformatica* 23, 299–322. DOI 10.1007/s10707-018-00339-6.** The GAMA developers' requested citation (GAMA 1.8, the GAML language, spatial and multi-level features).

**Saval, A., Minh, D.P., Chapuis, K., Tranouez, P., Caron, C., Daudé, É., Taillandier, P. (2023). Dealing with mixed and non-normative traffic. An agent-based simulation with the GAMA platform. *PLOS ONE* 18(3), e0281658. DOI 10.1371/journal.pone.0281658; PMC9987808.**
- *Content:* the GAMA built-in traffic plugin (driving skills; GAMA 1.8.2), covering cars, motorcycles, buses and bicycles. It supports city-level simulations with tens of thousands of driver agents and reproduces traffic in Hanoi, Vietnam.
- *Verification:* the full author list is from Crossref.

**Carbó, J., Molina, J.M. (2023). Trust model of privacy-concerned, emotionally aware agents in a cooperative logistics problem. *Applied Sciences* 13(15), 8681. DOI 10.3390/app13158681 (preprint arXiv:2401.14436).**
- *Model:* GAMA 1.8.2/GAML, BDI agents and **FIPA Call-for-Proposals / Contract-Net protocols** (chained sequentially), with humans and unmanned vehicles.
- *Relevance:* the group's direct precedent for "GAMA + FIPA". It must be cited, and it means the toolchain is not novel.

**Carbo, J., Zubelzu, S., Molina, J.M. (2026). An agents-based tool for simulating farmers operation in irrigation districts. *Computers and Electronics in Agriculture* 245, 111518. DOI 10.1016/j.compag.2026.111518.** This is the template article.
- *Agents:* farmers, a deliverer agent and a weather-station agent providing daily forecasts. Hydraulic pressure-head calculations are combined with agent interaction; implemented in GAMA for GIS integration.
- *Agent knowledge:* private (farmers do not share crop status, soil moisture or expected irrigation times). Decisions combine economic and moral considerations through explainable logic.
- *Verification:* volume 245 (April 2026) is confirmed by DBLP and ScienceDirect. Whether its interactions use FIPA protocols was not confirmed from the full text.

**Carbo, J., Sanchez-Pi, N., Molina, J.M. (2018). Agent-based simulation with NetLogo to evaluate ambient intelligence scenarios. *Journal of Simulation* 12(1), 42–52. DOI 10.1057/jos.2016.10.** NetLogo with FIPA/BDI extensions. It shows the group's long-standing methodology of FIPA-style interaction in ABS, which migrated from JADE to NetLogo to GAMA.

I found no Carbó/Molina paper on bus or public-transport simulation.

## 3. Comparison table of key works

| Work | Granularity | Passenger representation | Agent types / architecture | Platform | Calibration / validation data | Scale | Main analysis |
|---|---|---|---|---|---|---|---|
| Horni et al. 2016 (MATSim) | Micro (travellers); queue-based vehicles | Individual agents with daily plans, OD | Utility-based, co-evolutionary | MATSim (Java) | Surveys, census, smart card | City/region | Mode/route/time choice, policy |
| Toledo et al. 2010; Cats et al. 2010 (BusMezzo) | Meso vehicles | Operations focus; individual passenger layer in later versions (verify 2010) | Bus/vehicle entities; control strategies | BusMezzo/Mezzo | Operator AVL/schedules | Line to network | Holding, frequency, reliability |
| Cats et al. 2011; Cats & West 2020 | Meso vehicles + micro passengers | Individual agents; path choice, learning, crowding | Utility-based, learning | BusMezzo | Stockholm network data | Network | Real-time information, crowding, learning |
| Wahba & Shalaby 2014 (MILATRAS) | Micro | Individual agents | RL/MDP learning agents | MILATRAS | Toronto (thesis) | Network | Departure-time and path choice |
| Adnan et al. 2016 (SimMobility) | Multi-scale micro | Individual activity-based agents | Activity-based (goal-driven, my reading) | SimMobility | Singapore | City | Integrated land-use/transport |
| Fourie et al. 2016; Erath et al. 2012 | Micro passengers, simplified vehicles | Agents from smart card trips | Utility-based (MATSim) | MATSim | Singapore smart card | City | Transit demand/supply |
| Leng & Corman 2020 | Micro | Individual agents | Utility-based | MATSim | Case network | Network | Information in disruptions |
| Meignan et al. 2007 | Micro | Passenger agents with routes | Bus, passenger and traffic agents; reactive/situated (my reading) | Custom MAS | Belfort network | Network | Network design evaluation |
| Kieu et al. 2020 | Meso-like | Counts/occupancy at stops/buses | Bus and stop agents; rule-based reactive (my reading) | Python | Synthetic GPS; particle filter | Single route | Short-term prediction, data assimilation |
| Quek et al. 2021 (EMB) | Meso-like | Stochastic exponential arrivals | Bus agents; empirical distributions | Custom Monte Carlo ABM | GPS (NTU shuttle) | Single loop | Bunching interventions |
| Zhao et al. 2003 | Operations | Demand rates (verify) | Bus and stop agents negotiating | Custom distributed MAS | Simulated | Line/network | Real-time holding coordination |
| Wang & Sun 2020 | Operations | Stochastic aggregate | Bus agents; learned (MAPPO) | Custom simulator | Simulated/real line data | Single line | Holding, bunching |
| Daganzo 2009; Bartholdi & Eisenstein 2012 | Macro/meso analytical | Aggregate arrival rates | Rule-based buses (not ABM) | Analytical/simulation | — | Single line | Headway control |
| arXiv:2510.19497 (Toulouse) | Micro | Individual LLM-driven agents | Inhabitant and vehicle agents; generative | **GAMA** | GTFS | City | Behavioural realism |
| Carbó & Molina 2023 | Micro (logistics) | n/a | BDI with **FIPA CFP** | **GAMA** | Scenario-based | Small | Trust/privacy |
| Carbo et al. 2026 | Micro (farmers) | n/a | Farmer/deliverer/weather agents | **GAMA** | Network GIS, hydraulics | District | Irrigation operations |
| **This article** | **Micro (Arch. A) vs meso (Arch. B)** | **Agents vs Binomial/Beta/Beta-Binomial counts** | **Bus/stop/(passenger); reactive goal-oriented, data-calibrated; FIPA** | **GAMA** | **EMT Madrid boarding/alighting per stop × time band** | **Single line (E01)** | **Architecture comparison** |

## 4. Terminology findings

- **"Reactive goal-oriented data-driven agent" is not an established term of art.** No verified source in this search uses the phrase. I did not run an exhaustive phrase search in Scopus, so this is "not found", not "proven absent". The article must define it as a composite and anchor each component:
  - *Reactive:* Wooldridge & Jennings (1995); Brooks (1986); Ferber (1999). These are agents that map percepts to actions without symbolic deliberation or planning.
  - *Goal-oriented:* Russell & Norvig's "goal-based agent". In Wooldridge & Jennings' terms it is *pro-activeness*. Strictly, a reactive rule-following agent with a fixed objective (keep schedule, serve stops) is closer to Russell & Norvig's **model-based reflex agent** with a designer-embedded goal than to a true goal-based agent that searches or plans. Reviewers in EAAI may press this point. Either justify "goal-oriented" (e.g., agents select among behaviours according to explicit goal states) or use **"hybrid reactive agents with goal-directed behaviour"**.
  - *Data-driven:* **DDABM** (Zhang et al. 2016; Kavak et al. 2018). Related: "empirical ABM" (Quek et al. 2021), "data assimilation for ABM" (Kieu et al. 2020), and the calibration/validation discussion of Crooks et al. (2018).
- **Closest established terms:** *mesoscopic transit simulation* (Toledo et al. 2010; Cats et al. 2010; Ingvardson et al. 2017); *hybrid meso-micro simulation* (Burghout et al. 2005); *multi-level ABM* (Morvan); *data-driven ABM* (Zhang et al. 2016); *empirical ABM* (Quek et al. 2021).
- **Recommended phrasing:** "a mesoscopic, multi-level agent architecture in which stop and bus agents are reactive, goal-directed agents whose passenger-flow behaviour is data-driven (calibrated from operator counts), following the DDABM principle at an aggregate level." This keeps the statistics as an enabling component, not the contribution, as the co-authors want.

## 5. Research gap, closest precedents and novelty assessment

**What is well established:**
1. Passenger-as-agent transit simulation at network scale (MATSim, BusMezzo, MILATRAS, SimMobility).
2. Mesoscopic vehicle representation in transit (BusMezzo).
3. Single-line bus ABMs or operations models with stochastic aggregate demand (Kieu et al. 2020; Quek et al. 2021; Wang & Sun 2020; analytical work by Daganzo and by Bartholdi & Eisenstein).
4. Bus/stop agents with interaction protocols for control (Zhao et al. 2003).
5. GAMA+FIPA agent simulation by the authors' own group (Carbó & Molina 2023; Carbo et al. 2026).

**Closest precedents that limit the novelty claim, ranked:**
1. Kieu, Malleson & Heppenstall (2020): bus and stop agents, single route, aggregate occupancy, data-driven calibration and assimilation.
2. Quek et al. (2021): single bus loop, empirical distributions, stochastic passenger arrivals.
3. Zhao, Bukkapatnam & Dessouky (2003): bus/stop agents with negotiation protocols.
4. Meignan, Simonin & Koukam (2007): bus/passenger MAS for an urban network.
5. The Cong et al. (2022, IJERPH) passenger/vehicle/station agent decomposition.
6. Carbó & Molina (2023): GAMA + FIPA in the authors' group.

A further candidate is a TRID-indexed paper, "Insights into the bus bunching problem: a multi-agent simulation approach". Its venue and DOI were not verified, so check it before submission. Neumann & Nagel (2010, VSP working paper 10-08) simulated bus bunching on Berlin line M44 in MATSim, but with individual passenger agents, and it is not confirmed as peer-reviewed.

**What appears not to exist (within this search):** a peer-reviewed model that **(a)** implements *both* a passenger-agent and an aggregate-flow agent architecture for the *same real bus line*, **(b)** calibrates stop × time-band boarding/alighting with Binomial/Beta/Beta-Binomial sampling from operator counts, **(c)** uses FIPA interaction protocols between bus and stop agents, and **(d)** runs in GAMA. Each element has precedents; the combination does not.

**Blunt assessment for EAAI:**
- **Weak claims to avoid:** "first ABM of a bus line"; "first agents without individual passengers"; "first data-driven bus ABM"; "first GAMA/FIPA simulation". Each is contradicted by the precedents above.
- **Defensible claim:** an *agent-engineering methodology* showing how granularity (who is an agent) can be shifted from passengers to infrastructure while preserving data fidelity. It would be supported by:
  - a formal definition of the reactive goal-directed data-driven agent;
  - explicit FIPA protocol specifications (e.g., request/inform/CFP between bus and stop);
  - a quantitative comparison of the two architectures on the same line: accuracy against held-out EMT counts, run time and memory scaling, and data requirements (individual OD vs. counts only).
- **The main risk:** if the paper does not quantitatively compare the two architectures, reviewers will likely see Architecture B as a re-implementation of Kieu et al. (2020) or Quek et al. (2021) with a different toolchain. The comparison is the contribution; make it the centrepiece.
- **Data requirements as the argument:** use the observation in Crooks et al. (2018) that individual-level data for ABM calibration are often only available in aggregate. Operator APC/AFC counts without card-level OD are exactly that case, which justifies Architecture B on data-availability grounds rather than only computational ones.

## 6. Caveats

- Author lists for Cong et al. (2022), Vu et al. (2025), Saval et al. (2023) and Rezazada et al. (2024) were completed from Crossref/PMC/arXiv metadata. Vu et al. (2025) is still a non-peer-reviewed preprint.
- Some DOIs or details come from consistent secondary reference lists rather than publisher pages: Wooldridge & Jennings; the Rieser et al. 2009 DOI; Cats et al. 2011; Brooks 1986; Klügl et al. 2010; Fourie et al. 2016 book details. Check them on Crossref.
- Granularity and architecture labels marked "my reading" or "my interpretation" are not the authors' terminology.
- Erath et al. (2012), Fourie et al. (2016) and Wahba & Shalaby (2005) are omitted from the BibTeX because key bibliographic fields are unverified; add them once confirmed.

## 7. BibTeX

```bibtex
@book{horni2016matsim,
  editor={Horni, Andreas and Nagel, Kai and Axhausen, Kay W.},
  title={The Multi-Agent Transport Simulation {MATSim}},
  publisher={Ubiquity Press}, address={London}, year={2016},
  doi={10.5334/baw}}

@article{rieser2009modechoice,
  author={Rieser, Marcel and Grether, Dominik and Nagel, Kai},
  title={Adding Mode Choice to a Multiagent Transport Simulation},
  journal={Transportation Research Record}, volume={2132}, pages={50--58}, year={2009},
  doi={10.3141/2132-06}, note={DOI from secondary sources; verify}}

@inproceedings{adnan2016simmobility,
  author={Adnan, Muhammad and Pereira, Francisco C. and Lima Azevedo, Carlos Miguel and Basak, Kakali and Lovric, Milan and Raveau, Sebasti{\'a}n and Zhu, Yi and Ferreira, Joseph and Zegras, Christopher and Ben-Akiva, Moshe},
  title={{SimMobility}: A Multi-Scale Integrated Agent-Based Simulation Platform},
  booktitle={Transportation Research Board 95th Annual Meeting Compendium of Papers},
  address={Washington, DC}, year={2016}, note={TRID 1393000}}

@article{toledo2010mesoscopic,
  author={Toledo, Tomer and Cats, Oded and Burghout, Wilco and Koutsopoulos, Haris N.},
  title={Mesoscopic simulation for transit operations},
  journal={Transportation Research Part C: Emerging Technologies},
  volume={18}, number={6}, pages={896--908}, year={2010},
  doi={10.1016/j.trc.2010.02.008}}

@article{cats2010busmezzo,
  author={Cats, Oded and Burghout, Wilco and Toledo, Tomer and Koutsopoulos, Haris N.},
  title={Mesoscopic Modeling of Bus Public Transportation},
  journal={Transportation Research Record}, volume={2188}, pages={9--18}, year={2010},
  doi={10.3141/2188-02}}

@article{cats2011realtime,
  author={Cats, Oded and Koutsopoulos, Haris N. and Burghout, Wilco and Toledo, Tomer},
  title={Effect of Real-Time Transit Information on Dynamic Path Choice of Passengers},
  journal={Transportation Research Record}, volume={2217}, pages={46--54}, year={2011},
  doi={10.3141/2217-06}}

@article{cats2020learning,
  author={Cats, Oded and West, Jens},
  title={Learning and Adaptation in Dynamic Transit Assignment Models for Congested Networks},
  journal={Transportation Research Record}, volume={2674}, number={1}, pages={113--124}, year={2020},
  doi={10.1177/0361198119900138}}

@article{wahba2014milatras,
  author={Wahba, Mohamed and Shalaby, Amer},
  title={Learning-based framework for transit assignment modeling under information provision},
  journal={Transportation}, volume={41}, number={2}, pages={397--417}, year={2014},
  doi={10.1007/s11116-013-9510-5}}

@article{leng2020information,
  author={Leng, Nuannuan and Corman, Francesco},
  title={The role of information availability to passengers in public transport disruptions: An agent-based simulation approach},
  journal={Transportation Research Part A: Policy and Practice}, volume={133}, pages={214--236}, year={2020},
  doi={10.1016/j.tra.2020.01.007}}

@article{cong2022raildisruption,
  author={Cong, C. and Li, X. and Yang, S. and Zhang, Q. and Lu, L. and Shi, Y.},
  title={Impact Estimation of Unplanned Urban Rail Disruptions on Public Transport Passengers: A Multi-Agent Based Simulation Approach},
  journal={International Journal of Environmental Research and Public Health},
  volume={19}, number={15}, pages={9052}, year={2022},
  doi={10.3390/ijerph19159052}}

@article{meignan2007bus,
  author={Meignan, David and Simonin, Olivier and Koukam, Abderrafi{\^a}a},
  title={Simulation and evaluation of urban bus-networks using a multiagent approach},
  journal={Simulation Modelling Practice and Theory}, volume={15}, number={6}, pages={659--671}, year={2007},
  doi={10.1016/j.simpat.2007.02.005}}

@article{mcdonnell2011brt,
  author={McDonnell, Simon and Zellner, Moira},
  title={Exploring the effectiveness of bus rapid transit: a prototype agent-based model of commuting behavior},
  journal={Transport Policy}, volume={18}, number={6}, pages={825--835}, year={2011},
  note={DOI not verified}}

@misc{vu2025toulouse,
  author={Vu, T.-D. and Gaudou, Benoit and Oberoi, K. S.},
  title={Modeling realistic human behavior using generative agents in a multimodal transport system: Software architecture and Application to {Toulouse}},
  year={2025}, eprint={2510.19497}, archivePrefix={arXiv}}

@article{balbo2024review,
  author={Balbo, Flavien and Mandiau, Ren{\'e} and Zargayouna, Mahdi},
  title={Extended review of multi-agent solutions to Advanced Public Transportation Systems challenges},
  journal={Public Transport}, volume={16}, number={1}, pages={159--186}, year={2024},
  doi={10.1007/s12469-023-00332-9}}

@article{klugl2010agents,
  author={Kl{\"u}gl, Franziska and Bazzan, Ana L. C. and Ossowski, Sascha},
  title={Agents in traffic and transportation},
  journal={Transportation Research Part C: Emerging Technologies}, volume={18}, number={1}, pages={69--70}, year={2010},
  note={DOI not verified}}

@article{rezazada2024bunching,
  author={Rezazada, M. and Nassir, N. and Tanin, E. and Ceder, A.},
  title={Bus bunching: a comprehensive review from demand, supply, and decision-making perspectives},
  journal={Transport Reviews}, volume={44}, number={4}, pages={766--790}, year={2024},
  doi={10.1080/01441647.2024.2313969}}

@article{kieu2020uncertainty,
  author={Kieu, Le-Minh and Malleson, Nicolas and Heppenstall, Alison},
  title={Dealing with uncertainty in agent-based models for short-term predictions},
  journal={Royal Society Open Science}, volume={7}, number={1}, pages={191074}, year={2020},
  doi={10.1098/rsos.191074}}

@article{quek2021emb,
  author={Quek, Wei Liang and Chung, Ning Ning and Saw, Vee-Liem and Chew, Lock Yue},
  title={Analysis and Simulation of Intervention Strategies against Bus Bunching by means of an Empirical Agent-Based Model},
  journal={Complexity}, volume={2021}, pages={2606191}, year={2021},
  doi={10.1155/2021/2606191}}

@article{zhao2003holding,
  author={Zhao, Jiamin and Bukkapatnam, Satish and Dessouky, Maged M.},
  title={Distributed architecture for real-time coordination of bus holding in transit networks},
  journal={IEEE Transactions on Intelligent Transportation Systems}, volume={4}, number={1}, pages={43--51}, year={2003},
  doi={10.1109/TITS.2003.809769}, note={First author's given name confirmed via Crossref}}

@article{wang2020holding,
  author={Wang, Jiawei and Sun, Lijun},
  title={Dynamic holding control to avoid bus bunching: A multi-agent deep reinforcement learning framework},
  journal={Transportation Research Part C: Emerging Technologies}, volume={116}, pages={102661}, year={2020},
  doi={10.1016/j.trc.2020.102661}}

@article{daganzo2009headway,
  author={Daganzo, Carlos F.},
  title={A headway-based approach to eliminate bus bunching: Systematic analysis and comparisons},
  journal={Transportation Research Part B: Methodological}, volume={43}, number={10}, pages={913--921}, year={2009},
  doi={10.1016/j.trb.2009.04.002}}

@article{bartholdi2012selfcoordinating,
  author={Bartholdi, John J., III and Eisenstein, Donald D.},
  title={A self-co{\"o}rdinating bus route to resist bus bunching},
  journal={Transportation Research Part B: Methodological}, volume={46}, number={4}, pages={481--491}, year={2012},
  doi={10.1016/j.trb.2011.11.001}}

@article{ingvardson2017mesoscopic,
  author={Ingvardson, Jesper Bl{\aa}foss and Jensen, Jonas Kornerup and Nielsen, Otto Anker},
  title={Analysing improvements to on-street public transport systems: a mesoscopic model approach},
  journal={Public Transport}, volume={9}, number={1}, pages={385--409}, year={2017},
  doi={10.1007/s12469-016-0151-x}}

@article{burghout2005hybrid,
  author={Burghout, Wilco and Koutsopoulos, Haris N. and Andr{\'e}asson, Ingmar},
  title={Hybrid Mesoscopic--Microscopic Traffic Simulation},
  journal={Transportation Research Record}, volume={1934}, pages={218--225}, year={2005},
  doi={10.1177/0361198105193400123}}

@misc{morvan2013multilevel,
  author={Morvan, Gildas},
  title={Multi-level agent-based modeling -- A literature survey},
  year={2013}, eprint={1205.0561}, archivePrefix={arXiv}, primaryClass={cs.MA}}

@article{zhang2016ddabm,
  author={Zhang, Haifeng and Vorobeychik, Yevgeniy and Letchford, Joshua and Lakkaraju, Kiran},
  title={Data-driven agent-based modeling, with application to rooftop solar adoption},
  journal={Autonomous Agents and Multi-Agent Systems}, volume={30}, number={6}, pages={1023--1049}, year={2016},
  doi={10.1007/s10458-016-9326-8}}

@inproceedings{kavak2018ddabm,
  author={Kavak, Hamdi and Padilla, Jose J. and Lynch, Christopher J. and Diallo, Saikou Y.},
  title={Big data, agents, and machine learning: towards a data-driven agent-based modeling approach},
  booktitle={Proceedings of the Annual Simulation Symposium (ANSS '18)}, pages={1--12}, year={2018}}

@incollection{crooks2018bigdata,
  author={Crooks, Andrew and Malleson, Nick and Wise, Sarah and Heppenstall, Alison},
  title={Big Data, Agents and the City},
  booktitle={Big Data for Regional Science}, editor={Schintler, Laurie A. and Chen, Zhenhua},
  publisher={Routledge}, year={2018}, note={Pages and DOI not verified}}

@article{wooldridge1995agents,
  author={Wooldridge, Michael and Jennings, Nicholas R.},
  title={Intelligent agents: theory and practice},
  journal={The Knowledge Engineering Review}, volume={10}, number={2}, pages={115--152}, year={1995},
  doi={10.1017/S0269888900008122}}

@inproceedings{rao1995bdi,
  author={Rao, Anand S. and Georgeff, Michael P.},
  title={{BDI} agents: from theory to practice},
  booktitle={Proceedings of the First International Conference on Multi-Agent Systems (ICMAS-95)},
  pages={312--319}, publisher={AAAI Press}, address={San Francisco}, year={1995}}

@book{russell2021aima,
  author={Russell, Stuart and Norvig, Peter},
  title={Artificial Intelligence: A Modern Approach}, edition={4},
  publisher={Pearson}, year={2021}, note={Edition/year not tool-verified}}

@article{brooks1986robust,
  author={Brooks, Rodney A.},
  title={A robust layered control system for a mobile robot},
  journal={IEEE Journal on Robotics and Automation}, volume={2}, number={1}, pages={14--23}, year={1986},
  doi={10.1109/JRA.1986.1087032}, note={Not tool-verified in this search}}

@book{ferber1999mas,
  author={Ferber, Jacques},
  title={Multi-Agent Systems: An Introduction to Distributed Artificial Intelligence},
  publisher={Addison-Wesley}, year={1999}}

@article{taillandier2019gama,
  author={Taillandier, Patrick and Gaudou, Benoit and Grignard, Arnaud and Huynh, Quang-Nghi and Marilleau, Nicolas and Caillou, Philippe and Philippon, Damien and Drogoul, Alexis},
  title={Building, composing and experimenting complex spatial models with the {GAMA} platform},
  journal={GeoInformatica}, volume={23}, pages={299--322}, year={2019},
  doi={10.1007/s10707-018-00339-6}}

@article{saval2023traffic,
  author={Saval, A. and Minh, D. P. and Chapuis, Kevin and Tranouez, Pierrick and Caron, Clement and Daud{\'e}, {\'E}ric and Taillandier, Patrick},
  title={Dealing with mixed and non-normative traffic. An agent-based simulation with the {GAMA} platform},
  journal={PLOS ONE}, volume={18}, number={3}, pages={e0281658}, year={2023},
  doi={10.1371/journal.pone.0281658}}

@article{carbo2023trust,
  author={Carb{\'o}, Javier and Molina, Jos{\'e} M.},
  title={Trust Model of Privacy-Concerned, Emotionally Aware Agents in a Cooperative Logistics Problem},
  journal={Applied Sciences}, volume={13}, number={15}, pages={8681}, year={2023},
  doi={10.3390/app13158681}}

@article{carbo2026irrigation,
  author={Carbo, Javier and Zubelzu, Sergio and Molina, Jos{\'e} M.},
  title={An agents-based tool for simulating farmers operation in irrigation districts},
  journal={Computers and Electronics in Agriculture}, volume={245}, pages={111518}, year={2026},
  doi={10.1016/j.compag.2026.111518}}

@article{carbo2018netlogo,
  author={Carbo, Javier and Sanchez-Pi, Nayat and Molina, Jos{\'e} M.},
  title={Agent-based simulation with {NetLogo} to evaluate ambient intelligence scenarios},
  journal={Journal of Simulation}, volume={12}, number={1}, pages={42--52}, year={2018},
  doi={10.1057/jos.2016.10}}
```