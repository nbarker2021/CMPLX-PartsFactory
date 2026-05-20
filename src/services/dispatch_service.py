"""Dispatch Service — Work dispatch through agent matching.

Port of TMN2 dispatch.py. Routes tasks to agents by SNAP label
Jaccard similarity. Priority queue with auto-retry on failure.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from collections import defaultdict
from typing import Any, Optional

logger = logging.getLogger("services.dispatch")

PORT = int(os.environ.get("PORT", "8000"))
COOP_URL = os.environ.get("COOP_URL", "http://host.docker.internal:8012")
BOARD_URL = os.environ.get("BOARD_URL", "http://host.docker.internal:8013")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))

PRIORITIES = {0: "critical", 1: "high", 2: "normal", 3: "low", 4: "background"}


class DispatchService:
    """Task dispatch with SNAP-label agent matching.

    Registers agents by SNAP label sets, dispatches tasks to the
    best-matching idle agent using Jaccard similarity, maintains a
    priority queue, and supports auto-retry on failure.
    """

    def __init__(self, governance=None):
        self._governance = governance
        self._agents: dict[str, dict] = {}
        self._queue: list[dict] = []
        self._active: dict[str, dict] = {}
        self._completed: list[dict] = []
        self._failed: list[dict] = []
        self._receipt_chain: str = "0" * 64
        self._stats = {
            "dispatched": 0, "completed": 0, "failed": 0,
            "retried": 0, "total_time": 0.0,
        }

    # ── Internal ─────────────────────────────────────────────

    @staticmethod
    def _jaccard(a: set, b: set) -> float:
        union = a | b
        return len(a & b) / len(union) if union else 0.0

    def _mint_receipt(self, op: str, data: dict) -> str:
        payload = json.dumps(
            {"op": op, "data": data, "prev": self._receipt_chain,
             "ts": time.time()},
            sort_keys=True, default=str,
        )
        self._receipt_chain = hashlib.sha256(payload.encode()).hexdigest()[:32]
        return self._receipt_chain

    def _find_best_agent(self, snap_labels: list[str]) -> Optional[dict]:
        task_labels = set(snap_labels)
        if not task_labels:
            return None

        best = None
        best_score = 0.0

        for agent_id, agent in self._agents.items():
            if agent["state"] != "idle":
                continue
            if agent["active_tasks"] >= agent["capacity"]:
                continue

            score = self._jaccard(task_labels, agent["labels_set"])
            if score > best_score:
                best_score = score
                best = {
                    "agent_id": agent_id, "score": score,
                    "department": agent["department"],
                }

        return best

    def _sort_queue(self):
        self._queue.sort(key=lambda x: (x["priority"], x["created_at"]))

    def _dispatch_one(self, task: dict) -> dict:
        dispatch_id = str(uuid.uuid4())[:12]
        match = self._find_best_agent(task["snap_labels"])

        dispatch_record = {
            "dispatch_id": dispatch_id,
            "task_description": task["task_description"],
            "snap_labels": task["snap_labels"],
            "priority": task["priority"],
            "priority_name": PRIORITIES.get(task["priority"], "unknown"),
            "reward": task["reward"],
            "matched_agent": match,
            "status": "dispatched" if match else "queued",
            "retries": task.get("retries", 0),
            "created_at": task.get("created_at", time.time()),
            "dispatched_at": time.time() if match else None,
            "receipt": self._mint_receipt("dispatch", {"dispatch_id": dispatch_id}),
        }

        if match:
            agent = self._agents.get(match["agent_id"])
            if agent:
                agent["active_tasks"] += 1
                if agent["active_tasks"] >= agent["capacity"]:
                    agent["state"] = "working"

            self._active[dispatch_id] = dispatch_record
            self._stats["dispatched"] += 1
            logger.info("Dispatched %s to agent %s (score=%.4f, priority=%s)",
                        dispatch_id, match["agent_id"], match["score"],
                        PRIORITIES.get(task["priority"], "?"))
        else:
            dispatch_record["queued_at"] = time.time()
            self._queue.append(dispatch_record)
            self._sort_queue()
            logger.info("Queued %s (no matching agent, priority=%s)",
                        dispatch_id, PRIORITIES.get(task["priority"], "?"))

        return dispatch_record

    def _try_drain_queue(self):
        if not self._queue:
            return
        still_queued = []
        for task in self._queue:
            match = self._find_best_agent(task.get("snap_labels", []))
            if match:
                dispatch_id = task.get("dispatch_id", str(uuid.uuid4())[:12])
                task["dispatch_id"] = dispatch_id
                task["matched_agent"] = match
                task["status"] = "dispatched"
                task["dispatched_at"] = time.time()
                task["receipt"] = self._mint_receipt(
                    "dispatch", {"dispatch_id": dispatch_id}
                )

                agent = self._agents.get(match["agent_id"])
                if agent:
                    agent["active_tasks"] += 1
                    if agent["active_tasks"] >= agent["capacity"]:
                        agent["state"] = "working"

                self._active[dispatch_id] = task
                self._stats["dispatched"] += 1
            else:
                still_queued.append(task)
        self._queue.clear()
        self._queue.extend(still_queued)

    # ── Public API ───────────────────────────────────────────

    def register_agent(self, agent_id: str, snap_labels: list[str] = None,
                       capacity: int = 1, department: str = "") -> dict:
        self._agents[agent_id] = {
            "agent_id": agent_id,
            "snap_labels": snap_labels or [],
            "labels_set": set(snap_labels or []),
            "capacity": capacity,
            "department": department,
            "state": "idle",
            "active_tasks": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "registered_at": time.time(),
        }
        self._mint_receipt("register_agent", {"agent_id": agent_id})
        logger.info("Registered agent %s with %d labels, capacity=%d",
                    agent_id, len(snap_labels or []), capacity)
        return {
            "registered": agent_id, "labels": len(snap_labels or []),
            "total_agents": len(self._agents),
        }

    def dispatch(self, task_description: str,
                 snap_labels: list[str] = None,
                 priority: int = 2, reward: float = 1.0) -> dict:
        task = {
            "task_description": task_description,
            "snap_labels": snap_labels or [],
            "priority": priority,
            "reward": reward,
            "created_at": time.time(),
            "retries": 0,
        }

        if self._governance:
            from governance.engine import BoundaryEvent
            self._governance.record_boundary_event(BoundaryEvent(
                event_id=f"dispatch-{uuid.uuid4().hex[:8]}",
                timestamp=time.time(), entropy_delta=0.0,
                receipt_data={"task": task_description[:60],
                              "priority": priority},
                boundary_type="dispatch_request",
            ))

        return self._dispatch_one(task)

    def batch_dispatch(self, tasks: list[dict]) -> dict:
        results = []
        for task_req in tasks:
            task = {
                "task_description": task_req["task_description"],
                "snap_labels": task_req.get("snap_labels", []),
                "priority": task_req.get("priority", 2),
                "reward": task_req.get("reward", 1.0),
                "created_at": time.time(),
                "retries": 0,
            }
            results.append(self._dispatch_one(task))

        dispatched = sum(1 for r in results if r["status"] == "dispatched")
        queued = sum(1 for r in results if r["status"] == "queued")

        return {"total": len(results), "dispatched": dispatched,
                "queued": queued, "results": results}

    def get_queue(self, priority: Optional[int] = None,
                  limit: int = 50) -> dict:
        filtered = self._queue
        if priority is not None:
            filtered = [q for q in filtered if q["priority"] == priority]
        return {
            "total_queued": len(self._queue),
            "filtered": len(filtered),
            "returned": min(limit, len(filtered)),
            "tasks": filtered[:limit],
        }

    def get_active(self, limit: int = 50) -> dict:
        active_list = sorted(
            self._active.values(),
            key=lambda x: x.get("dispatched_at", 0), reverse=True,
        )
        return {
            "total_active": len(self._active),
            "returned": min(limit, len(active_list)),
            "tasks": active_list[:limit],
        }

    def complete_task(self, dispatch_id: str,
                      result_summary: str = "") -> dict:
        if dispatch_id not in self._active:
            raise ValueError(f"Dispatch {dispatch_id} not found in active tasks")

        record = self._active.pop(dispatch_id)
        record["status"] = "completed"
        record["completed_at"] = time.time()
        record["result_summary"] = result_summary
        record["duration"] = record["completed_at"] - (
            record.get("dispatched_at") or record["created_at"]
        )
        record["receipt"] = self._mint_receipt(
            "complete", {"dispatch_id": dispatch_id}
        )

        if record.get("matched_agent"):
            agent_id = record["matched_agent"]["agent_id"]
            agent = self._agents.get(agent_id)
            if agent:
                agent["active_tasks"] = max(0, agent["active_tasks"] - 1)
                agent["tasks_completed"] += 1
                if agent["active_tasks"] < agent["capacity"]:
                    agent["state"] = "idle"

        self._completed.append(record)
        if len(self._completed) > 1000:
            self._completed.pop(0)

        self._stats["completed"] += 1
        self._stats["total_time"] += record["duration"]
        logger.info("Completed %s in %.2fs", dispatch_id, record["duration"])
        self._try_drain_queue()

        return record

    def fail_task(self, dispatch_id: str, reason: str = "") -> dict:
        if dispatch_id not in self._active:
            raise ValueError(f"Dispatch {dispatch_id} not found in active tasks")

        record = self._active.pop(dispatch_id)
        retries = record.get("retries", 0) + 1

        if record.get("matched_agent"):
            agent_id = record["matched_agent"]["agent_id"]
            agent = self._agents.get(agent_id)
            if agent:
                agent["active_tasks"] = max(0, agent["active_tasks"] - 1)
                agent["tasks_failed"] += 1
                if agent["active_tasks"] < agent["capacity"]:
                    agent["state"] = "idle"

        if retries <= MAX_RETRIES:
            record["retries"] = retries
            record["status"] = "queued"
            record["fail_reason"] = reason
            record["requeued_at"] = time.time()
            record["matched_agent"] = None
            record["dispatched_at"] = None
            self._queue.append(record)
            self._sort_queue()
            self._stats["retried"] += 1
            logger.info("Re-queued %s (retry %d/%d): %s",
                        dispatch_id, retries, MAX_RETRIES, reason)
            self._try_drain_queue()
            return {"dispatch_id": dispatch_id, "status": "requeued",
                    "retries": retries, "max_retries": MAX_RETRIES,
                    "reason": reason}
        else:
            record["status"] = "failed"
            record["fail_reason"] = reason
            record["failed_at"] = time.time()
            record["retries"] = retries
            record["receipt"] = self._mint_receipt(
                "fail", {"dispatch_id": dispatch_id}
            )
            self._failed.append(record)
            if len(self._failed) > 500:
                self._failed.pop(0)
            self._stats["failed"] += 1
            logger.warning("Failed %s after %d retries: %s",
                           dispatch_id, retries, reason)
            return {"dispatch_id": dispatch_id, "status": "failed",
                    "retries": retries, "reason": reason}

    def list_agents(self) -> dict:
        agents = []
        for aid, agent in self._agents.items():
            agents.append({
                "agent_id": aid, "state": agent["state"],
                "department": agent["department"],
                "labels": len(agent["snap_labels"]),
                "capacity": agent["capacity"],
                "active_tasks": agent["active_tasks"],
                "completed": agent["tasks_completed"],
                "failed": agent["tasks_failed"],
            })
        return {"total": len(agents), "agents": agents}

    @property
    def stats(self) -> dict:
        avg_time = (
            self._stats["total_time"] / self._stats["completed"]
            if self._stats["completed"] > 0 else 0
        )

        agent_summary = {}
        for aid, agent in self._agents.items():
            agent_summary[aid] = {
                "state": agent["state"], "department": agent["department"],
                "labels": len(agent["snap_labels"]),
                "capacity": agent["capacity"],
                "active_tasks": agent["active_tasks"],
                "completed": agent["tasks_completed"],
                "failed": agent["tasks_failed"],
            }

        priority_queue_counts = defaultdict(int)
        for q in self._queue:
            priority_queue_counts[PRIORITIES.get(q["priority"], "unknown")] += 1

        return {
            "service": "dispatch",
            "total_dispatched": self._stats["dispatched"],
            "total_completed": self._stats["completed"],
            "total_failed": self._stats["failed"],
            "total_retried": self._stats["retried"],
            "avg_completion_time": round(avg_time, 3),
            "queued": len(self._queue), "active": len(self._active),
            "agents": len(self._agents),
            "queue_by_priority": dict(priority_queue_counts),
            "agent_summary": agent_summary, "max_retries": MAX_RETRIES,
        }

    @property
    def health(self) -> dict:
        return {
            "ok": True, "service": "dispatch",
            "agents": len(self._agents), "queued": len(self._queue),
            "active": len(self._active), "completed": len(self._completed),
        }
