# Goel et al. 2026, BayesBeliefAgent (arXiv 2608.18490), read in full for version b

Read 2026-10-08 (HTML v1, body and appendices §7 to §11.6; the Hypothetical Minds prompt of §10.2 skimmed).
Goel, Ellendula, Tadiparthi, Moradi Pari, Nourkhiz Mahjoub, Chinchali (UT Austin, Honda Research Institute).

- **Belief**: a categorical distribution over the partner's current skill (six roles in the Burrito
  domain), add-alpha prior (alpha = 1), likelihood of the partner's last 10 primitive actions under the
  ego agent's own low-level controller, recursive Bayes update, prior reset when a skill completes.
- **Shown and used**: the posterior is shown to the LLM as text (MAP role, confidence, bars, a hint of
  complementary roles) and gates *when* code interrupts for a replan (likelihood under the old MAP
  < 0.04, MAP stable 3 updates, confidence >= 0.65, mid-skill, 6-step cooldown). The LLM always chooses
  *which* skill; code never computes the action.
- **Setting**: Burrito-AI (Overcooked), three layouts, 12 learned PPO partners (stochastic, policy unknown
  to the agent), GPT-4o (and GPT-5.2 as a check) at temperature 0, 20 episodes per layout and group.
- **Belief-action gap**: among decision points where the partner-skill estimate is correct, the share
  where the agent picks a non-complementary skill (fixed lookup table of complements). BayesBeliefAgent
  0.20 / 0.28 / 0.42 against ProAgent 0.41 / 0.38 / 0.47 (Open / Ring / Forced Coordination).
- **Ablations**: Full (shown + gated) > No prompt (gated only) > No replan (shown only, the LLM decides)
  > No belief, in most settings (Open G1 reward 1533 / 1405 / 1190 / 1080). Their conclusion: coupling
  the belief to replanning works better than relying on the planner to translate the belief.
- **Not done there**: scoring free-text beliefs against a known policy; checking whether the LLM's
  stated belief agrees with the posterior shown; small or local models; code choosing the action;
  evidence from communication (asks that go unanswered).

**For hoshi7.** b1 (belief shown, the model decides) is their "No replan" condition, on a different
kind of belief (one disposition of a scripted partner, from unanswered asks) and with cheaper models;
their result predicts it gains less than a gated arm. What is new here: the partner's policy known
exactly, free-text notes scored for truth, the agreement between the note and the posterior shown,
small models, and an arm where code decides.
