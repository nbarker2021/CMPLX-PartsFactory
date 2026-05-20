import sqlite3
from pathlib import Path

db = Path("data/token_index_identity_review.sqlite")
c = sqlite3.connect(db)
print("bonds", c.execute("select count(*) from token_bonds").fetchone()[0])
print("links", c.execute("select count(*) from translation_links").fetchone()[0])
print("streams", list(c.execute("select stream, count(*) from token_bonds group by stream")))
tables = [r[0] for r in c.execute("select name from sqlite_master where type='table'")]
if "morph_signatures" in tables:
    print("morph_signatures", c.execute("select count(*) from morph_signatures").fetchone()[0])
if "token_geometry" in tables:
    print("token_geometry", c.execute("select count(*) from token_geometry").fetchone()[0])
