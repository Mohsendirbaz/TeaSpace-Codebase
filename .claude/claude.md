# CLAUDE.md

## Repository

You are working inside `Mohsendirbaz/TEA-MD`.

This repository already contains:
- a React application shell in `src/App.js`
- the main workflow shell in `src/HomePage.js`
- a lightweight version context in `src/contexts/VersionStateContext.js`
- the main current state hook and supporting classes in `src/Consolidated2.js`
- scaling editors, form configuration, monitoring modules, CFA execution paths, and visualization tabs connected through `HomePage`

Treat these files as the current architectural seams unless inspection shows newer replacements.

---

## Mission

You will receive a single file containing 5 major transformation prompts.

Treat those prompts as one coordinated transformation program, not as unrelated tasks.

You must execute them in strict sequence, with verification gates between phases.

Do not skip ahead.
Do not blend later-phase semantics into earlier-phase implementation unless strictly necessary to preserve compile integrity.
Do not preserve outdated semantics silently.

---

## Non-negotiable architectural rules

These rules override local convenience:

1. `zone` is no longer part of the core application model.
2. Each version is associated with exactly one baseline configuration.
3. Each baseline occupies exactly one version slot.
4. Baseline is not a raw snapshot of all tab inputs.
5. Baseline submission consists of:
    - direct field inputs from:
        - project configuration
        - loan configuration
        - rates and fixed costs
    - plus only enabled final results from:
        - process quantities
        - process costs
        - additional revenue quantities
        - additional revenue prices
6. Scaling is the transformation engine.
7. Summary is derived fact.
8. Scoped duration for scaling is assumed and must be preserved.
9. Generalized duration must become the canonical comparison fabric of the platform.
10. Sensitivity must not remain a separate state-authoring grammar if it can be expressed through the unified model.
11. Human and agent-authored changes must land in the same comparable model.
12. Provenance, governance, and cell-level inspectability must remain visible.

If current code conflicts with these rules, refactor toward these rules.

---

## Required sequencing

Execute the 5 prompts in this exact order.

### Phase 1 — Core state architecture
Target files first:
- `src/Consolidated2.js`
- `src/contexts/VersionStateContext.js`
- `src/HomePage.js`

Goal:
- replace the fragmented state model with a version-centric, comparison-ready architecture

Must finish before moving on:
- version is the primary analytical container
- baseline assembly has a defined home
- `zone` is removed from the primary model or clearly quarantined behind adapters
- old parallel stores are mapped, deprecated, or structurally subordinated

Do not deeply redesign UI yet.

---

### Phase 2 — Generalized duration as canonical comparison workspace
Target files:
- `src/HomePage.js`
- new comparison/generalized-duration components you add under `src/components/` or `src/modules/`

Goal:
- create the canonical comparison surface for versions, branches, and later agent candidates

Must finish before moving on:
- at least two versions can be compared on the same duration matrix
- overlay and delta work
- selected cells remain stable and inspectable

Do not rebuild scaling or sensitivity semantics yet unless required to connect comparison plumbing.

---

### Phase 3 — Scaling, derived facts, baseline assembly
Target files:
- `src/HomePage.js`
- `src/Consolidated2.js`
- `src/components/scaling/SimpleScalingEditor.*`
- `src/GeneralFormConfig.*`
- related helper modules

Goal:
- make scaling outputs duration-aware derived facts and explicitly assemble baselines

Must finish before moving on:
- baseline assembly is explicit
- derived facts are no longer opaque flat summaries
- admitted/excluded derived facts are inspectable

Do not preserve hidden late payload rewriting if it can be removed safely.

---

### Phase 4 — Collapse sensitivity into unified mutations and ledgers
Target files:
- `src/HomePage.js`
- `src/Consolidated2.js`
- `src/components/modules/SensitivityMonitor.*`
- any orchestration/helper code that still treats sensitivity as separate authoring state

Goal:
- remove sensitivity as a competing state grammar and preserve only useful orchestration/reporting behavior

Must finish before moving on:
- version/branch differences are explainable through the unified mutation model
- a linear mutation/delta ledger exists
- the old sensitivity model is wrapped, reduced, or deprecated

---

### Phase 5 — Agent-facing comparability and end-to-end validation
Target files:
- the new model/comparison files from earlier phases
- `src/HomePage.js`
- any services/helpers/tests/docs added for candidate versions and validation

Goal:
- make agent-generated candidates first-class comparable versions under the same reality model

Must finish before declaring success:
- humans and agents share the same comparison surface
- scorecards and governance are visible
- the validation suite proves the new model works

---

## Verification mechanism

You must not continue from one phase to the next without completing all 6 verification steps below.

### 1. Contract verification
For the current phase, write down:
- new contracts/types introduced
- old contracts/types deprecated
- adapters added
- unresolved gaps

Store this in:
`docs/transformation_checkpoints.md`

Append a new section per phase.

---

### 2. Build verification
At the end of each phase, run the strongest available checks from this repo.

Minimum expected checks:
- install dependencies if needed
- `npm test -- --watch=false` or closest stable equivalent
- `npm run build`
- any local lint/type validation available

If a check cannot run:
- say exactly why
- record it in `docs/transformation_checkpoints.md`

Do not claim a phase passed if the repo is broken and unverified.

---

### 3. Behavioral verification
For each phase, exercise a minimal realistic path:

- Phase 1:
    - load app state
    - inspect version ownership
    - confirm zone is no longer core state

- Phase 2:
    - compare at least 2 versions on the generalized-duration surface
    - verify stable cell addressing

- Phase 3:
    - scale -> emit derived fact -> assemble baseline -> inspect admission status

- Phase 4:
    - create a branch/version difference -> inspect unified mutation ledger

- Phase 5:
    - create agent-style candidate -> compare to baseline -> inspect scorecard/governance

If a full manual run is not possible, create the closest automated or seed-driven verification.

---

### 4. Regression scan
At the end of every phase, scan for old patterns that should be disappearing.

Examples:
- hard dependency on `zone`
- global detached ownership of `V`, `R`, `F`, `RF`, `S` for core semantics
- hidden `useSummaryItems`-style summary injection as structural truth
- sensitivity-only authoring semantics
- comparison logic outside generalized duration
- agent-only hidden state paths

Record findings in `docs/transformation_checkpoints.md`.

---

### 5. Diff discipline
Keep the scope of each phase controlled.

Rules:
- do not silently implement major parts of later phases
- if you must touch later-phase files, keep changes minimal and mark them as provisional
- document cross-phase touches in the checkpoint file

---

### 6. Written gate decision
At the end of each phase, explicitly record one of:
- `PASS: next phase may begin`
- `BLOCKED: architectural correction required`
- `PARTIAL: compile-safe but verification incomplete`

Do not start the next phase without a recorded gate decision.

---

## Stop conditions

Stop and report before proceeding if:
- the build is broken and cannot be repaired within the current phase
- the current phase requires inventing semantics that contradict the architectural rules
- a later dependency reveals an earlier model decision is wrong
- the implementation is recreating parallel grammars instead of unifying them

When blocked:
- explain the issue
- propose the smallest corrective architecture move
- do not continue sequencing until the blocker is resolved

---

## Output discipline

After each phase, produce:
1. what changed
2. what contracts were introduced
3. what was deprecated
4. what passed verification
5. what remains risky
6. whether the next phase may begin

Also update:
`docs/transformation_checkpoints.md`

---

## Preferred implementation style

- explicit contracts over implicit conventions
- migration adapters over brittle big-bang rewrites
- deterministic baseline assembly over late payload mutation
- one unified model over parallel semantics
- stable inspectable surfaces over hidden state magic
- provenance and governance preserved at the cell level

---

## Final success condition

The transformation is successful only if TEA-MD ends with:
- one version-centric analytical model
- one explicit baseline assembly model
- one duration-aware comparison fabric
- one unified mutation grammar
- one shared comparable reality for humans and agents
- linear auditability for branched histories
- visible provenance and governance at cell level