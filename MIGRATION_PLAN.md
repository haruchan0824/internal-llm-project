# MIGRATION_PLAN.md

## Scope and intent
This migration plan is for an **incremental refactor** toward a portfolio-friendly layout for an internal LLM PoC.
The objective is to improve architecture clarity and reproducibility while preserving current behavior.

## Current structure summary (as of now)

### Reusable logic (good candidates to move under `src/internal_llm/`)
- `ingest/rag_core.py` (PDF extraction, chunking, citation formatting)
- `eval/rag_retrieval.py` (retriever/MMR logic)
- `meeting_summary/mask.py` (text masking helpers)
- `meeting_summary/templates.py` (prompt templates)
- `meeting_summary/eval_meeting_structuring.py` (evaluation functions currently mixed with CLI)
- `meeting_summary/connect_proposal_to_rag.py` (bridge logic currently mixed with CLI)
- `tools/batch_eval_summary.py` (aggregation/report logic currently mixed with CLI)

### Mostly CLI entry points
- `ingest/ingest.py`
- `eval/eval_retrieval.py`
- `eval/run_sweep.py`
- `meeting_summary/summarize_meeting.py`
- `meeting_summary/eval_meeting_structuring.py`
- `meeting_summary/compose_proposal.py`
- `meeting_summary/connect_proposal_to_rag.py`
- `tools/run_meeting_batch.py`
- `tools/batch_eval_summary.py`
- `tools/chroma_count.py`
- `tools/list_collections.py`
- `tools/check_gold_coverage.py`
- `tools/inspect_page_chunks.py`
- `app/app.py`

### Documentation / artifacts / sample data
- `README.md`
- `AGENTS.md`
- `failures.md`
- `docs/` (existing docs folder)
- `diagrams/` (existing diagrams folder)
- `meetings/` (sample meeting inputs)
- `outputs/` (generated summaries/evals)

## Target structure summary
- `src/internal_llm/`: reusable, testable implementation logic
- `scripts/`: thin CLI wrappers that parse args and call `src/internal_llm/`
- `configs/`: non-secret YAML/JSON settings
- `reports/`: portfolio-facing artifacts (tables, figures, interview Q&A)

## Recommended migration sequence (low-risk first)
1. **Extract pure functions** from one CLI file at a time into `src/internal_llm/`.
2. Add a **thin script wrapper** in `scripts/`.
3. Keep the old command path as a **backward-compatible wrapper** during transition.
4. Run the same command before/after refactor and verify output format/paths are unchanged.
5. Document migration progress in this plan and README.

## Proposed file moves/refactors (incremental)
- Step A (done in this change):
  - Extract `tools/batch_eval_summary.py` logic to `src/internal_llm/batch_eval_summary.py`
  - Add thin entrypoint at `scripts/batch_eval_summary.py`
  - Keep `tools/batch_eval_summary.py` as compatibility wrapper
- Step B (done in this change):
  - Split `meeting_summary/eval_meeting_structuring.py` into reusable logic and thin CLI:
    - `src/internal_llm/evaluation/meeting_structuring.py` (validation/metrics/markdown render)
    - `scripts/run_meeting_eval.py` (CLI)
  - Keep existing `meeting_summary/eval_meeting_structuring.py` callable as compatibility wrapper
- Step C (done in this change):
  - Split `meeting_summary/summarize_meeting.py` into reusable logic and thin CLI:
    - `src/internal_llm/meeting/summarize.py` (I/O helpers + LLM call + output write)
    - `scripts/run_meeting_summary.py` (CLI)
  - Keep existing `meeting_summary/summarize_meeting.py` callable as compatibility wrapper
  - Move prompt/masking reusable modules under `src/internal_llm/meeting/` with backward-compatible exports in `meeting_summary/`
- Step D (done in this change):
  - Add minimal YAML config files under `configs/` for stable non-secret defaults (`meeting.yaml`, `retrieval.yaml`, `paths.yaml`)
  - Add lightweight config loader in `src/internal_llm/utils/config.py`
  - Wire selected scripts to use: CLI args > config defaults, while keeping CLI interfaces unchanged
- Step E:
  - Consolidate portfolio outputs in `reports/` (summaries, failure cases, interview Q&A)

## What should NOT be changed yet
- Do not change core retrieval/chunking behavior (`ingest/rag_core.py`, `eval/rag_retrieval.py`) in the same commit as structural moves.
- Do not remove existing entrypoint files/commands yet.
- Do not claim new evaluation metrics unless regenerated from actual outputs.
- Do not introduce heavy frameworks or broad package rewrites at this stage.
- Do not move or expose any real internal/private data.

## Validation checklist per migration step
- Existing command still runs with same args.
- Output files and schema remain compatible.
- No secrets added to tracked config/docs.
- README/report claims remain evidence-based.


## Next recommended low-risk step
- Step E: improve portfolio-facing documentation and reproducible artifacts (`README.md`, `reports/` summaries/figures, and `reports/interview_qa.md`) aligned strictly with actual code and outputs.
