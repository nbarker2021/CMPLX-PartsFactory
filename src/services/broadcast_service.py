"""Broadcast Service — Event broadcasting with E8 directional routing.

Port of TMN2 broadcast.py. Publish events to channels with
E8-labeled routing. Subscribers receive events matching their
label filters via inbox delivery.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import time
import uuid
from collections import defaultdict, deque
from itertools import combinations, product
from typing import Any, Optional

logger = logging.getLogger("services.broadcast")

PORT = int(os.environ.get("PORT", "8000"))
MAX_EVENTS = int(os.environ.get("MAX_EVENTS", "10000"))
MAX_SUBSCRIBER_QUEUE = int(os.environ.get("MAX_SUBSCRIBER_QUEUE", "500"))

CHANNELS = ["system", "atoms", "agents", "economy",
            "governance", "pipeline", "board", "errors"]


def _generate_e8_directions() -> list[list[float]]:
    roots = []
    for i, j in combinations(range(8), 2):
        for si, sj in product([1.0, -1.0], repeat=2):
            vec = [0.0] * 8
            vec[i] = si
            vec[j] = sj
            roots.append(vec)
    return roots


_E8_ROOTS = _generate_e8_directions()
E8_DIRECTIONS = len(_E8_ROOTS)

_DIRECTION_DIMS = []
for vec in _E8_ROOTS:
    dom = max(range(8), key=lambda k: abs(vec[k]))
    _DIRECTION_DIMS.append(dom)


class BroadcastService:
    """Event broadcasting with E8 directional routing.

    Pub/sub messaging system with channel-based event distribution,
    SNAP label filtering, E8 directional broadcast computation,
    and inbox delivery for subscribers.
    """

    def __init__(self, governance=None):
        self._governance = governance
        self._events: deque = deque(maxlen=MAX_EVENTS)
        self._subscribers: dict[str, dict] = {}
        self._channel_events: dict[str, deque] = {
            ch: deque(maxlen=1000) for ch in CHANNELS
        }
        self._event_counter: int = 0
        self._receipt_chain: str = "0" * 64
        self._stats = {
            "published": 0, "delivered": 0, "replayed": 0,
            "subscribers_registered": 0,
        }

    # ── Internal ─────────────────────────────────────────────

    def _mint_receipt(self, op: str, data: dict) -> str:
        payload = json.dumps(
            {"op": op, "data": data, "prev": self._receipt_chain,
             "ts": time.time()},
            sort_keys=True, default=str,
        )
        self._receipt_chain = hashlib.sha256(payload.encode()).hexdigest()[:32]
        return self._receipt_chain

    @staticmethod
    def _jaccard(a: set, b: set) -> float:
        union = a | b
        return len(a & b) / len(union) if union else 0.0

    @staticmethod
    def _label_direction_alignment(labels: list[str],
                                    direction_idx: int) -> float:
        if not labels:
            return 0.0
        vec = _E8_ROOTS[direction_idx]
        total_dot = 0.0
        for label in labels:
            h = hashlib.sha256(label.encode()).digest()
            proj = [(b - 128) / 128.0 for b in h[:8]]
            norm = math.sqrt(sum(x * x for x in proj))
            if norm > 0:
                proj = [x / norm for x in proj]
            total_dot += abs(sum(p * v for p, v in zip(proj, vec)))
        return total_dot / len(labels)

    def _compute_e8_broadcast(self, labels: list[str]) -> list[dict]:
        if not labels:
            return []
        direction_scores = []
        for i in range(E8_DIRECTIONS):
            score = self._label_direction_alignment(labels, i)
            direction_scores.append((i, score))

        direction_scores.sort(key=lambda x: -x[1])
        return [
            {
                "direction_idx": idx, "alignment": round(score, 4),
                "dominant_dim": _DIRECTION_DIMS[idx],
                "vector": [round(v, 2) for v in _E8_ROOTS[idx]],
            }
            for idx, score in direction_scores[:10]
        ]

    def _deliver_to_subscribers(self, event: dict):
        channel = event.get("channel", "")
        event_labels = set(event.get("snap_labels", []))

        for sub_id, sub in self._subscribers.items():
            channels = sub.get("channels", set())
            if channels and channel not in channels:
                continue

            filter_labels = sub.get("filter_labels_set", set())
            if filter_labels:
                overlap = filter_labels & event_labels
                if not overlap:
                    continue

            inbox = sub.setdefault("inbox", deque(maxlen=MAX_SUBSCRIBER_QUEUE))
            inbox.append({
                "event_id": event["event_id"], "channel": channel,
                "event_type": event["event_type"],
                "payload_summary": str(event.get("payload", {}))[:100],
                "snap_labels": event.get("snap_labels", [])[:5],
                "timestamp": event["timestamp"],
            })
            sub["unread_count"] = sub.get("unread_count", 0) + 1
            self._stats["delivered"] += 1

    # ── Public API ───────────────────────────────────────────

    def publish(self, channel: str = "system", event_type: str = "info",
                payload: dict = None,
                snap_labels: list[str] = None) -> dict:
        if channel not in CHANNELS:
            raise ValueError(
                f"Unknown channel '{channel}'. Valid: {CHANNELS}"
            )

        self._event_counter += 1
        event_id = f"evt-{self._event_counter:06d}"

        event = {
            "event_id": event_id, "channel": channel,
            "event_type": event_type,
            "payload": payload or {},
            "snap_labels": snap_labels or [],
            "timestamp": time.time(),
            "receipt": self._mint_receipt(
                "publish", {"event_id": event_id, "channel": channel}
            ),
        }

        e8_broadcast = self._compute_e8_broadcast(snap_labels or [])
        event["e8_directions"] = e8_broadcast

        self._events.append(event)
        self._channel_events[channel].append(event)
        self._stats["published"] += 1

        self._deliver_to_subscribers(event)

        logger.info("Published %s on %s (type=%s, labels=%d)",
                    event_id, channel, event_type, len(snap_labels or []))

        if self._governance:
            from governance.engine import BoundaryEvent
            self._governance.record_boundary_event(BoundaryEvent(
                event_id=f"broadcast-{event_id}",
                timestamp=time.time(), entropy_delta=0.0,
                receipt_data={"channel": channel, "event_type": event_type},
                boundary_type="broadcast_publish",
            ))

        return {
            "event_id": event_id, "channel": channel,
            "event_type": event_type, "labels": len(snap_labels or []),
            "e8_directions": len(e8_broadcast),
            "receipt": event["receipt"],
            "total_events": len(self._events),
        }

    def subscribe(self, subscriber_id: str, channel: str = "system",
                  filter_labels: list[str] = None) -> dict:
        if channel and channel not in CHANNELS:
            raise ValueError(
                f"Unknown channel '{channel}'. Valid: {CHANNELS}"
            )

        if subscriber_id in self._subscribers:
            sub = self._subscribers[subscriber_id]
            if channel:
                sub["channels"].add(channel)
            if filter_labels:
                sub["filter_labels_set"].update(filter_labels)
                sub["filter_labels"] = list(sub["filter_labels_set"])
        else:
            self._subscribers[subscriber_id] = {
                "subscriber_id": subscriber_id,
                "channels": {channel} if channel else set(),
                "filter_labels": filter_labels or [],
                "filter_labels_set": set(filter_labels or []),
                "inbox": deque(maxlen=MAX_SUBSCRIBER_QUEUE),
                "unread_count": 0,
                "ack_cursor": 0,
                "created_at": time.time(),
            }
            self._stats["subscribers_registered"] += 1

        logger.info("Subscriber %s registered for channel=%s labels=%d",
                    subscriber_id, channel, len(filter_labels or []))

        return {
            "subscriber_id": subscriber_id,
            "channels": list(self._subscribers[subscriber_id]["channels"]),
            "filter_labels": list(
                self._subscribers[subscriber_id]["filter_labels_set"]
            ),
            "total_subscribers": len(self._subscribers),
        }

    def unsubscribe(self, subscriber_id: str, channel: str = "") -> dict:
        if subscriber_id not in self._subscribers:
            raise ValueError(f"Subscriber {subscriber_id} not found")

        if channel:
            self._subscribers[subscriber_id]["channels"].discard(channel)
            remaining = len(self._subscribers[subscriber_id]["channels"])
            if remaining == 0:
                del self._subscribers[subscriber_id]
                return {"unsubscribed": subscriber_id, "channel": channel,
                        "removed_entirely": True}
            return {"unsubscribed": subscriber_id, "channel": channel,
                    "remaining_channels": remaining}
        else:
            del self._subscribers[subscriber_id]
            return {"unsubscribed": subscriber_id, "removed_entirely": True}

    def get_channels(self) -> dict:
        channel_info = {}
        for ch in CHANNELS:
            sub_count = sum(
                1 for s in self._subscribers.values()
                if ch in s.get("channels", set())
            )
            event_count = len(self._channel_events.get(ch, []))
            channel_info[ch] = {
                "subscribers": sub_count, "events": event_count,
                "latest": self._channel_events[ch][-1]["timestamp"]
                if self._channel_events.get(ch) else None,
            }
        return {"channels": channel_info,
                "total_subscribers": len(self._subscribers)}

    def get_events(self, channel: Optional[str] = None,
                   event_type: Optional[str] = None,
                   limit: int = 50, offset: int = 0) -> dict:
        if channel and channel not in CHANNELS:
            raise ValueError(f"Unknown channel '{channel}'")

        source = (
            list(self._channel_events.get(channel, []))
            if channel else list(self._events)
        )

        if event_type:
            source = [e for e in source if e.get("event_type") == event_type]

        total = len(source)
        source.reverse()
        page = source[offset:offset + limit]

        trimmed = []
        for evt in page:
            trimmed.append({
                "event_id": evt["event_id"], "channel": evt["channel"],
                "event_type": evt["event_type"],
                "snap_labels": evt.get("snap_labels", [])[:5],
                "timestamp": evt["timestamp"],
                "payload_keys": list(evt.get("payload", {}).keys()),
                "e8_directions_count": len(evt.get("e8_directions", [])),
            })

        return {"total": total, "offset": offset, "limit": limit,
                "returned": len(trimmed), "events": trimmed}

    def list_subscribers(self, channel: Optional[str] = None) -> dict:
        subs = []
        for sub_id, sub in self._subscribers.items():
            if channel and channel not in sub.get("channels", set()):
                continue
            subs.append({
                "subscriber_id": sub_id,
                "channels": list(sub.get("channels", set())),
                "filter_labels": list(sub.get("filter_labels_set", set()))[:10],
                "unread_count": sub.get("unread_count", 0),
                "inbox_size": len(sub.get("inbox", [])),
                "created_at": sub.get("created_at"),
            })
        return {"total": len(subs), "subscribers": subs}

    def replay(self, subscriber_id: str, channel: str = "",
               count: int = 50) -> dict:
        if subscriber_id not in self._subscribers:
            raise ValueError(f"Subscriber {subscriber_id} not found")

        sub = self._subscribers[subscriber_id]

        if channel and channel in CHANNELS:
            source = list(self._channel_events.get(channel, []))
        else:
            source = list(self._events)

        replay_events = source[-count:]

        inbox = sub.setdefault("inbox", deque(maxlen=MAX_SUBSCRIBER_QUEUE))
        delivered = 0
        for evt in replay_events:
            inbox.append({
                "event_id": evt["event_id"],
                "channel": evt.get("channel", ""),
                "event_type": evt["event_type"],
                "payload_summary": str(evt.get("payload", {}))[:100],
                "snap_labels": evt.get("snap_labels", [])[:5],
                "timestamp": evt["timestamp"],
                "replayed": True,
            })
            delivered += 1

        sub["unread_count"] = sub.get("unread_count", 0) + delivered
        self._stats["replayed"] += delivered

        logger.info("Replayed %d events to %s (channel=%s)",
                    delivered, subscriber_id, channel or "all")

        return {"subscriber_id": subscriber_id, "channel": channel,
                "replayed": delivered, "inbox_size": len(inbox)}

    @property
    def health(self) -> dict:
        return {
            "ok": True, "service": "broadcast",
            "channels": CHANNELS,
            "e8_directions": E8_DIRECTIONS,
            "total_events": len(self._events),
            "subscribers": len(self._subscribers),
        }

    @property
    def stats(self) -> dict:
        channel_counts = {
            ch: len(self._channel_events.get(ch, [])) for ch in CHANNELS
        }
        return {
            "service": "broadcast", "total_events": len(self._events),
            "max_events": MAX_EVENTS, "published": self._stats["published"],
            "delivered": self._stats["delivered"],
            "replayed": self._stats["replayed"],
            "subscribers": len(self._subscribers),
            "subscribers_registered_total": self._stats["subscribers_registered"],
            "e8_directions": E8_DIRECTIONS,
            "channel_event_counts": channel_counts,
        }
