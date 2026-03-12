import json
from pathlib import Path
import chromadb
from chromadb.config import Settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHROMA_DIR = str(PROJECT_ROOT / "data" / "chroma")
QSET_PATH = PROJECT_ROOT / "eval" / "qset.jsonl"
COLLECTION = "pdf_chunks_cs800_co150"

def norm_source(x):
    if x is None:
        return None
    x = str(x)
    return x.split("\\")[-1].split("/")[-1]

def load_qset(path: Path):
    qset = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                qset.append(json.loads(line))
    return qset

client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
col = client.get_collection(COLLECTION)

# collection側の (source, page_start, page_end) を全部集める
meta = col.get(include=["metadatas"], limit=100000)["metadatas"]
ranges = []
for md in meta:
    src = norm_source(md.get("source"))
    ps = md.get("page_start")
    pe = md.get("page_end")
    if src is not None and ps is not None and pe is not None:
        ranges.append((src, int(ps), int(pe)))

qset = load_qset(QSET_PATH)

def covered(gsrc, gpage):
    gsrc = norm_source(gsrc)
    gpage = int(gpage)
    for src, ps, pe in ranges:
        if src == gsrc and ps <= gpage <= pe:
            return True
    return False

total = 0
covered_cnt = 0
miss_examples = []

for item in qset:
    for g in item.get("gold", []):
        src = g.get("source")
        page = g.get("page")
        if src is None or page is None:
            continue
        total += 1
        if covered(src, page):
            covered_cnt += 1
        else:
            if len(miss_examples) < 10:
                miss_examples.append((item.get("id"), norm_source(src), page, item.get("question")))

print("COLLECTION:", COLLECTION)
print("Gold items:", total)
print("Covered:", covered_cnt)
print("Coverage rate:", (covered_cnt / total) if total else None)
print("\nMiss examples (first 10):")
for x in miss_examples:
    print(x)
