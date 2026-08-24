# Writing for people and agents

Use this reference when creating or materially restructuring maintained repository documents.

## Shared document contract

A document should be readable linearly by a person and addressable in small sections by an agent. Prefer:

- a descriptive title and a two-to-five sentence purpose/current-state summary;
- headings that name domain concepts rather than generic buckets;
- a visible scope and canonical owner/source;
- links to deeper or authoritative material near the claim they qualify;
- decision tables for repeated mappings and state diagrams only when relationships are otherwise hard to follow;
- concrete repository-relative commands and paths where they are stable;
- explicit failure, recovery, compatibility, and recheck conditions when relevant.

Avoid:

- prose versions of source code or manifests;
- exhaustive file listings;
- duplicated instructions across root and component documents;
- headings with no useful content or generated template filler;
- chronology that Git already preserves;
- claims such as "enforced" without a real test, lint, CI, or runtime control;
- model transcripts, confidence scores, raw scan output, or machine-local paths in maintained prose.

## Index writing

A stable index should help a new maintainer answer in a few minutes:

- what the repository/product is and is not;
- which components exist and why;
- where public contracts and operational boundaries live;
- which commands are canonical for setup and verification;
- where architecture, decisions, runbooks, workstreams, and generated references live;
- who or what owns ambiguous cross-component decisions.

Describe component purpose and boundary, not every directory. Link to the component's own entrypoint instead of copying its documentation.

## Decision and runbook writing

An ADR preserves context, choice, credible alternatives, consequences, compatibility/rollout concerns, and a recheck or supersession trigger.

A runbook preserves trigger, authority/prerequisites, safe plan or dry-run, execution command, observation, failure interpretation, recovery/rollback, and completion evidence. The runbook should call deterministic automation rather than duplicate its internal steps.

## Freshness

Every durable document should have a natural recheck trigger even when it does not carry an explicit date. Examples include a manifest change, public-contract revision, component ownership change, release workflow change, fork sync, incident lesson, or superseding ADR.

Prefer repository-native link and documentation checks. Scheduled gardening may propose repairs, but inferred rules and policy promotions still require an owner.
