# hoshi7 strategy

Why this project exists, what it is trying to learn, and in what order.
The contracts and rules live in [SPEC.md](SPEC.md); this file is the why and
the when. Both are the common brief every working session starts from.

## The idea

AI personas arrive in a small world with nothing. They farm, gather, craft,
trade and talk, one in-game hour at a time, toward a goal the world states.
Then the world ends, and a new one begins, in another plane, with another
goal. The world forgets; the personas remember. What they carried over, and
how they learned to work together, is what we watch and measure.

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

What this project adds, and only this:

1. **Governed actions.** Every action is a tool call through flux7-mesh. The
   mesh traces are the world's history; a policy is a law of the world, and
   can differ per agent. A human approval can stand for a god who decides.
2. **Governed memory with continuity across worlds.** flux7-memory holds each
   persona's memory, scoped by the identity the mesh vouches for: an agent
   reads its own memory and the shared world's, never another agent's. The
   bi-temporal store answers "what did Ada know at hour 40"; the hash chain
   proves the history was not rewritten.
3. **The loop as the experiment.** The world changes plane and goal between
   runs; memory persists. The question is what transfers.
4. **A measurable world.** The true state is known at every tick, which
   turns "does the agent understand its world" into a calibration score.

## What we want to learn

1. Can LLM personas play a clear goal at all, in a long loop, with a small
   local model? (The gate; see Roadmap.)
2. Do two personas cooperate when the goal requires it, and how: dividing
   the work, sharing the one can, keeping promises?
3. Does anything carry over from one loop to the next: conventions, roles,
   trust, knowledge of the lore?
4. Does an agent with an explicit belief do better than an LLM alone?
5. Does the persona change what an agent decides, or only how it speaks?

Question 4 joins Marc's research on LLM agents with an explicit Bayesian
belief (a separate study): the LLM, or Jev, as a sensor of
likelihoods, the belief as a projection of an event log, the choice and the
stop computed. Here that becomes:

- **Partial sight**: an agent sees 5 tiles and hears 6; what it believes
  about the rest is a belief, and the world knows the truth.
- **Trust**: Jev classifies a sentence (`Said`) into a commitment ("I will
  water the east row before noon"); the log says whether it was kept; trust
  in a partner is a Beta(kept, broken) computed from events, not an
  impression of the LLM. It extends the rumor experiment, with sources whose
  reliability can be observed.
- **Explore or exploit**: examining lore (knowledge for a future loop)
  against farming now is a value-of-information choice. Whether the least
  action formalism fits it is an open question, not a claim.

A limit to keep in view: for one agent in a small world an exact optimum can
be computed (as in experiment 1 of the Bayes study). For two agents with
partial observation the problem is a Dec-POMDP, NEXP-complete in general
(Bernstein et al., 2002). There will be no exact oracle, only reference
brains: the scripted bots, the LLM alone, the hybrid.

### Who decides and who speaks (question 5)

An LLM agent playing a character mixes two things: the character colors its
choices as well as its words. The hybrid separates them: the decision is
computed, the persona is a voice. In hoshi7 the voice is not cosmetic: what a
persona says moves its partner's belief (a commitment read by Jev, trust
computed from kept promises), so the character reaches the outcome through
one measurable channel, speech.

Design: brain (LLM alone, hybrid) crossed with persona (two to four
contrasted characters, from avatar7), same worlds, same seeds.

- **H1**: with an LLM alone, the persona changes the outcome (harvest,
  refusals, cooperation): character biases decision.
- **H2**: with the hybrid, the persona's effect shrinks to the speech
  channel: clarity of commitments, the partner's trust.

H2 is a hypothesis to measure, not a property of the architecture: the
hybrid still consumes Jev's readings, and a persona's style may sway them.
Run-to-run variance of LLM agents (seen in the Bayes study) sets how many
runs each cell needs, and so the cost.

### What survives a loop: memory as reconstruction (question 3)

Three results from the study of human memory frame what a persona keeps:

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

hoshi7 can give each persona the same two layers: **episodes**, faithful and
perishable (correspondence), and a **journal** written in the persona's own
voice from them, which survives the loop (coherence). Each new journal is
written with the earlier ones in mind, a form of reconsolidation. When the
world restarts, only the journal carries over.

What the human studies lack and hoshi7 has is the original: the event log
is exact ground truth. Bartlett had to infer the drift; here it is measured.

- **Distortion**: distance between a persona's journal and the log, per
  persona, per loop.
- **Divergence**: distance between two personas' memories of the same event
  ("B forgot to water" against "the drought").
- **Transmission**: `say` passes a memory from one persona to another, who
  rebuilds it; across loops this is Bartlett's serial reproduction between
  agents. Does a useful convention survive the chain?

- **H3**: what carries over between loops, and how well two personas
  cooperate in the next one, depends on how each reconstructs memory, not
  on character alone. Divergence on shared events predicts broken
  cooperation; or, counter-intuitively, biased but compatible memories
  cooperate better than accurate ones.

The trust of question 4, Beta(kept, broken), would then be fed by remembered
events as well as logged ones: the gap between the two is itself a measure.

A check on the bridge: an LLM summarizing its episodes is not a human
reconstructing a memory. The correspondence is of form (two layers, a
summary written by a biased writer, rewritten on recall), not an identity of
mechanism; the human results suggest what to measure, they predict nothing
here.

First rehearsal, outside the game: avatar7's personas already keep episodes
(30 days) and journals in a mem7 of their own (`mem7-play`), each reading
only its own memory. Their first journals interpret as much as they record;
whether that deepens or caricatures over weeks, and whether a contradicting
fact is integrated or bent to fit, is the small version of H3.

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
| Control | mesh7 policy: what an NPC may do is a rule enforced on every action, traced | actions refused by policy; actions outside the rules that got through (must be 0) |
| Consistency | mem7 scopes: an NPC knows only what it lived or the world showed it; bi-temporal reads | information leaks across scopes (must be 0); contradictions with the agent's own log |
| Cost | local model; the decision is computed, the LLM only reads and speaks | tokens and seconds per in-game hour, per brain |
| Testability | event-sourced world, recorded turns, percepts rebuilt from the log | a run replayed from its log gives the same state; scripted runs are bit-identical |

What is not new: a computed decision (GOAP has done it for twenty years), a
generated voice. What may be new, to be checked against the state of the
art before any claim: **the LLM as a reliable sensor of free language**
feeding a belief that keeps the decision in the designer's hands. A player,
or another NPC, says a sentence; Jev turns it into a commitment with a
probability; the belief updates; the behavior stays governed. Current LLM
NPCs lack exactly this: understanding free speech without handing over
control.

A public write-up of this frame carries Marc's voice: it is written by him
(inverse loop), not drafted for him.

## Rules of honesty

- Measures are fixed before the runs they judge. Without them, "watching
  them evolve" means reading transcripts and projecting meaning onto them.
- A null result is a result.
- Every bridge to theory is checked: an identity, a precise correspondence,
  or only a resemblance of form? Corrections are made visibly.
- The scripted bots are the floor and the scale, not the opponent.

## Roadmap, with gates

Each phase ends on something run and measured. A gate decides whether the
next phase is worth its cost.

| Phase | Content | Done when | Where |
| --- | --- | --- | --- |
| 1 | World engine: event-sourced, three planes | tests pass, log replays | done |
| 1b | Playable loop: action catalog, percept, brains, runner, calibration | one scripted agent loses, a scripted pair wins, references recorded | done |
| 0 | Infra on void: mem7 token and scopes, `memory` upstream over streamable HTTP with `forward_identity`, one mesh7 identity per persona | a scoped read is refused across agents | void |
| 2 | The world as an MCP server behind mesh7; actions as tools, traces as history | a scripted brain plays through the mesh | void |
| 3 | One LLM persona (Ollama, `gpt-oss:20b`) | **Gate A**: completes a farming cycle coherently in one in-game day; otherwise change model, add Haiku at key moments, or structure the agent | void |
| 4 | Two personas, private and shared memory | a run with both, measures written | void |
| 5 | Loops: the same pair across planes and goals | transfer measures compared with a pair without memory | void |
| 6 | Research arms: LLM alone, hybrid (belief + Jev + value of information), scripted; crossed with personas (question 5); the four game-AI measures | the comparison table, with the Bayes study's protocol | void |
| 7 | Presentation, layer 1: a flux7-mods mod replays a run with the personas' faces, lines and Piper voices, as in avatar7 | a run watched end to end | flux7-mods |
| 8 | Presentation, layer 2: animation (web with Phaser or PixiJS in TypeScript, or Godot) on the same event contract | only after a result worth watching | later |

Marc can play as well as watch: a human is one more identity in the mesh,
and a `human` brain is one more brain. Nothing in the engine may assume an
LLM behind an agent.

## Risks

- **Long-loop degradation**: repetition, lost goals, waiting forever. Gate A
  is there for it.
- **Malformed actions** from a small model: constrained JSON, `wait` when
  the answer is invalid, and the refusal is logged (it is data).
- **Memory reset**: continuity is the point, starting over must stay
  possible. One identity per lineage (`ada-1`, `ada-2`).
- **Scope**: a Stardew-like game client is years of work for one person
  (Stardew took four and a half). The client stays a viewer until the
  agents give something worth watching.
