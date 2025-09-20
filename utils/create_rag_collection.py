# recreate_collection.py (fixed)
import os
from astrapy import DataAPIClient
from dotenv import load_dotenv

load_dotenv()

ASTRA_COLLECTION = os.getenv("ASTRA_COLLECTION", "rag_chunks")
DIM = 1536

def main():
    db_id   = os.environ["ASTRA_DB_ID"]
    region  = os.environ["ASTRA_DB_REGION"]
    token   = os.environ["ASTRA_DB_APPLICATION_TOKEN"]
    keyspace = os.getenv("ASTRA_KEYSPACE", "default_keyspace")
    endpoint = f"https://{db_id}-{region}.apps.astra.datastax.com"

    client = DataAPIClient(token)
    db     = client.get_database_by_api_endpoint(endpoint, token=token, keyspace=keyspace)

    # Drop existing collection if present
    try:
        db.drop_collection(ASTRA_COLLECTION)
        print(f"Dropped existing collection: {ASTRA_COLLECTION}")
    except Exception as e:
        print(f"(No existing collection to drop) {e}")

    # Create with correct indexing rule: DO NOT index text_full
    db.create_collection(
        ASTRA_COLLECTION,
        definition={
            "vector": {"dimension": DIM, "metric": "cosine"},
            "indexing": {"deny": ["text_full"]}   # <-- only deny; no allow
        }
    )
    print(f"Created collection: {ASTRA_COLLECTION} (dim={DIM}, metric=cosine, deny index on text_full)")

if __name__ == "__main__":
    main()
