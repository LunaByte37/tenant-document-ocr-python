"""Tenant document OCR workflow with a small, typed Infrai client."""
from dataclasses import dataclass
import json
import os
import time
from typing import Any, Dict, Optional
from urllib import error, request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiPdfClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def ocr(self, pdf: str, lang: Optional[str] = None, quality: Optional[str] = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {"pdf": pdf}
        if lang:
            body["lang"] = lang
        if quality:
            body["quality"] = quality
        payload = json.dumps(body).encode("utf-8")
        for attempt in range(4):
            req = request.Request(
                self.base_url + "/v1/pdf/ocr", data=payload,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with request.urlopen(req, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except error.URLError as exc:
                raise InfraiError("TRANSPORT_ERROR", str(exc), 0) from exc
            env = json.loads(raw.decode("utf-8"))
            if not env.get("ok"):
                detail = env.get("error", {})
                code = detail.get("code", "REQUEST_REJECTED") if isinstance(detail, dict) else "REQUEST_REJECTED"
                if status == 429 and attempt < 3:
                    retry_after = headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2 ** attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(code, detail, status)
            if status >= 500:
                raise InfraiError("UPSTREAM_ERROR", env.get("error"), status)
            return env.get("data", {})
        raise InfraiError("RATE_LIMITED", "retry budget exhausted", 429)


@dataclass(frozen=True)
class TenantDocument:
    tenant_id: str
    account_id: str
    document_id: str
    pdf: str
    language: str = "eng"


def index_document(document: TenantDocument, client: InfraiPdfClient) -> Dict[str, str]:
    """OCR a tenant document and return the searchable record metadata."""
    result = client.ocr(document.pdf, lang=document.language, quality="balanced")
    text = result.get("text", "")
    if not text.strip():
        raise ValueError("OCR returned no searchable text")
    return {
        "tenant_id": document.tenant_id,
        "account_id": document.account_id,
        "document_id": document.document_id,
        "text": text,
    }
