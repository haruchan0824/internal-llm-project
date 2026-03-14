# Internal LLM PoC Portfolio (RAG + Meeting Structuring)

## 1. Project overview
このリポジトリは、**社内向けLLM活用のPoC**を想定した、公開可能なポートフォリオプロジェクトです。  
主眼は「業務文書検索」と「議事録構造化」を分断せず、意思決定に使える形へつなぐことです。

本プロジェクトは次の3つを組み合わせています。
- 技術PDFを対象にしたRAG（根拠ページ付き検索）
- 議事録の安全寄りな構造化要約（不明は不明として残す設計）
- 構造化された提案方針から、技術資料根拠を再検索するブリッジ処理

実装は段階的に `src/internal_llm/` へ移行中で、`scripts/` に薄いCLI、`configs/` に非機密デフォルト設定を置く構成に整理しています。互換のために一部 legacy パスも残しています。

---

## 2. Why this project matters
- **実務に近い一連の流れ**（会議→要約→技術根拠検索）を1リポジトリで示せる。
- **安全優先の出力方針**（推測抑制・unknown明示）を評価スクリプトとセットで扱える。
- **PoCとしての再現性**を意識し、コマンドと出力アーティファクトを対応付けて確認できる。

---

## 3. Key features
- PDF RAG: ChromaDB + Top-k/MMR 検索、Hit@k/MRR 評価スクリプトあり。  
- Meeting structuring: 議事録（`.md/.txt/.docx`）からJSON構造化。  
- Safety helper: ルールベースの簡易マスキング関数。  
- Bridge: `proposal_directions` をクエリ化し、技術資料から根拠候補を収集。  
- Portfolio-friendly refactor: `src/internal_llm/`（再利用ロジック） + `scripts/`（薄いCLI） + `configs/`（非機密デフォルト）。

---

## 4. Repository structure
```text
.
├─ src/internal_llm/          # 再利用ロジック（meeting/evaluation/utils など）
├─ scripts/                   # 推奨CLI（薄いエントリポイント）
├─ configs/                   # 非機密デフォルト設定（YAML）
├─ eval/                      # 検索評価スクリプト・qset
├─ meeting_summary/           # 互換用エントリポイント（段階移行中）
├─ tools/                     # 補助スクリプト
├─ outputs/                   # サンプル出力・評価アーティファクト
├─ meetings/                  # サンプル議事録
└─ reports/                   # 今後拡充予定（評価サマリ、図表、Q&A）
```

---

## 5. Quickstart
### 5.1 セットアップ
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5.2 Meeting structuring（推奨: scripts パス）
```bash
python scripts/run_meeting_summary.py --input meetings/sample_meeting.md
```

### 5.3 Meeting evaluation
```bash
python scripts/run_meeting_eval.py --summary outputs/sample_meeting.summary.json
```

### 5.4 Batch summary（meeting eval 集計）
```bash
python scripts/batch_eval_summary.py --pattern "real_*.summary.eval.json"
```

### 5.5 Retrieval evaluation
```bash
python eval/eval_retrieval.py --collection pdf_chunks_cs1600_co250 --top_k 7
```

> 既存ワークフロー互換のため、`meeting_summary/` や `tools/` の旧パスも一部利用可能です。

---

## 6. Pipeline / architecture
### A. PDF-based RAG
1. PDFを取り込み、チャンク化してChromaDBへ保存。  
2. 質問に対し Top-k/MMR で関連チャンクを取得。  
3. 評価では Hit@k / MRR を算出。

### B. Meeting structuring
1. 議事録テキストを読み込み（`.md/.txt/.docx`）。  
2. JSONスキーマを前提に構造化要約を生成。  
3. 構造・項目充足・推測表現を評価し、`.eval.json/.eval.md` を出力。

### C. Bridge (meeting -> retrieval)
1. `proposal_directions` から「根拠探索用クエリ」を生成。  
2. 技術資料コレクションへ検索し、ページ付き根拠候補を保存。  
3. 根拠付き提案文（Markdown）の作成を支援。

---

## 7. Evaluation
このリポジトリの評価は、**実装済みスクリプト + 生成済みアーティファクト**を中心に確認できます。

### 7.1 Retrieval evaluation
- スクリプト: `eval/eval_retrieval.py`  
- 指標: Hit@k, MRR  
- 入力: `eval/qset.jsonl` と Chroma collection  
- 出力: 単発評価結果（標準出力）、または compare モードで Top-k と MMR を比較

### 7.2 Meeting structuring evaluation
- スクリプト: `scripts/run_meeting_eval.py`（互換: `meeting_summary/eval_meeting_structuring.py`）  
- 出力: `*.eval.json`, `*.eval.md`  
- 確認内容:
  - required fields の有無
  - topics/global schema に応じた件数・充足率
  - 推測表現フラグ（要人手確認）

### 7.3 Batch artifacts
- `outputs/batch_eval_summary.md`: meeting評価の集計表（mean/min/max, per-file）
- `outputs/batch_eval.md`: 各ファイルの評価結果と人手チェック項目

> 注意: このPoCの評価はサンプル・手元データ中心で、ベンチマークとしての網羅性は限定的です。

---

## 8. Limitations
- **PoCスコープ**: 本リポジトリは本番運用を前提とした完成品ではありません。  
- **評価範囲の限定**: 評価は既存クエリセット・既存議事録サンプル中心です。  
- **再実行条件**: 要約・提案生成など一部処理は `OPENAI_API_KEY` を設定した環境が必要です。  
- **構成移行中**: `src/internal_llm/` へ移行中のため、互換目的で legacy パスが併存します。  
- **設定の最小実装**: `configs/` は軽量な既定値管理に留めており、包括的設定管理基盤は未導入です。

---

## 9. Future work
- `reports/` 配下に、評価表・失敗ケース・図表を整理して再現性を強化。  
- READMEと評価結果の対応をさらに明確化（コマンド→成果物リンク）。  
- `connect_proposal_to_rag` / `compose_proposal` を `src/internal_llm/` 側へ段階移行。  
- `reports/interview_qa.md` を整備し、設計判断・トレードオフ・限界を明文化。

---

## Main commands (current)
```bash
# Meeting summary
python scripts/run_meeting_summary.py --input meetings/sample_meeting.md

# Meeting eval
python scripts/run_meeting_eval.py --summary outputs/sample_meeting.summary.json

# Batch eval summary
python scripts/batch_eval_summary.py --pattern "real_*.summary.eval.json"

# Retrieval eval
python eval/eval_retrieval.py --collection pdf_chunks_cs1600_co250 --top_k 7
```
