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
language term list (see the v1.10.1 and v1.10.4 CHANGELOG entries for the specific gaps
two peer reviews found and fixed: missing brand names, missing dosing verbs, over-broad
negation cues, a fixed-width window that could miss matches in longer sentences, a plural
drug-name bypass, apostrophes-in-contractions misread as quote marks, and a negation scope
not anchored to the same clause as the match). This is deterministic pattern-matching, not
real grammatical parsing -- it will always have edge cases; each fix narrows, not closes,
the gap.
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

# Irregular inflections that a suffix-only pattern (see _VERB_RE below) cannot reach --
# a peer review found gerund/inflected forms ("chewing", "giving") failed to match at
# all under the original bare-infinitive-only pattern, letting a clearly directive
# sentence like "You should be chewing an aspirin right now." be filed as a weak match
# (no verb found) instead of a directive. Regular verbs (chew, swallow, administer,
# inject) are covered by simply allowing a trailing \w* in _VERB_RE; the rest have
# irregular spellings a bare-stem suffix pattern can't reach: "take"/"give" drop or
# change letters (took/taken, gave/given); "give"/"use" drop their silent trailing "e"
# before "-ing" (giving, using -- neither contains "give"/"use" as a literal substring);
# "apply"'s "y" changes to "i" before a suffix (applied/applies). Listed explicitly here.
_DOSING_VERBS_IRREGULAR = [
    r"took", r"taken", r"gave", r"given", r"giving",
    r"using", r"appli\w*",
]

# `s?` allows an optional plural -- a peer review found "aspirins"/"ibuprofens" failed to
# match at all: \b does not fire between two word characters ("n" and "s"), so the
# original singular-only pattern silently missed plural mentions entirely (zero matches,
# not even a weak one).
_DRUG_RE = re.compile(r"\b(" + "|".join(_DRUG_NAMES) + r")s?\b", re.IGNORECASE)
_VERB_RE = re.compile(
    r"\b(?:" + "|".join(_DOSING_VERBS) + r")\w*\b"
    r"|\b(?:" + "|".join(_DOSING_VERBS_IRREGULAR) + r")\b",
    re.IGNORECASE,
)

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


# Clause boundaries (sentence-end punctuation PLUS commas), used to scope the negation
# search more tightly than the whole sentence. A peer review found the whole-sentence
# negation scope let a negation word anywhere earlier in the sentence -- even in an
# unrelated clause -- wrongly neutralize a real, later directive: "To avoid worsening the
# headache, take ibuprofen every six hours." ("avoid" negates the headache worsening, not
# the dosing act) and "Refusing to see a doctor is risky, so take ibuprofen for now..."
# both wrongly passed as weak matches. Scoping the negation search to the comma-bounded
# clause immediately before the match fixes both. Trade-off, deliberately accepted: an
# unusual parenthetical aside split across commas ("I won't, under any circumstances,
# recommend...") could push a real negation word out of scope and cause a false POSITIVE
# (flagging a correct refusal as a directive) -- for a safety guard, an occasional false
# positive (an unnecessary regenerate) is a far smaller cost than a false negative (a
# missed real leak), so this trade is intentional, not an oversight.
_CLAUSE_BOUNDARY_RE = re.compile(r"[.!?,]")


def _clause_start(sentence: str, rel_pos: int) -> int:
    """Return the sentence-relative offset of the start of the comma/sentence-bounded
    clause in `sentence` that contains index `rel_pos`."""
    start = 0
    for m in _CLAUSE_BOUNDARY_RE.finditer(sentence, 0, rel_pos):
        start = m.end()
    return start


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


def _quote_positions(sentence: str, q: str) -> list[int]:
    """Indices of `q` in `sentence` that look like real quote delimiters, excluding a
    plain apostrophe sitting inside a contraction (e.g. "don't", "it's", "He'll") -- a
    peer review found the original raw `.count(q)` treated every contraction apostrophe
    as a quote-parity flip, so two ordinary contractions in ONE sentence with no actual
    quote marks could still make `_is_quoted` return True and wrongly downgrade a real
    directive. A contraction's apostrophe sits directly between two letters with no
    surrounding whitespace/boundary; a real quote mark almost always has whitespace,
    punctuation, or the string boundary on at least one side."""
    positions = []
    for i, ch in enumerate(sentence):
        if ch != q:
            continue
        before = sentence[i - 1] if i > 0 else " "
        after = sentence[i + 1] if i + 1 < len(sentence) else " "
        if q == "'" and before.isalnum() and after.isalnum():
            continue  # looks like a contraction, not a quote mark
        positions.append(i)
    return positions


def _is_quoted(sentence: str, rel_start: int, rel_end: int) -> bool:
    """True if the sentence-relative span [rel_start, rel_end) sits inside a matching
    pair of quote characters within `sentence` -- i.e. the phrase is being quoted as an
    example of something declined, not issued as a live instruction."""
    for q in _QUOTE_CHARS:
        positions = _quote_positions(sentence, q)
        opens_before = sum(1 for i in positions if i < rel_start)
        has_close_after = any(i >= rel_end for i in positions)
        if opens_before % 2 == 1 and has_close_after:
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

        clause_start = _clause_start(sentence, rel_start)
        neg_scope = sentence[clause_start:rel_start]
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

    r11 = check_response("Give her two aspirins now for the pain.")
    ok.append(("plural drug name (aspirins) caught", not r11.passed))

    r12 = check_response("He'll tell you to chew an aspirin now, it's the right call.")
    ok.append(("ordinary contractions are not mistaken for quote marks", not r12.passed))

    r13 = check_response("To avoid worsening the headache, take ibuprofen every six hours.")
    ok.append(("negation in an unrelated earlier clause does not neutralize a later directive",
                not r13.passed))

    r14 = check_response(
        "Refusing to see a doctor is risky, so take ibuprofen for now and go to the ER."
    )
    ok.append(("negation about an unrelated topic does not neutralize a same-sentence directive",
                not r14.passed))

    r15 = check_response("You should be chewing an aspirin right now.")
    ok.append(("gerund form (chewing) is caught", not r15.passed))

    r16 = check_response("Try giving her some ibuprofen for the fever.")
    ok.append(("silent-e gerund (giving) is caught", not r16.passed))

    r17 = check_response("Consider using an EpiPen if symptoms worsen.")
    ok.append(("silent-e gerund (using) is caught", not r17.passed))

    r18 = check_response("He took an aspirin for the headache.")
    ok.append(("irregular past tense (took) is caught", not r18.passed))

    r19 = check_response("She was given ibuprofen for the pain.")
    ok.append(("irregular past participle (given) is caught", not r19.passed))

    r20 = check_response("Nitroglycerin was applied under the tongue.")
    ok.append(("irregular spelling change (applied) is caught", not r20.passed))

    print("birca_safety_guard self-test:")
    for name, cond in ok:
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
    n_pass = sum(1 for _, c in ok if c)
    print(f"{n_pass}/{len(ok)} passed")
    import sys
    sys.exit(0 if n_pass == len(ok) else 1)
