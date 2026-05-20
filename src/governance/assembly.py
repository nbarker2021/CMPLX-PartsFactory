"""AssemblyLine — Atomic-level boundary validation and operational review.
Uses GeometricGovernance for all audit and event recording."""
from __future__ import annotations
import math
import time
import uuid
import logging
from typing import Dict, List, Any

logger = logging.getLogger("assembly")


class AssemblyLine:
    """Atomic-level boundary validation and operational review.
    
    Each expert operation is validated against:
    - Defined atomic boundaries with validation rules
    - Entropy constraints per boundary
    - Geometric governance for all boundary events
    """

    def __init__(self, governance):
        self.governance = governance
        self.boundaries: Dict[str, Dict[str, Any]] = {}
        self.validation_queue: List[Dict[str, Any]] = []
        self.entropy_predictions: List[Dict[str, Any]] = []
        self.operational_reviews: List[Dict[str, Any]] = []

    def define_boundary(self, boundary_id: str, spec: Dict[str, Any]) -> None:
        self.boundaries[boundary_id] = {
            "boundary_id": boundary_id,
            "specification": spec,
            "validation_rules": spec.get("validation_rules", []),
            "entropy_constraints": spec.get("entropy_constraints", {}),
            "created_at": time.time(),
        }

    def validate(self, boundary_id: str, operation: str,
                 operation_data: Dict[str, Any]) -> Dict[str, Any]:
        if boundary_id not in self.boundaries:
            return {"boundary_id": boundary_id, "valid": False,
                    "error": f"Unknown boundary: {boundary_id}"}

        boundary = self.boundaries[boundary_id]
        result = {
            "boundary_id": boundary_id,
            "operation": operation,
            "operation_data": operation_data,
            "timestamp": time.time(),
            "violations": [],
            "entropy_impact": 0.0,
            "valid": True,
        }

        for rule in boundary["validation_rules"]:
            if not self._check_rule(rule, operation_data):
                result["violations"].append(rule)
                result["valid"] = False

        result["entropy_impact"] = self._compute_entropy(operation_data)
        max_entropy = boundary["entropy_constraints"].get("max_entropy_delta", 1.0)
        if result["entropy_impact"] > max_entropy:
            result["violations"].append("entropy_constraint_exceeded")
            result["valid"] = False

        self.validation_queue.append(result)

        if result["valid"]:
            from .engine import BoundaryEvent
            self.governance.record_boundary_event(BoundaryEvent(
                event_id=f"atomic_{boundary_id}_{int(time.time())}",
                timestamp=time.time(),
                entropy_delta=result["entropy_impact"],
                receipt_data=result,
                boundary_type="atomic_validation",
            ))

        return result

    def _check_rule(self, rule: str, data: Dict[str, Any]) -> bool:
        if rule == "non_negative_values":
            return all(v >= 0 for v in data.values() if isinstance(v, (int, float)))
        if rule == "required_fields":
            required = ["operation_type", "timestamp"]
            return all(f in data for f in required)
        return True

    def _compute_entropy(self, data: dict) -> float:
        data_str = str(data)
        if not data_str:
            return 0.0
        entropy = 0.0
        for char in set(data_str):
            p = data_str.count(char) / len(data_str)
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy / 8.0

    def predict_entropy(self, time_horizon: float = 3600.0) -> Dict[str, Any]:
        current = time.time()
        recent = [v for v in self.validation_queue
                  if current - v["timestamp"] < time_horizon]
        if not recent:
            return {"prediction": "no_data", "confidence": 0.0}
        total = sum(v["entropy_impact"] for v in recent)
        avg_rate = total / len(recent)
        prediction = {
            "time_horizon": time_horizon,
            "predicted_entropy_delta": avg_rate * (time_horizon / 3600.0),
            "confidence": min(len(recent) / 10.0, 1.0),
            "trend": "increasing" if avg_rate > 0.1 else "stable",
        }
        self.entropy_predictions.append(prediction)
        return prediction

    def send_review(self, review_data: Dict[str, Any]) -> None:
        review = {
            "review_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "validation_summary": {
                "total": len(self.validation_queue),
                "successful": sum(1 for v in self.validation_queue if v["valid"]),
                "total_entropy": sum(v["entropy_impact"] for v in self.validation_queue),
            },
            "recommendations": self._generate_recommendations(),
            "review_data": review_data,
        }
        self.operational_reviews.append(review)

    def _generate_recommendations(self) -> List[str]:
        recs = []
        if self.validation_queue:
            fail_rate = sum(1 for v in self.validation_queue if not v["valid"]) / len(self.validation_queue)
            if fail_rate > 0.1:
                recs.append("High validation failure rate — review boundary specifications")
            avg_entropy = sum(v["entropy_impact"] for v in self.validation_queue) / len(self.validation_queue)
            if avg_entropy > 0.5:
                recs.append("High entropy impact — consider optimization")
        return recs
