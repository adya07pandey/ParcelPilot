import asyncio
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.ai.providers import QdrantDocumentStore, VoyageEmbeddings  # noqa: E402


async def main() -> None:
    store = QdrantDocumentStore()
    vector = (await VoyageEmbeddings().embed_texts(["test query"]))[0]
    print("vector_size", len(vector))
    await store.ensure_collection(len(vector))

    async with httpx.AsyncClient(timeout=30) as client:
        collection = await client.get(store.collection_url, headers=store._headers())
        print("get_collection", collection.status_code, collection.text[:500])

        if collection.status_code == 404:
            created = await client.put(
                store.collection_url,
                headers=store._headers(),
                json={"vectors": {"size": len(vector), "distance": "Cosine"}},
            )
            print("create_collection", created.status_code, created.text[:500])

        search = await client.post(
            f"{store.collection_url}/points/search",
            headers=store._headers(),
            json={
                "vector": vector,
                "limit": 3,
                "with_payload": True,
                "filter": store._tenant_filter("ACCT-001"),
            },
        )
        print("search", search.status_code, search.text[:1000])


if __name__ == "__main__":
    asyncio.run(main())
