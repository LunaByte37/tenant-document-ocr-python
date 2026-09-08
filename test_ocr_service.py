import json
from ocr_service import InfraiPdfClient, TenantDocument, index_document


class FakeClient(InfraiPdfClient):
    def __init__(self):
        pass

    def ocr(self, pdf, lang=None, quality=None):
        assert (pdf, lang, quality) == ("data:application/pdf;base64,scan", "eng", "balanced")
        return {"text": "Invoice 1042\nApproved"}


def test_index_document_keeps_tenant_and_account_boundaries():
    record = index_document(
        TenantDocument("tenant-acme", "acct-7", "doc-1042", "data:application/pdf;base64,scan"),
        FakeClient(),
    )
    assert record == {
        "tenant_id": "tenant-acme", "account_id": "acct-7", "document_id": "doc-1042",
        "text": "Invoice 1042\nApproved",
    }
