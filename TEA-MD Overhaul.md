Below is a fully tailored set for `Mohsendirbaz/TEA-MD`.

I tailored these against the actual repo shape:

* `README.md` positions TEA Space around time-scoped parameters, centralized scaling, scenario import/export, and a matrix-based computation layer
* `src/HomePage.js` is the current workflow shell, wiring `VersionStateContext`, `useMatrixFormValues`, `GeneralFormConfig`, `SimpleScalingEditor`, CFA runs, sensitivity runs, summary-item injection, and the major tabs/subtabs
* `src/contexts/VersionStateContext.js` currently keeps only a simple `version` and `selectedVersions` context
* `src/Consolidated2.js` is the main state seam today, still centered on `versions`, `zones`, `formMatrix`, `S`, `V`, `R`, `F`, `RF`, `scalingGroups`, `finalResults`, efficacy handling, and backend sync/export classes

## Prompt 1 — Replace the core state model in `TEA-MD`

```text
You are working inside the repository `Mohsendirbaz/TEA-MD`.

Your job is to replace the current state architecture with a version-centric, comparison-ready analytical model.

Ground truth about the current repo:
- `src/HomePage.js` is the main workflow shell and currently coordinates input tabs, scaling tabs, CFA/sensitivity runs, visualization tabs, and monitoring.
- `src/contexts/VersionStateContext.js` currently exposes only `version`, `setVersion`, `selectedVersions`, and `setSelectedVersions`.
- `src/Consolidated2.js` currently owns the main analytical state through `useMatrixFormValues()` and still includes:
  - `versions`
  - `zones`
  - `formMatrix`
  - `S`, `V`, `R`, `F`, `RF`
  - `scalingGroups`
  - `finalResults`
  - efficacy helpers
  - backend sync/export classes
- The repo already has explicit efficacy/scoped-time concepts and scaling hooks, but the primary state contract is still fragmented.

Fixed architectural decisions:
1. Zone is no longer needed in the core application model.
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
8. Generalized duration must become the canonical comparison fabric.
9. Sensitivity must not remain a separate state-authoring grammar if the same modeling power can be represented by the unified model.
10. Human and agent-authored changes must land in the same comparable model.

Your task:
- Refactor the current state model in `src/Consolidated2.js` and adjacent ownership seams so the application is centered on first-class version objects rather than parallel global stores.
- Introduce explicit core types/structures for:
  - `VersionSlot`
  - `BaselineAssembly`
  - `DerivedSummaryFact`
  - `ScopedMutation`
  - `VersionProjection`
  - `ComparisonSession`
- Remove `zone` from the primary domain model and phase it out from active state, UI assumptions, and backend payload construction.
- Preserve backward compatibility only through explicit adapters where necessary.
- Ensure the model can represent:
  - direct inputs
  - derived facts
  - scoped duration
  - version ownership
  - lineage/provenance
  - comparison projections
- Refactor `VersionStateContext` so it no longer remains a shallow side context detached from the real analytical model.
- Add architecture documentation explaining how the new model maps from the old `formMatrix` / `S` / `V` / `R` / `F` / `RF` / `scalingGroups` / `finalResults` structure.

Primary files to inspect and modify:
- `src/Consolidated2.js`
- `src/contexts/VersionStateContext.js`
- `src/HomePage.js`
- any helper/services/types files you create to support the new model

Deliverables:
- New version-centric state model
- Removal/deprecation of zone from the core model
- Migration adapters from old state shape to new state shape
- Updated `VersionStateContext`
- In-repo architecture note under `docs/`

Acceptance criteria:
- No new core logic depends on `zone`.
- A version is the primary container of submitted analytical reality.
- Baseline assembly has a clear explicit home in the model.
- Existing app surfaces still compile after the transition.
- The codebase is structurally ready for generalized-duration comparison work.
```

## Prompt 2 — Make generalized duration the comparison fabric in `TEA-MD`

```text
You are working inside `Mohsendirbaz/TEA-MD`.

Your job is to turn the generalized duration module into the canonical comparison workspace of the application.

Use the actual repo context:
- `src/HomePage.js` already provides the central tabbed workflow and is the correct place to integrate a new comparison-capable workspace.
- The current app already distinguishes input, scaling, CFA, dynamic subplots, plots, and consolidation, but comparison is not yet normalized around a shared duration surface.
- The platform direction already emphasizes time-scoped parameters and matrix-native analysis.

Fixed design decisions:
1. Generalized duration is not just a visualization layer.
2. It must become the canonical comparison fabric.
3. Canonical year is the default header view.
4. The user must be able to drill into nested scoped duration levels.
5. The matrix must remain stable and cell-inspectable.
6. Comparison must not become a detached module; it must be a mode of the same duration workspace.
7. The comparison workspace must support human-authored and agent-authored versions on the same surface.

Your task:
- Implement a generalized-duration comparison workspace inside the TEA-MD UI.
- Introduce a comparison-ready cell model with at least:
  - `targetId`
  - `durationPath`
  - `versionId`
  - `resolvedValue`
  - `participationState`
  - `sourceType`
  - `precedenceStatus`
  - `lineageRef`
  - `deltaFromReference`
- Add comparison modes:
  - overlay
  - delta
  - governance
  - lineage
- Add version selection / reference selection UI so the user can compare:
  - baseline vs baseline
  - baseline vs derived version
  - candidate vs candidate
  - agent-generated schedule vs baseline
- Add a right-side inspector that explains the selected compared cell.
- Preserve exact path/cell inspectability and stable addressing.
- Add a linear companion explanation layer or hook that later prompts can use for mutation-ledger views.

Primary files to inspect and likely modify:
- `src/HomePage.js`
- any generalized-duration UI file already added to this repo, if present
- create new components if needed under `src/components/`
- connect to the new state/projection model from Prompt 1

Deliverables:
- Generalized-duration comparison workspace
- Comparable cell projection layer
- Comparison modes
- Inspector for selected compared cells
- Clear state flow from version projection -> duration comparison surface

Acceptance criteria:
- At least two versions can be compared on the same duration matrix.
- Overlay and delta work without breaking matrix stability.
- Selected cells reveal compared state, winner/suppressed context, and lineage hooks.
- The module can serve as the common comparison space for the rest of the transformation.
```

## Prompt 3 — Refactor scaling and baseline assembly in `TEA-MD`

```text
You are working inside `Mohsendirbaz/TEA-MD`.

Your job is to refactor scaling outputs and baseline assembly so they fit the unified model and generalized-duration comparison system.

Ground truth from the current repo:
- `src/HomePage.js` wires four scaling sections through `SimpleScalingEditor`:
  - `Amount4` Process Quantities
  - `Amount5` Process Costs
  - `Amount6` Additional Revenue Quantities
  - `Amount7` Additional Revenue Prices
- `src/Consolidated2.js` currently stores scaling-related state in:
  - `scalingGroups`
  - `scalingBaseCosts`
  - `finalResults`
  - `handleFinalResultsGenerated`
- Current CFA and sensitivity run handlers in `src/HomePage.js` build modified `formValues` by injecting summary items back into the payload when `useSummaryItems` is enabled.

Fixed design decisions:
1. Scoped duration for scaling is already assumed and must be preserved.
2. Scaling is the transformation engine.
3. Summary is derived fact.
4. Only enabled derived results from Amount4/5/6/7 are admitted into baseline submission.
5. Baseline assembly must be explicit and deterministic.
6. The generalized-duration workspace must be able to compare admitted vs excluded derived facts across versions/scopes.

Your task:
- Refactor the scaling pipeline so it emits duration-aware derived facts rather than only opaque `finalResults`.
- Preserve the existing expressive power of scaling groups and math operations.
- Replace ad hoc late payload rewriting with an explicit baseline assembly function.
- Ensure each derived summary fact carries:
  - source workspace
  - source scaling lineage
  - resolved scoped duration
  - resolved value by duration
  - admission/participation state
  - provenance
- Refactor `handleFinalResultsGenerated` and related scaling data flow so it produces reusable derived-fact objects.
- Implement explicit baseline assembly:
  - direct baseline-native inputs
  - admitted derived facts from Amount4/5/6/7
- Update CFA execution flow so it consumes baseline assembly rather than silently patching `formValues` at run time.

Primary files to inspect and likely modify:
- `src/HomePage.js`
- `src/Consolidated2.js`
- `src/components/scaling/SimpleScalingEditor.*`
- `src/GeneralFormConfig.*`
- any summary/scaling helper files that currently emit or consume `finalResults`

Deliverables:
- Duration-aware derived-fact output from scaling
- Explicit baseline assembly implementation
- Refactored run payload preparation
- Admission/exclusion handling for derived facts
- Documentation of how scaling output now enters baseline

Acceptance criteria:
- Baseline assembly is explicit.
- Derived facts are no longer treated as flat unstructured summaries.
- CFA execution can use assembled baseline input directly.
- Generalized-duration comparison can inspect admitted/excluded derived facts.
```

## Prompt 4 — Collapse sensitivity into unified mutations and comparable ledgers in `TEA-MD`

```text
You are working inside `Mohsendirbaz/TEA-MD`.

Your job is to remove sensitivity as a separate state-authoring paradigm and preserve only its useful operational capabilities inside the unified version/mutation/comparison model.

Ground truth from the current repo:
- `src/HomePage.js` still has a distinct `handleRuns()` sensitivity flow with multiple sequential calls:
  - `/run-baseline`
  - `/sensitivity/configure`
  - `/runs`
  - `/calculate-sensitivity`
  - summary/report/visualization endpoints
- `src/Consolidated2.js` still stores `S` as a dedicated sensitivity state object and includes helper classes like `SensitivityConfigGenerator`.
- `SensitivityMonitor` is still mounted in the main workspace.

Fixed design decisions:
1. Sensitivity should not remain a separate authoring grammar if the same modeling power already exists through unified mutations and scaling.
2. Useful automation can remain:
   - experiment generation
   - batch execution
   - reporting
   - visualization
   - optimization orchestration
3. Branched changes must remain linearly auditable.
4. Generalized duration must be able to expose branch history and deltas in linear form.

Your task:
- Refactor the repo so sensitivity configuration is represented through unified scoped mutations and version deltas rather than a parallel semantic model.
- Preserve useful sensitivity operations as orchestration/reporting layers, not as competing state ownership.
- Introduce a linear mutation/delta ledger view and data contract that can explain:
  - what changed
  - where
  - over which scoped duration
  - relative to which reference version
  - whether it won / was suppressed
  - what downstream impact it had
- Update or wrap `SensitivityMonitor` so it reads from the unified model rather than a detached sensitivity-only grammar.
- Reduce or eliminate direct reliance on raw `S` as the primary authoring surface.
- Keep backward compatibility only where necessary, with explicit deprecation comments and migration notes.

Primary files to inspect and likely modify:
- `src/HomePage.js`
- `src/Consolidated2.js`
- `src/components/modules/SensitivityMonitor.*`
- any helper classes or API adapters that currently treat sensitivity as separate authoring state

Deliverables:
- Unified mutation representation for branch-like differences
- Linear mutation/delta ledger
- Refactored sensitivity orchestration pathway
- Updated monitor logic and UI labels where needed
- Migration note from old `S` semantics to new model

Acceptance criteria:
- No core model change requires a distinct sensitivity-only authoring grammar.
- Branch/version differences can be explained through the same mutation model and ledger.
- Existing useful sensitivity workflows survive as orchestration/reporting tools.
- The generalized-duration comparison workspace can consume the same mutation/ledger model.
```

## Prompt 5 — Add agent-facing comparability and end-to-end validation in `TEA-MD`

```text
You are working inside `Mohsendirbaz/TEA-MD`.

Your job is to finish the transformation by making the platform equally usable by humans and agents under the same comparable reality model.

Ground truth from the repo:
- TEA-MD already presents itself as a matrix-native techno-economic platform with time-scoped parameters, centralized scaling, and scenario-oriented analysis.
- The homepage workflow already manages versions, batch creation/removal, CFA execution, sensitivity execution, plots, CSV/HTML outputs, scaling, and consolidation.
- The transformation underway is intended to unify all of that under one version-centric, duration-aware, comparison-ready model.

Fixed design decisions:
1. The generalized-duration module is the canonical comparison fabric.
2. Versions are the main containers of submitted analytical reality.
3. Agents must be able to generate combinatoric schedules and optimization candidates.
4. Human and agent-authored changes must land in the same model.
5. Provenance, governance, and cell-level inspectability must remain visible.

Your task:
- Add an agent-facing candidate/projection/orchestration layer that can:
  - create candidate versions
  - propose scoped mutations
  - generate optimization schedules
  - materialize version projections
  - attach rationale and objective scores
- Ensure agent-generated candidates are first-class comparable versions inside the generalized-duration workspace.
- Add comparison scorecards for candidate versions, including:
  - objective score
  - delta from baseline
  - affected targets
  - duration coverage
  - admitted/excluded derived facts
- Add governance visibility for compared cells:
  - winning fact/mutation
  - suppressed alternatives
  - rationale
- Add end-to-end validation and tests for:
  - version state model
  - baseline assembly
  - derived-fact admission
  - comparison projections
  - mutation ledger linearization
  - agent candidate comparability

Primary files to inspect and likely modify:
- `src/HomePage.js`
- the new comparison/generalized-duration files from earlier prompts
- state/model files from earlier prompts
- any orchestration or helper layer you create under `src/services/`, `src/lib/`, or `src/components/`
- test files you add to validate the transformed architecture

Deliverables:
- Agent-facing candidate/projection support
- Comparison scorecards
- Governance explanation surfaces
- End-to-end validation suite
- Final architecture summary under `docs/`

Acceptance criteria:
- Agent-generated candidates appear exactly like human-authored versions on the comparison surface.
- Humans can inspect agent schedules through the same matrix, inspector, and ledger.
- Governance and provenance remain visible.
- The repo contains enough validation and documentation to continue development safely.
```


