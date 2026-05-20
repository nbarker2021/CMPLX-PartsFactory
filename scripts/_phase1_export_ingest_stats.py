"""Export ingest stats bundle from token index DB."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cmplx.transform.token_index.store import TokenIndexStore  # noqa: E402
from cmplx.transform.translation_store import TranslationLinkStore  # noqa: E402

db = Path("data/token_index_identity_review.sqlite")
out = Path("data/ingest_identity_review_stats.json")
store = TokenIndexStore(db)
links = TranslationLinkStore.from_connection(store._conn, str(db))
link_stats = links.stats()
bond_by_stream = {
    str(row[0]): int(row[1])
    for row in store._conn.execute(
        "SELECT stream, COUNT(*) FROM token_bonds GROUP BY stream"
    )
}
dual_keys = store._conn.execute(
    """
    SELECT COUNT(*) FROM (
      SELECT translation_key FROM translation_links
      GROUP BY translation_key HAVING COUNT(DISTINCT stream) >= 2
    )
    """
).fetchone()[0]
morph_count = store._conn.execute("SELECT COUNT(*) FROM morph_signatures").fetchone()[0]
geom_count = store._conn.execute("SELECT COUNT(*) FROM token_geometry").fetchone()[0]
bundle = {
    "streams_note": "per-stream ingest counters from last bounded run may be stale; bond/link counts are live",
    "translation_links": link_stats,
    "bonds_by_stream": bond_by_stream,
    "dual_stream_translation_keys": int(dual_keys),
    "token_geometry_rows": int(geom_count),
    "morph_signatures_rows": int(morph_count),
}
out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
print(json.dumps(bundle, indent=2))
store.close()
links.close()
