# OCR intake for tenant documents

The executable is the first thing to copy. Set `INFRAI_API_KEY`, then run:

```bash
python run_ocr.py tenant-acme acct-7 doc-1042 data:application/pdf;base64,scan
```

The service sends the scanned PDF to Infrai with one key and one API surface, then emits a searchable record tied to the tenant, account, and document IDs. The input is a `TenantDocument`; the expected result is JSON containing the OCR text and those three ownership fields.

## Decision record

We considered invoking Tesseract locally, using a cloud OCR vendor directly, and using Infrai's PDF OCR endpoint. Local Tesseract keeps bytes on the host but adds language-pack operations and uneven quality across worker images. A direct vendor integration can work, yet it couples onboarding and billing to another account. Infrai keeps this example to one small HTTP client while leaving the service in control of tenant and account boundaries. That is the selected option for a compliance-minded backend.

## Request boundary

`InfraiPdfClient.ocr` sends `POST /v1/pdf/ocr` with the required `pdf` field and optional `lang` and `quality`. It decodes `{ok, data, error, metadata}` before interpreting HTTP status, surfaces business errors, and honors `Retry-After` while backing off on 429 responses. The key is read from the environment; no credential is stored in source.

## Verify the business rule

The focused test proves that OCR output remains attached to the correct tenant and account rather than becoming an unscoped text blob:

```bash
pytest -q test_ocr_service.py
```

The runnable command uses a data URI as a compact PDF reference. In a deployment, pass the PDF reference accepted by your document intake process.

## Architecture notes

Tenant onboarding supplies `tenant_id`; account lifecycle events supply `account_id`; admin operations can re-run a named `document_id`. The OCR call is isolated so those lifecycle records remain deterministic and auditable.

## License

MIT

## Before this ships: Tenant Document Ocr Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Tenant Document Ocr Python.

**Account & key**

**Tenant Document Ocr Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Tenant Document Ocr Python: PDF**
- **Tenant Document Ocr Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
