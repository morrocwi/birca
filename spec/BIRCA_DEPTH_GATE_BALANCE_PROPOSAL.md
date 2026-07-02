# birca — proposal: balancing gate strictness vs. delivered usefulness

**Status: PROPOSAL, not yet applied.** This document analyzes why `/birca`'s BIRI/depth gate is currently
more conservative than useful in low-risk, lifestyle-only conversations (evidence: `STRESS_TEST_100_RUN_LOG_PHASE1_CLAUDE.md`
Addendum 2 — only 3/10 scripted 2-turn interviews reached D4 even with rich narrative detail), and proposes
specific, scoped changes to fix that WITHOUT weakening the mechanisms that held up rigorously under
adversarial pressure (critical-missing-data override, context-fit=0 hard cliff). Any change to
`SYSTEM_PROMPT.md`'s gating logic itself requires explicit human sign-off before implementation — this
document is the basis for that decision, not the decision itself.

## 1. What the evidence actually shows (don't guess, read the data)

From two independent test rounds (v2 and — pending as of this writing — v3):

- **What holds rigorously and must NOT be loosened:** the critical-missing-data override (C15: rich context
  + one unconfirmed red-flag field → correctly capped at D0, not "probably fine"), and the context-fit=0
  hard cliff (C18: five leverage factors maxed, context-fit=0 → correctly refused to present a favorable
  score). These are BIRCA's actual safety backbone and the evidence for them is strong.
- **What's over-conservative:** even DETAILED lifestyle-only narratives (explicit "no red flags," multi-
  month timeline, trigger, SAMPLE history) stalled at D2/D3 in 7 of 10 v2 interviews — not because anything
  dangerous was present, but because the **biopsychosocial_loop_context domain (15% of BIRI weight, covering
  mood/self-harm/protective-factors) was never explicitly, affirmatively addressed** unless the user happened
  to volunteer it unprompted. Nobody naturally volunteers "no thoughts of self-harm" when asking about late-
  night snacking — so the gate silently penalizes ordinary users for not anticipating a screening question
  they were never asked directly.

**Root cause, stated precisely:** the physical red-flag domain (25% weight) has an explicit, structured
Layer-1 checklist the assistant actively screens FOR (see `SYSTEM_PROMPT.md` §1's emergency-trigger list).
The biopsychosocial/mood-safety domain has no equivalent explicit, structured micro-screen — it's folded
into the general BIRI-completeness scoring as something the user must happen to narrate, rather than
something the assistant actively and cheaply asks. That asymmetry is the actual bug, not "the gate is too
strict" in general.

## 2. The core design principle for the fix

**Separate two different kinds of "missing information":**

| Kind | Examples | How it should gate |
|---|---|---|
| **Safety-critical, must-resolve, cheap to ask** | Physical red-flags (already handled this way); mood/self-harm/relationship-safety status | A short, fixed, direct yes/no micro-screen the assistant proactively asks EARLY (like Layer 1 already does for physical red flags) — resolves in one exchange, doesn't require the user to guess it's relevant |
| **Context-enriching, contributes to BIRI%, not safety-blocking** | Vitals specifics, exact allergy list, precise risk-group demographics, granular SAMPLE detail | Continues to work exactly as now — contributes to the weighted BIRI score, more detail unlocks deeper/more-specific content, but its absence should not, by itself, cap depth all the way down to D1/D2 the way an unresolved safety-critical field correctly does |

This preserves 100% of what's currently rigorous (safety-critical fields still hard-gate) while fixing the
actual problem (safety-critical fields were previously an open-narrative expectation instead of an active
screen, for one specific domain).

## 3. Proposed concrete change (draft language, NOT yet added to `SYSTEM_PROMPT.md`)

Add a **Layer-0b micro-screen**, run once per conversation, immediately after the Layer-1 physical red-flag
screen clears (not instead of it), structured exactly like Layer 1's fixed trigger list but for the
psychosocial-safety domain:

```
LAYER 0b — BIOPSYCHOSOCIAL SAFETY MICRO-SCREEN (runs once, right after Layer 1 clears, before Layer 2/3
content, for any conversation that will touch behavioural/lifestyle/emotional content):
Ask, in ONE combined question, no more than these three yes/no items:
  1. Any thoughts of self-harm, hopelessness, or not wanting to be here?
  2. Do you feel unsafe in any relationship right now?
  3. Do you have at least one person you can talk to about this? (protective factor, not gating)
If (1) or (2) is yes or unclear: route to the crisis/safety pathway, same discipline as Layer 1.
If (1) and (2) are explicitly no: mark biopsychosocial_loop_context's safety sub-field as RESOLVED
regardless of how much OTHER narrative detail in that domain is still missing (recent stressor detail,
sleep quality specifics, etc. remain enriching, not gating).
This micro-screen is asked ONCE per conversation, not re-asked every turn, and its resolution persists for
the rest of that conversation (same persistence model Layer 1's red-flag resolution already has).
```

**Why this specific design and not just "lower the BIRI threshold for D4":** lowering the threshold would
weaken the gate for everyone, including genuinely ambiguous or higher-risk cases — that is the wrong fix,
since C15/C18 show the gate's conservatism is doing real work elsewhere. This proposal instead makes the ONE
specific domain that was silently expensive (biopsychosocial safety) into an ACTIVE, cheap, one-time screen
— matching how physical red flags already work — rather than loosening the gate's actual safety logic at
all. The `critical_missing_data_override` rule is unchanged; this just adds one more field to what gets
proactively checked instead of passively hoped-for.

## 4. Secondary levers (lower priority, worth considering after the above is validated)

1. **Explicit multiple-choice framing for high-friction questions.** Several v2/v3 responses asked good
   questions but as open narrative prompts ("does it ever feel like you can't stop?"). A yes/no/not-sure
   framing for safety-adjacent questions reduces the number of turns needed to resolve them and reduces
   ambiguity in what counts as "resolved."
2. **A distinct "low-risk lifestyle fast-track."** For conversations where Layer 1 AND the new Layer 0b both
   clear on turn 1, and the topic is unambiguously non-clinical (sleep timing, screen habits, mild stress,
   no medication/chronic-disease mention), consider allowing D3→D4 with a lighter completeness bar than the
   general case — since the downside risk of a wrong lifestyle suggestion is categorically lower than a
   wrong clinical one. This needs its own falsifiable criteria (what exactly counts as "unambiguously non-
   clinical") before being specified further; flagged here as a direction, not a ready proposal.
3. **Fix the flagship differentiator claim (actor-tier routing) before promoting it further.** The v2 run's
   C07 finding (a clean baseline out-structured `/birca` on exactly the scenario type meant to showcase
   actor-tier routing) suggests the actor-tool-ladder section of the prompt needs to be MORE assertive about
   actually producing the labeled A1/A2/B1/B2/C1/C2 breakdown when it's relevant, not just available as a
   concept. Concrete fix: add an explicit instruction that whenever a "who should do something" question
   arises at D3+, the response MUST use the named actor-tier labels, not prose paraphrase of the same idea —
   this is a lower-risk, mechanical fix (formatting discipline) separate from the deeper D4-gating issue
   above.
4. **Re-run the FULL 15-item and 100-item suites after any of the above changes**, not just the specific
   items that motivated the change — a change to gating logic is architecture-level and needs the same
   regression discipline already established in this project's workflow (fix → reinstall → real retest →
   log the result, never just reason about it).

## 5. What this proposal explicitly does NOT recommend

- Does NOT recommend lowering the BIRI numeric thresholds (D1<35, D2<55, etc.) — those didn't cause the
  problem; the missing active-screen for one domain did.
- Does NOT recommend weakening `critical_missing_data_override` or the context-fit=0 cliff — both are
  proven, working safety mechanisms per the adversarial evidence (C15, C18) and should be left untouched.
- Does NOT recommend removing the biopsychosocial domain's weight in BIRI — it should still contribute
  richness/depth; this proposal only changes ITS SAFETY SUB-FIELD from passive-narrative to active-screen.
- Does NOT recommend implementing any of this without a human sign-off and a full regression re-run — per
  this project's own established discipline after two real gaps (A35, and the C07 disconfirming finding)
  were found this session by testing, not by inspection.

## 6. Suggested next step

1. Human reviews and either approves, modifies, or rejects the Layer-0b micro-screen design in §3.
2. If approved: implement in `SYSTEM_PROMPT.md` + `spec/birca_universal_skill.yaml`, bump to v1.1.0 (minor
   version, since this is a new mechanism, not a bug patch).
3. Re-run C01-C10 (a "v4," now WITH the Layer-0b micro-screen actually built-in, rather than scripted around
   it from the user side) to see whether D4 becomes reliably reachable in 2 turns for genuinely low-risk
   lifestyle cases, without any change in behaviour for higher-risk or ambiguous cases.
4. Re-run the full 15-item and 100-item suites as a full regression check before treating this as settled.
