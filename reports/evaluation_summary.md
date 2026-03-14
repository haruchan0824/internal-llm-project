# Evaluation Summary

このドキュメントは、リポジトリ内の**既存スクリプト**と**既存出力アーティファクト**に基づく評価の現状整理です。数値や主張は、確認できるファイルのみを参照しています。

## 1. Retrieval evaluation

### 実行スクリプト
- `eval/eval_retrieval.py`
  - `Hit@k` / `MRR` を計算
  - `--mode single|compare` で単体評価または Top-k と MMR 比較
  - 既定の入力として `eval/qset.jsonl`、Chroma path、collection、`top_k` などを使用

### 想定出力
- 現状は主に**標準出力**で結果を確認する設計です。
- 代表コマンド:
  - `python eval/eval_retrieval.py --collection pdf_chunks_cs1600_co250 --top_k 7`

### 補足
- 評価データの土台として `eval/qset.jsonl` が含まれます。
- 本リポジトリ内 `outputs/` には retrieval の固定レポートファイルは確認できず、実行時出力中心です。

## 2. Meeting structuring evaluation

### 実行スクリプト
- `scripts/run_meeting_eval.py`（互換: `meeting_summary/eval_meeting_structuring.py`）
  - 入力: `--summary outputs/*.summary.json`
  - 出力: `*.eval.json` と `*.eval.md`
- `scripts/batch_eval_summary.py`（互換: `tools/batch_eval_summary.py`）
  - 複数 `*.summary.eval.json` を集計し、バッチサマリを Markdown 出力

### 既存アーティファクト（`outputs/`）
- `outputs/batch_eval.md`
  - 各ファイルの structural checks、metrics、human checklist を列挙
- `outputs/batch_eval_summary.md`
  - 集計表（mean/min/max）と per-file 指標を記録
- `outputs/sample_meeting.summary.json`
  - 構造化サマリのサンプル

### 何を確認しているか
- required fields の充足状況
- topics/global いずれかのスキーマ前提での件数・率
- 推測表現フラグ（人手確認対象）
- バッチ単位での傾向（issues/open questions/actions/decisions、owner/due の充足率）

## 3. Evidence policy

- このPoCでは、README・reportsの主張は**コードと出力アーティファクトで追跡可能**な内容に限定します。
- 本ドキュメントも、以下を根拠に記述しています。
  - 実行スクリプト: `eval/eval_retrieval.py`, `scripts/run_meeting_eval.py`, `scripts/batch_eval_summary.py`
  - 出力物: `outputs/batch_eval.md`, `outputs/batch_eval_summary.md`, `outputs/sample_meeting.summary.json`
- 未生成の数値、未実行ベンチマーク、外部比較は記載しません。

## 4. Future evaluation improvements

- retrieval 評価結果を `reports/` に保存する仕組み（再実行時の追跡性向上）
- meeting 評価での失敗ケース抜粋を `reports/` に追加（代表例を明示）
- 実行コマンドと生成物の対応表を `reports/` に集約
- 比較条件（collection, top_k, method）の固定テンプレート化

> 方針: 小さく再現可能な評価を積み上げ、過大な主張を避ける。
