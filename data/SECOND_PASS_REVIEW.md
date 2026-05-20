# Second-Pass Review Playbook

> The merger produces two tiers of canonicals: **hardened** (high
> replica count, validated, made runnable) and **pending review**
> (low replica count, preserved for re-inclusion after the hardened
> set stabilizes). This document is the policy for evaluating
> pending canonicals on second pass.

## The principle

Premature pruning loses the system's forward motion.

A symbol that appears in 50 source files is the *standardized* version
of an idea. A symbol that appears in 1-9 files is more likely:

- a **novel adaptation** that had not yet propagated when the snapshot
  was taken;
- a **recently-added upgrade** that exists only in one or two places,
  possibly superseding the hardened version;
- a **specific-purpose fix** or **adaptation layer** that addresses
  one particular need the broader set doesn't cover;
- or genuine **noise** the first-pass noise filter missed.

The first three are exactly the material we **want** to preserve and
re-consider. The fourth is the only one we want to drop. The default
of "low replica = discard" gets this backwards.

## The two-tier layout

```
src/cmplx/<family>/<Name>.py             # hardened — runnable target
src/cmplx_pending/<family>/<Name>.py     # preserved for review

projections/<family>/<Name>.py           # hardened domain projection
projections_pending/<family>/<Name>.py   # preserved domain projection
```

Both trees are full canonical Python files. Pending files differ
only in their header docstring (review-criteria explanation) and
their location.

## Threshold

Default: **`chosen_witness_count >= 10`** goes to hardened.

This is configurable via `partition_canonicals.py --threshold N`.
Set lower (e.g. 5) to be more inclusive in hardened; higher (e.g. 25)
to be stricter.

## When to do a second pass

After the hardened tier has been:

1. **Made runnable** — imports resolved, smoke tests passing, the
   `src/cmplx/` package can be imported cleanly.
2. **Functionally validated** — at least one round of "what can this
   actually do" exercising key canonicals.
3. **Cross-checked against external use** — confirmed (manually or via
   Codex/Kimi catalog joins) that the hardened set actually meets the
   needs of the production deployments.

Once these three are true, the hardened set is the *baseline*. The
second pass reviews the pending tree against that baseline.

## Review criteria for each pending file

When evaluating a pending file, walk these questions:

### (a) Coverage check

Is the file's functionality already in the hardened set?

- **YES, fully covered** → check (b).
- **YES, partially covered** → check (c).
- **NO, not at all covered** → check (d).

### (b) Novel-material check (when hardened covers the same functionality)

Read the pending file's class body. Does it have any of:

- Methods the hardened version doesn't?
- Field/attribute additions the hardened version doesn't?
- Different signature on a method that suggests a newer API?
- A docstring or comment that documents intent the hardened version lacks?

If **yes to any**: this is novel material worth merging into the
hardened canonical. Add to the next compose pass with explicit
preservation. Record the decision in `decisions_v2.jsonl`.

If **no to all**: this is a stale duplicate. Mark `drop_with_rationale`
and move it to `data/pending_review_dropped.jsonl` with the
note "fully redundant with hardened version `<path>`".

### (c) Specialization check (when hardened partially covers it)

The pending file may be a specialization for a specific context.

- Is its specialization meaningful (a real customization for a real
  use case)? → Promote to hardened as a *subclass* or *variant* of
  the existing canonical, kept distinct rather than merged.
- Is the specialization brittle/abandoned? → Drop with rationale.

### (d) Promotion check (when nothing covers it)

The pending file is novel.

- Does the functionality fit an existing family? → Move to hardened
  under that family.
- Does it justify a new family? → Create a new family directory.
- Is it actually noise? (test, demo, scratch experiment that got
  past the filter) → Drop with rationale.

### (e) Newer-than-hardened check

Run this **before** (a)-(d) for any pending file:

- Compare the witness file's path / timestamp against the witnesses
  of the corresponding hardened canonical.
- If the pending file's witnesses are from a *more recent* corpus
  or build than the hardened ones, the pending version may actually
  be a *newer rewrite* that has not yet replicated. **Treat it as a
  potential supersession candidate.**
- If supersession is genuine: promote the pending version to
  hardened, archive the old hardened to `cmplx_archive/`.

## Output of a second-pass review session

For each pending file, the review produces one of these dispositions:

| Disposition | What happens |
|---|---|
| `promote_as_is` | Move to `src/cmplx/` unchanged. Decision logged. |
| `promote_supersedes` | Move to `src/cmplx/`, archive the displaced hardened canonical. |
| `merge_into_hardened` | Run an explicit method-union pass with the named hardened canonical. Composed source replaces the hardened canonical. Pending file archived. |
| `keep_as_specialization` | Move to `src/cmplx/<family>/specializations/` as a sibling of the canonical. Documented as a deliberate variant. |
| `drop_with_rationale` | Move to `data/pending_review_dropped.jsonl` with rationale. File deleted from pending tree. |
| `defer_to_next_pass` | Leave in pending. Re-evaluate next cycle. |

## Automation hooks

`partition_canonicals.py` writes structured metadata into each pending
file's header. A future `review_pending.py` could:

- Auto-classify each pending file by re-querying the index for
  "is the qualname in hardened? same signature? newer witness?"
- Emit a `pending_review_proposals.csv` with one suggested disposition
  per file.
- A human or LLM agent walks the CSV and confirms/overrides each
  disposition.
- Run an `apply_review.py` that executes the dispositions.

This stays consistent with the queue-and-worker pattern: the review
is a batch of decisions, each with a recordable disposition.

## Why this matters

The default reflex on "low replica" is "delete." That reflex would
discard:

- the prototype for a feature being added (it's only in one file
  because someone just wrote it)
- the fix for an edge case the broader codebase hasn't seen (it's
  only in one file because that's the only place the bug appeared)
- the experiment that worked and was on its way to being broadly
  adopted (it's only in two files because adoption was in progress)

These are the system's growing edges. The two-tier model preserves
them while letting the hardened set stabilize on what's already
shared. That's the right shape for an actually-evolving codebase.

## Companion files

- `data/HARDENED_INDEX.md` — table of every hardened canonical
- `data/PENDING_REVIEW_INDEX.md` — table of every pending canonical
- `data/atomic_index.sqlite` — full provenance for both trees
- `data/MASTER_BUILD_TEMPLATE.md` — the target layout overall
