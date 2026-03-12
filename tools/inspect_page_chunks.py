import chromadb
from chromadb.config import Settings

CHROMA_DIR = "data/chroma"
COLLECTION = "pdf_chunks_cs800_co150"

SOURCE = "STKネットの基礎知識.pdf"
PAGE = 3  # goldのページ

client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
col = client.get_collection(COLLECTION)

res = col.get(include=["metadatas", "documents"], limit=100000)

hits = []
for md, doc in zip(res["metadatas"], res["documents"]):
    if md.get("source") != SOURCE:
        continue
    ps = md.get("page_start")
    pe = md.get("page_end")
    if ps is None or pe is None:
        continue
    if int(ps) <= PAGE <= int(pe):
        hits.append((md, doc))

print("hits:", len(hits))
for i, (md, doc) in enumerate(hits[:3], start=1):
    print(f"\n--- hit {i} ---")
    print("metadata:", md)
    print("text head:", (doc or "")[:400])
