# AGENTS.md

## Project goal
This repository is a portfolio project for an internal LLM PoC.

The goal is to demonstrate:
- PDF-based RAG with citation-aware retrieval
- Meeting-minutes structuring with safety-first design
- Bridging structured meeting outputs to technical-document retrieval

This project is intended for AI engineer job applications, so the repository should emphasize:
- clarity of architecture
- reproducibility
- evaluation with evidence
- realistic limitations and failure cases

## Rules
- Do not expose real internal documents or secrets.
- Prefer anonymous sample data in `pdfs/` and `meetings/`.
- Do not fabricate evaluation results.
- Keep README concise and evidence-based.
- Do not over-engineer new features; prioritize documentation, cleanup, and reproducibility.
- Do not make production-scale claims for this PoC.
- Keep all claims aligned with actual code, outputs, and evaluation artifacts.

## Environment
- Python project
- Main scripts are currently under `meeting_summary/`, `eval/`, and `tools/`
- ChromaDB path is `data/chroma`

## Current key commands
- Retrieval eval:
  - `python eval/eval_retrieval.py --collection pdf_chunks_cs1600_co250 --top_k 7`
- Meeting structuring:
  - `python meeting_summary/summarize_meeting.py --input meetings/sample_meeting.md`
- Meeting eval:
  - `python meeting_summary/eval_meeting_structuring.py --summary outputs/sample_meeting.summary.json`
- Batch meeting eval:
  - `python tools/batch_eval_summary.py --pattern "real_*.summary.eval.json"`

## Documentation priorities
1. Improve README clarity
2. Organize outputs and sample files
3. Generate diagrams in `diagrams/`
4. Keep explanations aligned with actual code and metrics

## Refactoring policy
- Preserve current behavior unless explicitly changing it.
- Refactor incrementally instead of doing a large one-shot rewrite.
- Prefer moving reusable logic into `src/internal_llm/`.
- Prefer keeping command-line entry points in `scripts/`.
- Keep existing commands working during migration whenever practical.
- Avoid unnecessary abstractions or frameworks.


## Incremental migration working agreement
- Keep refactors small and reviewable (one script/module at a time).
- For each move to `src/internal_llm/`, keep or add a thin CLI wrapper under `scripts/`.
- Keep legacy entrypoints (`meeting_summary/`, `eval/`, `tools/`) working during migration whenever practical.
- Prefer wrappers/delegation over deleting old files early.
- Validate command compatibility after each step and document what changed in `MIGRATION_PLAN.md`.

## Portfolio evidence policy (operational)
- Any metric reported in README/reports must be traceable to committed code and artifacts.
- If a result is incomplete or provisional, label it explicitly.
- Include at least one representative failure/limitation example when summarizing evaluations.

## Target repository layout
The repository should gradually move toward the following layout:

- `src/internal_llm/` for reusable implementation code
- `scripts/` for thin runnable entry points
- `configs/` for tracked non-secret configuration
- `reports/` for portfolio-facing evaluation artifacts, tables, figures, and interview materials

This migration should be incremental. Existing directories such as:
- `meeting_summary/`
- `eval/`
- `tools/`

may remain temporarily during migration.

## Configuration policy
- Move hard-coded parameters to `configs/` where practical.
- Keep secrets only in `.env`, never in tracked config files.
- Prefer simple YAML or JSON configs.
- Do not introduce heavy config frameworks unless clearly necessary.

## Portfolio deliverables
The repository should eventually include the following portfolio-facing deliverables:

- A README with:
  - project overview
  - motivation / problem setting
  - architecture
  - setup and quickstart
  - usage examples
  - evaluation results
  - limitations
  - future work

- Reproducible artifacts under `reports/`, such as:
  - evaluation summaries
  - tables
  - figures
  - error / failure case examples

- Interview preparation material:
  - a Q&A document based only on actual architecture, code, and evaluation results

## README policy
- README should be easy to scan for hiring managers and engineers.
- Start with a short project summary and key achievements.
- Prefer concise explanations plus diagrams/tables over long prose.
- Tie every technical claim to actual code structure and actual outputs.
- Explicitly state limitations and non-goals.

## Evaluation policy
- Evaluation must be based on actual outputs only.
- Do not invent metrics, scores, or benchmark comparisons.
- When metrics are incomplete, say so clearly.
- Include representative failure cases if available.
- Prefer small but honest evaluation over broad but weak claims.

## Diagram policy
- Diagrams should reflect the implemented pipeline, not an imagined future architecture.
- Prefer simple, readable diagrams for:
  - RAG pipeline
  - meeting structuring flow
  - bridge from structured meeting outputs to document retrieval

## Interview preparation
- Generate interview Q&A from actual repository contents only.
- Focus on:
  - architecture decisions
  - safety design
  - evaluation choices
  - trade-offs and limitations
  - why this project is useful as an internal LLM PoC
- Avoid exaggerated claims about scalability or deployment maturity.

## Expected coding style
- Keep functions reasonably small and composable.
- Separate business logic from CLI entry points where practical.
- Prefer explicit naming over clever abstraction.
- Add docstrings or short comments where they improve readability.
- Minimize dead code and outdated files.

## Migration outputs to create
During cleanup and migration, prefer creating:
- `MIGRATION_PLAN.md`
- updated `README.md`
- `reports/interview_qa.md`
- any small helper docs needed to explain evaluation artifacts

## Safety and privacy
- Never include real company names, personal names, or confidential technical content unless already anonymized and explicitly safe.
- Preserve the portfolio-safe nature of this repository.
