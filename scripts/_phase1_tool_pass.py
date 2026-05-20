"""One-shot tool pass for Phase 1 (bounded keys)."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cmplx.transform.tool_pass import TokenToolPass  # noqa: E402

db = Path("data/token_index_identity_review.sqlite")
limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50
runner = TokenToolPass.from_db(db)
stats = {"keys_run": 0, "receipts": 0, "errors": 0}
t0 = time.time()
try:
    cur = runner.links._conn.execute(
        """
        SELECT translation_key FROM translation_links
        GROUP BY translation_key
        HAVING COUNT(DISTINCT stream) >= 2
        ORDER BY translation_key
        LIMIT ?
        """,
        (limit,),
    )
    keys = [str(row[0]) for row in cur.fetchall()]
    for i, key in enumerate(keys):
        try:
            result = runner.run(key)
            stats["keys_run"] += 1
            stats["receipts"] += len(result.receipts)
        except Exception as exc:
            stats["errors"] += 1
            if stats["errors"] <= 3:
                print(f"error on {key}: {exc}", file=sys.stderr)
        if (i + 1) % 10 == 0:
            print(f"progress {i+1}/{len(keys)}", flush=True)
finally:
    runner.links.close()
stats["elapsed_seconds"] = round(time.time() - t0, 3)
print(json.dumps(stats, indent=2))
