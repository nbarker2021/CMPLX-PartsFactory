"""
DocReviewClient — client for the document review production API.

Queries the PartsFactory document review index:
  - Full-text search over extracted document text
  - Document metadata, reports, and extracts
  - Follow-up task tracking
  - Wave statistics

Environment:
  DOC_REVIEW_API_URL — base URL of the doc-review-api service
  DOC_REVIEW_API_KEY — optional API key (not yet enforced by server)
"""

import os
from typing import Any, Dict, List, Optional

import requests

DEFAULT_BASE = os.environ.get("DOC_REVIEW_API_URL", "http://localhost:8820")


class DocReviewClient:
    """Client for the doc-review-api service."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or DEFAULT_BASE).rstrip("/")
        self.api_key = api_key or os.environ.get("DOC_REVIEW_API_KEY", "")
        self._session = requests.Session()
        if self.api_key:
            self._session.headers["X-API-Key"] = self.api_key

    def _get(self, path: str, params: dict | None = None) -> dict:
        resp = self._session.get(f"{self.base_url}{path}", params=params or {}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def health(self) -> dict:
        """Health check."""
        try:
            return self._get("/health")
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    def stats(self) -> dict:
        """Aggregate statistics."""
        return self._get("/stats")

    def search(self, query: str, limit: int = 20) -> List[dict]:
        """Full-text search over document extracts."""
        return self._get("/search", {"q": query, "limit": limit})

    def list_documents(
        self,
        status: str | None = None,
        extension: str | None = None,
        wave_id: str | None = None,
        top_level_folder: str | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        """List documents with optional filters."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if extension:
            params["extension"] = extension
        if wave_id:
            params["wave_id"] = wave_id
        if top_level_folder:
            params["top_level_folder"] = top_level_folder
        if q:
            params["q"] = q
        return self._get("/documents", params)

    def get_document(self, doc_id: str) -> dict:
        """Get full document metadata."""
        return self._get(f"/documents/{doc_id}")

    def get_report(self, doc_id: str, format: str = "json") -> dict | str:
        """Get literal report (json or md)."""
        resp = self._session.get(
            f"{self.base_url}/documents/{doc_id}/report",
            params={"format": format},
            timeout=30,
        )
        resp.raise_for_status()
        if format == "json":
            return resp.json()
        return resp.text

    def get_extract(self, doc_id: str) -> str:
        """Get extracted text for a document."""
        resp = self._session.get(
            f"{self.base_url}/documents/{doc_id}/extract",
            timeout=30,
        )
        resp.raise_for_status()
        return resp.text

    def list_followups(
        self,
        status: str | None = None,
        extension: str | None = None,
        wave_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        """List follow-up tasks."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if extension:
            params["extension"] = extension
        if wave_id:
            params["wave_id"] = wave_id
        return self._get("/followups", params)

    def list_waves(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        """List waves."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        return self._get("/waves", params)
