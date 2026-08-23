import argparse
import asyncio
import hashlib
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
sys.path.append(str(ROOT))

from app.ai.providers import QdrantDocumentStore, VoyageEmbeddings  # noqa: E402
from app.core.exceptions import ExternalServiceError  # noqa: E402

DOCUMENTS = {
    "01_Support_Policy_v3_CURRENT.pdf": {
        "document_id": "support-policy-v3",
        "document_type": "support_policy",
        "version": "v3",
        "status": "CURRENT",
        "effective_from": "2026-05-01",
        "effective_to": None,
        "scope": "GLOBAL",
        "account_id": None,
        "authority": 4,
    },
    "02_Support_Policy_v2_DEPRECATED.pdf": {
        "document_id": "support-policy-v2",
        "document_type": "support_policy",
        "version": "v2",
        "status": "DEPRECATED",
        "effective_from": "2025-01-01",
        "effective_to": "2026-04-30",
        "scope": "GLOBAL",
        "account_id": None,
        "authority": 2,
    },
    "03_Cancellation_and_Service_Credit_SOP_v4.pdf": {
        "document_id": "cancellation-service-credit-sop-v4",
        "document_type": "sop",
        "version": "v4",
        "status": "CURRENT",
        "effective_from": "2026-05-01",
        "effective_to": None,
        "scope": "GLOBAL",
        "account_id": None,
        "authority": 4,
    },
    "04_Product_Operations_Guide_and_Known_Issues.pdf": {
        "document_id": "product-operations-guide",
        "document_type": "product_guide",
        "version": "current",
        "status": "CURRENT",
        "effective_from": "2026-05-01",
        "effective_to": None,
        "scope": "GLOBAL",
        "account_id": None,
        "authority": 3,
    },
    "05_Northstar_Logistics_Enterprise_Agreement.pdf": {
        "document_id": "northstar-enterprise-agreement",
        "document_type": "customer_agreement",
        "version": "2026",
        "status": "CURRENT",
        "effective_from": "2026-01-01",
        "effective_to": None,
        "scope": "ACCOUNT",
        "account_id": "ACCT-001",
        "authority": 5,
    },
    "06_LumenWorks_Service_Agreement.pdf": {
        "document_id": "lumenworks-service-agreement",
        "document_type": "customer_agreement",
        "version": "2026",
        "status": "CURRENT",
        "effective_from": "2026-01-01",
        "effective_to": None,
        "scope": "ACCOUNT",
        "account_id": "ACCT-002",
        "authority": 5,
    },
}


def read_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(page.strip() for page in pages if page.strip())


def chunk_text(text: str, *, chunk_size: int = 1400, overlap: int = 180) -> list[str]:
    clean = " ".join(text.split())
    chunks = []
    start = 0
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        chunks.append(clean[start:end])
        if end == len(clean):
            break
        start = max(0, end - overlap)
    return chunks


def point_id(document_id: str, chunk_index: int) -> str:
    digest = hashlib.sha256(f"{document_id}:{chunk_index}".encode("utf-8")).hexdigest()
    return f"{digest[:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"


async def ingest(data_dir: Path) -> None:
    embeddings = VoyageEmbeddings()
    store = QdrantDocumentStore()
    all_points = []

    for filename, metadata in DOCUMENTS.items():
        path = data_dir / filename
        if not path.exists():
            print(f"missing {filename}")
            continue
        chunks = chunk_text(read_pdf_text(path))
        print(f"embedding {filename}: {len(chunks)} chunks")
        try:
            vectors = await embed_with_rate_limit(embeddings, chunks)
        except Exception as exc:
            print(f"failed {filename}: {exc}")
            raise
        for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
            payload = {
                **metadata,
                "source_file": filename,
                "chunk_index": index,
                "text": chunk,
            }
            all_points.append(
                {
                    "id": point_id(metadata["document_id"], index),
                    "vector": vector,
                    "payload": payload,
                }
            )
        print(f"prepared {filename}: {len(chunks)} chunks")

    await store.upsert_chunks(all_points)
    print(f"upserted {len(all_points)} chunks")


async def embed_with_rate_limit(embeddings: VoyageEmbeddings, chunks: list[str]) -> list[list[float]]:
    attempts = 0
    while True:
        attempts += 1
        try:
            return await embeddings.embed_texts(chunks)
        except ExternalServiceError as exc:
            message = str(exc)
            if "429" not in message or attempts >= 6:
                raise
            wait_seconds = 65
            print(f"Voyage rate limit hit; waiting {wait_seconds}s before retry {attempts + 1}/6")
            await asyncio.sleep(wait_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest ParcelPilot PDFs into Qdrant.")
    parser.add_argument("--data-dir", default=str(PROJECT_ROOT / "data"))
    args = parser.parse_args()
    asyncio.run(ingest(Path(args.data_dir)))


if __name__ == "__main__":
    main()
