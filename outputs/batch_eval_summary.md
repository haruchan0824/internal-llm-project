# Batch Eval Summary (Meeting Structuring)

- files: 5

## Aggregate (mean / min / max)

| metric | mean | min | max |
|---|---:|---:|---:|
| issues_cnt | 9.400 | 7 | 13 |
| open_questions_cnt | 4.200 | 2 | 6 |
| next_actions_cnt | 6.800 | 5 | 8 |
| decisions_cnt | 5.800 | 4 | 8 |
| action_owner_filled_rate | 1.000 | 1.000 | 1.000 |
| action_due_filled_rate | 0.205 | 0.000 | 0.400 |

## Per-file

| file | issues | openQ | actions | decisions | owner_rate | due_rate | due_missing_cnt | speculation |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| real_01.summary.json | 13 | 5 | 8 | 5 | 1.000 | 0.250 | 6 | False |
| real_02.summary.json | 12 | 3 | 7 | 4 | 1.000 | 0.000 | 7 | False |
| real_03.summary.json | 8 | 2 | 5 | 5 | 1.000 | 0.400 | 3 | False |
| real_04.summary.json | 7 | 5 | 6 | 7 | 1.000 | 0.000 | 6 | False |
| real_05.summary.json | 7 | 6 | 8 | 8 | 1.000 | 0.375 | 5 | False |

## Notes
- High open_questions_cnt is expected for thin meeting minutes; it indicates unknowns are captured instead of hallucinated.
- due_rate can be low when minutes omit deadlines; we intentionally avoid guessing deadlines (safety-first).
