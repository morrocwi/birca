"""
birca_safety_guard.py -- deterministic, code-level guard for the birca skill.

Pure function, no LLM call, no network access. This is the "recommended stronger defense
for tool-calling-capable platforms" that spec/birca_universal_skill.yaml and
spec/V1_2_0_FIX_VERIFICATION_LOG.md have flagged as an open gap since v1.2.0 (the A09
finding: SYSTEM_PROMPT.md's own "MANDATORY SELF-CHECK" is a prompt-level instruction to
the model, which is a stochastic mitigation, not a deterministic one).

Scans a candidate response for the exact drug-name / dosing-verb combinations the
SYSTEM_PROMPT.md's Layer-1 self-check already names, using deterministic regex matching
-- not another LLM call. Designed to be run by any MCP-capable client, in tool-calling
mode, BEFORE sending a Layer-1 STOP response, as a second, independent check behind the
prompt-level one.

claim tier: this is ordinary code, not a clinical claim of any kind. It reduces (does not
eliminate) the residual risk of a medication-instruction leak; it cannot verify clinical
correctness, only the absence of the specific forbidden terms.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Drug/substance names named verbatim in SYSTEM_PROMPT.md's Layer-1 MANDATORY SELF-CHECK.
# Keep this list in sync with SYSTEM_PROMPT.md by hand -- there is no shared source file
# (SYSTEM_PROMPT.md must stay a portable, dependency-free text blob; see
# spec/birca_universal_skill.yaml's autonomic_respiratory_connectors note on the same
# portable-prompt-cannot-import-code tension).
_DRUG_NAMES = [
    r"aspirin", r"nitroglycerin", r"ibuprofen",
    r"acetaminophen", r"paracetamol",
    r"epinephrine", r"adrenaline",
]

# Dosing/administration verbs named in the same self-check list.
_DOSING_VERBS = [
    r"chew", r"take", r"swallow", r"administer", r"inject", r"apply",
]

# A verb within a short window of a drug name is treated as a directive-shaped match.
# A drug name mentioned alone (e.g. in a refusal: "I won't suggest aspirin") still flags
# as a WEAK match so a human/client can inspect context -- see BircaSafetyResult.weak_matches.
_WINDOW_CHARS = 60

# Negation/refusal cues that, if present in a wider window before the match, mean the
# drug+verb pairing is almost certainly a SELF-REFERENTIAL REFUSAL (naming the exact thing
# being declined -- e.g. "I'm not going to suggest 'chew an aspirin'") rather than an
# actual instruction. This is the exact nuance found by hand in the A09 human review: a
# raw keyword match cannot tell a leak from a correct refusal that quotes the leak it's
# avoiding. A quoted/parenthesized match is treated the same way -- quoting an example is
# not issuing it as a directive.
_NEGATION_WINDOW_CHARS = 100
_NEGATION_CUES = re.compile(
    r"\b(not going to|won'?t|will not|don'?t|refus\w*|declin\w*|avoid\w*|"
    r"never (suggest|recommend|tell|say|advise)|no (medication|dosing|drug)\b|"
    r"including things like|such as|for example|like ['\"])",
    re.IGNORECASE,
)

_DRUG_RE = re.compile(r"\b(" + "|".join(_DRUG_NAMES) + r")\b", re.IGNORECASE)
_VERB_RE = re.compile(r"\b(" + "|".join(_DOSING_VERBS) + r")\b", re.IGNORECASE)


@dataclass
class BircaSafetyResult:
    """Result of a deterministic scan. `passed=False` means at least one directive-shaped
    drug+verb pairing was found and the response should be regenerated before sending,
    per SYSTEM_PROMPT.md's fail-closed Layer-1 rule."""

    passed: bool
    directive_matches: list[str] = field(default_factory=list)
    weak_matches: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "directive_matches": self.directive_matches,
            "weak_matches": self.weak_matches,
        }


def check_response(text: str) -> BircaSafetyResult:
    """Scan `text` (a candidate birca Layer-1 STOP response) for drug-name + dosing-verb
    directive pairings. Deterministic, case-insensitive, language-agnostic only in the
    sense that it matches the English drug/verb terms literally -- non-English bystander
    conventions (the actual A35 finding) are NOT caught by this regex and remain reliant
    on the prompt-level instruction; this tool narrows, it does not close, the full gap.
    """
    drug_hits = list(_DRUG_RE.finditer(text))
    if not drug_hits:
        return BircaSafetyResult(passed=True)

    directive_matches: list[str] = []
    weak_matches: list[str] = []

    for m in drug_hits:
        window_start = max(0, m.start() - _WINDOW_CHARS)
        window_end = min(len(text), m.end() + _WINDOW_CHARS)
        window = text[window_start:window_end]
        verb_hit = _VERB_RE.search(window)
        snippet = text[max(0, m.start() - 20): min(len(text), m.end() + 20)].strip()

        if not verb_hit:
            weak_matches.append(snippet)
            continue

        neg_window_start = max(0, m.start() - _NEGATION_WINDOW_CHARS)
        neg_window = text[neg_window_start:m.start()]
        if _NEGATION_CUES.search(neg_window):
            # Drug+verb pair present, but preceded by a refusal/negation/quoting cue --
            # treat as a self-referential refusal, not a directive. Still surfaced as a
            # weak match so a human/client can double-check, per the A09 lesson.
            weak_matches.append(snippet)
        else:
            directive_matches.append(snippet)

    return BircaSafetyResult(
        passed=len(directive_matches) == 0,
        directive_matches=directive_matches,
        weak_matches=weak_matches,
    )


if __name__ == "__main__":
    # Minimal self-test, real execution -- not a substitute for the MCP-level test.
    ok = []

    r1 = check_response("Please chew an aspirin now and call emergency services.")
    ok.append(("directive-shaped leak is caught", not r1.passed and len(r1.directive_matches) == 1))

    r2 = check_response(
        "I'm not going to give medication or dosing suggestions of any kind here "
        "(including things like 'chew an aspirin') -- that decision needs a clinician."
    )
    ok.append(("self-referential refusal flagged only as weak, not directive",
                r2.passed and len(r2.weak_matches) >= 1))

    r3 = check_response("Sit down, call your local emergency number, and stay with someone.")
    ok.append(("clean non-medication response passes with zero matches",
                r3.passed and not r3.directive_matches and not r3.weak_matches))

    r4 = check_response("Take ibuprofen for the pain if you have some at home.")
    ok.append(("second drug/verb pair (ibuprofen/take) also caught", not r4.passed))

    print("birca_safety_guard self-test:")
    for name, cond in ok:
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
    n_pass = sum(1 for _, c in ok if c)
    print(f"{n_pass}/{len(ok)} passed")
    import sys
    sys.exit(0 if n_pass == len(ok) else 1)
