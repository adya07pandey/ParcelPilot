from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError, ValidationError


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float
    metadata: dict[str, Any]


class VoyageEmbeddings:
    endpoint = "https://api.voyageai.com/v1/embeddings"
    fallback_models = ("voyage-3.5", "voyage-3", "voyage-2")

    def __init__(self) -> None:
        self.settings = get_settings()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self.settings.voyage_api_key:
            raise ValidationError("VOYAGE_API_KEY is not configured", code="VOYAGE_NOT_CONFIGURED")
        if not texts:
            return []

        errors = []
        models = [self.settings.voyage_embedding_model]
        models.extend(model for model in self.fallback_models if model not in models)

        async with httpx.AsyncClient(timeout=30) as client:
            for model in models:
                try:
                    response = await client.post(
                        self.endpoint,
                        headers={"Authorization": f"Bearer {self.settings.voyage_api_key}"},
                        json={"model": model, "input": texts},
                    )
                except httpx.RequestError as exc:
                    errors.append(f"{model} -> connection failed: {exc}")
                    continue
                if response.status_code < 400:
                    break
                errors.append(f"{model} -> {response.status_code}: {response.text[:240]}")
                if response.status_code == 429:
                    break
            else:
                response = None

        if response is None or response.status_code >= 400:
            raise ExternalServiceError(
                f"Voyage embedding request failed: {' | '.join(errors)}",
                code="VOYAGE_REQUEST_FAILED",
            )

        payload = response.json()
        embeddings = [item["embedding"] for item in payload.get("data", [])]
        if len(embeddings) != len(texts):
            raise ExternalServiceError(
                f"Voyage returned {len(embeddings)} embeddings for {len(texts)} inputs",
                code="VOYAGE_RESPONSE_MISMATCH",
            )
        return embeddings


class QdrantDocumentStore:
    keyword_indexes = (
        "scope",
        "account_id",
        "document_id",
        "document_type",
        "status",
        "version",
    )

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def collection_url(self) -> str:
        if not self.settings.qdrant_url:
            raise ValidationError("QDRANT_URL is not configured", code="QDRANT_NOT_CONFIGURED")
        return f"{self.settings.qdrant_url.rstrip('/')}/collections/{self.settings.qdrant_collection}"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.settings.qdrant_api_key:
            headers["api-key"] = self.settings.qdrant_api_key
        return headers

    async def ensure_collection(self, vector_size: int) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                existing = await client.get(self.collection_url, headers=self._headers())
            except httpx.RequestError as exc:
                raise ExternalServiceError(
                    f"Qdrant collection check failed: {exc}",
                    code="QDRANT_CONNECTION_FAILED",
                ) from exc
            if existing.status_code == 404:
                try:
                    created = await client.put(
                        self.collection_url,
                        headers=self._headers(),
                        json={"vectors": {"size": vector_size, "distance": "Cosine"}},
                    )
                except httpx.RequestError as exc:
                    raise ExternalServiceError(
                        f"Qdrant collection creation failed: {exc}",
                        code="QDRANT_CONNECTION_FAILED",
                    ) from exc
                if created.status_code >= 400:
                    raise ExternalServiceError(
                        f"Qdrant collection creation failed ({created.status_code}): {created.text[:500]}",
                        code="QDRANT_COLLECTION_CREATE_FAILED",
                    )
            elif existing.status_code != 200:
                raise ExternalServiceError(
                    f"Qdrant collection check failed ({existing.status_code}): {existing.text[:500]}",
                    code="QDRANT_COLLECTION_CHECK_FAILED",
                )

            await self.ensure_payload_indexes(client)

    async def ensure_payload_indexes(self, client: httpx.AsyncClient) -> None:
        for field_name in self.keyword_indexes:
            try:
                response = await client.put(
                    f"{self.collection_url}/index",
                    headers=self._headers(),
                    params={"wait": "true"},
                    json={"field_name": field_name, "field_schema": "keyword"},
                )
            except httpx.RequestError as exc:
                raise ExternalServiceError(
                    f"Qdrant payload index creation failed: {exc}",
                    code="QDRANT_CONNECTION_FAILED",
                ) from exc
            if response.status_code >= 400 and "already exists" not in response.text.lower():
                raise ExternalServiceError(
                    f"Qdrant payload index creation failed ({response.status_code}): {response.text[:500]}",
                    code="QDRANT_INDEX_CREATE_FAILED",
                )

    async def search(
        self,
        *,
        vector: list[float],
        account_id: str | None,
        include_all_accounts: bool = False,
        limit: int = 6,
        effective_at: str | None = None,
    ) -> list[RetrievedChunk]:
        await self.ensure_collection(len(vector))
        tenant_filter = self._tenant_filter(account_id, include_all_accounts=include_all_accounts)
        _ = effective_at

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    f"{self.collection_url}/points/search",
                    headers=self._headers(),
                    json={
                        "vector": vector,
                        "limit": limit,
                        "with_payload": True,
                        "filter": tenant_filter,
                    },
                )
            except httpx.RequestError as exc:
                raise ExternalServiceError(
                    f"Qdrant search request failed: {exc}",
                    code="QDRANT_CONNECTION_FAILED",
                ) from exc
        if response.status_code >= 400:
            raise ExternalServiceError(
                f"Qdrant search request failed ({response.status_code}): {response.text[:500]}",
                code="QDRANT_SEARCH_FAILED",
            )

        results = response.json().get("result", [])
        return [
            RetrievedChunk(
                chunk_id=str(item.get("id")),
                text=(item.get("payload") or {}).get("text", ""),
                score=float(item.get("score", 0)),
                metadata={key: value for key, value in (item.get("payload") or {}).items() if key != "text"},
            )
            for item in results
        ]

    async def upsert_chunks(self, points: list[dict[str, Any]]) -> None:
        if not points:
            return
        await self.ensure_collection(len(points[0]["vector"]))
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.put(
                    f"{self.collection_url}/points?wait=true",
                    headers=self._headers(),
                    json={"points": points},
                )
            except httpx.RequestError as exc:
                raise ExternalServiceError(
                    f"Qdrant upsert request failed: {exc}",
                    code="QDRANT_CONNECTION_FAILED",
                ) from exc
        if response.status_code >= 400:
            raise ExternalServiceError(
                f"Qdrant upsert request failed ({response.status_code}): {response.text[:500]}",
                code="QDRANT_UPSERT_FAILED",
            )

    async def scroll_account_documents(
        self,
        *,
        account_id: str,
        document_type: str = "customer_agreement",
        limit: int = 4,
    ) -> list[RetrievedChunk]:
        if not account_id:
            return []
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    f"{self.collection_url}/points/scroll",
                    headers=self._headers(),
                    json={
                        "limit": limit,
                        "with_payload": True,
                        "filter": {
                            "must": [
                                {"key": "scope", "match": {"value": "ACCOUNT"}},
                                {"key": "account_id", "match": {"value": account_id}},
                                {"key": "document_type", "match": {"value": document_type}},
                            ]
                        },
                    },
                )
            except httpx.RequestError as exc:
                raise ExternalServiceError(
                    f"Qdrant account document fetch failed: {exc}",
                    code="QDRANT_CONNECTION_FAILED",
                ) from exc
        if response.status_code >= 400:
            raise ExternalServiceError(
                f"Qdrant account document fetch failed ({response.status_code}): {response.text[:500]}",
                code="QDRANT_SCROLL_FAILED",
            )

        points = response.json().get("result", {}).get("points", [])
        return [
            RetrievedChunk(
                chunk_id=str(item.get("id")),
                text=(item.get("payload") or {}).get("text", ""),
                score=1.0,
                metadata={key: value for key, value in (item.get("payload") or {}).items() if key != "text"},
            )
            for item in points
        ]

    def _tenant_filter(self, account_id: str | None, *, include_all_accounts: bool = False) -> dict[str, Any]:
        allowed_scopes: list[dict[str, Any]] = [{"key": "scope", "match": {"value": "GLOBAL"}}]
        if include_all_accounts:
            allowed_scopes.append({"key": "scope", "match": {"value": "ACCOUNT"}})
        elif account_id:
            allowed_scopes.append({"key": "account_id", "match": {"value": account_id}})
        return {"should": allowed_scopes}


class GroqChat:
    endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self) -> None:
        self.settings = get_settings()

    async def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.1) -> str:
        if not self.settings.groq_api_key:
            raise ValidationError("GROQ_API_KEY is not configured", code="GROQ_NOT_CONFIGURED")

        async with httpx.AsyncClient(timeout=45) as client:
            try:
                response = await client.post(
                    self.endpoint,
                    headers={"Authorization": f"Bearer {self.settings.groq_api_key}"},
                    json={
                        "model": self.settings.groq_model,
                        "messages": messages,
                        "temperature": temperature,
                    },
                )
            except httpx.RequestError as exc:
                raise ExternalServiceError(
                    f"Groq chat request failed: {exc}",
                    code="GROQ_CONNECTION_FAILED",
                ) from exc
        if response.status_code >= 400:
            raise ExternalServiceError(
                f"Groq chat request failed ({response.status_code}): {response.text[:500]}",
                code="GROQ_REQUEST_FAILED",
            )

        payload = response.json()
        return payload["choices"][0]["message"]["content"]


async def search_authorized_documents(
    *,
    query: str,
    account_id: str | None,
    include_all_accounts: bool = False,
    effective_at: str | None = None,
    limit: int = 6,
) -> list[RetrievedChunk]:
    embeddings = VoyageEmbeddings()
    vector = (await embeddings.embed_texts([query]))[0]
    return await QdrantDocumentStore().search(
        vector=vector,
        account_id=account_id,
        include_all_accounts=include_all_accounts,
        effective_at=effective_at,
        limit=limit,
    )


async def fetch_authorized_account_agreement(*, account_id: str | None, limit: int = 4) -> list[RetrievedChunk]:
    if not account_id:
        return []
    return await QdrantDocumentStore().scroll_account_documents(account_id=account_id, limit=limit)
