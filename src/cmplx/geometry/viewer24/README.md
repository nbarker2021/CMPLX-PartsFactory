
# Viewer24 v2 + CA + Inverse Residue Viewer (stdlib)

- Main Viewer: CA electromagnetic overlay across 24 screens (edge-aligned).
- Inverse Residue Viewer: captures a baseline EM-hex map, steps CA, and renders
  a residue likelihood (delta-hex minus seam delta) plus a red wrap mask showing
  regions that look like "wrap awaiting closure".
- Per tile, /api/ca/tile also returns hex codes for each pixel; inverse produces
  16-bin nibble histograms per channel (R,G,B) as fingerprints.

Run:
  python server.py
  # open http://127.0.0.1:9091  (Main Viewer)
  # open http://127.0.0.1:9091/inverse  (Inverse Viewer)
