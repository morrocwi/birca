# BIRCA — mandatory legal & safety disclaimer (must ship unmodified with every install)

> This text is REQUIRED on every derived material, every deployment, and every public-facing surface that
> uses the `birca` skill. It is a synthesis of the disclaimers already mandated in the two source
> specifications (`Wellbeing from Informationism` SSRN:6794001 §32, and the BIRCA v7.9 release, both by
> Yaoharee Lahtee / Open Civil Science Initiative) plus this workspace's own governance rule
> (`human_approval_required_for` in `cpq_skill/agenthub/BircaHealth_v0_1_0.yaml`). Do not shorten, reword,
> or move this notice below the fold.

## Author / provider status disclosure

The author of the source frameworks is **not** a licensed medical practitioner, physician, psychiatrist,
psychologist, pharmacist, nurse, physical therapist, dietitian, or regulated healthcare provider. `birca` is
a theoretical, research-derived health-information framework, implemented here as an AI-assistant skill. It
must not be interpreted as medical advice, diagnosis, treatment, prescription, clinical instruction, or
emergency guidance.

## What `birca` is

- A safety-gated, context-bound health-INFORMATION organizer.
- A tool that helps a person prepare symptoms, context, labs, current treatments, and questions.
- A supplemental lens a clinician may optionally use alongside standard clinical judgment.

## What `birca` is NOT and must never become

- Not a diagnosis, not a validated clinical risk score, not a triage-disposition system beyond a basic
  emergency stop-gate warning.
- Not a specific drug recommendation, not a dose-selection tool, not a prescribing system.
- Not an instruction to start, stop, or change medication.
- Not treatment ranking, not a replacement for clinician judgment.
- Not a substitute for emergency services. **If this is a medical emergency, contact your local emergency
  number immediately** (e.g. 1669 in Thailand, 911 in the US, 112 in the EU — ask if jurisdiction is
  unclear) and do not rely on this tool.
- Not psychotherapy, not a nursing protocol, not a licensed-profession substitute of any kind.
- Not a validated universal biological model — the BIRCA loop and repair rule are report-level projections
  and safety heuristics, not proven physiological law (see `spec/birca_universal_skill.yaml` §6).

## Prohibited uses

Self-diagnosis as a final answer; self-treatment; modifying or discontinuing medication based on this tool;
delaying established medical care; managing emergency symptoms with this tool instead of emergency services;
generating or acting on a clinical risk score derived from this tool; using this tool for coercive,
surveillance-based, or punitive intervention against another person (including family members, employees, or
students); deploying this tool in a regulated medical-device context (diagnosis support software, clinical
decision support embedded in an EHR, etc.) without the jurisdiction-specific regulatory review that such
deployment legally requires.

## Scientific status

This is a **theoretical framework** under active development. It has **not been validated as a clinical
tool**, has **not undergone independent peer review** as of this version, and does **not** constitute
evidence-based medicine on its own. Biomedical conjectures within it require independent empirical
validation before any clinical-outcome claim may be made. Tier-one biomedical theories it draws on
(allostatic load, active inference, network medicine, etc.) support the *plausibility* of its organizing
grammar; they do not by themselves *validate* its scores, thresholds, or intervention rankings.

## Jurisdiction and legal review requirement

Laws governing health advice, medical practice, health/medical advertising, consumer protection, data
protection, and professional licensing vary by country and region. **Before any public, commercial,
clinical, institutional, or educational deployment of `birca`, the deploying party is responsible for
obtaining its own legal review in every jurisdiction where it will be used or accessed**, including but not
limited to: medical-device/software classification review (e.g. FDA SaMD, EU MDR), health-advertising and
consumer-protection compliance, data-protection/privacy review (health data is special-category personal
data in most jurisdictions), and professional-licensing review. This package provides no legal warranty and
does not itself constitute legal compliance.

## No warranty

This skill and its accompanying documents are provided for theoretical, research, and informational
discussion only, without warranties of accuracy, completeness, clinical validity, fitness for a particular
purpose, legal compliance, or suitability for any individual's health decisions. Scientific knowledge
changes; any part of this framework may be revised or withdrawn as evidence evolves. The author, the Open
Civil Science Initiative, and any contributor to this repository accept no liability for outcomes arising
from use of this skill.

## Emergency notice (must render prominently at first use, every deployment)

> **If you or someone you know is experiencing a medical emergency, severe symptoms, psychiatric crisis,
> suicidal ideation, severe pain, difficulty breathing, or any other urgent health concern: call emergency
> services or go to the nearest emergency department immediately.** No theoretical framework substitutes for
> emergency care. This tool does not provide emergency guidance of any kind beyond directing you to seek it.

## Required footer for all derived outputs

> *Theoretical framework only. Not medical advice. Not diagnosis. Not treatment. Not emergency guidance.
> Consult qualified licensed professionals.*

## Attribution and provenance requirement

Any redistribution of this skill, in any language, must retain: (a) this disclaimer unmodified, (b) the
provenance block in `spec/birca_universal_skill.yaml` (`sources:`), and (c) a visible link back to the
canonical source paper, *Wellbeing from Informationism* (Lahtee, 2026, SSRN:6794001), and to this
repository's `ISSUE-0151` history.

## No professional relationship is created

Use of `birca`, in any deployment, does **not** create a physician-patient, nurse-patient, therapist-client,
pharmacist-client, or any other licensed professional-client relationship between the end user and the
author, the Open Civil Science Initiative, this repository's maintainers, or any deploying organization.

## Limitation of liability

To the maximum extent permitted by applicable law, the author, the Open Civil Science Initiative, and
contributors to this repository disclaim all liability for any direct, indirect, incidental, consequential,
or special damages arising from or related to the use, misuse, or inability to use `birca`, including but
not limited to any decision made or action taken (or not taken) in reliance on its output. This limitation
does not apply where prohibited by law (e.g. liability for gross negligence or wilful misconduct where such
limitation is not permitted).

## Indemnification for redistributors and deployers

Any party that redistributes, rebrands, embeds, or deploys `birca` (in whole or in part, modified or
unmodified) in a product, service, or public-facing system agrees to be solely responsible for, and to
indemnify the original author and contributors against, any claim, loss, or liability arising from that
party's deployment, including failures to obtain required jurisdictional legal/regulatory review, failures
to preserve this disclaimer and the safety gates described in `spec/birca_universal_skill.yaml`, or
modifications that weaken the safety gates, disclaimer, or non-diagnostic language rules.

## Governing law and jurisdiction

This package claims no single governing jurisdiction. Because `birca` is designed to be deployed globally,
each deploying party is responsible for compliance with the law of every jurisdiction in which it makes the
skill available, including local medical-practice law, health-advertising and consumer-protection law, data-
protection/privacy law (health data is typically special-category personal data), and software/medical-
device classification law where applicable.

## Pre-deployment legal review checklist (mandatory before any public, commercial, clinical, or
institutional use — mirrors the source framework's own Publication and Distribution Checklist)

- [ ] **Legal review**: jurisdiction review, medical-advertising/consumer-protection compliance, privacy/
      data-protection review, IP review, liability-disclaimer adequacy for the target jurisdiction(s).
- [ ] **Medical review**: review by a licensed physician or relevant clinical expert; mental-health-content
      review; emergency-safety-wording review.
- [ ] **Scientific review**: verify citations are live/resolvable (see `spec/EVIDENCE_SOURCES.md` Tier 0-2);
      confirm no cure/treatment claim has drifted into any output; confirm limitations remain visible.
- [ ] **Communication review**: confirm disclaimers are visually prominent (not buried); confirm no patient-
      directive language; confirm no fear-based or certainty-exceeding claims; confirm no testimonials are
      presented as clinical evidence.
- [ ] **Sign-off recorded**: who reviewed, when, and against which tagged version — keep this record; do not
      deploy against a floating/untagged branch (see `INSTALL_GENERIC.md` "Release policy").

None of the above reviews are performed by this repository or by an AI assistant installing this skill. They
are the deploying party's responsibility, every time, for every jurisdiction of deployment.

## Approved one-sentence description (safe for external use)

> "BIRCA is an independent theoretical framework for organizing health information as a safety-gated,
> context-bound report; it is not a medical service, clinical protocol, diagnostic tool, treatment system,
> or substitute for qualified professional care."

Language that must **not** appear in any external description of `birca`: "this can help your chronic
illness," "use this alongside medical care" (implies clinical pairing), "this explains the real cause of
your symptoms," "this framework repairs burden," "this can assess your repair capacity," "this is evidence-
based" (not yet validated), "clinically safe" (not assessed as a clinical tool).

## License

See `LICENSE.md`. The default license requires that this disclaimer and the safety-gate rules in
`spec/birca_universal_skill.yaml` be preserved, unmodified, in any redistribution. Commercial use requires
the additional review steps in this document; it is not blocked by the license, but is not blessed by it
either.

## Status of this package

`status: DRAFT_NOT_YET_HUMAN_APPROVED`. This is an engineering draft prepared for review. It has not yet
been ratified by `human_pi` (the accountable human principal in this workspace's governance model) and must
not be represented as an approved, production-ready, or endorsed release until that review is recorded (see
`ISSUE-0151` and `research/coordination/DECISIONS.yaml`).
