# Receipt sale candidates (suggestions only)

Local production must work before packaging. Candidates after `docker compose -f docker-compose.receipt.yml up` + green `pytest tests/receipt/`.

| SKU idea | What ships | Buyer value |
|----------|------------|-------------|
| Audit API | Hosted `/mint` + `/verify` + export | Compliance trail |
| Verification SDK | `ReceiptChain.verify` + JSONL run verifier | CI gates |
| Run ledger kit | `write_run_receipt` + HMAC | SpeedLight-style pipelines |
| Compliance export | `ledger_manager.export_ledger` + spine merge | CQE audit bundles |

Not in scope: repo-kernel route promotion, wallet fallback removal, SNAP delegation.
