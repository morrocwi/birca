# BIRCA — license

> **This repository, and everything in it, is published FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY. IT IS
> NOT LICENSED FOR ANY COMMERCIAL USE.** "Commercial use" means any use intended for or directed toward
> commercial advantage or monetary compensation, in any form — selling access to it, embedding it (in whole
> or in part, modified or unmodified) in a paid product or service, using it to generate advertising or
> subscription revenue, offering it as part of a consulting/clinical/commercial deployment, or any other
> revenue-generating use. No commercial use of any kind is licensed without separate, explicit, written
> permission from the rights holder, obtained in advance.

**Status: in effect for this repository.** This file sets the license for the `birca` universal skill
package (`SYSTEM_PROMPT.md`, `spec/`, `INSTALL_*.md`, `LEGAL_DISCLAIMER.md`, `install.sh`, `README.md`, and
everything else in this repo). Ratified by the rights holder (`human_pi`) when authorizing this repo's
public release; see the source monorepo's `research/coordination/DECISIONS.yaml`
(`DEC-birca-universal-skill-2026-0709` and its public-release entry) for the decision record.

## License: CC BY-NC-SA 4.0, plus a mandatory-preservation condition

Content in this directory is proposed to be licensed under **Creative Commons
Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**:
<https://creativecommons.org/licenses/by-nc-sa/4.0/>

In addition to the standard CC BY-NC-SA terms, redistribution under this license is conditioned on:

1. **Preserve `LEGAL_DISCLAIMER.md` unmodified**, in full, in any redistribution or derivative — including
   translations (a translated derivative must carry both the translation and a link to this canonical
   English original).
2. **Preserve the safety gates** in `spec/birca_universal_skill.yaml` (Intake gate, Layer-1 emergency
   screen, diagnosis-language guardrail, medication/high-risk rule, prohibited-behaviours list, conflict-
   resolution precedence) unmodified in substance. You may translate or restyle the prose; you may not
   remove or weaken a gate.
3. **Attribute** the canonical source: *Wellbeing from Informationism* (Lahtee, Yaoharee, 2026,
   SSRN:6794001) and this repository's `ISSUE-0151` provenance trail.
4. **No commercial use without separate permission** from the rights holder (`human_pi` / the Open Civil
   Science Initiative) — this is the "NC" (non-commercial) clause and it is a hard requirement, not a
   suggestion. This repository exists to be studied, critiqued, and experimented with for education and
   research; it is not offered as, and must not be turned into, a commercial product or paid service without
   that separate written permission. A prospective commercial deployer must complete the pre-deployment
   legal review checklist in `LEGAL_DISCLAIMER.md` and obtain that permission before any revenue-linked use.

## Why CC BY-NC-SA and not MIT/Apache

Code-style permissive licenses (MIT/Apache) do not require preserving a disclaimer or a safety gate — a
redistributor could legally strip both and still comply with the license. Because `birca` touches health
information and carries an explicit clinical-safety boundary, a share-alike, attribution-required, non-
commercial-by-default license is the more defensible default until a human-reviewed, jurisdiction-cleared
commercial license is separately negotiated.

## Amending this license

Changing the license terms (allowing commercial use by default, dual-licensing, switching to a different
share-alike license) is a governance/business decision reserved to the rights holder (`human_pi`), recorded
as a new entry in the source monorepo's `research/coordination/DECISIONS.yaml` referencing `ISSUE-0151`.
