"""Count how many distinct semantic-target address classes the
current substrate collapses onto. This is the size table 2 would
need to be."""
import sqlite3

con = sqlite3.connect("data/token_index.sqlite")
total = con.execute("SELECT COUNT(*) FROM token_bonds").fetchone()[0]

queries = [
    ("distinct_snap_keys", "SELECT COUNT(DISTINCT snap_key) FROM token_bonds"),
    ("distinct_e8_signatures", "SELECT COUNT(DISTINCT e8_signature) FROM token_bonds"),
    ("distinct_lanes", "SELECT COUNT(DISTINCT lane) FROM token_bonds"),
    ("distinct_DRs", "SELECT COUNT(DISTINCT digital_root) FROM token_bonds"),
    (
        "distinct_lane_x_DR",
        "SELECT COUNT(DISTINCT (lane || ':' || digital_root)) FROM token_bonds",
    ),
    (
        "distinct_lane_x_DR_x_snap",
        "SELECT COUNT(DISTINCT (lane || ':' || digital_root || ':' || snap_key)) "
        "FROM token_bonds",
    ),
]

print(f"{'metric':45s} {'count':>12s} {'compression':>14s}")
print("-" * 75)
print(f"{'total_rows':45s} {total:>12,} {'1.0x':>14s}")
for name, sql in queries:
    n = con.execute(sql).fetchone()[0]
    ratio = total / max(n, 1)
    print(f"{name:45s} {n:>12,} {ratio:>13.1f}x")
