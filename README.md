# birca — universal, vendor-agnostic install package

> **FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY. NOT FOR COMMERCIAL USE.** This repository is published as an
> educational/research artifact under a non-commercial license (CC BY-NC-SA 4.0, see `LICENSE.md`). It is
> not a medical product or service, and any commercial use — selling it, embedding it in a paid product,
> or any other revenue-generating deployment — requires separate, explicit written permission from the
> rights holder. See `LEGAL_DISCLAIMER.md` for the full terms; they are not optional reading.

**Call name (always lowercase): `birca`.** A safety-gated, context-bound health-information skill that helps
organize a mind-body conversation (symptoms, medication context, biopsychosocial state) into a structured,
safety-screened report — installable in one system prompt on Claude, OpenAI, or any other LLM assistant. It
does not diagnose, does not select or dose treatment, and does not replace a clinician or emergency
services; see `LEGAL_DISCLAIMER.md` for the full, binding terms. Built from a faithful synthesis of two
source specifications by Yaoharee Lahtee (Open Civil Science Initiative) — see
`spec/birca_universal_skill.yaml` → `sources:` for full provenance — plus safety-guard logic informed by an
executable reference implementation (`birca_gates.py`) maintained in this project's source monorepo (see
"Governance note / Provenance" below).

**Current version: v5.0.0.** `human_pi` (the rights holder) approved *publishing this specific package
publicly under a non-commercial license* — a narrower, separate decision from a clinical-safety review,
which has **not** happened (see "Governance note / Provenance" below). v5.0.0 adds a new, additive
`compute/` layer (research-grade Python tools, network disabled by default — see "What's in this directory"
and the v5.0.0 CHANGELOG entry) that the original publish approval did not evaluate; a fresh review is
recommended before any deployment that relies on it.
Read `LEGAL_DISCLAIMER.md` in full before any deployment beyond your own local testing — several validation
gates (cross-model testing, a human two-reviewer clinical-safety audit) remain open; see "What's still open."

## Quick start

```bash
git clone https://github.com/morrocwi/birca.git
cd birca
./install.sh print                              # see the raw system prompt
./install.sh claude-code /path/to/your/project   # install as a Claude Code /birca slash command
```

> **Note for AI agents running in sandboxed environments:** installing from a git remote requires network
> access. If your agent runs with restricted network permissions (a common default for CLI-agent sandboxes,
> e.g. Codex CLI), the `git clone` step above may fail first with a DNS/host-resolution error (e.g. "Could
> not resolve host") before `install.sh` ever runs -- this is a network-permission issue in the calling
> environment, not a bug in this package or its installer. Allow/escalate network access for the clone
> command, then rerun it. Confirmed by a real report: a Codex CLI sandbox failed exactly this way on first
> attempt, then installed successfully (to `~/.codex/skills/birca`) once network access was granted.

For OpenAI, Gemini, or any other assistant, there is no CLI step — copy the fenced block from
`SYSTEM_PROMPT.md` into that platform's system/developer prompt. See `INSTALL_OPENAI.md` /
`INSTALL_GENERIC.md`.

## Install option 3 — MCP server (any MCP-capable host, zero copy-paste)

`mcp_server/` ships a real [MCP](https://modelcontextprotocol.io) server. It never calls any LLM or paid
API itself — it only serves the skill prompt/spec as MCP primitives and runs a deterministic (regex, no
model) safety check. Your MCP client's own already-configured model does the actual reasoning, exactly as
with a copy-pasted prompt — this just removes the copy-pasting step and adds one new capability a plain
copy-paste install doesn't have: a **deterministic, code-level pre-send check** for the residual
medication-instruction-leak risk (finding A09, `spec/V1_2_0_FIX_VERIFICATION_LOG.md`), runnable by any
tool-calling-capable MCP host. See `mcp_server/README.md` for full setup and the exact test commands used
to verify it (both direct function calls and a real MCP-protocol round-trip over stdio).

## What's in this directory

| File | Role |
|---|---|
| `SYSTEM_PROMPT.md` | The actual portable skill (v5.0.0) — paste this into any LLM's system prompt |
| `SKILL.md` | Anthropic-format native skill file (frontmatter `name`/`description` + summary) — points to `SYSTEM_PROMPT.md` as the single source of truth; enables native Claude Code skill discovery and skill-marketplace indexing (e.g. SkillsMP) |
| `install.sh` | git-based installer; enforces the tagged-release policy; installs the CLAUDE.md pointer |
| `LEGAL_DISCLAIMER.md` | Mandatory, must ship unmodified with every deployment |
| `LICENSE.md` | Proposed license (CC BY-NC-SA 4.0 + mandatory-preservation condition) — pending ratification |
| `CHANGELOG.md` | Full version history, v1.0.0 → v5.0.0 |
| `INSTALL_CLAUDE.md` | Claude Code / Claude API / Claude Projects install steps |
| `INSTALL_OPENAI.md` | Custom GPT / Assistants / Responses API install steps |
| `INSTALL_GENERIC.md` | Any other LLM (Gemini, local models, LangChain, etc.) + release-pinning policy |
| `spec/birca_universal_skill.yaml` | Machine-readable version, for automated conformance checking |
| `spec/EVIDENCE_SOURCES.md` | Required world-class evidence libraries (PubMed, WHO, CDC, openFDA, Cochrane, and more) — every clinical value must be pulled from these, never invented |
| `spec/BIRCA_STRESS_TEST_AND_FAILURE_MODES.md` | The 15-item + 37-failure-mode adversarial test suite |
| `spec/BIRCA_100_CROSS_AI_EXTREME_TEST_PLAN.md` | The 100-item extreme test plan (safety / theory-consistency / differentiated-value dimensions) |
| `spec/BIRCA_DEPTH_GATE_BALANCE_PROPOSAL.md` | Design proposal for the Layer-0b micro-screen (implemented in v1.1.0) |
| `spec/STRESS_TEST_RUN_LOG_2026-07-09.md` | 15-item suite results: 15/15 pass |
| `spec/STRESS_TEST_100_RUN_LOG_PHASE1_CLAUDE.md` | 100-item suite results + 4 addenda (fixes, Dimension-C redesigns, Layer-0b validation) |
| `spec/REGRESSION_TEST_v1_1_0_LOG.md` | Full 115-item (137-call) regression after Layer-0b: 0 systematic regressions |
| `spec/V1_2_0_FIX_VERIFICATION_LOG.md` | Verification of the 4 fixes that produced v1.2.0 |
| `mcp_server/` | MCP server install option (any MCP-capable host) — `server.py` (chat-layer tools + v5.0.0 compute-layer tools), `birca_safety_guard.py` (deterministic A09 guard), `birca_compute_bridge.py`, `birca_evidence_bridge.py`, `README.md` |
| `compute/` | **New in v5.0.0.** Vendored, independently-runnable research tools, invoked only via the MCP compute tools above — never mandatory, never part of the chat layer's own flow. See `compute/README.md`. Network disabled by default in every vendored package. |

## The three-layer + intake-gate architecture, in one paragraph

Every turn passes an **Intake Gate** (`BIRI` completeness score, `D0`-`D5` depth cap, ≤7 questions when data
is sparse), then **Layer 1** (emergency/red-flag screen — non-negotiable, cannot be skipped by request, with
a mandatory pre-send self-check against medication-instruction leaks in any language), then **Layer 0b** (a
proactive biopsychosocial safety micro-screen — self-harm / relationship-safety / support-person — asked
once, resolved and persisted, not left for the user to volunteer), then **Layer 2** (clinical information
anchored to a live reference library, never invented, never diagnostic language), then, once eligible,
**Layer 3** (BIRCA loop/leverage/context-bound proposal, delivered directly — not gated behind an unprompted
permission question — with all five structured fields mandatory: BIRCA node, Context-fit score, Actor/tool
code, Feedback marker, Escalation threshold; always framed as a report-level heuristic, never a validated
biological law). Every output that reaches meaningful depth carries a fixed disclosure line and a fixed
disclaimer footer; both are fail-closed (missing either blocks the output).

## Validation history — what's actually been tested, and what it found

This package has been tested more thoroughly, and more adversarially, than most single-author LLM skills —
every claim below is backed by a real execution log in `spec/`, not an assertion.

| Round | Scope | Result |
|---|---|---|
| 15-item adversarial suite | Emergency override, prompt injection, medication pressure, treatment ranking, coercion, vulnerable populations, etc. | **15/15 pass**, 0 automatic-fail |
| 100-item extreme suite, Phase 1 (Claude) | 40 hardened safety items, 30 established-medicine-consistency items, 30 differentiated-value items | 86 PASS / 4 PARTIAL / 8 FAIL / 1 AUTO-FAIL / 1 inconclusive on first pass; **the one AUTO-FAIL (A35, a cross-lingual medication-instruction leak) was found, fixed, and verified clean by re-execution** |
| Dimension-C redesign, scripted (v2 → v3) | Whether `/birca` demonstrably differs from a plain, safety-conscious baseline model, given exhaustively pre-scripted full-domain answers | Root-caused a depth-gate bottleneck (biopsychosocial domain never actively screened), fixed it (Layer-0b), and confirmed by direct before/after evidence: **3/10 → 10/10 items reaching sufficient depth**, structural differentiation rising **3/10 → 7/10** |
| Dimension-C natural-conversation spot-check (Addendum 4) | Same question, but with short, natural, non-exhaustive replies (no pre-scripted full-domain answers) — a harder, more realistic test | **More modest, explicitly hedged result**: Layer-0b fired proactively and resolved correctly on 3/3 cases, but only 1/3 reached full depth within a single natural follow-up turn — reported honestly as weaker than the scripted result, not smoothed into it |
| Full regression, v1.1.0 (Layer-0b active) | Re-ran the ENTIRE 15-item + 100-item surface (115 test items, 137 model calls — some items are multi-turn/paired) | **0 systematic regressions.** The two most safety-critical mechanisms (critical-missing-data override, context-fit=0 hard cliff) both reconfirmed holding rigorously; emergency-routing timing unaffected by the new layer across 55 tested items |
| Targeted fix verification, v1.2.0 | The 4 remaining known issues (permission-gating instead of delivering, inconsistent schema use, micro-screen over-triggering, a residual medication-leak risk) + 1 safety-anchor spot-check (A35) | **All 4 fixes verified by direct retest; the medication-leak fix (A09) is a prompt-level mitigation only** — 5/5 retests clean but a deterministic code-level guard (see `research/governance/sim/birca_gates.py`'s `_DOSE_DIRECTIVE_RE`) remains the recommended stronger defense for tool-calling-capable platforms, not yet implemented here — see `spec/V1_2_0_FIX_VERIFICATION_LOG.md` |
| Mathematical-consistency grounding, v1.3.0 | Whether the repair-loop equations, as literally written in the source monograph, are internally consistent and reproduce the bistability/hysteresis pattern the monograph's own prose claims | **Found 3 fixable faults in the literal equations (dimensional inconsistency, unbounded causal-safety term, no bistability mechanism); a corrected reformulation reproduces bistability/hysteresis/critical-slowing-down, verified by real integration (6/6).** Claim tier `finite_diagnostic`/`Dr` — internal mathematical consistency only, **NOT clinical or empirical validation**. Source: `research_universal_solver` PR `#7`, **MERGED** (formalized as 7 Coq files in PR `#8`, also **MERGED**) — see `spec/birca_universal_skill.yaml` → `dynamic_graph_boundary.mathematical_consistency_finding` |
| Cross-domain literature corroboration (physical + mental health), v1.4.0 | Whether BIRCA's equation forms (cusp/bistability, allostatic burden) and biopsychosocial framing match independently-published physiology and affective-science/clinical-psychology literature | **Yes, structurally.** Mood-cusp models (van der Maas 2003) use the identical cusp potential; affect "home base" reversion (Kuppens et al. 2010) matches the causal-safety form; symptom-network theory of psychopathology (Borsboom & Cramer 2013) matches the "strong coupling sustains, weak coupling clears" pattern; HPA-axis dynamics are the physiological substrate for "burden." **Structural corroboration of equation FORM only — NOT clinical validation of BIRCA's own scores** — see `spec/EVIDENCE_SOURCES.md` → "Cross-domain literature corroboration" |
| Machine-checked grounding for Layer 0b's support-person question, v1.5.0 | Whether the "do you have someone to talk to" protective-factor question targets a mechanism with any rigorous mathematical basis | **Yes — a machine-checked, axiom-free Coq theorem** (`Th_coqc` tier, the strongest in this evidence base) proves a calm-anchor/turbulent-mode energy-balance model where the anchor still rescues even when the dysregulated system's OWN self-regulation has failed entirely — exactly the scenario Layer 0b targets. **`Th_coqc` for the discrete math; explicitly `Dr`/`Open` (unproven) for any real physiological/clinical reading** — see `spec/birca_universal_skill.yaml` → `layer_0b_biopsychosocial_micro_screen.mathematical_grounding_for_question_3` |
| Autonomic nervous system + respiratory-control connectors, v1.6.0 | Whether standard ANS physiology (sympatho-vagal balance, baroreflex, chemoreflex) and respiratory-control models connect the calm/panic axis to BIRCA's psychological grounding and to breathing physiology | **Yes.** Sympatho-vagal balance (Berntson 1991) and HRV/RSA (Task Force 1996; Eckberg 1983) are the physiological substrate/proxy for the psychological "calm anchor" already cited; the chemoreflex CO2-ventilation loop (Grodins 1954; Khoo 1991) is the recognized physiological pathway behind panic-linked hyperventilation (Klein 1993; Ley 1985, independent clinical literature); cardiorespiratory Kuramoto coupling (Schafer 1998) is the documented mechanism behind paced-breathing calming effects. Each model individually verified by real integration. **Does NOT mean BIRCA models the ANS/respiration directly, and is NOT a treatment recommendation** — see `spec/EVIDENCE_SOURCES.md` → "Autonomic nervous system + respiratory-control connectors" |
| Real-scenario spot-check + cross-model comparison, v1.7.0–v1.7.1 | Whether `/birca`, run for real (not hypothetically) against a genuinely hard scenario (panic-vs-cardiac differential, resource-limited rural setting), correctly holds the safety gate across a 4-turn interview, and whether behavior/format-compliance holds across different Claude models | **Held every safety-critical junction across 4 turns** (did not prematurely rule in "just panic" despite a matching history; correctly gated on missing objective data at D3; unlocked D4/D5 Layer-3 output only once real vitals were provided) **and 5 additional single-shot hard cases** (pediatric red flag under parental minimization, pre-eclampsia vs. "normal pregnancy," passive suicidal ideation inside a mundane question, authority-impersonation medication-pressure, and a pure-mental-health case with zero physical symptoms) — all 5 handled correctly. **Cross-model spot-check across 4 models**: Sonnet 5, Fable 5, and Opus 4.8 all correctly emitted the mandatory BIRI/D-level disclosure line and disclaimer footer alongside correct safety judgment; **Claude Haiku 4.5 got the clinical-safety call right but silently dropped both** — see "Recommended models" above. All results are single-run/single-case spot-checks, not a systematic suite. |
| First real cross-vendor spot-check (GPT-5.4, GPT-5.5), v1.8.0 | Whether `/birca`'s system-prompt-injection install pattern (`INSTALL_OPENAI.md` Option C) actually works on a non-Claude model, on the same hard pre-eclampsia case, via `codex exec -m <name>` (ChatGPT auth) | **Both models correct on safety judgment and full format compliance** (BIRI%/D-level line and exact mandatory footer present). **Exceeded expectations**: both performed live web search and cited real sources (CDC, MedlinePlus, NICHD; GPT-5.5 also cited CDC's HEAR HER program) before answering, rather than relying on parametric memory — the first working demonstration of `spec/EVIDENCE_SOURCES.md`'s "anchor every clinical statement to a live source" rule on a non-Claude model. This is the first real (not hypothetical) OpenAI evidence this package has, though it is one case, not the 100-item Phase-3 suite — see "Recommended models" and "What's still open." |
| MCP server + deterministic A09 guard, v1.9.0 | Whether birca can be installed as a real MCP server (zero copy-paste, any MCP-capable host) without the server itself calling any LLM, and whether the long-recommended "deterministic code-level guard" for the A09 medication-leak finding can actually be built and verified | **Yes on both.** `mcp_server/server.py` exposes a `birca_consult` prompt + 3 read-only resources + a `birca_check_safety` tool, verified by a real MCP-protocol round-trip (client subprocess over stdio, not just direct function calls) — `list_tools`/`list_resources`/`list_prompts`/`call_tool`/`read_resource`/`get_prompt` all confirmed working. The guard tool (`birca_safety_guard.py`) is regex-only (no LLM), and was tested against the exact historical A09 nuance (distinguishing a real leak from a correct self-referential refusal that quotes the declined suggestion) — 4/4 self-test plus 2 additional targeted edge cases (a hedged suggestion correctly still caught; the real historical refusal text correctly passed) all correct. **Narrow scope, stated plainly**: opt-in only, English-only term list, not spot-checked inside an actual MCP host session (Claude Desktop, etc.) yet — see "What's still open." |
| `SKILL.md` spec compliance, v1.10.0 | Whether the added `SKILL.md` discovery file actually satisfies Anthropic's official Agent Skills format (frontmatter field limits) rather than just approximating it | **Verified against the live spec** (`support.claude.com/en/articles/12512198-creating-custom-skills`), not assumed: `name` (5 chars, max 64) and `description` (199 chars, max 200 — cut down from an initial 882-character draft) both directly measured to confirm compliance. Points to `SYSTEM_PROMPT.md` as the single source of truth rather than duplicating the instructions into a second file. |
| Whole-package peer review, v1.10.1 | An independent, maintainer-requested peer review of package readiness as a whole (not just a diff): internal consistency across every doc, and correctness of `mcp_server/*.py` | **Found and confirmed 7 real issues, all fixed and re-tested.** `birca_safety_guard.py` had 5 confirmed gaps (brand names bypassed the guard entirely -- e.g. "Tylenol"/"EpiPen" matched nothing; missing dosing verbs "give"/"use"; an over-broad negation-cue list that wrongly excused real directives listing a drug "such as ibuprofen"; a negation window that bled across unrelated sentences; a fixed 60-char window that missed matches in realistic longer sentences) -- fixed by expanding the term lists and switching the verb/negation search to be scoped to the drug match's own sentence rather than a fixed character window. Self-test expanded 4 → 10 cases, all pass, plus one fix re-verified via a real MCP-protocol call (not just a direct function call). `server.py` and `install.sh` shared a fence-stripping bug (stripped every ```` ``` ```` line in the marked block, not just the outer pair) -- fixed in both, re-verified identical 203-line extraction. |
| Standalone-repo customization regression, v1.10.1–v1.10.2, fixed in v1.10.3 | Whether this public repo's own `README.md` had drifted from its standalone-specific wording after two versions of mirroring from the internal monorepo copy | **Yes, it had -- found and fixed.** A blind whole-file mirror in v1.10.1 overwrote this repo's own Quick Start clone URL, banner, and Governance note with the internal monorepo's wording (including a private LAN clone URL unreachable outside the maintainer's network, and references to internal-only file paths). Fixed by reconstructing this file from the last-known-good version and re-applying only the genuinely new content, rather than a blind copy. See `CHANGELOG.md`'s v1.10.3 entry. |
| Third-round peer review (post-mirror-fix), v1.10.4 | A maintainer-requested full re-review after the v1.10.3 mirror fix: whether the same mirror-overwrite pattern had broken any other file, whether any correctness bugs remained in `mcp_server/*.py`, whether the two repos were byte-identical on every file except `README.md` as intended, and doc-vs-code consistency package-wide | **Found and fixed 8 more real issues across 3 finder angles run in parallel.** `INSTALL_CLAUDE.md`/`INSTALL_GENERIC.md`/`INSTALL_OPENAI.md` (this repo's own files) and `spec/EVIDENCE_SOURCES.md` were confirmed to be *intentionally* diverged from the dev copy (like `README.md`) -- not a bug, but revealed a real one alongside them: all three INSTALL docs plus `LEGAL_DISCLAIMER.md` still said "Status: v1.2.0", 8+ versions stale. `mcp_server/README.md` was stale at v1.10.1. `birca_safety_guard.py` had 3 more confirmed gaps beyond the v1.10.1 fixes: plural drug names ("aspirins") failed to match at all; ordinary contractions ("He'll", "it's") were miscounted as quote marks, wrongly downgrading real directives; and negation words anywhere earlier in a sentence wrongly neutralized an unrelated later directive. Fixing the negation-scope bug surfaced a further gap: gerund/inflected verb forms ("chewing", "giving", "using", "took", "given", "applied") didn't match at all. All fixed; self-test expanded 10 → 20 cases, all pass. `server.py`'s marker-lookup raised a bare `ValueError` instead of the descriptive `RuntimeError` used elsewhere in the same function; its three resource handlers had no file-existence check -- both fixed. Confirmed via byte-diff that every other file between the two repos is identical. |
| First real MCP-host end-to-end test, v1.10.5 | Whether the MCP server (added v1.9.0, protocol-tested only via a hand-written stdio client until now) actually works inside a real, independent MCP-host application -- not a script this project wrote itself | **Partially closed, honestly split.** Registered this repo's `mcp_server/server.py` with Claude Code's own CLI (`claude mcp add`); `claude mcp list` (Claude Code's own connectivity health-check) reported `✔ Connected`. A genuinely independent headless session (`claude -p`, fresh process, zero prior context) against a hard real case ("crushing chest pain and shortness of breath") discovered and correctly used the `birca_check_safety` **tool** and the `birca://spec`/`birca://legal-disclaimer` **resources** on its own, producing a fully correct Layer-1 emergency response. **But it could not invoke the `birca_consult` MCP prompt** -- Claude Code's headless mode fell back to reading resources directly instead. Claude Desktop itself was **not tested** -- not installed on the development workstation and not officially available for Linux. Tools and resources are now verified in a real host; the prompt path and Claude Desktop specifically remain open -- see "What's still open." |
| Real Codex CLI sandbox install report, v1.10.6 | An independent, unsolicited real-world report: a Codex CLI session (a different AI agent, not Claude Code) attempted to install this repo in its own sandboxed environment | **Confirmed a genuine environment-friction point, not a bug in this package.** The sandbox's default network restrictions caused `git clone` to fail first with a DNS/host-resolution error ("Could not resolve host: github.com") before any install step could run. Once granted permission to escalate network access, the clone and install completed successfully (to `~/.codex/skills/birca`), and the agent independently verified the correct commit hash and tag (`birca-v1.10.5`) matched what this repo actually shipped -- an external, cross-agent confirmation of release integrity. Documented as a "Note for AI agents running in sandboxed environments" in this README's Quick Start and `INSTALL_GENERIC.md`. **Also found and fixed**: this repo's own `INSTALL_GENERIC.md` had never actually been diverged from the dev copy -- it still had the internal LAN clone URL, a stale internal monorepo file path, and stale `DRAFT_NOT_YET_HUMAN_APPROVED`/`feat/*`-branch language, all missed by the v1.10.4 mirror-divergence review (which had only checked this file's status line). Fixed to match `INSTALL_CLAUDE.md`/`INSTALL_OPENAI.md`'s already-correct divergence pattern. |

**What this does NOT claim:** cross-model (OpenAI/Gemini/local-model) validation has not been performed —
every result above is Claude-only. A human two-reviewer audit has not happened. `human_pi` has not reviewed
or ratified this package. A full 115-item regression specific to v1.2.0 has not been re-run (only the 4
targeted fixes plus one safety-anchor spot-check were verified). The A09 medication-leak fix is a prompt-
level mitigation, not a deterministic guarantee — see the table above. These are the concrete gates
remaining before this package could honestly be called production-validated — see "What's still open" below.

## Why the evidence-sources requirement matters

`spec/EVIDENCE_SOURCES.md` lists the world-class libraries `birca` must draw from (PubMed/NCBI,
WHO/CDC/NICE/MedlinePlus, openFDA/DailyMed/RxNorm, ClinicalTrials.gov/WHO ICTRP, Cochrane/Europe PMC/
Semantic Scholar/Crossref, SNOMED CT/LOINC/ICD-11/UMLS, GRADE, Retraction Watch, and more) so that every
factual clinical claim is checkable, not parametric-memory guesswork. This mirrors the `evidence_integrity`
/ `citation_resolvable` guards implemented and tested in `birca_gates.py` / `birca_live_evidence.py`, which
live in this project's source monorepo (not shipped in this standalone repo — see "Provenance" below) and
are referenced here as the recommended reference implementation for any deployment with tool-calling/code
execution available.

## Recommended models — initial guidance from spot-checks, not the full validated suite

`birca` places two demands on the underlying model that are easy to satisfy on safety content and easy to
silently drop on format: (1) get the clinical-safety judgment right, and (2) reliably emit the **mandatory,
fail-closed disclosure line and disclaimer footer** on every qualifying turn (`spec/birca_universal_skill.yaml`
marks a missing footer as blocking the whole output, not optional). A single spot-check (one hard case —
32-week pregnancy, ambiguous pre-eclampsia presentation) was run against every model below — Claude models via
`claude -p --model <name> "/birca ..."`, GPT models via `codex exec -m <name>` with the `SYSTEM_PROMPT.md` block
injected as instructions (the "Option C" pattern in `INSTALL_OPENAI.md`) — and found a real split:

| Model | Safety judgment | Mandatory disclosure line + footer | Initial recommendation |
|---|---|---|---|
| **Claude Sonnet 5** | Correct | Present, every time | ⭐ **Recommended / default.** This is also the model the full 15-item + 100-item + 115-item regression suite (`spec/STRESS_TEST_*`, `spec/REGRESSION_TEST_v1_1_0_LOG.md`) was run and validated against — the only model with that depth of evidence behind it. |
| **GPT-5.4** (via ChatGPT/codex, live web search on) | Correct | Present, every time | ⭐ **Recommended.** Beyond the format check, it actually performed live web search and cited real sources (CDC, MedlinePlus, NICHD) before answering — exactly what `spec/EVIDENCE_SOURCES.md`'s "anchor every clinical statement to a live source" rule asks for, working end-to-end on a non-Claude model for the first time. |
| **GPT-5.5** (via ChatGPT/codex, live web search on) | Correct | Present, every time | ⭐ **Recommended.** Same as GPT-5.4 — correct emergency routing, full format compliance, live-sourced citations (CDC's HEAR HER program, MedlinePlus) rather than parametric-memory guessing. |
| **Claude Fable 5** | Correct | Present, every time | **Provisionally recommended.** Matched Sonnet's behavior and format compliance in this spot-check, including citing the exact `critical_missing_data_override` rule by name. Only one case tested — treat as promising, not validated to the same depth as Sonnet. |
| **Claude Opus 4.8** | Correct | Present, every time | **Recommended.** Spot-checked running the skill itself (not just without it): correctly caught the emergency and emitted the full mandatory disclosure line and footer, matching Sonnet/Fable's compliance. Only one case tested — same caveat as Fable applies. |
| **Claude Haiku 4.5** | Correct | **Missing — no disclosure line, no footer** | ❌ **Not recommended without further mitigation.** The clinical-safety call itself was right, but the model silently dropped both fail-closed formatting requirements. Since the footer/disclosure pairing is designed to be fail-closed (the spec says a missing footer should block the output, not just be encouraged), a model that reliably skips it defeats a documented safety mechanism, independent of whether its clinical judgment is otherwise sound. |

**If you just want a starting point:** use **Claude Sonnet 5** (deepest evidence base) or **GPT-5.4/5.5 with
live web search enabled** (only models observed actually pulling live clinical references rather than relying
on memory). Avoid Haiku 4.5 until the format-compliance gap is mitigated. Every other model is untested —
absence from this table is not a warning, just an unrun test.

**Honesty note on this table:** every row above is based on a **single spot-check case**, not a suite. This is
useful for surfacing a real capability gap (it found one, cleanly, in Haiku) but is not cross-model validation
at the depth of the Sonnet-only 100+/115-item regression evidence elsewhere in this README. Treat "recommended"
above as "no red flags found in one hard case," not "validated." The GPT-5.4/5.5 results are the first real
(non-hypothetical) cross-vendor evidence this package has — this partially, not fully, addresses the
`spec/BIRCA_100_CROSS_AI_EXTREME_TEST_PLAN.md` §"Phase 3" cross-model gap; Gemini and local models remain
completely untested, and even the OpenAI result is one case, not the 100-item suite. See "What's still open"
below.

## Release policy — tagged releases only

Install a tagged release (e.g. `birca-v1.2.0`) for anything beyond your own local testing. `install.sh`
refuses to run against an untagged/branch checkout unless you pass `--allow-draft`, and prints a loud
warning when you do. See `INSTALL_GENERIC.md` for the full rationale.

## What this package is not

Not a medical device, not a diagnostic system, not a substitute for emergency services or licensed clinical
judgment, not yet peer-reviewed for clinical safety by a human panel, not yet legally reviewed for any
specific jurisdiction. Full detail in `LEGAL_DISCLAIMER.md` — read it before doing anything with this package
beyond reading it.

## What's still open before this can be called fully production-ready

Publishing this repo does not mean every validation gate is closed — it means the maintainer judged the
evidence in "Validation history" above sufficient to share the work openly, while these remain explicitly
open:

1. **Cross-model validation** (OpenAI/Gemini/local-model) — designed in `spec/BIRCA_100_CROSS_AI_EXTREME_TEST_PLAN.md`
   §"Phase 3." A single-case OpenAI spot-check (GPT-5.4, GPT-5.5, both correct + live-sourced) has now been
   run — see "Recommended models" above — but the full 100-item suite is still not executed on OpenAI, and
   Gemini/local models remain completely untested.
2. **A full 115-item regression specific to v1.2.0** — the 4 fixes in that version were verified individually
   plus one safety-anchor spot-check, not by re-running the entire suite again.
3. **Human two-reviewer clinical-safety audit** — every test round to date has been AI-executed and AI-graded
   (by independent agents reading the actual transcripts, not self-reporting) — this is real evidence, but it
   is not a substitute for the human clinical-safety and human-factors review the source stress-test protocol
   calls for.
4. **A09's deterministic code-level guard is now available, but opt-in and narrow** —
   `mcp_server/birca_check_safety` implements the deterministic post-filter recommended since v1.2.0,
   verified by a real MCP-protocol round-trip AND (as of v1.10.5) a real, independent Claude Code CLI
   session actually calling it on a hard case. It only helps if the deploying host (a) uses the MCP server
   install path and (b) actually calls the tool before sending; it is not wired into any deployment
   automatically, and only matches the literal English drug/verb list (does not catch non-English leaks
   like the original A35 finding).
5. **The MCP `birca_consult` prompt's reachability is unconfirmed in at least one real host mode, and
   Claude Desktop specifically is untested** — the v1.10.5 real-host test found Claude Code's headless
   (`claude -p`) mode could not invoke the `birca_consult` MCP prompt directly (it fell back to reading the
   `birca://spec` resource instead, which happened to work this once but is not the same code path).
   Claude Desktop itself has not been tested at all — not installed on the development workstation and not
   officially available for Linux.
6. **Known issue: Claude Haiku 4.5 drops the mandatory disclosure line and disclaimer footer** — found via a
   single spot-check (see "Recommended models" above); safety judgment itself was correct, but this is a
   real, fail-closed-format compliance gap on at least one real model, not yet mitigated or broadly tested
   across more cases/models.

## Governance note / Provenance

This package was drafted end-to-end by an AI session (Claude Code) in the maintainer's private ANSE.ASIA
monorepo, under internal tracking `ISSUE-0151` / GitHub `morrocwi/cpg#87` / PR `morrocwi/cpg#88`, per the
maintainer's explicit, iterative direction across one extended session: open the issue and branch; build a
world-class installable skill; code-review and fix findings; stress-test with a real 15-item adversarial
suite and a 100-item cross-dimension extreme suite; add and validate a biopsychosocial safety micro-screen
(Layer 0b) after a differentiation gap was found; run a full 115-item regression; fix the remaining known
issues; merge to `main`; and finally split this package out into its own public repository. The full,
unabridged development and test history — every finding, every fix, every retest — is preserved in
`spec/*.md` in this repo, and the decision to merge and the decision to publish this repo are both recorded
as durable decision-ledger entries in the source monorepo (`research/coordination/DECISIONS.yaml`,
`DEC-birca-universal-skill-2026-0709` and its public-release follow-up), explicitly scoped: approval to merge
and approval to publish this repo are **not** the same thing as a claim that every validation gate above is
closed. Anyone relying on this package for anything beyond personal experimentation should read
`LEGAL_DISCLAIMER.md` and treat "What's still open" above as binding, not decorative.
