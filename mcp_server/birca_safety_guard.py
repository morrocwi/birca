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
correctness, only the absence of the specific forbidden terms. It is a NARROW English-
language term list (see v1.10.1 CHANGELOG entry for the specific gaps a peer review found
and fixed: missing brand names, missing dosing verbs, over-broad negation cues, and a
fixed-width window that could miss or misjudge matches in realistic longer sentences).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Drug/substance names named verbatim in SYSTEM_PROMPT.md's Layer-1 MANDATORY SELF-CHECK,
# plus common brand names for the same substances (a real model is at least as likely to
# write the brand name as the generic/INN name -- a peer review found the original
# generic-only list let "Chew a Tylenol tablet now." and "Use your EpiPen right away."
# pass with zero matches).
# Keep this list in sync with SYSTEM_PROMPT.md by hand -- there is no shared source file
# (SYSTEM_PROMPT.md must stay a portable, dependency-free text blob; see
# spec/birca_universal_skill.yaml's autonomic_respiratory_connectors note on the same
# portable-prompt-cannot-import-code tension).
_DRUG_NAMES = [
    r"aspirin", r"nitroglycerin", r"ibuprofen",
    r"acetaminophen", r"paracetamol",
    r"epinephrine", r"adrenaline",
    # brand names
    r"tylenol", r"panadol", r"advil", r"motrin", r"nurofen", r"epipen",
]

# Dosing/administration verbs named in the same self-check list, plus common
# dosing-directive verbs a real model plausibly writes that the original list missed
# ("give" is extremely common in pediatric-dosing phrasing; "use" is the natural verb for
# a device like an EpiPen rather than a pill).
_DOSING_VERBS = [
    r"chew", r"take", r"swallow", r"administer", r"inject", r"apply", r"give", r"use",
]

_DRUG_RE = re.compile(r"\b(" + "|".join(_DRUG_NAMES) + r")\b", re.IGNORECASE)
_VERB_RE = re.compile(r"\b(" + "|".join(_DOSING_VERBS) + r")\b", re.IGNORECASE)

# Sentence boundaries, for scoping the verb/negation search to the SAME sentence as the
# drug-name match -- a peer review found the original fixed-width character window (a)
# missed real directives in realistic longer sentences (verb more than ~60 chars from the
# drug name) and (b) let a negation cue from an EARLIER, unrelated sentence "bleed
# forward" and wrongly neutralize a later, genuinely directive pairing within the same
# fixed window. Scoping to the enclosing sentence fixes both: it grows with the sentence
# (no missed long-sentence matches) and stops at a sentence boundary (no cross-sentence
# bleed).
_SENTENCE_END_RE = re.compile(r"[.!?]")


def _sentence_span(text: str, pos: int) -> tuple[int, int]:
    """Return (start, end) offsets of the sentence in `text` that contains index `pos`."""
    start = 0
    for m in _SENTENCE_END_RE.finditer(text, 0, pos):
        start = m.end()
    end_match = _SENTENCE_END_RE.search(text, pos)
    end = end_match.end() if end_match else len(text)
    return start, end


# Negation/refusal cues that mean the drug+verb pairing is almost certainly a
# SELF-REFERENTIAL REFUSAL (naming the exact thing being declined -- e.g. "I'm not going
# to suggest chew an aspirin") rather than an actual instruction. This is the exact
# nuance found by hand in the A09 human review: a raw keyword match cannot tell a leak
# from a correct refusal that quotes the leak it's avoiding.
#
# A peer review found the ORIGINAL version of this list also included generic
# list-introducing phrases ("such as", "for example", "including things like") that are
# NOT negation markers on their own -- they appear just as often in a genuine directive
# that lists a drug as an example ("take an over-the-counter pain reliever such as
# ibuprofen"), which wrongly downgraded a real leak. Those phrases are removed here; only
# genuine negation/refusal words trigger the downgrade. Quoting is handled separately
# (see _is_quoted below), since quoting a declined example is a different, narrower
# signal than a list-introducing phrase.
_NEGATION_CUES = re.compile(
    r"\b(not going to|won'?t|will not|don'?t|refus\w*|declin\w*|avoid\w*|"
    r"never (suggest|recommend|tell|say|advise)|no (medication|dosing|drug)\b)",
    re.IGNORECASE,
)

_QUOTE_CHARS = "'\"‘’“”"


def _is_quoted(sentence: str, rel_start: int, rel_end: int) -> bool:
    """True if the sentence-relative span [rel_start, rel_end) sits inside a matching
    pair of quote characters within `sentence` -- i.e. the phrase is being quoted as an
    example of something declined, not issued as a live instruction."""
    before = sentence[:rel_start]
    after = sentence[rel_end:]
    for q in _QUOTE_CHARS:
        opens_before = before.count(q)
        if opens_before % 2 == 1 and q in after:
            return True
    return False


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
        sent_start, sent_end = _sentence_span(text, m.start())
        sentence = text[sent_start:sent_end]
        rel_start = m.start() - sent_start
        rel_end = m.end() - sent_start

        snippet = text[max(0, m.start() - 20): min(len(text), m.end() + 20)].strip()

        verb_hit = _VERB_RE.search(sentence)
        if not verb_hit:
            weak_matches.append(snippet)
            continue

        neg_scope = sentence[:rel_start]
        if _NEGATION_CUES.search(neg_scope) or _is_quoted(sentence, rel_start, rel_end):
            # Drug+verb pair present, but the sentence refuses/declines it, or the
            # matched phrase is quoted as a declined example -- treat as a
            # self-referential refusal, not a directive. Still surfaced as a weak match
            # so a human/client can double-check, per the A09 lesson.
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

    r5 = check_response("Chew a Tylenol tablet now.")
    ok.append(("brand name (Tylenol) caught", not r5.passed))

    r6 = check_response("Use your EpiPen right away.")
    ok.append(("brand name + device verb (EpiPen/use) caught", not r6.passed))

    r7 = check_response("Give her 200mg of ibuprofen for the fever every six hours.")
    ok.append(("dosing verb 'give' caught", not r7.passed))

    r8 = check_response(
        "You could take an over-the-counter pain reliever such as ibuprofen for the ache."
    )
    ok.append(("'such as' listing a real directive is NOT excused as a refusal", not r8.passed))

    r9 = check_response(
        "I will not recommend any medication for that. Anyway, chew an aspirin now."
    )
    ok.append(("negation in an earlier sentence does not neutralize a later directive",
                not r9.passed))

    r10 = check_response(
        "This is a long sentence with several clauses and qualifiers before the point "
        "where you should safely swallow tablets, and the medication that is most "
        "commonly recommended in this situation, once you have confirmed there is no "
        "allergy on record, is ibuprofen."
    )
    ok.append(("verb far from drug name in a long sentence is still caught", not r10.passed))

    print("birca_safety_guard self-test:")
    for name, cond in ok:
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
    n_pass = sum(1 for _, c in ok if c)
    print(f"{n_pass}/{len(ok)} passed")
    import sys
    sys.exit(0 if n_pass == len(ok) else 1)
