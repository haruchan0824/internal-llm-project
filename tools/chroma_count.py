import chromadb
from chromadb.config import Settings

CHROMA_DIR = "data/chroma"
COLLECTION = "pdf_chunks_cs800_co150"

client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
col = client.get_collection(COLLECTION)

print("collection:", COLLECTION)
print("count:", col.count())

# 1件だけ取り出してメタデータの形を確認
res = col.get(limit=1, include=["metadatas", "documents"])
print("\nSAMPLE id:", res["ids"][0])                 # ids は include 指定不要
print("SAMPLE metadata:", res["metadatas"][0])
doc0 = res["documents"][0] or ""
print("SAMPLE text head:", doc0[:200])

