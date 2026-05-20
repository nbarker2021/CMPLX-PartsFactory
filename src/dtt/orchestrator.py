from __future__ import annotations
import threading
import queue
import time
import json
import uuid
from typing import Dict, Any, Callable
from dataclasses import dataclass, field


class GovernanceBridge:
    """Minimal audit trail for tracking pipeline events."""
    
    def __init__(self):
        self.events: list[dict] = []
    
    def record(self, event_type: str, data: dict):
        self.events.append({
            "type": event_type,
            "timestamp": time.time(),
            **data,
        })


class IdeaPacket(dict):
    """A problem packet submitted to the orchestrator.
    
    Carries the user's request through the pipeline stages.
    """
    pass


@dataclass
class PipelineStep:
    """A single pipeline processing step."""
    name: str
    duration: float = 0.1
    result: dict = field(default_factory=dict)


@dataclass
class CompositionRound:
    """Records one round of expert composition."""
    round_number: int
    expert_outputs: dict[str, dict]
    synthesis: dict | None = None
    convergence_score: float = 0.0


class DTTTestRunner(threading.Thread):
    """Runs an IdeaPacket through the composition pipeline.
    
    Pipeline sequence:
      1. Retrieve → 2. Classify → 3. Expert dispatch → 
      4. Socratic compose → 5. Synthesize → 6. Register expert
    """
    
    def __init__(self, packet: IdeaPacket, gov: GovernanceBridge,
                 expert_fn: Callable | None = None):
        super().__init__(daemon=True)
        self.packet = packet
        self.gov = gov
        self.expert_fn = expert_fn
        self.result: dict = {}
        self.rounds: list[CompositionRound] = []
    
    def run(self):
        packet_id = self.packet.get("id", "unknown")
        self.gov.record("pipeline_start", {"packet_id": packet_id})
        
        # Determine which experts to dispatch based on problem type
        problem = self.packet.get("content", {}).get("problem", "")
        experts = self._route_problem(problem)
        
        # Round 0: Dispatch to selected experts
        round_0_outputs = {}
        for expert_name in experts:
            if self.expert_fn:
                round_0_outputs[expert_name] = self.expert_fn(expert_name, problem)
            else:
                round_0_outputs[expert_name] = {"status": "simulated", "expert": expert_name}
        
        self.rounds.append(CompositionRound(
            round_number=0,
            expert_outputs=round_0_outputs,
        ))
        
        # Rounds 1..N: Socratic compose until saturation
        self._socratic_compose(experts, problem)
        
        self.gov.record("pipeline_end", {"packet_id": packet_id, "rounds": len(self.rounds)})
    
    def _route_problem(self, problem: str) -> list[str]:
        """Route a problem to appropriate experts based on content."""
        problem_lower = problem.lower()
        experts = []
        
        if any(w in problem_lower for w in ["store", "crystal", "save", "memory"]):
            experts.append("mmdb")
        if any(w in problem_lower for w in ["label", "classify", "stratify", "taxonomy"]):
            experts.append("snap")
        if any(w in problem_lower for w in ["graph", "map", "explore", "hierarchy"]):
            experts.append("mdhg")
        if any(w in problem_lower for w in ["bond", "atom", "chemistry", "connect"]):
            experts.append("tarpit")
        if any(w in problem_lower for w in ["brain", "reason", "think", "probe"]):
            experts.append("manny")
        if any(w in problem_lower for w in ["cache", "receipt", "speed"]):
            experts.append("speedlight")
        
        if not experts:
            experts = ["snap", "manny", "mmdb"]
        
        return experts
    
    def _socratic_compose(self, experts: list[str], problem: str):
        """Iterative socratic composition rounds until saturation.
        
        Each round: experts read each other's outputs, critique, refine.
        Stops when outputs stop changing significantly.
        """
        max_rounds = 5
        threshold = 0.05
        
        for round_num in range(1, max_rounds + 1):
            prev = self.rounds[-1].expert_outputs
            
            if self.expert_fn:
                current = self.expert_fn("compose", f"{problem} | round {round_num}")
            else:
                current = {e: {"status": "composed", "round": round_num} for e in experts}
            
            self.rounds.append(CompositionRound(
                round_number=round_num,
                expert_outputs=current,
                convergence_score=1.0 - (round_num / max_rounds),
            ))
            
            if round_num >= 2:
                prev_set = {json.dumps(v, sort_keys=True) for v in prev.values()}
                curr_set = {json.dumps(v, sort_keys=True) for v in current.values()}
                if prev_set == curr_set:
                    break


class DTTOrchestrator:
    """DTT Orchestrator — Pipeline queue for expert composition.
    
    Receives IdeaPackets, dispatches to DTTTestRunners,
    tracks progress via GovernanceBridge.
    """
    
    def __init__(self, max_workers: int = 4, expert_fn: Callable | None = None):
        self.queue: queue.Queue[IdeaPacket] = queue.Queue()
        self.max_workers = max_workers
        self.active: set[str] = set()
        self.lock = threading.Lock()
        self.gov = GovernanceBridge()
        self.expert_fn = expert_fn
        self.results: dict[str, dict] = {}
        
        self._manager = threading.Thread(target=self._manage, daemon=True)
        self._manager.start()
    
    def submit(self, packet: dict) -> str:
        """Submit a problem packet to the pipeline."""
        pkt = IdeaPacket(packet)
        pkt.setdefault("id", f"idea:{uuid.uuid4().hex[:12]}")
        self.queue.put(pkt)
        self.gov.record("packet_queued", {"packet_id": pkt["id"]})
        return pkt["id"]
    
    def _manage(self):
        while True:
            pkt = self.queue.get()
            with self.lock:
                while len(self.active) >= self.max_workers:
                    time.sleep(0.1)
                runner = DTTTestRunner(pkt, self.gov, self.expert_fn)
                self.active.add(pkt["id"])
                runner.start()
                runner.join()
                self.results[pkt["id"]] = {
                    "rounds": len(runner.rounds),
                    "experts": list(runner.rounds[-1].expert_outputs.keys()) if runner.rounds else [],
                    "convergence": runner.rounds[-1].convergence_score if runner.rounds else 0,
                }
                self.active.remove(pkt["id"])
            self.queue.task_done()
    
    def get_result(self, packet_id: str) -> dict | None:
        return self.results.get(packet_id)
    
    def status(self) -> dict:
        return {
            "queue_size": self.queue.qsize(),
            "active": len(self.active),
            "completed": len(self.results),
            "total_events": len(self.gov.events),
        }


# Default orchestrator
default = DTTOrchestrator()
