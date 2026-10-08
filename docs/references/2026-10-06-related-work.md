# Related work, 2026-10-06: partner models, private beliefs, non-events, hybrids

Gathered by a documentalist agent on 2026-10-06 for gate 2 and its amendment 1. Complements
`docs/related-work.md` (2026-10-05: Crafter, SPRING, Voyager, StarDojo, governance, memory), which is
not repeated here.

**Method and limits.** Every arXiv id below was resolved through the arXiv API (title, authors, date
and abstract checked); links are `https://arxiv.org/abs/<id>`. Full text (arXiv HTML) was read in part
for 2608.18490, 2607.13618, 2605.00226, 2608.24691, 2609.05279 and 2606.16613; the rest is abstract
only. Venues are given when the arXiv comment or a publisher page states them; "venue not checked"
otherwise. Search: arXiv API keyword queries and a local SearXNG (Google CSE, Mojeek; DuckDuckGo,
Brave, Qwant and Startpage were blocked), so recall on blogs and non-arXiv venues is weak. "Not found"
means not found by these queries, not "does not exist".

Closeness to hoshi7 is judged on four features: (P) a partner whose policy is fixed and known to the
experimenter, (B) the LLM's stated beliefs scored against ground truth, (S) a decision / execution
split with a random floor, (N) belief update from a non-event.

## 1. LLM agents with fixed, scripted or unseen partners

| paper | measures | closeness |
| --- | --- | --- |
| Carroll et al. 2019, *On the Utility of Learning about Humans for Human-AI Coordination*, NeurIPS 2019, [1910.05789](https://arxiv.org/abs/1910.05789) | Overcooked-AI; self-play agents fail with a fixed human model, a planner given the exact partner model succeeds | Partial (P): the origin of "the partner is the difficulty"; no LLM, no beliefs |
| Zhang et al. 2023, *ProAgent*, AAAI 2024, [2308.11339](https://arxiv.org/abs/2308.11339) | LLM infers teammate intention in Overcooked, belief correction against observed acts | Partial (P, B as a module): beliefs are a component, not scored against the true policy; partners are RL agents |
| Agashe et al. 2023, *LLM-Coordination*, Findings of NAACL 2025 ([ACL Anthology](https://aclanthology.org/2025.findings-naacl.448/)), [2310.03903](https://arxiv.org/abs/2310.03903) | Agentic coordination in 4 games + CoordQA (environment, ToM, joint planning) | Partial: LLMs good when the environment decides, weak when the partner's intentions matter; same finding as hoshi7 gate 1, without a known-policy partner |
| Liu et al. 2023, *HLA*, AAMAS 2024, [2312.15224](https://arxiv.org/abs/2312.15224) | Hierarchical agent: slow LLM for intention, fast mind for macro-actions, human-AI Overcooked | Partial (S): decision / execution split, latency-motivated; no random-intention floor found |
| Sun et al. 2025, *Collab-Overcooked*, EMNLP 2025, [2502.20073](https://arxiv.org/abs/2502.20073) | 13 LLMs, process metrics of collaboration via language | Different: LLM-LLM, no known partner policy |
| Liang et al. 2025, *LLM-Hanabi*, EMNLP 2025 Wordplay workshop, [2510.04980](https://arxiv.org/abs/2510.04980) | ToM scored from rationales, correlated with game score; first-order ToM matters most | Partial (B): rationales scored automatically, but the partner is another LLM, so no exact ground truth |
| Ramesh et al. 2026, *Sparks of Cooperative Reasoning: LLMs as Strategic Hanabi Agents*, [2601.18077](https://arxiv.org/abs/2601.18077), venue not checked | 17 LLMs, three scaffolds (minimal, Bayesian-style deductions, working memory) | Partial: scaffold ablation by model scale, like gate 1's ladder |
| Mu et al. 2026, *Adaptive Theory of Mind for LLM-based Multi-Agent Coordination*, AAAI 2026, [2603.16264](https://arxiv.org/abs/2603.16264) | Agent estimates partner's ToM order; mismatched orders hurt | Different: ToM depth, not belief truth |
| Wallace et al. 2025, *ReCollab*, [2512.22129](https://arxiv.org/abs/2512.22129), venue not checked | LLM classifies partner *types* from trajectories (rubric), ad hoc teamwork in Overcooked | Close on (P, B): partner types are known, classification accuracy is scored; the belief is a forced label, not a free note |
| **Goel et al. 2026, *Bayesian Partner Modelling enables Adaptive Replanning for LLM Coordination* (BayesBeliefAgent), preprint, [2608.18490](https://arxiv.org/abs/2608.18490)** | Hierarchical LLM skill planner + Bayesian posterior over partner's skill; interrupts only on contradicting evidence; defines the **belief-action gap** (correct partner estimate, non-complementary skill) | **Closest on (P, S)**: skill library + low-level controllers is gate 2's intention hybrid; Bayesian partner tracking is amendment 1's Beta trust. Differences: partners are diverse but not scripted-and-known in hoshi7's sense, beliefs are a posterior not a free-text note, GPT-4o / GPT-5.2 only, no random-skill floor seen in the parts read, update is driven by *observed actions*, not by the absence of one |
| Gao et al. 2026, *Testing Interchangeability in LLM Agent Teams*, [2609.05279](https://arxiv.org/abs/2609.05279) | Each agent keeps a private notebook; swaps raise communication cost; **greedy decoding lowers drift between teams** | Partial: private notebooks and a temperature ablation, but notebooks are not scored for truth |
| Liu et al. 2024, [2406.12224](https://arxiv.org/abs/2406.12224); Shi et al. 2023, Avalon ad hoc teamwork, [2312.17515](https://arxiv.org/abs/2312.17515) | LLM ad hoc teamwork (heterogeneous robots; Avalon) | Different |
| Chang et al. 2024, *PARTNR*, [2411.00081](https://arxiv.org/abs/2411.00081) | Embodied human-robot planning benchmark | Different |

## 2. LLM societies and common-pool resources

| paper | measures | closeness |
| --- | --- | --- |
| Park et al. 2023, *Generative Agents*, UIST 2023, [2304.03442](https://arxiv.org/abs/2304.03442) | Believability of 25 agents with memory, reflection, planning | Different: no ground truth for beliefs; see 2026-10-05 digest |
| Vezhnevets et al. 2023, *Concordia*, [2312.03664](https://arxiv.org/abs/2312.03664) | Library for generative agent-based models with a game master | Partial: grounded actions via a game master, not belief scoring |
| Smith et al. 2025, *Concordia contest*, NeurIPS 2025 D&B, [2512.03318](https://arxiv.org/abs/2512.03318) | Zero-shot cooperation of submitted agents with diverse background partners | Partial (P): background populations, outcome scoring only |
| Agapiou et al. 2022, *Melting Pot 2.0*, [2211.13746](https://arxiv.org/abs/2211.13746) | Substrate + fixed background population; generalisation to novel partners | Partial (P): the canonical "focal agent vs fixed co-players" protocol, RL-oriented |
| Mosquera et al. 2024, [2403.11381](https://arxiv.org/abs/2403.11381) | LLM agents in Melting Pot (GPT-4, GPT-3.5) | Partial |
| Cross et al. 2024, *Hypothetical Minds*, ICLR 2025 (per OpenReview author profiles), [2407.07086](https://arxiv.org/abs/2407.07086) | ToM module writes natural-language hypotheses about other agents' strategies, keeps those that predict their behaviour; Melting Pot | **Close on (P, B)**: hypotheses in text about fixed-policy co-players, refined by prediction. Not scored against the true policy as an outcome of interest, no decision / execution split with floor |
| Chacon-Chamorro et al. 2025, [2512.11689](https://arxiv.org/abs/2512.11689) | Humans vs LLM agents in Melting Pot commons, with a **persistent unsustainable-consumption bot** | Partial (P): a scripted adverse bot, measured on group resilience, not beliefs |
| Piatti et al. 2024, *GovSim*, NeurIPS 2024, [2404.16698](https://arxiv.org/abs/2404.16698) | Sustainability of a shared resource; only the strongest LLMs survive (< 54 %) | Partial: capacity ladder like gate 1; all partners are LLMs |
| Curvo et al. 2025, GovSim reproducibility, [2505.09289](https://arxiv.org/abs/2505.09289) | Replication; small models fail without universalization | Partial |
| Rehm 2026, *GovSim-SelfGovern*, [2609.22600](https://arxiv.org/abs/2609.22600) | Agents write and vote executable laws | Different (relevant to mesh7 policies as laws, not to beliefs) |
| Lei et al. 2024, *FairMindSim / BREM*, KDD 2026, [2410.10398](https://arxiv.org/abs/2410.10398) | Belief evolution in repeated economic games, LLMs vs 1,017 humans | Partial (B): latent belief inferred by a model, not stated notes |

## 3. Declared vs revealed beliefs

| paper | measures | closeness |
| --- | --- | --- |
| Zhu, Zhang, Wang 2024, *Language Models Represent Beliefs of Self and Others*, [2402.18496](https://arxiv.org/abs/2402.18496), venue not checked | Linear probes decode self/other belief status; steering changes ToM answers | Different setting (static stories); relevant only if hoshi7 ever probes activations (local models) |
| Gu et al. 2024, *SimpleToM*, ICLR 2026, [2410.13648](https://arxiv.org/abs/2410.13648) | Explicit mental-state inference good, applied behaviour prediction poor | Partial: names the declared/applied gap, static stories |
| Riemer et al. 2024, *ToM Benchmarks are Broken*, ICML 2025 (position), [2412.19726](https://arxiv.org/abs/2412.19726) | **Literal ToM** (predict the partner) vs **functional ToM** (adapt to it in context) | Conceptual frame for hoshi7: the note measures literal ToM, the harvest and `ask_can` share measure functional ToM |
| **Sobotka, Karabag, Topcu 2026, *Why Do LLMs Struggle in Strategic Play? Broken Links Between Observations, Beliefs, and Actions*, [2605.00226](https://arxiv.org/abs/2605.00226)** | Against a **fixed opponent strategy** (repeated matrix games) and in Kuhn poker, Chameleon: internal (probed) beliefs more accurate than verbal ones; beliefs drift from Bayesian coherence over long play; belief-action gap | **Close on (P, B)**: fixed known opponent, stated beliefs vs ground truth, drift over turns. Differences: open-weight models only, matrix games not an embodied world, no hybrid, no non-event |
| **Joshi 2026, *Confident at the moment of action*, [2608.24691](https://arxiv.org/abs/2608.24691)** and *Replication Without Persistence*, [2609.22478](https://arxiv.org/abs/2609.22478) | Hidden-information chess: a stated distribution over the hidden piece elicited **every turn, separately from the move**, scored against ground truth; replication across batches | **Close on (B)**: per-turn private belief elicitation scored against an exactly logged hidden state; adversarial, not cooperative, no scripted partner |
| **Deb, Krishnan 2026, *STOCKTAKE*, [2607.13618](https://arxiv.org/abs/2607.13618)** | Supply-chain POMDP; fair oracle = exact Bayes filter on the agent's own observations; floor = symptom-blind policy; each week's **written rationale graded by an LLM** (gpt-5-mini, temperature 0, audited) gives detection lag and a knowing-doing rate; Claude Sonnet 5 "freezing" exhibit | **Closest methodologically on (B, S-floor)**: rationale graded against hidden truth, oracle and floor bracketing skill, detection lag = hoshi7's "first hour the note says the bot will not give". Differences: single agent, no partner, no intention hybrid |
| Li et al. 2026, *Mind or Message?*, [2609.24146](https://arxiv.org/abs/2609.24146) | Negotiations with known hidden preferences; counterfactual probes show agents read the message, not the mind; random acceptable package does as well | Partial (B, floor): ground-truth audit of ToM and a random comparator, LLM-LLM |
| Gao et al. 2026, Werewolf belief audit, [2607.10814](https://arxiv.org/abs/2607.10814) | External belief state, logged belief-action deviations | Partial: belief kept outside the model (like version b of the hybrid) |
| Yan et al. 2026, *Belief Without Behavior* (MOSAIC), [2608.20975](https://arxiv.org/abs/2608.20975) | ToM inference vs coordinated action in VLMs | Partial |
| Shaji et al. 2026, [2605.03855](https://arxiv.org/abs/2605.03855) | 2D collaborative game; **LLM judges detect collaborative behaviours** (ToM, perspective taking), agreement with humans fair to substantial | Partial: LLM-as-judge on agent traces, with human agreement reported (a model for validating hoshi7's rubric) |
| Gu, Wang, Han 2025, stated vs revealed preferences, [2506.00751](https://arxiv.org/abs/2506.00751); Geng et al. 2025, *Accumulating Context Changes the Beliefs of LMs*, [2511.01805](https://arxiv.org/abs/2511.01805) | Stated principles vs contextual choices; stated beliefs shift with context | Different setting, same distinction |

## 4. Non-events, loops, temperature, decision / execution splits

| paper | measures | closeness |
| --- | --- | --- |
| Fu et al. 2025, *AbsenceBench*, [2506.11440](https://arxiv.org/abs/2506.11440) | LLMs detect inserted information far better than omitted information (Claude 3.7 Sonnet 69.6 % F1); attributed to attention not attending to gaps | Partial (N): absence in static documents; hoshi7's "no Gave event" is the agentic, temporal version |
| Wang, Ward, Zhang 2026, reversal learning, IPMU 2026, [2604.04182](https://arxiv.org/abs/2604.04182) | Win-stay near ceiling, **lose-shift attenuated**: asymmetric use of negative evidence, perseveration after reversals | Partial (N): closest behavioural analogue of "ask 120 times", but losses are explicit outcomes there |
| **Gumaan 2026, *Feedback That Backfires*, [2608.23651](https://arxiv.org/abs/2608.23651)** | Small models (135M-1.7B): a failed call recorded in context *raises* the probability of repeating it (0.06 to 0.54); 83 % from the surface form; greedy decoding reproduces it | **Close on loops**, and in tension: there the failure *is* in context and backfires; in hoshi7 the ask leaves *no* record. The two conditions (failure shown vs non-event) are a clean contrast to run |
| Xu et al. 2022, *Learning to Break the Loop*, NeurIPS 2022, [2206.02369](https://arxiv.org/abs/2206.02369) | Sentence repetition self-reinforces under greedy-like decoding | Mechanism candidate for Mistral's 120 identical notes at temperature 0.15 (G2-X1) |
| Krishnamurthy et al. 2024, *Can LLMs explore in-context?*, NeurIPS 2024, [2403.15371](https://arxiv.org/abs/2403.15371) | Bandits: LLMs fail to explore unless history is summarised as sufficient statistics | Partial: supports giving the agent counts (asks, gives) rather than a raw journal |
| Schmied et al. 2025, *LLMs are Greedy Agents*, [2504.16078](https://arxiv.org/abs/2504.16078) | Greediness, **frequency bias** (repeating frequent actions), knowing-doing gap; RL fine-tuning narrows them | Partial: frequency bias matches the `ask_can` fixed point |
| Renze, Guven 2024, temperature, Findings of EMNLP 2024, [2402.05201](https://arxiv.org/abs/2402.05201) | Temperature 0 to 1 has no significant effect on MCQA accuracy | Tension: single-turn QA says temperature does not matter; multi-turn agent loops (2206.02369, 2609.05279) say it does. hoshi7's confound (0.15 vs 1.0) sits on that line |
| Xiong et al. 2026, evidence use and information seeking, [2607.26845](https://arxiv.org/abs/2607.26845); Sasso et al. 2025, NeurIPS 2025 workshop, [2509.19924](https://arxiv.org/abs/2509.19924) | Thinking does not produce directed exploration; knowing-doing gap in control, hybrid LLM-guided exploration | Partial |
| Ahn et al. 2022, *SayCan*, [2204.01691](https://arxiv.org/abs/2204.01691), venue not checked (CoRL 2022 by memory) | LLM scores skills, affordances gate feasibility | Partial (S): the ancestor of "LLM picks, skills execute"; infeasible-intention = affordance |
| Huang et al. 2022, *Inner Monologue*, [2207.05608](https://arxiv.org/abs/2207.05608); Shinn et al. 2023, *Reflexion*, [2303.11366](https://arxiv.org/abs/2303.11366) | Success-detection feedback in language; verbal reflection memory | Partial (N): both assume an explicit outcome signal; hoshi7's journal lacks one for `ask` |
| Nasiri et al. 2026, EPLA, [2609.29366](https://arxiv.org/abs/2609.29366) | LLM proposes typed actions, a symbolic guard executes against authoritative state | Partial (S), no empirical floor |
| Liu, Wang 2026, *HESP*, [2609.33446](https://arxiv.org/abs/2609.33446) | Controller holds the procedure outside the local LLM, ledger of explanations, probes by information gain, pre-registered | Closest prior of the linked Kafka study, already known |

A decision / execution split **scored against a random-choice floor over the same executor** was not
found in the LLM-agent papers read (SayCan, HLA, ProAgent, BayesBeliefAgent compare against other
agents, not against random skills). STOCKTAKE and Mind or Message use floors of a different kind
(symptom-blind policy; random acceptable package).

## 5. Long-horizon agent benchmarks (added on request)

| benchmark | measures | closeness |
| --- | --- | --- |
| Backlund, Petersson 2025, *Vending-Bench*, [2502.15840](https://arxiv.org/abs/2502.15840) | Running a vending machine over > 20M tokens; high variance, "meltdown" loops, failures not tied to context filling | Partial: long-horizon coherence and loops, single agent, no partner, no belief scoring |
| Andon Labs, *Vending-Bench 2* ([andonlabs.com/evals/vending-bench-2](https://andonlabs.com/evals/vending-bench-2); leaderboard [benchmarklist.com/benchmarks/vending_bench_2](https://benchmarklist.com/benchmarks/vending_bench_2)), not on arXiv | One simulated year, final bank balance from 500 $. Checked on both pages 2026-10-06: Claude Haiku 4.5 458.89 $ (5 runs), Sonnet 4.5 3,838.74 $ (5), Opus 5.5 9,235.25 $ (6, rank 8; leaders above 10,000 $) | Partial: the same capacity ladder as gate 1 (Haiku far below Sonnet), on a different task; vendor eval, outcome only |
| Sugiura et al. 2026, *CoffeeBench*, [2606.16613](https://arxiv.org/abs/2606.16613) | 90-day multi-firm economy; **the evaluated model plays one roaster, the other five firms are fixed reference agents**; passive no-action baseline; **Claude Haiku 4.5 "idle drift"**: about 40 of 90 days only `wait_for_next_day()`, negative net income | **Close on (P) and on a floor**: an LLM among fixed reference agents, scored against a do-nothing floor. No belief notes, no hybrid. Haiku's idle drift is worth setting beside its behaviour in hoshi7 |
| Fan et al. 2026, *E-Commerce Bench*, [2608.30730](https://arxiv.org/abs/2608.30730) | Year-long store operation, 18 models; **counterparts deterministic** (fixed demand model, negotiation kernel; LLM only verbalises) | Partial (P): deterministic counterpart whose words come from an LLM, the inverse of hoshi7's scripted bot with templated speech; no belief scoring |
| Shi et al. 2026, *MerchantBench*, [2607.28956](https://arxiv.org/abs/2607.28956) | 365-day e-commerce, delayed outcomes, long-term coherence | Partial: delayed feedback is a cousin of the non-event |
| Zhang et al. 2026, *RetailBench*, [2606.15862](https://arxiv.org/abs/2606.15862) (author comment: duplicate of 2603.16453) | 180-day supermarket POMDP against a privileged oracle; gaps from incomplete evidence acquisition | Partial: oracle, no floor, no partner |
| Chen, Wang, Qu 2026, *The Horizon Gap* (survey of 1,547 papers), [2608.06663](https://arxiv.org/abs/2608.06663) | Outcome-only signals become uninformative as horizons grow; the field answers with denser step-level signals | Frame: hoshi7's per-hour note and wasted-hour counts are such step-level signals; the coordinator's reading (open question separating model capability from system design) was not checked in the full text |
| Pu et al. 2026, *Explore More, Drift Less* (CANOPY), [2609.01245](https://arxiv.org/abs/2609.01245) | Outcome-only RL on AppWorld; signal starvation and policy drift | Different (training), relevant only if a local model is ever fine-tuned |
| Paglieri et al. 2024, *BALROG*, ICLR 2025, [2411.13543](https://arxiv.org/abs/2411.13543) | Agentic LLM/VLM on games (BabyAI to NetHack) | Partial, already in the 2026-10-05 digest |

## What combines several features

| work | P | B | S + floor | N |
| --- | --- | --- | --- | --- |
| BayesBeliefAgent (2608.18490) | partly (diverse partners) | posterior, not stated | split yes, floor not seen | no (contradiction by acts) |
| STOCKTAKE (2607.13618) | no partner | yes, LLM-graded rationale | oracle + floor, no LLM/executor split | detection lag |
| Sobotka et al. (2605.00226) | yes (fixed opponent) | verbal and probed | no | no |
| Hypothetical Minds (2407.07086) | yes (background bots) | hypotheses, scored by prediction | hierarchical, no floor | no |
| CoffeeBench (2606.16613) | yes (fixed reference firms) | no | passive floor | no |
| Joshi (2608.24691) | adversary | yes, per turn vs truth | no | no |
| hoshi7 gate 2 | yes, exact | free note, LLM-judged vs exact policy | intention hybrid + random intentions | "no Gave" |

**Not found:** a study with all four. Nearest pairs: BayesBeliefAgent (P, S), STOCKTAKE (B, floor),
Sobotka (P, B).

## Gaps that look real (within this search)

1. **Belief update from a non-event in an agentic setting.** AbsenceBench is static text; reversal
   learning and Feedback That Backfires use explicit outcomes. An ask that leaves no trace, measured
   with a Beta trust as reference, was not found.
2. **Free-text private notes scored against a partner whose policy is exact.** Closest: LLM-Hanabi
   (rationales, LLM partner), Joshi (adversary, probability not text), Hypothetical Minds (hypotheses
   not scored as an outcome).
3. **Intention hybrid against a random-intention floor over the same executor.** Not found.
4. **Temperature as a confound of belief revision in agents.** Partial evidence only (greedy loops,
   greedy lowers drift); a controlled test (G2-X1 to X3) was not found.

## Tensions to keep in mind

- *Feedback That Backfires* predicts that writing the refusal into the journal could make small models
  repeat more, not less; the natural fix for the non-event (show "the bot did not give") may backfire
  on Mistral. Worth measuring both.
- Renze and Guven find temperature irrelevant on QA; loop studies find it decisive in multi-turn
  generation. hoshi7's G2-X1 is on the multi-turn side.
- BayesBeliefAgent and STOCKTAKE both find the belief often right and the action wrong (belief-action /
  knowing-doing gap); hoshi7's Mistral shows the opposite failure first (the belief itself frozen).
  Haiku and Sonnet may show the known one.
