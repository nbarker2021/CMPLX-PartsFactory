# Data State

Lattice Forge uses two data layers.

## Seed

The bundled seed database is package data under `lattice_forge.ledger.data`.
It is opened read-only by `SeedStore` and contains the canonical starter state:
objects, exact vectors, Gram forms, morphisms, admissibility edges, terminal
forms, glue requirements, obstructions, NSL profiles, witnesses, and path
metrics.

Terminal forms are executable seed views. The package can generate a terminal
composition tree from existing seed rows without mutating the seed: terminal
record, component decompositions, component embeddings, source reflection
actions, discriminant profile, and legacy glue rows are assembled into a
canonical route and emergent residue trace.

For rootful terminal forms, missing exact reflection rows are represented as
computed compact simple-reflection generators with explicit `computed_profile`
evidence. The Leech lattice is represented as the rootless 24D terminal with
pending-import evidence for exact code-construction data.

The seed is verified with SQLite `PRAGMA integrity_check` and the ledger's
semantic `verify()` method.

## Overlay

Project-local state is created at `.lattice_forge/overlay.sqlite`.

Overlay tables hold:

- receipts
- events
- query cache
- handoffs
- imports

New project-specific or external records must enter the overlay first. The seed
database is not mutated by queries.
