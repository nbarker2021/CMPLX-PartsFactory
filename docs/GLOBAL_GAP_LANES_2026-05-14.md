# Global Gap Lanes

Generated: 2026-05-14

## Purpose

The coverage map exposed additional unassigned clusters after the primary
system lanes were added. These clusters are now first-class global systems.

## Added From Coverage Gaps

| System | Global API | Cluster It Owns |
| --- | --- | --- |
| `formalization` | `/api/global/formalization` | proof, theorem, axiom, planner, octet, unfold, handshake, channel protocol |
| `ai-runtime` | `/api/global/ai-runtime` | infer, model, embed, generate, LLM/chat runtime surfaces |
| `operations` | `/api/global/operations` | health, status, metrics, dashboard, manager, restart, scale, report, cache, dock |
| `eventing` | `/api/global/eventing` | broadcast, subscribe, dispatch, publish, events, channels, replay |
| `community` | `/api/global/community` | board, posts, threads, bounties, OpenClaw/board bridge, planets |
| `economy` | `/api/global/economy` | mint, economy, marketplace, commissions, lending, staking, pools |
| `validation` | `/api/global/validation` | data stewardship, conservation, gate checks, audit, quality |
| `synthesis` | `/api/global/synthesis` | brain, integrator, interrogation, canon builder, folder librarian, Free5e porter |
| `simulation` | `/api/global/simulation` | sim, CA simulation, CPL, Julia/planet dynamics |

## Runtime Evidence

`operations` owns TMN management ports such as `11150` through `11163` and
`11172`. `eventing` owns `11191`, `11192`, and `11193`. `ai-runtime` currently
maps model/chat surfaces with `3000` as the known Next/API runtime evidence.

## Policy

These lanes were added because coverage identified them as implementation
needs. They remain planning-only until a runtime slice is selected,
health-checked, and explicitly approved.
