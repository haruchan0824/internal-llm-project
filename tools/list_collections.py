import chromadb
from chromadb.config import Settings

CHROMA_DIR = "data/chroma"

client = chromadb.PersistentClient(
    path=CHROMA_DIR,
    settings=Settings(anonymized_telemetry=False),
)

print("collections:", [c.name for c in client.list_collections()])
