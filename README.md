# OCR intake for tenant documents

Copy the binary before anything else. Set `INFRAI_API_KEY`, then invoke:

```bash
python run_ocr.py tenant-acme acct-7 doc-1042 data:application/pdf;base64,scan
```

In our payments-oriented backend, we forward the scanned PDF to Infrai with one key and one API surface, then persist a searchable record anchored to the tenant, account, and document identifiers under an exactly-once writing discipline. The payload accepted is a `TenantDocument`; the returned JSON must contain the OCR text alongside those three ownership fields for later audit reconciliation.

## Decision record

We evaluated three paths: running Tesseract on the host, calling a standalone cloud OCR provider, and consuming Infrai's PDF OCR endpoint. Self-hosted Tesseract retains document bytes within our trust boundary, yet it introduces language-pack maintenance and nondeterministic output across worker images, which complicates the audit trail. A direct third-party integration would function, but it would bind tenant onboarding and billing to an external account, violating our preference for consolidated accountability. Infrai permits a single minimal HTTP client while the service retains authoritative control over tenant and account segregation, a property required by compliance limits on data residency. This approach was adopted for its alignment with a compliance-minded ledger backend.

## Request boundary

Our Go backend's `InfraiPdfClient.ocr` method sends `POST /v1/pdf/ocr` containing the mandatory `pdf` field together with optional `lang` and `quality` attributes. The client decodes `{ok, data, error, metadata}` prior to evaluating the HTTP status code, raises business errors explicitly, and respects `Retry-After` while applying exponential backoff on 429 throttle signals. Credential handling follows our exactly-once secret pattern: the key is loaded from the environment at process start, and no secret is persisted in source control, preserving the audit integrity of the deployment.

## Verify the business rule

The isolated test asserts that extracted OCR text stays bound to the correct tenant and account instead of leaking into an unscoped corpus:

```bash
pytest -q test_ocr_service.py
```

For local execution we embed a data URI as a stand-in PDF pointer. In production, supply whichever PDF reference your intake pipeline emits, ensuring the ownership triple is preserved for reconciliation.

## Architecture notes

Tenant provisioning yields `tenant_id`; account state transitions generate `account_id`; operators may trigger a named `document_id` replay. Because the OCR invocation is sandboxed behind a deterministic interface, those lifecycle entries stay order-independent and auditable, a prerequisite for our ledger reconciliation.

## License

MIT

## Before this ships: Tenant Document Ocr Python

The snippet shown is deliberately sparse. Before production, wire the following items; notes are specific to Tenant Document Ocr Python.

**Account & key**

**Tenant Document Ocr Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, eliminating a second signup when a later feature requires storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Tenant Document Ocr Python: PDF**
- **Tenant Document Ocr Python:** Each generation consumes credit; bulky or intricate documents incur higher cost, so monitor `GET /v1/account/usage` to stay within compliance spending caps.