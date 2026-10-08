# hoshi7 strategy

Why this project exists, what it is trying to learn, and in what order.
The contracts and rules live in [SPEC.md](SPEC.md), the measures in
[results.md](results.md); this file is the why and the when.

## The idea

AI agents arrive in a small world with nothing. They farm, gather, craft and
talk, one in-game hour at a time, toward a goal the world states. There is one
watering can for everyone, so they have to cooperate. Every action is an event
in a log that replays alone, and the world knows the truth at every tick: what
an agent believes about its partner and about the rules can be checked against
it.

Later, the world ends and a new one begins, in another plane, with another
goal. The world forgets; the agents remember. What they carry over, and how
they learn to work together, is the long-term question.

Three influences, each for one thing:

- **Stardew Valley** (ConcernedApe, 2016): the daily life. Days cut into
  hours, crops that grow on watered days, a shared field, relations built by
  what you do for each other.
- **Outer Wilds** (Mobius Digital, 2019): the loop. The world resets; only
  knowledge survives, and knowledge is the only progression.
- **Planescape: Torment** (Black Isle, 1999): the planes and the memory. A
  being who dies and starts again and rebuilds itself from what it recovers;
  worlds as planes joined by a hub.

Three planes so far, one per aesthetic pole: **cyber** (a rooftop above a
city), **Belle Epoque** (a glass and cast-iron conservatory), **space** (a
greenhouse dome on an asteroid). The engine is the same; a plane is a file.
The runs so far play on the rooftop.

No asset, name or text is taken from those games. "Stardew-like" describes;
it does not borrow.

## What is new here, and what is not

Agents living in a small simulated world are not new:

- Generative Agents (Park et al., 2023): 25 agents in "Smallville", memory,
  reflection and planning.
- AI Town (a16z): the open, playable version of Smallville, in pixel art.
- Voyager (Wang et al., NVIDIA, 2023): one agent in Minecraft, a growing
  skill library.
- Project Sid (Altera, 2024): hundreds of agents in Minecraft, roles and
  rules emerging.

What this project adds today:

1. **Beliefs checked against the truth.** The partners can be scripted bots
   whose policy is known exactly, and each hour an agent can write a private
   note of what it believes about its partner and about the world's rules.
   Every belief can be scored true or false, turn by turn, which a world of
   LLM agents alone cannot offer.
2. **A measurable, replayable world.** The world is event-sourced: a run's log
   replays alone, the true state is known at every tick, every refusal of the
   world is recorded, and the percept an agent received can be rebuilt from
   the log.

What it will add next:

3. **Governed actions.** Every action will be a tool call through flux7-mesh
   (mesh7, a policy proxy for agents' tool calls): a policy is a law of the
   world, it can differ per agent, and the traces are the world's history.
4. **Governed memory with continuity across worlds.** flux7-memory (mem7) will
   hold each agent's memory, scoped by the identity the mesh vouches for: an
   agent reads its own memory and the shared world's, never another agent's.
   The bi-temporal store answers "what did this agent know at hour 40"; the
   hash chain proves the history was not rewritten.
5. **The loop as the experiment.** The world will change plane and goal
   between runs while memory persists; the question is what transfers, false
   beliefs included.

## What we want to learn

1. **Can an LLM agent play a clear goal with a partner at all?** Answered on
   the rooftop (gate 1): Claude Sonnet 5.5 plays at the scripted bots' level,
   Claude Haiku 4.5 harvests about half as much, the local models tried fail
   (gpt-oss 20b already alone; Mistral Small 3.2 as soon as it must reason
   about its partner). The difficulty is the partner, not the farming.
2. **What does an agent believe about its partner and about the world, are
   those beliefs true, and how do they shape what it does?** The private note
   gives the first answers (Sonnet infers the bot's policy, Haiku attributes
   intentions to it and holds superstitious rules, Mistral does not model it);
   the next step is to count them, and to see when a belief forms and whether
   a refusal corrects it.
3. **Does the persona change what an agent decides, or only how it speaks?**
4. **Do agents discover rules and places that are not given to them?** The
   `--pure` version removes what hands the rules over; the counter-intuitive
   test world (moss that grows on dry days) separates discovery from prior
   knowledge.
5. **Does anything carry over from one loop to the next**: conventions, roles,
   trust, knowledge of the lore, and false beliefs?

### Who decides and who speaks (question 3)

An LLM agent playing a character mixes two things: the character colors its
choices as well as its words. A hybrid brain separates them: the model picks
an intention and code carries it out, or the decision is computed from an
explicit belief, and the persona is a voice. The voice is not cosmetic: what a
persona says moves its partner's belief, so the character reaches the outcome
through one measurable channel, speech.

Design: brain (LLM alone, hybrid) crossed with persona (contrasted characters:
VESPER, a cold strategist; LEDGER-7, a support unit; MOTE, a curious one),
same worlds, same seeds, and the private note in every arm.

- **H1**: with an LLM alone, the persona changes the outcome (harvest,
  refusals, cooperation): character biases decision.
- **H2**: with the hybrid, the persona's effect shrinks to the speech
  channel: clarity of commitments, the partner's trust.

H2 is a hypothesis to measure, not a property of the architecture. Run-to-run
variance of LLM agents sets how many runs each cell needs, and so the cost.

For two agents with partial observation the problem is a Dec-POMDP,
NEXP-complete in general (Bernstein et al., 2002): there is no exact oracle,
only reference brains: the scripted bots, the LLM alone, the hybrid.

### What survives a loop: memory as reconstruction (question 5)

Three results from the study of human memory frame what an agent keeps:

- **Bartlett (1932, *Remembering*)** had English students retell a Native
  American tale, *The War of the Ghosts*, several times over weeks, and
  measured what each retelling changed: the story shortened, the strange
  dropped out, details shifted toward the students' own culture (canoes
  became boats). Remembering is reconstruction from one's schemas, not the
  reading of a trace; serial reproduction, one person retelling to the next,
  drifts the same way.
- **Conway and Pleydell-Pearce (2000, *Psychological Review*)**, the
  self-memory system: autobiographical memory answers to correspondence
  (faithful to what happened) and to coherence (consistent with who one is
  and what one wants); the working self filters what is encoded and
  recalled, and over time coherence tends to win.
- **Nader, Schafe and LeDoux (2000, *Nature*)**, in rats: a recalled memory
  becomes labile and is stored again, possibly changed. To recall is to
  rewrite a little.

hoshi7 can give each agent the same two layers: **episodes**, faithful and
perishable (correspondence), and a **journal** written in the persona's own
voice from them, which survives the loop (coherence). Each new journal is
written with the earlier ones in mind, a form of reconsolidation. When the
world restarts, only the journal carries over.

What the human studies lack and hoshi7 has is the original: the event log
is exact ground truth. Bartlett had to infer the drift; here it is measured.

- **Distortion**: distance between an agent's journal and the log, per agent,
  per loop.
- **Divergence**: distance between two agents' memories of the same event
  ("B forgot to water" against "the drought").
- **Transmission**: `say` passes a memory from one agent to another, who
  rebuilds it; across loops this is Bartlett's serial reproduction between
  agents. Does a useful convention survive the chain? Does a false belief?

- **H3**: what carries over between loops, and how well two agents cooperate
  in the next one, depends on how each reconstructs memory, not on character
  alone. Divergence on shared events predicts broken cooperation; or,
  counter-intuitively, biased but compatible memories cooperate better than
  accurate ones.

A check on the bridge: an LLM summarizing its episodes is not a human
reconstructing a memory. The correspondence is of form (two layers, a summary
written by a biased writer, rewritten on recall), not an identity of
mechanism; the human results suggest what to measure, they predict nothing
here.

## The frame: AI in video games

The study speaks beyond this world, to how AI is built into games.

Game AI has long separated decision from expression: finite state machines,
behavior trees, GOAP (F.E.A.R., Orkin, "Three States and a Plan", GDC 2006),
utility AI and HTN decide; written dialogue and barks, triggered by the
decision, speak. Interactive drama tried to go further (Facade, Mateas and
Stern, 2005; Versu, Evans and Short). Since 2023, LLM-driven NPCs arrive
(Inworld, NVIDIA ACE, Ubisoft's NEO NPC shown at GDC 2024, many mods), and
with them four tensions:

1. **Designer control**: the NPC may do or say anything, leave the lore,
   break a quest.
2. **Consistency**: it forgets, contradicts itself, reveals what it should
   not know.
3. **Cost and latency**: inference paid for every line, on a server.
4. **Testability**: a non-deterministic behavior can be neither tested nor
   replayed.

How this stack answers each, and the measure that checks it in hoshi7:

| Tension | Answer | Measure |
| --- | --- | --- |
| Control | mesh7 policy (planned): what an NPC may do is a rule enforced on every action, traced | actions refused by policy; actions outside the rules that got through (must be 0) |
| Consistency | mem7 scopes (planned): an NPC knows only what it lived or the world showed it; bi-temporal reads | information leaks across scopes (must be 0); contradictions with the agent's own log |
| Cost | a hybrid brain: the decision computed or executed by code, the LLM reads and speaks; prompt caching | tokens, dollars and seconds per in-game hour, per brain |
| Testability | event-sourced world, recorded turns, percepts rebuilt from the log | a run replayed from its log gives the same state; scripted runs are bit-identical |

What is not new: a computed decision (GOAP has done it for twenty years), a
generated voice. What may be new, to be checked against the state of the art
before any claim: **the LLM as a reliable sensor of free language** feeding a
belief that keeps the decision in the designer's hands. A player, or another
NPC, says a sentence; a small judging model turns it into a commitment with a
probability; the belief updates; the behavior stays governed. Current LLM NPCs
lack exactly this: understanding free speech without handing over control.

## Rules of honesty

- Measures are fixed before the runs they judge. Without them, "watching
  them evolve" means reading transcripts and projecting meaning onto them.
- A null result is a result.
- Every bridge to theory is checked: an identity, a precise correspondence,
  or only a resemblance of form? Corrections are made visibly.
- The scripted bots are the floor and the scale, not the opponent.
- The harness is part of the measure. A change to what the agents see makes
  earlier runs incomparable: they are archived, or shown unchanged by replay.

## Roadmap, with gates

Each step ends on something run and measured. A gate decides whether the next
step is worth its cost.

| Step | Content | State |
| --- | --- | --- |
| Engine | event-sourced world, three planes, action catalog, percept, scripted brains, runner, calibration | done |
| LLM brains | Ollama and Claude brains, harness stages, options (`present`, `coords`, `seen`, `note`, `pure`), viewer | done |
| Gate 1: capacity | each model with a fixed scripted partner and with itself | done (results.md) |
| Gate 2: hybrid | the model picks an intention, code carries it out: does a cheaper model play once execution is taken from it? Closes on G2-H1 to H3 and amendments 1 to 3; G2-X5 (counted facts from mem7) moves to the first loop | next |
| Gate 3: beliefs | the private note scored against the bots' policies and the world's rules, turn by turn, with a rubric fixed before scoring (beliefs-rubric.md): true, false, unverifiable; when a belief forms; whether a refusal corrects it | planned, before any loop |
| Gate 4: first loop | two agents, episodes and a journal in mem7 (scoped per agent, no mesh7), a second world after the first; transfer against agents without memory; distortion and divergence measured against the log (H3) | planned |
| Gate 5: persona | VESPER, LEDGER-7, MOTE crossed with LLM alone and hybrid (H1, H2); a bot that hands the can over on request makes negotiation measurable | planned |
| Gate 6: discovery | `--pure` and `--with seen`, on the rooftop and the counter-intuitive world | planned |
| Governed world | the world as an MCP server behind mesh7; one identity per agent; policies as laws of the world | when a loop is worth governing, or a mesh7 demonstration needs it |
| Loops | the same agents across planes and goals, at length | planned |

**Why this order (2026-10-08).** The long-term question is what carries over
between worlds (question 5); the earlier order put it behind persona and
discovery, which it does not depend on. It depends on two things only: a model
that plays on a correct harness (gate 2), and beliefs that can be scored, since
a false belief cannot be seen to carry over before it can be seen to be false
(gate 3). Persona and discovery come after, and use the same scoring. Serving
the world through mesh7 is infrastructure, not a question: memory continuity
is tested with mem7 alone.

**A ceiling to lift before gates 4 to 6.** Six days allow one crop cycle, so
the harvest saturates (amendment 2 of gate 2). Later gates need longer runs or
another outcome measure, chosen before their runs.

A human can play as well as watch: a human is one more identity, and a
`human` brain one more brain. Nothing in the engine may assume an LLM behind
an agent.

## Risks

- **Long-loop degradation**: repetition, lost goals, waiting forever. Measured
  as repeated refusals per run, never broken by the harness.
- **Malformed actions**: constrained JSON, `wait` when the answer is invalid,
  a missing parameter named in the refusal (it is data).
- **A biased harness**: what the agents see is part of the measure; a defect
  there biases every result (one did, until 2026-10-06).
- **Cost**: the model that plays well is a paid one; prompt caching, the
  hybrid and local models for long series keep it in check.
- **Scope**: a Stardew-like game client is years of work for one person
  (Stardew took four and a half). The client stays a viewer until the
  agents give something worth watching.
