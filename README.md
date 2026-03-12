# Internal Document RAG System (PDF-based)

社内技術資料（PDF）を対象とした Retrieval-Augmented Generation (RAG) システムです。  
PDFの内容を検索・要約し、**根拠付きで質問応答を行うこと**を目的としています。

本プロジェクトでは、単なるRAG構築にとどまらず、  
**検索精度評価・chunk設計の検証・セキュリティ配慮**までを含めた設計を行いました。

---

## Features

- PDF文書の自動読み込み・分割（chunking）
- ベクトル検索（ChromaDB）
- Top-k / MMR 検索切替
- 根拠（文書名・ページ）付き回答
- 検索精度の定量評価（Hit@k / MRR）
- chunkサイズ・検索パラメータの比較検証
- セキュリティ配慮（マスキング・運用前提の明示）

---

## System Overview

```text
PDF Documents
     │
     ▼
[ Ingest ]
  - PDF Parsing
  - Chunking (size / overlap)
  - Embedding
     │
     ▼
[ Vector DB (Chroma) ]
     │
     ▼
[ Retriever ]
  - Top-k / MMR
  - Similarity Search
     │
     ▼
[ Context Selection ]
  - Relevant Chunks
     │
     ▼
[ LLM (OpenAI API) ]
  - Answer Generation
  - Citation Control

Ingest Pipeline

PDFをページ単位で読み込み

指定した chunk_size / chunk_overlap で分割

各chunkに以下のメタデータを付与：

source（PDF名）

page_start

page_end

heading（抽出可能な場合）

Retrieval & Evaluation
Evaluation Metrics

Hit@k：Top-k以内に正解根拠が含まれる割合

MRR (Mean Reciprocal Rank)：正解が出現する順位の平均的早さ

Chunk Size Comparison (k=7)
Chunk Size	Overlap	Hit@7	MRR
800	150	0.72	0.44
1200	200	0.74	0.41
1600	250	0.78	0.45
Conclusion

技術資料では定義文・構造説明が複数段落にまたがるため、
chunkを大きめに取る方が検索精度が安定

本プロジェクトでは
chunk_size=1600 / overlap=250 / Top-k(k=7) を採用

Answer Quality Control

回答生成は 検索で取得した文書のみ を文脈として使用

文書名・ページ番号を引用として明示

回答前に文書要約を行い、冗長な情報を削減

完全自動化は行わず、意思決定支援ツールとして設計

Security Considerations

OpenAI API を使用し、送信データはモデル学習には使用されない前提

社内文書中の固有名詞・個人情報は、LLM送信前にマスキング可能

マスキングはルールベース＋人確認前提

出力結果は支援目的であり、最終判断は人が行う

Limitations & Future Work

見出し抽出精度の改善

用語揺れ（同義語）への対応

議事録を対象とした構造化要約・営業提案支援への拡張

回答再ランキングの高度化

Tech Stack

Python

ChromaDB

OpenAI API

PDF parsing libraries


---

# 🖼 README用 図解（文章版）
READMEに **図として描く場合の説明文**です。  
（Mermaid / draw.io / PowerPoint どれでも描けます）

### 図タイトル
**PDF-based RAG Architecture**

### 図の構成


[PDF Files]
↓
[PDF Loader]
↓
[Chunking]
(size=1600 / overlap=250)
↓
[Embedding Model]
↓
[Vector DB (Chroma)]
↓
[Retriever]
(Top-k / MMR)
↓
[Relevant Chunks]
↓
[LLM (OpenAI API)]
↓
[Answer + Citations]
