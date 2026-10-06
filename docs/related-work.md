# Related work (digest of 2026-10-05)

Literature digest gathered by a documentalist agent on 2026-10-05 evening, each reference checked through the arXiv API; full text read for Crafter, SPRING, SmartPlay, BALROG, Voyager, Generative Agents, ProAgent, MindAgent, LLM-Coordination, Project Sid, StarDojo, Too Good to be Bad, Zep; abstracts only for the others. Venues of SPRING, Voyager, MindAgent and LLM-Coordination not confirmed.

## What worked, and hoshi7 can take

1. **Navigation delegated to the engine.** Generative Agents (named place, path computed), ProAgent (controller with a path planner), MindAgent (`goto(agent, location)`), Voyager (Mineflayer primitives). StarDojo (Stardew Valley benchmark, ECCV 2026, arXiv 2507.07445) excludes its `navigate(name)` on purpose and tops at 12.7 % with GPT-4.1. hoshi7's `go` follows the dominant practice: a choice of abstraction level, to state as such.
2. **Space as structured text, not a drawn grid.** BALROG (ICLR 2025, 2411.13543), StarDojo, and maze studies of 2025-2026 (2604.10690: adjacency lists 80-86 % against a textual grid 16-34 %, Claude Haiku 4.5 among the models; 2502.16690: Cartesian coordinates best; 2510.20198: accuracy drops 42.7 % as grids grow).
3. **The recipe in context, organised by dependencies.** SPRING (2305.15486, GPT-4 on Crafter): without context, random level; the question DAG gives about +65 % over a flat list.
4. **Explain the failure to the agent.** Voyager's precise error messages, ProAgent's Verificator (without it 20 % success), BALROG's invalid-action feedback. hoshi7's outcome journal is this.
5. **Self-verification at the end of a task, and change sub-goal after N failures** (Voyager: self-verification is the most useful feedback; Project Sid: loops and propagated hallucinations).
6. **Model the partner explicitly.** ProAgent's Belief Correction (+20 points) compares the intention attributed to the partner with its acts; LLM-Coordination (2310.03903): theory of mind is the weak point.
7. **Memory retrieved by recency, importance and relevance, plus reflection** (Generative Agents, UIST 2023, 2304.03442); their failure modes: memory not retrieved, embellished or fabricated memories.
8. **A tandem for personas:** a base model for the voice, an instruct model for consistency (Kang et al. 2609.22607; Moon et al. 2601.16355: base models with a rich narrative biography reproduce identity behaviour better than instructed chat models).

## What no one has done (as far as this digest went)

- **Governing actions by a policy (mesh7) inside a multi-agent game world**, the policy as social physics (who may take the can). AgentSpec (ICSE 2026, 2503.18666) and Governance-as-a-Service (2508.18765) intercept agent actions with declarative rules, AgentSpec on embodied agents; none in a game world. ProAgent's Verificator checks feasibility, not authorisation.
- **Governed memory with provenance and two time axes in a simulated world.** Zep (2501.13956, vendor paper) is bi-temporal (valid and ingestion time, invalidated edges) for enterprise agents, without provenance chain nor scopes. None of Smallville, Sid or Voyager dates memories on two axes or traces their origin.
- **Persona x aligned or base brain on acts executed in an environment.** Covered for speech and for social-dilemma decisions without embodiment (Moon et al.), and for villains in text (Too Good to be Bad, 2511.04962: fidelity drops as the character becomes immoral, reasoning does not help). Nothing found on executed acts such as refusing the can: the observation of 2026-10-05 (VESPER keeps the can) sits in this gap.
- **Loops where only memory survives.** Voyager's skill library survives across worlds (code, not episodic memory); Generative Agents and Sid run continuously. Not found as an isolated regime (two queries only).

## Other references seen

Crafter (Hafner, ICLR 2022, 2109.06780); SmartPlay (ICLR 2024, 2310.01557: best Crafter score 0.32, spatial reasoning named as a gap); Project Sid (2411.00114: spatial reasoning their main limit; personalities shape the social graph, gifts guided by affinity); HLA (AAMAS 2024, 2312.15224); CoELA (ICLR 2024, 2307.02485); AI Town (a16z, GitHub); SPASM (ACL Findings 2026, 2604.09212, persona drift and echoing between two LLMs); ASCII read/write asymmetry (2604.14641).
