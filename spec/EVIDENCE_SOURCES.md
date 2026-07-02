# BIRCA Universal — Required Evidence Libraries (world-class sourcing layer)

**Rule zero:** every clinical/medical value the skill states as fact (drug label text, adverse-event
signal, published instrument band, guideline recommendation, trial existence) **must be pulled live from
one of the libraries below**, never invented, never recalled from parametric memory alone. If a live call
is unavailable, the skill must say so explicitly and fall back to a broader, more conservative referral —
never to a guessed value. This mirrors `RULE-036` (plausibility ≠ validation) in the BIRCA v7.9 dynamic-graph
boundary and the `evidence_integrity` / `citation_resolvable` guards, whose executable reference
implementation (`birca_gates.py` + `birca_live_evidence.py`) lives in this project's source monorepo, not in
this standalone repo — see the README's "Governance note / Provenance" section.

## Tier 1 — Point-of-care clinical reference (Layer 2 primary anchor)

| Library | Use | Access |
|---|---|---|
| **MSD / Merck Manual — Professional Edition** | Disease mechanism, standard-care summaries | public site; no key |
| **UpToDate** | Point-of-care clinical guidance | licensed — org must hold a subscription |
| **BMJ Best Practice** | Point-of-care clinical guidance | licensed — org must hold a subscription |
| **NICE guidance** | UK national clinical guidance | public site; no key |
| **WHO** (guidelines, ICD-11, GHO) | Global health guidance + population statistics | public API (GHO OData); ICD-11 API needs a free client-id/secret |
| **CDC** | US public-health guidance | public site; no key |
| **MedlinePlus** (NLM/NIH) | Consumer health information | public API/XML feed; **must carry NLM courtesy attribution line verbatim, no logo** |
| **NCBI Bookshelf** (StatPearls etc.) | Reference works | public via NCBI E-utilities |

## Tier 2 — Research literature (evidence-integrity layer, Layer 3 hypothesis support only)

| Library | Use | Access |
|---|---|---|
| **PubMed / NCBI E-utilities** (`esearch`, `efetch`, `esummary`) | Round-trip-verify every citation before it is shown: real PMID, not retracted, title matches claim | public API; register an NCBI API key for higher rate limits |
| **PubMed attribution rule** | Any cited item must carry "cite PubMed + DOI link" per NCBI's legal attribution terms | enforced by `pubmed_attribution_ok` guard |

**Fail-closed rule:** a network error/timeout on citation round-trip → **WITHHOLD**, never show unverified. A
not-found PMID → **DROP** (treat as fabricated). A retracted or title-mismatched record → **DROP**.

## Tier 3 — Drug / treatment reference (medication & high-risk rule, verbatim-only)

| Library | Use | Access |
|---|---|---|
| **openFDA** (drug label, event, NDC endpoints) | Verbatim label text, **approved sections only** — dosage/administration section is hard-blocked | public API; no key required for low volume |
| **DailyMed** (NLM) | Verbatim structured product labels | public API |
| **FAERS** (via openFDA) | Adverse-event **population signal only** (aggregate units: reporting rate, cases-per-million, PRR) — never a personal-risk number | public API |
| **National formulary / FDA / EMA / Thai FDA labels / British National Formulary / Lexicomp** | Country-specific drug reference | licensed or public depending on source; jurisdiction-tagged |

## Tier 4 — Trials / population registries (pointer-only, never interpreted)

| Library | Use | Access |
|---|---|---|
| **ClinicalTrials.gov** | "Active research exists" pointer with verified NCT ID | public API |
| **WHO ICTRP** | International trial registry pointer (TCTR/ISRCTN/ACTRN/ChiCTR/DRKS/EUCTR IDs) | public search interface; no-commercial-use / no-emblem terms apply |
| **WHO GHO** | Population health statistics — must carry a jurisdiction provenance tag; a US/global rate must never be rendered as Thai-applicable without an explicit tag | public OData API |

## Tier 5 — Instrument reference (education only, never scored on a person)

| Instrument | Use |
|---|---|
| **PHQ-9 / GAD-7 / EPDS published bands** | Explain generically only; do not compute or assign a score to the user; item-9 (PHQ-9) / item-10 (EPDS) self-harm content routes straight to the crisis pathway |

## Tier 6 — Terminology & interoperability standards (so codes/labels stay machine-consistent)

| Library | Use | Access |
|---|---|---|
| **ICD-11 (WHO)** | Diagnosis coding — **ClinicianHandoff path only, never shown on the user-facing path**, self-hosted / zero-egress preferred | free API with client-id/secret |
| **SNOMED CT** | Clinical concept normalization for internal structuring of symptoms/findings | licensed (SNOMED International / national release centre, e.g. NHS in UK, Thai release where available) |
| **LOINC** | Lab/observation code normalization so lab values map to a stable identifier + unit + reference-range convention | free registration |
| **RxNorm / RxNav (NLM)** | Drug name normalization + drug-drug interaction lookups (informational, not a prescribing act) | public API |
| **UMLS Metathesaurus** | Cross-mapping between vocabularies (SNOMED/ICD/LOINC/RxNorm) when reconciling multi-source data | free UMLS license (NLM) |
| **Orphanet** | Rare-disease nomenclature, only for context/education, never diagnosis | public |

## Tier 7 — Evidence-quality / systematic-review layer (raises hypothesis quality above single-study citation)

| Library | Use | Access |
|---|---|---|
| **Cochrane Library** (systematic reviews) | Highest-tier synthesized evidence for a claim; prefer over a single primary study when available | licensed (Cochrane) or open abstracts |
| **Europe PMC** | Full-text biomedical literature search, complements PubMed (better full-text coverage) | public API |
| **Semantic Scholar API** | Citation-graph context (is this claim widely replicated or an outlier?) | public API, free key |
| **Crossref API** | DOI resolution/validation for any citation carrying a DOI (catches fabricated DOIs) | public API |
| **PROSPERO** | Registered systematic-review protocols — supports "is this an active area of rigorous review" claims | public search |
| **GRADE framework** | Evidence-quality grading vocabulary (high/moderate/low/very-low certainty) — apply this label whenever a Layer-3 hypothesis cites literature, so confidence is never overstated | methodology, not an API — apply as a labelling convention |

## Tier 8 — Specialty-society and population-health anchors (deepen Layer 2 for common chronic domains)

| Library | Use | Access |
|---|---|---|
| **ADA Standards of Care** (diabetes) | Endocrine/metabolic domain anchor | public |
| **AHA/ACC guidelines** (cardiology) | Cardiovascular domain anchor | public (some behind society membership) |
| **NCCN Guidelines** (oncology) | Cancer domain anchor | free registration |
| **GOLD/GINA** (COPD/asthma) | Respiratory domain anchor | public |
| **KDIGO** (kidney disease) | Renal domain anchor | public |
| **WHO Global Burden of Disease (IHME GBD)** | Population-level burden context (never a personal risk number) | public, aggregate-only |
| **mhGAP Intervention Guide (WHO)** | Mental-health first-contact structure already used as the crisis-screen scaffold in this repo's `birca_gates.py` | public |

## Tier 0 — Identifier & retraction integrity (runs before any Tier 1-8 item is shown)

| Library | Use | Access |
|---|---|---|
| **Retraction Watch Database** | Cross-check a citation is not on the retracted list before surfacing it | licensed/CSV dump, or via Crossref's retraction metadata where flagged |
| **ORCID** | Author-identity verification when a claim is attributed to a named researcher | public API |

## Integration pattern (reference implementation already exists in this repo)

```
research/governance/sim/birca_gates.py          # pure, fail-closed guards (license, jurisdiction, drug, trial, evidence)
research/governance/sim/birca_live_evidence.py  # live PubMed round-trip via an injectable fetch (deterministic for tests)
```

Any new deployment (Claude, OpenAI, or other) that wires this skill to live tools should implement the same
shape: **a pure decision guard function + an injectable network fetch**, so the safety logic stays testable
and the live call stays swappable per platform (Claude tool-use / OpenAI function-calling / plain HTTP
client for a generic system).

## Non-negotiable

- No clinical fact is stated from parametric memory alone when a Tier 1-4 library call is available and the
  claim is checkable. If none is available, the skill must say "cannot verify current guidance" and default
  to the safer, broader referral.
- Every library call is READ-ONLY. Nothing in this skill writes to any external system, prescribes, or
  transmits identifiable patient data outbound to any of these libraries.

## Theoretical/mathematical grounding (separate from clinical evidence above — internal-consistency tier)

`research_universal_solver` (`src/anse_spine/solvers/birca_repair.py`, `health_atlas.py`; PR
`morrocwi/research_universal_solver#7`, not yet merged) re-derives BIRCA's repair-loop dynamical objects as
faces of that project's canonical spine equation, fixing 3 concrete faults in the source monograph's literal
Eq(2)/Eq(4)/Eq(3-7) and verifying (by real numerical integration, not assertion) that the corrected form
reproduces the bistability/hysteresis/critical-slowing-down the monograph's own prose claims. Claim tier:
`finite_diagnostic`/`Dr` (internal mathematical consistency, readout-not-truth) — **this is not clinical or
empirical evidence** and must never be cited as such; it does not substitute for, or get mixed into, the
Tier 0-8 clinical evidence libraries above. See `spec/birca_universal_skill.yaml`
→ `dynamic_graph_boundary.mathematical_consistency_finding` for the full, scoped statement.

## Cross-domain literature corroboration — physical AND mental health (independent published sources, not
## BIRCA-derived)

The mathematical FORM used by BIRCA's corrected repair-loop equation (a double-well/cusp potential with a
restoring term) and its allostatic-burden concept are not ad hoc — the same structural forms appear
independently, with real citations, in established quantitative physiology and affective-science /
clinical-psychology literature. This is **structural corroboration of the equation FORM only** — it does
**not** validate BIRCA's own specific scores, thresholds, or intervention rankings; the same
`plausibility_vs_validation` standard in `spec/birca_universal_skill.yaml` applies. Verified (real numerical
integration, `finite_diagnostic` tier) by the maintainer, code not shipped in this repo:

- **Mood cusp / bistable affect** — van der Maas, H.L.J. et al. (2003), catastrophe/cusp model of
  hysteresis applied to affect; independently uses the identical cusp potential `V(m)=m⁴/4 − m²/2 + hm`
  that BIRCA's corrected repair equation uses, with control `h` read as life-stress minus support instead
  of BIRCA's burden-minus-causal-safety.
- **Affect "home base" (Ornstein-Uhlenbeck)** — Kuppens, P. et al. (2010), *Emotion*: mood reverts to an
  individual baseline with characteristic variability — the same linear-relaxation form as BIRCA's
  corrected causal-safety equation.
- **Critical slowing down as an early-warning signal** — Scheffer, M. et al. (2009), *Nature*; van de
  Leemput, I.A. et al. (2014), *PNAS*, applied to depression relapse: rising autocorrelation/variance near
  a tipping point. Same phenomenon as BIRCA's claimed critical-slowing-down (monograph sec 3.5) — **honest
  caveat: this specific early-warning signature is reported in that literature as mostly-not-novel /
  weak-evidence for real-world clinical prediction**, not a strong validated early-warning tool; cited here
  for structural correspondence only, not as proof of clinical utility.
- **Symptom-network theory of psychopathology** — Borsboom, D. & Cramer, A.O.J. (2013), *Annual Review of
  Clinical Psychology*; Cramer, A.O.J. et al. (2016): symptoms causally activate one another; strong
  coupling sustains a self-reinforcing symptomatic state after a stressor is removed (multistability), weak
  coupling returns to baseline. Structurally the same "strong coupling sustains, weak coupling clears"
  pattern BIRCA's repair/burden framing describes for the biopsychosocial domain (Layer 0b). Requires an
  added gradient-flow-closure assumption to map onto a potential-well form; flagged as such in the source
  literature, not an intrinsic property of the raw network model.
- **HPA axis (stress-hormone) dynamics** — a 3-node CRH→ACTH→cortisol negative-feedback cascade (canonical
  form in the endocrine-modeling literature, e.g. Andersen-class HPA models) is the physiological substrate
  most directly underlying "chronic burden"/allostatic load — cortisol dysregulation from sustained
  activation without adequate negative feedback is the biological mechanism BIRCA's burden concept is a
  report-level abstraction OF, not a claim that replaces it.
- **Circadian rhythm** — a delayed-negative-transcriptional-feedback ~24h limit cycle (Goodwin-type,
  Leloup–Goldbeter 1999 reduced form) underlies sleep/wake regulation, relevant background for any
  biopsychosocial intake that touches sleep disruption.

None of the above upgrades BIRCA's own claim tier, eligibility gates, or "report-level projection, not
proven physiological law" framing. It is cited to show the equation forms BIRCA borrows are recognized,
independently-published structures in physiology and affective/clinical-psychology science — not
inventions unique to, or validated specifically for, this skill.
