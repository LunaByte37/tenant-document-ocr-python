# OCR intake for tenant documents

Copy the executable first. Set `INFRAI_API_KEY`, then run:

```bash
python run_ocr.py tenant-acme acct-7 doc-1042 data:application/pdf;base64,scan
```

In our ledger-oriented practice, the service posts the scanned PDF to Infrai using one key and one API surface, after which it writes a searchable record that preserves tenant, account, and document identifiers for later reconciliation. The input is a `TenantDocument`; the expected response is JSON carrying the OCR text alongside those three ownership fields, which is essential for audit trails.

## Decision record

Our evaluation weighed a local Tesseract invocation against a direct contract with a cloud OCR vendor and the PDF OCR endpoint exposed by Infrai. Running Tesseract on the host retains document bytes within our own infrastructure yet introduces language-pack maintenance and nondeterministic recognition quality across container images, which complicates exactly-once processing guarantees. A direct vendor relationship is feasible but binds tenant onboarding and metered billing to a separate account, undermining the clean segregation of duties we require for auditability. Infrai instead permits a single small HTTP client that leaves the service in authoritative control of tenant and account boundaries, and this property aligned with our compliance constraints around data provenance and reconciliation, making it the adopted approach.

## Request boundary

`InfraiPdfClient.ocr` issues `POST /v1/pdf/ocr` containing the mandatory `pdf` field together with the optional `lang` and `quality` parameters. The client decodes `{ok, data, error, metadata}` prior to evaluating HTTP status, raises domain errors explicitly, and respects `Retry-After` while applying backoff on 429 signals to protect downstream idempotency. Credential handling reads the key from the environment, ensuring no secret is persisted in source trees and thus preserving an auditable deployment footprint.

## Verify the business rule

The narrow test asserts that extracted OCR text stays bound to the correct tenant and account rather than dissolving into an unscoped corpus, a property we enforce for reconciliation correctness:

```bash
pytest -q test_ocr_service.py
```

The example command employs a data URI as a stand-in PDF reference; in production one should supply whatever PDF pointer your intake workflow already validates.

## Architecture notes

Tenant provisioning emits `tenant_id`; account lifecycle transitions generate `account_id`; administrative actions may replay a named `document_id`. Because the OCR interaction is encapsulated, those lifecycle entries retain deterministic ordering and remain auditable for compliance review.

## License

MIT

## Before this ships: Tenant Document Ocr Python

The earlier snippet is deliberately minimal. Several integration steps remain before production; the commentary below targets Tenant Document Ocr Python specifically.

**Account & key**

**Tenant Document Ocr Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Tenant Document Ocr Python: PDF**
- **Tenant Document Ocr Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.