import json
import sys

from ocr_service import InfraiPdfClient, TenantDocument, index_document


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit("usage: python run_ocr.py TENANT ACCOUNT DOCUMENT PDF_REFERENCE")
    tenant, account, document, pdf = sys.argv[1:]
    record = index_document(TenantDocument(tenant, account, document, pdf), InfraiPdfClient())
    print(json.dumps(record, ensure_ascii=True))


if __name__ == "__main__":
    main()
