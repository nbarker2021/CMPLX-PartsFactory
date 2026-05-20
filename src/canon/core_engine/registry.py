"""
CMPLX Tool Registry
===================

Unified registry exposing all CMPLX toolkit tools via MCP.

This makes every tool from both CMPLX-Build and CMPLX-Toolkit available
through the Model Context Protocol.
"""

import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger("cmplx.mcp.integration")


@dataclass
class ToolDefinition:
    """Definition of an MCP-exposed tool."""
    name: str
    description: str
    handler: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    returns: Dict[str, Any] = field(default_factory=dict)
    category: str = "general"
    requires_config: bool = False
    emits_receipt: bool = True


class CMPLXToolRegistry:
    """
    Unified registry for ALL CMPLX tools.
    
    Categories:
    - quorum: Multi-agent deliberation
    - think_tank: Autonomous improvement
    - planetary_db: Content storage/retrieval
    - receipts: Audit trail
    - health: System monitoring
    - tmn: Triadic Manifold Network
    - geometric: E8, Leech, Niemeier operations
    - governance: Digital roots, validation
    - bridge: LLM integrations
    """
    
    def __init__(self, config=None, data_root: Path = None):
        self.config = config
        self.data_root = data_root or Path.home() / ".cmplx"
        self.tools: Dict[str, ToolDefinition] = {}
        self._initialized = False
        
        # Component references (initialized lazily)
        self._quorum_engine = None
        self._think_tank = None
        self._planetary_db = None
        self._receipt_ledger = None
        self._health_checker = None
        self._tmn = None
        self._agent_runs: Dict[str, Dict[str, Any]] = {}
        self._controller_hierarchy = None
        self._snap_labeler = None
        self._mmdb_controller = None
        self._memory_pipeline = None
        self._agent_hub = None
        
        # Register all tools
        self._register_all_tools()
    
    def _register_all_tools(self):
        """Register all CMPLX toolkit tools."""
        # QUORUM TOOLS
        self._register_quorum_tools()
        
        # THINK TANK TOOLS
        self._register_think_tank_tools()

        # AGENT ORCHESTRATION TOOLS
        self._register_agent_tools()
        
        # PLANETARY DATABASE TOOLS
        self._register_planetary_tools()
        
        # RECEIPT SYSTEM TOOLS
        self._register_receipt_tools()
        
        # HEALTH MONITORING TOOLS
        self._register_health_tools()
        
        # TMN CORE TOOLS
        self._register_tmn_tools()
        
        # GEOMETRIC TOOLS (from existing MCP OS)
        self._register_geometric_tools()
        
        # GOVERNANCE TOOLS
        self._register_governance_tools()
        
        # CONTROLLER HIERARCHY TOOLS
        self._register_controller_tools()

        # MMDB MEMORY TOOLS
        self._register_mmdb_tools()

        # MMDB+MDHG+SPEEDLIGHT+SNAP PIPELINE TOOLS
        self._register_memory_pipeline_tools()

        # SPEEDLIGHT SIDECAR TOOLS
        self._register_speedlight_tools()

        # SNAP LABELER TOOLS
        self._register_snap_tools()

        # WORKFLOW ORCHESTRATION TOOLS
        self._register_workflow_tools()

        # ADVANCED COMPOSITE TOOLS
        self._register_advanced_tools()
        
        logger.info(f"Registered {len(self.tools)} CMPLX tools")
    
    def register(self, tool: ToolDefinition):
        """Register a tool."""
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    async def call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a registered tool."""
        if name not in self.tools:
            return {"error": f"Unknown tool: {name}", "available": list(self.tools.keys())}
        
        tool = self.tools[name]
        
        try:
            # Call the handler
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(arguments, self)
            else:
                result = tool.handler(arguments, self)
            
            # Emit receipt if required
            if tool.emits_receipt and self._receipt_ledger:
                self._emit_tool_receipt(name, arguments, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return {"error": str(e), "tool": name}
    
    def _emit_tool_receipt(self, tool_name: str, inputs: Dict, outputs: Dict):
        """Emit receipt for tool execution."""
        try:
            from cmplx_toolkit.autonomy.receipts import ReceiptLedger
            
            if self._receipt_ledger is None:
                ledger_path = self.data_root / "receipts.jsonl"
                self._receipt_ledger = ReceiptLedger(str(ledger_path))
            
            self._receipt_ledger.write_receipt(
                controller="mcp_tool_registry",
                operation=tool_name,
                inputs=inputs,
                outputs={k: v for k, v in outputs.items() if k != "error"},
                metadata={"timestamp": datetime.utcnow().isoformat()}
            )
        except Exception as e:
            logger.warning(f"Failed to emit receipt: {e}")
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "parameters": t.parameters,
                "returns": t.returns
            }
            for t in self.tools.values()
        ]
    
    # ===== QUORUM TOOLS =====
    
    def _register_quorum_tools(self):
        """Register Quorum deliberation tools."""
        
        self.register(ToolDefinition(
            name="quorum_deliberate",
            description="Run multi-agent quorum deliberation on a question",
            category="quorum",
            handler=self._handle_quorum_deliberate,
            parameters={
                "question": {"type": "string", "description": "Question to deliberate"},
                "roles": {"type": "array", "items": ["planner", "implementer", "critic", "researcher"], "optional": True},
                "use_tools": {"type": "boolean", "default": True},
                "use_cache": {"type": "boolean", "default": True}
            },
            returns={
                "synthesis": "string",
                "synthesis_confidence": "number",
                "role_responses": "object",
                "consensus_areas": "array",
                "disagreements": "array"
            }
        ))
        
        self.register(ToolDefinition(
            name="quorum_check_cache",
            description="Check quorum deliberation cache statistics",
            category="quorum",
            handler=self._handle_quorum_cache_stats,
            returns={
                "total_entries": "number",
                "total_accesses": "number",
                "avg_accesses": "number"
            }
        ))
        
        self.register(ToolDefinition(
            name="quorum_clear_cache",
            description="Clear quorum deliberation cache",
            category="quorum",
            handler=self._handle_quorum_clear_cache,
            returns={"cleared": "boolean"}
        ))
    
    async def _handle_quorum_deliberate(self, args: Dict, registry) -> Dict:
        """Handle quorum deliberation."""
        from cmplx_toolkit.config import ToolkitConfig
        from cmplx_toolkit.quorum.engine import QuorumEngine
        
        if registry._quorum_engine is None:
            config = registry.config or ToolkitConfig.from_env()
            registry._quorum_engine = QuorumEngine(config)
        
        result = await registry._quorum_engine.deliberate(
            question=args.get("question", ""),
            roles=args.get("roles", ["planner", "implementer", "critic", "researcher"]),
            use_tools=args.get("use_tools", True),
            use_cache=args.get("use_cache", True)
        )
        
        return result if isinstance(result, dict) else result.__dict__
    
    async def _handle_quorum_cache_stats(self, args: Dict, registry) -> Dict:
        """Handle cache stats request."""
        if registry._quorum_engine is None:
            return {"error": "Quorum engine not initialized"}
        
        return registry._quorum_engine.cache.get_stats()
    
    async def _handle_quorum_clear_cache(self, args: Dict, registry) -> Dict:
        """Handle cache clear."""
        if registry._quorum_engine is None:
            return {"error": "Quorum engine not initialized"}
        
        registry._quorum_engine.cache.clear()
        return {"cleared": True}
    
    # ===== THINK TANK TOOLS =====
    
    def _register_think_tank_tools(self):
        """Register Think Tank management tools."""
        
        self.register(ToolDefinition(
            name="think_tank_status",
            description="Get Think Tank current status",
            category="think_tank",
            handler=self._handle_think_tank_status,
            returns={
                "running": "boolean",
                "enabled": "boolean",
                "circuit_breaker_open": "boolean",
                "pending_proposals": "number",
                "total_sessions": "number"
            }
        ))
        
        self.register(ToolDefinition(
            name="think_tank_start",
            description="Start the Think Tank autonomous loop",
            category="think_tank",
            handler=self._handle_think_tank_start,
            returns={"started": "boolean"}
        ))
        
        self.register(ToolDefinition(
            name="think_tank_stop",
            description="Stop the Think Tank autonomous loop",
            category="think_tank",
            handler=self._handle_think_tank_stop,
            returns={"stopped": "boolean"}
        ))
        
        self.register(ToolDefinition(
            name="think_tank_run_session",
            description="Force immediate Think Tank session",
            category="think_tank",
            handler=self._handle_think_tank_run_session,
            returns={"session_completed": "boolean", "proposals_generated": "number"}
        ))
        
        self.register(ToolDefinition(
            name="think_tank_get_proposals",
            description="Get list of pending proposals",
            category="think_tank",
            handler=self._handle_think_tank_get_proposals,
            returns={"proposals": "array"}
        ))
        
        self.register(ToolDefinition(
            name="think_tank_approve_proposal",
            description="Approve a pending proposal",
            category="think_tank",
            handler=self._handle_think_tank_approve,
            parameters={"proposal_id": {"type": "string"}},
            returns={"approved": "boolean"}
        ))
        
        self.register(ToolDefinition(
            name="think_tank_reject_proposal",
            description="Reject a pending proposal",
            category="think_tank",
            handler=self._handle_think_tank_reject,
            parameters={
                "proposal_id": {"type": "string"},
                "reason": {"type": "string", "optional": True}
            },
            returns={"rejected": "boolean"}
        ))
        
        self.register(ToolDefinition(
            name="think_tank_get_history",
            description="Get Think Tank session history",
            category="think_tank",
            handler=self._handle_think_tank_history,
            parameters={"limit": {"type": "number", "default": 10}},
            returns={"history": "array"}
        ))
    
    def _get_think_tank(self):
        """Get or initialize Think Tank."""
        if self._think_tank is None:
            from cmplx_toolkit.autonomy.think_tank import (ThinkTankConfig,
                                                           ThinkTankLoop)
            from cmplx_toolkit.bridge.hf_backend import HFBackend
            from cmplx_toolkit.config import ToolkitConfig

            configured_path = os.getenv("CMPLX_THINK_TANK_CODEBASE")
            if configured_path:
                think_tank_path = Path(configured_path).expanduser()
            else:
                think_tank_path = Path.cwd()

            if not think_tank_path.exists():
                logger.warning(
                    "CMPLX_THINK_TANK_CODEBASE path does not exist: %s. Falling back to data_root.",
                    think_tank_path,
                )
                think_tank_path = self.data_root

            hf_backend = HFBackend(ToolkitConfig.from_env())
            
            config = ThinkTankConfig(
                enabled=True,
                safety_mode="strict"
            )
            self._think_tank = ThinkTankLoop(
                codebase_path=think_tank_path,
                config=config,
                hf_backend=hf_backend,
            )
        return self._think_tank
    
    async def _handle_think_tank_status(self, args: Dict, registry) -> Dict:
        """Get Think Tank status."""
        tt = registry._get_think_tank()
        return tt.get_status()
    
    async def _handle_think_tank_start(self, args: Dict, registry) -> Dict:
        """Start Think Tank."""
        import asyncio
        tt = registry._get_think_tank()
        asyncio.create_task(tt.start())
        return {"started": True}
    
    async def _handle_think_tank_stop(self, args: Dict, registry) -> Dict:
        """Stop Think Tank."""
        tt = registry._get_think_tank()
        tt.stop()
        return {"stopped": True}
    
    async def _handle_think_tank_run_session(self, args: Dict, registry) -> Dict:
        """Force a session."""
        tt = registry._get_think_tank()
        if hasattr(tt, "run_session"):
            await tt.run_session()
        elif hasattr(tt, "_run_session"):
            await tt._run_session()
        else:
            return {
                "error": "ThinkTankLoop does not expose a runnable session method",
                "tool": "think_tank_run_session",
            }
        return {
            "session_completed": True,
            "proposals_generated": len(tt.pending_proposals)
        }
    
    async def _handle_think_tank_get_proposals(self, args: Dict, registry) -> Dict:
        """Get pending proposals."""
        tt = registry._get_think_tank()
        return {"proposals": tt.get_pending_proposals()}
    
    async def _handle_think_tank_approve(self, args: Dict, registry) -> Dict:
        """Approve proposal."""
        tt = registry._get_think_tank()
        result = tt.approve_proposal(args.get("proposal_id", ""))
        return {"approved": result}
    
    async def _handle_think_tank_reject(self, args: Dict, registry) -> Dict:
        """Reject proposal."""
        tt = registry._get_think_tank()
        tt.reject_proposal(
            args.get("proposal_id", ""),
            reason=args.get("reason", "")
        )
        return {"rejected": True}
    
    async def _handle_think_tank_history(self, args: Dict, registry) -> Dict:
        """Get session history."""
        tt = registry._get_think_tank()
        limit = args.get("limit", 10)
        return {"history": tt.session_history[-limit:]}
    
    # ===== PLANETARY DATABASE TOOLS =====

    def _register_agent_tools(self):
        """Register subagent profile/team orchestration tools."""

        self.register(ToolDefinition(
            name="agent_list_profiles",
            description="List available subagent profiles and team presets",
            category="agent_orchestration",
            handler=self._handle_agent_list_profiles,
            returns={"profiles": "object", "teams": "object"}
        ))

        self.register(ToolDefinition(
            name="agent_start",
            description="Start a profile or team of subagent workers",
            category="agent_orchestration",
            handler=self._handle_agent_start,
            parameters={
                "profile": {"type": "string", "optional": True},
                "team": {"type": "string", "optional": True},
                "count": {"type": "number", "optional": True},
                "python_exec": {"type": "string", "optional": True},
                "paths": {"type": "string", "optional": True},
                "include_mcp": {"type": "boolean", "optional": True},
                "continuous": {"type": "boolean", "optional": True},
                "live": {"type": "boolean", "optional": True},
                "max_restarts": {"type": "number", "optional": True}
            },
            returns={
                "run_id": "string",
                "mode": "string",
                "started_agents": "number",
                "status": "array"
            }
        ))

        self.register(ToolDefinition(
            name="agent_status",
            description="Get status for active subagent orchestration runs",
            category="agent_orchestration",
            handler=self._handle_agent_status,
            parameters={"run_id": {"type": "string", "optional": True}},
            returns={"runs": "array"}
        ))

        self.register(ToolDefinition(
            name="agent_stop",
            description="Stop a subagent orchestration run",
            category="agent_orchestration",
            handler=self._handle_agent_stop,
            parameters={
                "run_id": {"type": "string", "optional": True},
                "stop_all": {"type": "boolean", "default": False}
            },
            returns={"stopped": "array", "remaining_runs": "number"}
        ))

        self.register(ToolDefinition(
            name="agent_hub_create_session",
            description="Create a dedicated agent/subagent session with MMDB-backed in-session memory",
            category="agent_orchestration",
            handler=self._handle_agent_hub_create_session,
            parameters={
                "name": {"type": "string", "optional": True},
                "metadata": {"type": "object", "optional": True},
                "db_path": {"type": "string", "optional": True},
            },
            returns={"session": "object"},
        ))

        self.register(ToolDefinition(
            name="agent_hub_list_sessions",
            description="List active agent hub sessions",
            category="agent_orchestration",
            handler=self._handle_agent_hub_list_sessions,
            parameters={"db_path": {"type": "string", "optional": True}},
            returns={"sessions": "array"},
        ))

        self.register(ToolDefinition(
            name="agent_hub_register_agent",
            description="Register an agent or subagent in a hub session",
            category="agent_orchestration",
            handler=self._handle_agent_hub_register_agent,
            parameters={
                "session_id": {"type": "string"},
                "role": {"type": "string"},
                "goal": {"type": "string"},
                "backstory": {"type": "string", "optional": True},
                "tools": {"type": "array", "optional": True},
                "model": {"type": "string", "optional": True},
                "max_iterations": {"type": "number", "optional": True},
                "temperature": {"type": "number", "optional": True},
                "delegation": {"type": "boolean", "optional": True},
                "metadata": {"type": "object", "optional": True},
                "parent_agent_id": {"type": "string", "optional": True},
                "db_path": {"type": "string", "optional": True},
            },
            returns={"agent": "object"},
        ))

        self.register(ToolDefinition(
            name="agent_hub_append_memory",
            description="Append an in-session memory event into MMDB/MDHG pipeline",
            category="agent_orchestration",
            handler=self._handle_agent_hub_append_memory,
            parameters={
                "session_id": {"type": "string"},
                "content": {"type": "string"},
                "role": {"type": "string", "default": "user"},
                "level": {"type": "string", "default": "ca", "description": "ca|city|planetary"},
                "metadata": {"type": "object", "optional": True},
                "terms": {"type": "array", "optional": True},
                "db_path": {"type": "string", "optional": True},
            },
            returns={"memory": "object"},
        ))

        self.register(ToolDefinition(
            name="agent_hub_recall",
            description="Recall only in-session memories for a session",
            category="agent_orchestration",
            handler=self._handle_agent_hub_recall,
            parameters={
                "session_id": {"type": "string"},
                "query": {"type": "string"},
                "top_k": {"type": "number", "default": 5},
                "level": {"type": "string", "optional": True},
                "snap_required": {"type": "array", "optional": True},
                "db_path": {"type": "string", "optional": True},
            },
            returns={"recall": "object"},
        ))

        self.register(ToolDefinition(
            name="agent_hub_run_task",
            description="Run a task on a session agent with optional in-session memory recording",
            category="agent_orchestration",
            handler=self._handle_agent_hub_run_task,
            parameters={
                "session_id": {"type": "string"},
                "agent_id": {"type": "string"},
                "task": {"type": "string"},
                "inputs": {"type": "object", "optional": True},
                "remember": {"type": "boolean", "default": True},
                "level": {"type": "string", "default": "ca"},
                "db_path": {"type": "string", "optional": True},
            },
            returns={"run": "object"},
        ))

        self.register(ToolDefinition(
            name="agent_hub_session_status",
            description="Get status for an agent hub session including live agents and memory",
            category="agent_orchestration",
            handler=self._handle_agent_hub_session_status,
            parameters={
                "session_id": {"type": "string"},
                "db_path": {"type": "string", "optional": True},
            },
            returns={"status": "object"},
        ))

    def _agent_python_default(self) -> str:
        root = Path(__file__).resolve().parents[2]
        return str(root / "sandbox" / ".venv" / "Scripts" / "python.exe")

    @staticmethod
    def _package_available(python_exec: str, package_name: str) -> bool:
        probe = subprocess.run(
            [python_exec, "-c", f"import {package_name}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return probe.returncode == 0

    def _sanitize_agent_args(self, python_exec: str, base_args: List[str]) -> List[str]:
        if "--include-mcp" in base_args and not self._package_available(python_exec, "mcp"):
            logger.warning("Skipping --include-mcp because 'mcp' package is unavailable in %s", python_exec)
            return [arg for arg in base_args if arg != "--include-mcp"]
        return base_args

    async def _handle_agent_list_profiles(self, args: Dict, registry) -> Dict:
        from agents.subagent_profiles import load_profiles_and_teams

        profiles, teams = load_profiles_and_teams()
        return {"profiles": profiles, "teams": teams}

    async def _handle_agent_start(self, args: Dict, registry) -> Dict:
        from agents.manager import AgentManager
        from agents.subagent_profiles import (profile_to_manager_options,
                                              resolve_profile, resolve_team)

        python_exec = args.get("python_exec") or self._agent_python_default()
        explicit_profile = args.get("profile")
        explicit_team = args.get("team")

        if explicit_profile and explicit_team:
            return {"error": "Provide either profile or team, not both"}

        managers: List[AgentManager] = []
        mode = "team" if explicit_team else "profile"

        if explicit_team:
            selected_profiles = resolve_team(explicit_team)
        else:
            selected_profiles = [resolve_profile(explicit_profile or "maintainer")]

        for profile in selected_profiles:
            options = profile_to_manager_options(profile)
            base_args = options["base_args"]
            if args.get("paths"):
                base_args = ["--paths", args.get("paths")]
            if args.get("include_mcp") is True and "--include-mcp" not in base_args:
                base_args.append("--include-mcp")

            manager = AgentManager(
                python_exec=python_exec,
                base_args=self._sanitize_agent_args(python_exec, base_args),
                max_restarts=int(args.get("max_restarts", options["max_restarts"])),
                run_once=not bool(args.get("continuous", not options["run_once"])),
                dry_run=not bool(args.get("live", not options["dry_run"])),
                name_prefix=options["name_prefix"],
            )
            manager.start_agents(int(args.get("count", options["count"])))
            managers.append(manager)

        run_id = f"run_{uuid4().hex[:12]}"
        self._agent_runs[run_id] = {
            "mode": mode,
            "created_at": datetime.utcnow().isoformat(),
            "spec": {"profile": explicit_profile, "team": explicit_team},
            "managers": managers,
        }

        status: List[Dict[str, Any]] = []
        for manager in managers:
            status.extend(manager.status())

        return {
            "run_id": run_id,
            "mode": mode,
            "started_agents": len(status),
            "status": status,
        }

    async def _handle_agent_status(self, args: Dict, registry) -> Dict:
        run_id = args.get("run_id")
        runs = []

        selected = self._agent_runs.items()
        if run_id:
            if run_id not in self._agent_runs:
                return {"error": f"Unknown run_id: {run_id}", "runs": []}
            selected = [(run_id, self._agent_runs[run_id])]

        for rid, run in selected:
            combined = []
            for manager in run["managers"]:
                combined.extend(manager.status())
            runs.append({
                "run_id": rid,
                "mode": run["mode"],
                "created_at": run["created_at"],
                "spec": run["spec"],
                "agents": combined,
            })

        return {"runs": runs}

    async def _handle_agent_stop(self, args: Dict, registry) -> Dict:
        run_id = args.get("run_id")
        stop_all = bool(args.get("stop_all", False))

        if not self._agent_runs:
            return {"stopped": [], "remaining_runs": 0}

        if stop_all:
            target_ids = list(self._agent_runs.keys())
        elif run_id:
            if run_id not in self._agent_runs:
                return {"error": f"Unknown run_id: {run_id}", "stopped": [], "remaining_runs": len(self._agent_runs)}
            target_ids = [run_id]
        else:
            return {"error": "Provide run_id or set stop_all=true", "stopped": [], "remaining_runs": len(self._agent_runs)}

        stopped = []
        for rid in target_ids:
            run = self._agent_runs.pop(rid, None)
            if not run:
                continue
            for manager in run["managers"]:
                manager.stop_agents()
            stopped.append(rid)

        return {"stopped": stopped, "remaining_runs": len(self._agent_runs)}

    def _get_agent_hub(self, db_path: Optional[str] = None):
        from cmplx_hub.agent_hub import AgentManagementHub

        pipeline = self._get_memory_pipeline(db_path=db_path)
        if self._agent_hub is None:
            self._agent_hub = AgentManagementHub(memory_pipeline=pipeline)
        else:
            if self._agent_hub.memory_pipeline.db_path != pipeline.db_path:
                self._agent_hub = AgentManagementHub(memory_pipeline=pipeline)
        return self._agent_hub

    async def _handle_agent_hub_create_session(self, args: Dict, registry) -> Dict:
        hub = registry._get_agent_hub(db_path=args.get("db_path"))
        session = hub.create_session(
            name=args.get("name", ""),
            metadata=args.get("metadata", {}),
        )
        return {"session": session}

    async def _handle_agent_hub_list_sessions(self, args: Dict, registry) -> Dict:
        hub = registry._get_agent_hub(db_path=args.get("db_path"))
        return {"sessions": hub.list_sessions()}

    async def _handle_agent_hub_register_agent(self, args: Dict, registry) -> Dict:
        from cmplx_hub.agent_runtime import AgentSpec

        hub = registry._get_agent_hub(db_path=args.get("db_path"))
        spec = AgentSpec(
            role=args.get("role", "agent"),
            goal=args.get("goal", ""),
            backstory=args.get("backstory", ""),
            tools=args.get("tools", []),
            model=args.get("model", ""),
            max_iterations=int(args.get("max_iterations", 25)),
            temperature=float(args.get("temperature", 0.7)),
            delegation=bool(args.get("delegation", False)),
            metadata=args.get("metadata", {}),
        )
        result = hub.register_agent(
            session_id=args.get("session_id", ""),
            spec=spec,
            parent_agent_id=args.get("parent_agent_id"),
        )
        return {"agent": result}

    async def _handle_agent_hub_append_memory(self, args: Dict, registry) -> Dict:
        hub = registry._get_agent_hub(db_path=args.get("db_path"))
        result = await hub.append_memory(
            session_id=args.get("session_id", ""),
            content=args.get("content", ""),
            role=args.get("role", "user"),
            level=args.get("level", "ca"),
            metadata=args.get("metadata", {}),
            terms=args.get("terms"),
        )
        return {"memory": result}

    async def _handle_agent_hub_recall(self, args: Dict, registry) -> Dict:
        hub = registry._get_agent_hub(db_path=args.get("db_path"))
        result = await hub.recall(
            session_id=args.get("session_id", ""),
            query=args.get("query", ""),
            top_k=int(args.get("top_k", 5)),
            level=args.get("level"),
            snap_required=args.get("snap_required", []),
        )
        return {"recall": result}

    async def _handle_agent_hub_run_task(self, args: Dict, registry) -> Dict:
        hub = registry._get_agent_hub(db_path=args.get("db_path"))
        result = await hub.run_agent_task(
            session_id=args.get("session_id", ""),
            agent_id=args.get("agent_id", ""),
            task_description=args.get("task", ""),
            inputs=args.get("inputs", {}),
            remember=bool(args.get("remember", True)),
            level=args.get("level", "ca"),
        )
        return {"run": result}

    async def _handle_agent_hub_session_status(self, args: Dict, registry) -> Dict:
        hub = registry._get_agent_hub(db_path=args.get("db_path"))
        result = hub.session_status(args.get("session_id", ""))
        return {"status": result}

    # ===== PLANETARY DATABASE TOOLS =====
    
    def _register_planetary_tools(self):
        """Register Planetary Database tools."""
        
        self.register(ToolDefinition(
            name="planetary_admit",
            description="Admit content to the planetary database",
            category="planetary_db",
            handler=self._handle_planetary_admit,
            parameters={
                "content": {"type": "string"},
                "layer": {"type": "string", "enum": ["fast", "slow"], "default": "fast"},
                "tags": {"type": "array", "optional": True}
            },
            returns={
                "admission_id": "string",
                "crystal_id": "string",
                "planet": "string"
            }
        ))
        
        self.register(ToolDefinition(
            name="planetary_query",
            description="Query the planetary database",
            category="planetary_db",
            handler=self._handle_planetary_query,
            parameters={
                "query": {"type": "string"},
                "use_quorum": {"type": "boolean", "default": False},
                "limit": {"type": "number", "default": 10}
            },
            returns={
                "results": "array",
                "total": "number",
                "strategy": "string"
            }
        ))
        
        self.register(ToolDefinition(
            name="planetary_store_crystal",
            description="Store content as a named crystal",
            category="planetary_db",
            handler=self._handle_planetary_crystal,
            parameters={
                "content": {"type": "string"},
                "name": {"type": "string", "optional": True},
                "tags": {"type": "array", "optional": True}
            },
            returns={
                "crystal_id": "string",
                "name": "string",
                "resonance_signature": "array"
            }
        ))
        
        self.register(ToolDefinition(
            name="planetary_get_stats",
            description="Get planetary database statistics",
            category="planetary_db",
            handler=self._handle_planetary_stats,
            returns={
                "planets": "number",
                "crystals": "number",
                "text_index_tokens": "number"
            }
        ))
    
    def _get_planetary_db(self):
        """Get or initialize Planetary DB."""
        if self._planetary_db is None:
            from cmplx_toolkit.db.planetary_db import PlanetaryDatabase
            
            self._planetary_db = PlanetaryDatabase(self.data_root)
            self._planetary_db.initialize()
        return self._planetary_db
    
    async def _handle_planetary_admit(self, args: Dict, registry) -> Dict:
        """Admit content."""
        db = registry._get_planetary_db()
        return db.admit(
            content=args.get("content", ""),
            layer=args.get("layer", "fast")
        )
    
    async def _handle_planetary_query(self, args: Dict, registry) -> Dict:
        """Query database."""
        db = registry._get_planetary_db()
        results = db.query(
            query=args.get("query", ""),
            use_quorum=args.get("use_quorum", False)
        )
        # Ensure consistent return format
        if isinstance(results, dict):
            return results
        return {"results": results, "total": len(results), "strategy": "direct"}
    
    async def _handle_planetary_crystal(self, args: Dict, registry) -> Dict:
        """Store crystal."""
        db = registry._get_planetary_db()
        return db.store_crystal(
            content=args.get("content", ""),
            name=args.get("name"),
            tags=args.get("tags", [])
        )
    
    async def _handle_planetary_stats(self, args: Dict, registry) -> Dict:
        """Get stats."""
        db = registry._get_planetary_db()
        return db.get_stats()
    
    # ===== RECEIPT SYSTEM TOOLS =====
    
    def _register_receipt_tools(self):
        """Register Receipt system tools."""
        
        self.register(ToolDefinition(
            name="receipt_verify_chain",
            description="Verify the integrity of the receipt chain",
            category="receipts",
            handler=self._handle_receipt_verify,
            returns={"valid": "boolean", "entries": "number"}
        ))
        
        self.register(ToolDefinition(
            name="receipt_get_recent",
            description="Get recent receipts",
            category="receipts",
            handler=self._handle_receipt_get_recent,
            parameters={"limit": {"type": "number", "default": 10}},
            returns={"receipts": "array"}
        ))
    
    async def _handle_receipt_verify(self, args: Dict, registry) -> Dict:
        """Verify receipt chain(s) — scans all .jsonl receipt files."""
        import json as _json
        from pathlib import Path as _Path

        data_root = _Path(registry.data_root)
        # Collect all candidate receipt JSONL files
        candidates = list(data_root.rglob("*receipts*.jsonl"))
        # Also check the legacy flat path
        legacy = data_root / "receipts.jsonl"
        if legacy.exists() and legacy not in candidates:
            candidates.append(legacy)

        if not candidates:
            return {"valid": True, "entries": 0, "files_checked": 0}

        total_entries = 0
        all_valid = True
        file_results = []

        for fpath in candidates:
            try:
                with open(fpath, encoding="utf-8") as fh:
                    lines = [l.strip() for l in fh if l.strip()]
                count = len(lines)
                total_entries += count

                # Detect format and verify chain
                valid = True
                if count > 0:
                    first = _json.loads(lines[0])
                    if "receipt_hash" in first:
                        # ReceiptLedger format
                        from cmplx_toolkit.autonomy.receipts import \
                            ReceiptLedger
                        ledger = ReceiptLedger(str(fpath))
                        valid = ledger.verify_chain()
                    elif "hash" in first:
                        # SandboxLedger format — verify prev_hash chain
                        prev = "0" * 64
                        for line in lines:
                            entry = _json.loads(line)
                            if entry.get("prev_hash") != prev:
                                valid = False
                                break
                            prev = entry.get("hash", "")

                if not valid:
                    all_valid = False
                file_results.append({
                    "file": str(fpath.relative_to(data_root)),
                    "entries": count,
                    "valid": valid,
                })
            except Exception as exc:
                file_results.append({
                    "file": str(fpath.relative_to(data_root)),
                    "error": str(exc),
                    "valid": False,
                })
                all_valid = False

        return {
            "valid": all_valid,
            "entries": total_entries,
            "files_checked": len(candidates),
            "details": file_results,
        }
    
    async def _handle_receipt_get_recent(self, args: Dict, registry) -> Dict:
        """Get recent receipts from all receipt files."""
        import json as _json
        from pathlib import Path as _Path

        data_root = _Path(registry.data_root)
        candidates = list(data_root.rglob("*receipts*.jsonl"))
        legacy = data_root / "receipts.jsonl"
        if legacy.exists() and legacy not in candidates:
            candidates.append(legacy)

        if not candidates:
            return {"receipts": []}

        limit = args.get("limit", 10)
        all_receipts = []
        try:
            for fpath in candidates:
                with open(fpath, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            all_receipts.append(_json.loads(line))
            # Sort by timestamp (ts or timestamp field)
            all_receipts.sort(
                key=lambda r: r.get("ts", r.get("timestamp", 0)),
                reverse=True,
            )
            return {"receipts": all_receipts[:limit]}
        except Exception as e:
            return {"receipts": [], "error": str(e)}
    
    # ===== HEALTH MONITORING TOOLS =====
    
    def _register_health_tools(self):
        """Register Health monitoring tools."""
        
        self.register(ToolDefinition(
            name="health_check",
            description="Run comprehensive health check",
            category="health",
            handler=self._handle_health_check,
            returns={
                "healthy": "boolean",
                "checks": "object",
                "metrics": "object"
            }
        ))
        
        self.register(ToolDefinition(
            name="health_component",
            description="Check specific component health",
            category="health",
            handler=self._handle_health_component,
            parameters={
                "component": {"type": "string", "enum": ["think_tank", "circuit_breaker", "tmn", "database", "receipts"]}
            },
            returns={"healthy": "boolean", "status": "string"}
        ))
    
    async def _handle_health_check(self, args: Dict, registry) -> Dict:
        """Run health check."""
        from cmplx_toolkit.utils.health import HealthChecker
        
        checker = HealthChecker(
            think_tank=registry._think_tank,
            planetary_db=registry._planetary_db
        )
        
        status = checker.check_all()
        return status.to_dict()
    
    async def _handle_health_component(self, args: Dict, registry) -> Dict:
        """Check specific component."""
        from cmplx_toolkit.utils.health import HealthChecker
        
        checker = HealthChecker(
            think_tank=registry._think_tank,
            planetary_db=registry._planetary_db
        )
        
        component = args.get("component", "")
        check_methods = {
            "think_tank": checker._check_think_tank,
            "circuit_breaker": checker._check_circuit_breaker,
            "tmn": checker._check_tmn,
            "database": checker._check_database,
            "receipts": checker._check_receipts
        }
        
        if component in check_methods:
            return check_methods[component]()
        
        return {"error": f"Unknown component: {component}"}
    
    # ===== TMN CORE TOOLS =====
    
    def _register_tmn_tools(self):
        """Register TMN core tools."""
        
        self.register(ToolDefinition(
            name="tmn_learn",
            description="Train TMN on input-output pair",
            category="tmn",
            handler=self._handle_tmn_learn,
            parameters={
                "input_code": {"type": "string"},
                "output_code": {"type": "string"}
            },
            returns={"epoch": "number", "mutual_information": "number"}
        ))
        
        self.register(ToolDefinition(
            name="tmn_state",
            description="Get current TMN state",
            category="tmn",
            handler=self._handle_tmn_state,
            returns={"epoch": "number", "dims": "number", "mutual_information": "number"}
        ))
        
        self.register(ToolDefinition(
            name="tmn_save",
            description="Save TMN state",
            category="tmn",
            handler=self._handle_tmn_save,
            returns={"saved": "boolean", "receipt_id": "string"}
        ))
        
        self.register(ToolDefinition(
            name="tmn_load",
            description="Load TMN state",
            category="tmn",
            handler=self._handle_tmn_load,
            returns={"loaded": "boolean"}
        ))
    
    def _get_tmn(self):
        """Get or initialize TMN."""
        if self._tmn is None:
            from cmplx_toolkit.autonomy.tmn_core import TriadicManifoldNetwork
            self._tmn = TriadicManifoldNetwork()
        return self._tmn
    
    async def _handle_tmn_state(self, args: Dict, registry) -> Dict:
        """Get TMN state."""
        tmn = registry._get_tmn()
        return tmn.state_dict()
    
    async def _handle_tmn_save(self, args: Dict, registry) -> Dict:
        """Save TMN state."""
        from cmplx_toolkit.autonomy.receipts import ReceiptLedger
        from cmplx_toolkit.autonomy.think_tank import TMNStateManager
        
        tmn = registry._get_tmn()
        
        # Create minimal state store
        class SimpleStateStore:
            def __init__(self, path):
                self.path = path
            def save(self, **kwargs):
                import json
                with open(self.path / "tmn_state.json", "w") as f:
                    json.dump(kwargs, f)
                return kwargs.get("state_id")
            def list(self, limit=10):
                return []
        
        store = SimpleStateStore(registry.data_root)
        ledger = ReceiptLedger(str(registry.data_root / "receipts.jsonl"))
        
        manager = TMNStateManager(store, ledger)
        receipt_id = manager.save_state(tmn, context="mcp_tool")
        
        return {"saved": True, "receipt_id": receipt_id}
    
    async def _handle_tmn_load(self, args: Dict, registry) -> Dict:
        """Load TMN state."""
        from cmplx_toolkit.autonomy.receipts import ReceiptLedger
        from cmplx_toolkit.autonomy.think_tank import TMNStateManager
        
        tmn = registry._get_tmn()
        
        class SimpleStateStore:
            def __init__(self, path):
                self.path = path
            def load(self, state_id):
                return None
            def list(self, limit=10):
                return []
        
        store = SimpleStateStore(registry.data_root)
        ledger = ReceiptLedger(str(registry.data_root / "receipts.jsonl"))
        
        manager = TMNStateManager(store, ledger)
        loaded = manager.load_state(tmn)
        
        return {"loaded": loaded}
    
    # ===== GEOMETRIC TOOLS (from existing MCP OS) =====
    
    def _register_geometric_tools(self):
        """Register geometric tools (E8, Leech, Niemeier, Weyl)."""
        
        self.register(ToolDefinition(
            name="l2_project_e8",
            description="Project vector to E8 lattice",
            category="geometric",
            handler=self._handle_l2_project_e8,
            parameters={"vector": {"type": "array", "items": "number", "minItems": 8, "maxItems": 8}},
            returns={"handle": "string", "lattice": "string", "norm": "number"}
        ))
        
        self.register(ToolDefinition(
            name="l2_nearest_leech",
            description="Find nearest Leech lattice point",
            category="geometric",
            handler=self._handle_l2_nearest_leech,
            parameters={"vector": {"type": "array", "items": "number", "minItems": 24, "maxItems": 24}},
            returns={"handle": "string", "distance": "number"}
        ))
        
        self.register(ToolDefinition(
            name="l2_digital_root",
            description="Calculate digital root",
            category="geometric",
            handler=self._handle_l2_digital_root,
            parameters={"number": {"type": "number"}},
            returns={"digital_root": "number", "meaning": "string"}
        ))
    
    async def _handle_l2_project_e8(self, args: Dict, registry) -> Dict:
        """Handle E8 projection."""
        from ..server.tools import Layer2Tools
        
        l2 = Layer2Tools()
        return await l2._l2_e8_project(args, registry.data_root)
    
    async def _handle_l2_nearest_leech(self, args: Dict, registry) -> Dict:
        """Handle Leech projection."""
        from ..server.tools import Layer2Tools
        
        l2 = Layer2Tools()
        # Map to existing method or implement directly
        vector = args.get("vector", [0] * 24)
        return {
            "handle": f"leech_{hash(str(vector)) % 10000}",
            "distance": 0.5,
            "note": "Leech projection - simplified implementation"
        }
    
    async def _handle_l2_digital_root(self, args: Dict, registry) -> Dict:
        """Handle digital root."""
        from ..server.tools import Layer4Tools
        
        l4 = Layer4Tools()
        return await l4._l4_digital_root(args, registry.data_root)
    
    # ===== GOVERNANCE TOOLS =====
    
    def _register_governance_tools(self):
        """Register governance and validation tools."""
        
        self.register(ToolDefinition(
            name="governance_validate",
            description="Validate artifact against governance rules",
            category="governance",
            handler=self._handle_governance_validate,
            parameters={
                "artifact": {"type": "object"},
                "tier": {"type": "number", "default": 1}
            },
            returns={"valid": "boolean", "violations": "array"}
        ))
        
        self.register(ToolDefinition(
            name="governance_meaning",
            description="Get meaning of digital root",
            category="governance",
            handler=self._handle_governance_meaning,
            parameters={"digital_root": {"type": "number", "min": 0, "max": 9}},
            returns={"meaning": "string", "type": "string"}
        ))
    
    async def _handle_governance_validate(self, args: Dict, registry) -> Dict:
        """Validate artifact against governance rules."""
        artifact = args.get("artifact", {})
        tier = args.get("tier", 1)
        
        # Basic validation - in real implementation, would use PolicyHierarchy
        violations = []
        
        # Check for required fields
        if not artifact.get("type"):
            violations.append("Missing artifact type")
        
        # Tier-specific checks
        if tier >= 1 and not artifact.get("description"):
            violations.append("Tier 1+ requires description")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "tier_checked": tier
        }
    
    async def _handle_governance_meaning(self, args: Dict, registry) -> Dict:
        """Get meaning of digital root."""
        dr = args.get("digital_root", 0)
        
        meanings = {
            0: {"meaning": "Ground state, potential", "type": "void"},
            1: {"meaning": "Unity, singularity", "type": "unity"},
            2: {"meaning": "Duality, balance", "type": "balance"},
            3: {"meaning": "Creativity, expression", "type": "creative"},
            4: {"meaning": "Structure, foundation", "type": "structure"},
            5: {"meaning": "Change, freedom", "type": "dynamic"},
            6: {"meaning": "Harmony, service", "type": "harmony"},
            7: {"meaning": "Wisdom, analysis", "type": "wisdom"},
            8: {"meaning": "Power, abundance", "type": "power"},
            9: {"meaning": "Completion, mastery", "type": "completion"}
        }
        
        return meanings.get(dr, {"meaning": "Unknown", "type": "unknown"})
    
    async def _handle_tmn_learn(self, args: Dict, registry) -> Dict:
        """Train TMN on input-output pair."""
        tmn = registry._get_tmn()
        
        input_code = args.get("input_code", "")
        output_code = args.get("output_code", "")
        
        # Train
        tmn.learn(input_code, output_code)
        
        state = tmn.state_dict()
        return {
            "epoch": state.get("epoch", 0),
            "mutual_information": state.get("mutual_information", 0)
        }
    
    # ===== CONTROLLER HIERARCHY TOOLS =====

    def _get_hierarchy(self):
        """Get or initialize controller hierarchy."""
        if self._controller_hierarchy is None:
            from cmplx_toolkit.controllers.hierarchy import ControllerHierarchy
            self._controller_hierarchy = ControllerHierarchy()
        return self._controller_hierarchy

    def _get_snap_labeler(self):
        """Get or initialize SNAP labeler."""
        if self._snap_labeler is None:
            from cmplx_toolkit.controllers.snap_labeler import SNAPLabeler
            self._snap_labeler = SNAPLabeler()
        return self._snap_labeler

    def _get_mmdb_controller(self, db_path: Optional[str] = None):
        """Get or initialize MMDB controller for memory operations."""
        from cmplx_toolkit.controllers.mmdb import MMDBController

        target_db_path = db_path or str((self.data_root / "mmdb" / "mmdb.sqlite3"))
        Path(target_db_path).parent.mkdir(parents=True, exist_ok=True)

        if self._mmdb_controller is None:
            self._mmdb_controller = MMDBController(db_path=target_db_path)
        else:
            current_path = self._mmdb_controller.db.db_path
            if current_path != target_db_path:
                self._mmdb_controller.db.close()
                self._mmdb_controller = MMDBController(db_path=target_db_path)

        return self._mmdb_controller

    def _register_mmdb_tools(self):
        """Register MMDB and crystal-ball memory tools."""

        self.register(ToolDefinition(
            name="mmdb_execute",
            description="Execute MMDB memory operations for go-to-memory and recall",
            category="mmdb",
            handler=self._handle_mmdb_execute,
            parameters={
                "operation": {"type": "string", "description": "MMDB operation name"},
                "db_path": {"type": "string", "optional": True},
                "inputs": {
                    "type": "object",
                    "optional": True,
                    "description": "Operation-specific fields merged into MMDB inputs",
                },
            },
            returns={"result": "object", "db_path": "string"},
        ))

        self.register(ToolDefinition(
            name="mmdb_status",
            description="Get MMDB controller status and active database details",
            category="mmdb",
            handler=self._handle_mmdb_status,
            parameters={"db_path": {"type": "string", "optional": True}},
            returns={"status": "object"},
        ))

        self.register(ToolDefinition(
            name="crystal_ball_sqlite_files",
            description="Expose the exact SQLite files needed now for MMDB recall tasks",
            category="mmdb",
            handler=self._handle_crystal_ball_sqlite_files,
            parameters={
                "db_path": {"type": "string", "optional": True},
                "include_sidecars": {"type": "boolean", "default": True},
                "include_receipts": {"type": "boolean", "default": True},
                "receipts_path": {"type": "string", "optional": True},
                "existing_only": {"type": "boolean", "default": False},
            },
            returns={"db_path": "string", "files": "array", "existing_files": "array"},
        ))

    async def _handle_mmdb_execute(self, args: Dict, registry) -> Dict:
        db_path = args.get("db_path")
        controller = registry._get_mmdb_controller(db_path=db_path)
        payload = {"operation": args.get("operation", "stats")}
        payload.update(args.get("inputs", {}))
        result = await controller.execute(payload)
        return {"result": result, "db_path": controller.db.db_path}

    async def _handle_mmdb_status(self, args: Dict, registry) -> Dict:
        controller = registry._get_mmdb_controller(db_path=args.get("db_path"))
        return {"status": controller.get_status()}

    async def _handle_crystal_ball_sqlite_files(self, args: Dict, registry) -> Dict:
        from cmplx_toolkit.controllers.crystal_ball import resolve_sqlite_files

        controller = registry._get_mmdb_controller(db_path=args.get("db_path"))
        receipts_path = args.get("receipts_path")
        if not receipts_path:
            receipts_path = str((registry.data_root / "receipts.jsonl"))

        return resolve_sqlite_files(
            db_path=controller.db.db_path,
            include_sidecars=bool(args.get("include_sidecars", True)),
            include_receipts=bool(args.get("include_receipts", True)),
            receipts_path=receipts_path,
            existing_only=bool(args.get("existing_only", False)),
        )

    def _get_memory_pipeline(self, db_path: Optional[str] = None):
        """Get or initialize integrated MMDB-MDHG-SpeedLight-SNAP pipeline."""
        from cmplx_toolkit.controllers.memory_pipeline import \
            MMDBMDHGSpeedLightPipeline

        target_db_path = db_path or str((self.data_root / "mmdb" / "mmdb.sqlite3"))
        target_root = str(Path(target_db_path).parent)

        if self._memory_pipeline is None:
            self._memory_pipeline = MMDBMDHGSpeedLightPipeline(
                db_path=target_db_path,
                data_root=target_root,
            )
        else:
            if self._memory_pipeline.db_path != target_db_path:
                self._memory_pipeline = MMDBMDHGSpeedLightPipeline(
                    db_path=target_db_path,
                    data_root=target_root,
                )

        return self._memory_pipeline

    def _register_memory_pipeline_tools(self):
        """Register integrated memory pipeline tools."""

        self.register(ToolDefinition(
            name="memory_pipeline_ingest",
            description="Ingest content through MMDB, SpeedLight, SNAP, and MDHG at chosen granularity",
            category="mmdb",
            handler=self._handle_memory_pipeline_ingest,
            parameters={
                "db_path": {"type": "string", "optional": True},
                "level": {"type": "string", "default": "planetary", "description": "ca|city|planetary"},
                "corpus_label": {"type": "string", "optional": True},
                "source_path": {"type": "string", "optional": True},
                "content": {"type": "string", "description": "Text payload to ingest"},
                "metadata": {"type": "object", "optional": True},
                "terms": {"type": "array", "optional": True},
            },
            returns={"ingested": "boolean", "chunk_id": "string", "snap": "object", "mdhg": "object"},
        ))

        self.register(ToolDefinition(
            name="memory_pipeline_query",
            description="Query integrated memory across selected MDHG granularity and MMDB",
            category="mmdb",
            handler=self._handle_memory_pipeline_query,
            parameters={
                "db_path": {"type": "string", "optional": True},
                "term": {"type": "string", "description": "Search term"},
                "top_k": {"type": "number", "default": 5},
                "level": {"type": "string", "optional": True, "description": "ca|city|planetary or omit for all"},
                "snap_required": {"type": "array", "optional": True},
            },
            returns={"results": "array", "count": "number", "mdhg_by_level": "object"},
        ))

        self.register(ToolDefinition(
            name="memory_pipeline_stats",
            description="Get integrated MMDB-MDHG-SpeedLight-SNAP pipeline stats",
            category="mmdb",
            handler=self._handle_memory_pipeline_stats,
            parameters={"db_path": {"type": "string", "optional": True}},
            returns={"mmdb": "object", "mdhg": "object", "speedlight": "object", "snap": "object"},
        ))

        self.register(ToolDefinition(
            name="memory_pipeline_snap_query",
            description="Query cached SNAP labels from pipeline by label",
            category="mmdb",
            handler=self._handle_memory_pipeline_snap_query,
            parameters={
                "db_path": {"type": "string", "optional": True},
                "label": {"type": "string", "description": "SNAP label to search"},
            },
            returns={"matches": "array", "count": "number"},
        ))

        self.register(ToolDefinition(
            name="memory_pipeline_promotion_cycle",
            description="Run one cross-level MDHG promotion cycle (ca→city→planetary)",
            category="mmdb",
            handler=self._handle_memory_pipeline_promotion_cycle,
            parameters={
                "db_path": {"type": "string", "optional": True},
                "ca_to_city_confidence": {"type": "number", "optional": True},
                "city_to_planetary_confidence": {"type": "number", "optional": True},
            },
            returns={"cycle_completed": "boolean", "promotions": "object", "status": "object"},
        ))

        self.register(ToolDefinition(
            name="memory_pipeline_cycle_status",
            description="Get latest promotion-cycle status for memory pipeline",
            category="mmdb",
            handler=self._handle_memory_pipeline_cycle_status,
            parameters={"db_path": {"type": "string", "optional": True}},
            returns={"runs": "number", "last_run": "string", "last_promotions": "object"},
        ))

    async def _handle_memory_pipeline_ingest(self, args: Dict, registry) -> Dict:
        pipeline = registry._get_memory_pipeline(db_path=args.get("db_path"))
        payload = {
            "level": args.get("level", "planetary"),
            "corpus_label": args.get("corpus_label", "default"),
            "source_path": args.get("source_path", "memory://mcp_ingest"),
            "content": args.get("content", ""),
            "metadata": args.get("metadata", {}),
            "terms": args.get("terms"),
        }
        return await pipeline.ingest(payload)

    async def _handle_memory_pipeline_query(self, args: Dict, registry) -> Dict:
        pipeline = registry._get_memory_pipeline(db_path=args.get("db_path"))
        payload = {
            "term": args.get("term", ""),
            "top_k": int(args.get("top_k", 5)),
            "level": args.get("level"),
            "snap_required": args.get("snap_required", []),
        }
        return await pipeline.query(payload)

    async def _handle_memory_pipeline_stats(self, args: Dict, registry) -> Dict:
        pipeline = registry._get_memory_pipeline(db_path=args.get("db_path"))
        return await pipeline.stats()

    async def _handle_memory_pipeline_snap_query(self, args: Dict, registry) -> Dict:
        pipeline = registry._get_memory_pipeline(db_path=args.get("db_path"))
        matches = pipeline.list_snap_by_label(args.get("label", ""))
        return {"matches": matches, "count": len(matches)}

    async def _handle_memory_pipeline_promotion_cycle(self, args: Dict, registry) -> Dict:
        pipeline = registry._get_memory_pipeline(db_path=args.get("db_path"))
        payload = {
            "ca_to_city_confidence": args.get("ca_to_city_confidence", 0.45),
            "city_to_planetary_confidence": args.get("city_to_planetary_confidence", 0.6),
        }
        return await pipeline.run_promotion_cycle(payload)

    async def _handle_memory_pipeline_cycle_status(self, args: Dict, registry) -> Dict:
        pipeline = registry._get_memory_pipeline(db_path=args.get("db_path"))
        return pipeline.cycle_status()

    def _register_controller_tools(self):
        """Register controller hierarchy management tools."""

        self.register(ToolDefinition(
            name="controller_register",
            description="Register a new controller in the hierarchy",
            category="controller",
            handler=self._handle_controller_register,
            parameters={
                "name": {"type": "string", "description": "Controller name"},
                "tier": {"type": "string", "description": "Tier: ATOM|MICRO|MESO|MACRO|META|MASTER"},
                "tags": {"type": "array", "optional": True},
                "parent": {"type": "string", "optional": True, "description": "Parent controller name"},
            },
            returns={"registered": "boolean", "controller_id": "string", "info": "object"},
        ))

        self.register(ToolDefinition(
            name="controller_wire",
            description="Wire a child controller under a parent (enforces tier ordering)",
            category="controller",
            handler=self._handle_controller_wire,
            parameters={
                "parent": {"type": "string"},
                "child": {"type": "string"},
            },
            returns={"wired": "boolean"},
        ))

        self.register(ToolDefinition(
            name="controller_execute",
            description="Execute a named controller with given inputs",
            category="controller",
            handler=self._handle_controller_execute,
            parameters={
                "name": {"type": "string"},
                "inputs": {"type": "object", "optional": True},
            },
            returns={"result": "object"},
        ))

        self.register(ToolDefinition(
            name="controller_info",
            description="Get info about a specific controller",
            category="controller",
            handler=self._handle_controller_info,
            parameters={"name": {"type": "string"}},
            returns={"info": "object"},
        ))

        self.register(ToolDefinition(
            name="controller_tree",
            description="Get ASCII tree of the entire controller hierarchy",
            category="controller",
            handler=self._handle_controller_tree,
            returns={"tree": "string"},
        ))

        self.register(ToolDefinition(
            name="controller_summary",
            description="Get structured summary of the controller hierarchy",
            category="controller",
            handler=self._handle_controller_summary,
            returns={"summary": "object"},
        ))

        self.register(ToolDefinition(
            name="controller_find_by_tier",
            description="Find all controllers at a given tier",
            category="controller",
            handler=self._handle_controller_find_tier,
            parameters={"tier": {"type": "string"}},
            returns={"controllers": "array"},
        ))

        self.register(ToolDefinition(
            name="controller_find_by_tag",
            description="Find all controllers with a given tag",
            category="controller",
            handler=self._handle_controller_find_tag,
            parameters={"tag": {"type": "string"}},
            returns={"controllers": "array"},
        ))

        self.register(ToolDefinition(
            name="controller_find_by_snap",
            description="Find all controllers with a given SNAP label",
            category="controller",
            handler=self._handle_controller_find_snap,
            parameters={"label": {"type": "string"}},
            returns={"controllers": "array"},
        ))

        self.register(ToolDefinition(
            name="controller_unregister",
            description="Remove a controller from the hierarchy",
            category="controller",
            handler=self._handle_controller_unregister,
            parameters={"name": {"type": "string"}},
            returns={"unregistered": "boolean"},
        ))

    # -- Controller handlers --

    async def _handle_controller_register(self, args: Dict, registry) -> Dict:
        from cmplx_toolkit.controllers.base_controller import ControllerTier

        hierarchy = registry._get_hierarchy()
        tier_str = args.get("tier", "MESO").upper()
        tier = ControllerTier[tier_str]
        tags = args.get("tags", [])
        parent = args.get("parent")

        # Create a simple concrete controller for dynamic registration
        class DynamicController:
            pass

        from cmplx_toolkit.controllers.base_controller import BaseController

        class _Registered(BaseController):
            async def execute(self, inputs):
                return {"status": "executed", "controller": self.name, "inputs": inputs}
            def get_status(self):
                return {"name": self.name, "status": self._status}

        ctrl = _Registered(name=args["name"], tier=tier, tags=tags)
        hierarchy.register(ctrl, parent=parent)
        return {"registered": True, "controller_id": ctrl.controller_id, "info": ctrl.info()}

    async def _handle_controller_wire(self, args: Dict, registry) -> Dict:
        hierarchy = registry._get_hierarchy()
        hierarchy.wire(args["parent"], args["child"])
        return {"wired": True}

    async def _handle_controller_execute(self, args: Dict, registry) -> Dict:
        hierarchy = registry._get_hierarchy()
        result = await hierarchy.execute(args["name"], args.get("inputs", {}))
        return {"result": result}

    async def _handle_controller_info(self, args: Dict, registry) -> Dict:
        hierarchy = registry._get_hierarchy()
        ctrl = hierarchy.get(args["name"])
        if ctrl is None:
            return {"error": f"Controller {args['name']!r} not found"}
        return {"info": ctrl.info()}

    async def _handle_controller_tree(self, args: Dict, registry) -> Dict:
        hierarchy = registry._get_hierarchy()
        return {"tree": hierarchy.tree()}

    async def _handle_controller_summary(self, args: Dict, registry) -> Dict:
        hierarchy = registry._get_hierarchy()
        return {"summary": hierarchy.summary()}

    async def _handle_controller_find_tier(self, args: Dict, registry) -> Dict:
        from cmplx_toolkit.controllers.base_controller import ControllerTier
        hierarchy = registry._get_hierarchy()
        tier = ControllerTier[args["tier"].upper()]
        ctrls = hierarchy.find_by_tier(tier)
        return {"controllers": [c.info() for c in ctrls]}

    async def _handle_controller_find_tag(self, args: Dict, registry) -> Dict:
        hierarchy = registry._get_hierarchy()
        ctrls = hierarchy.find_by_tag(args["tag"])
        return {"controllers": [c.info() for c in ctrls]}

    async def _handle_controller_find_snap(self, args: Dict, registry) -> Dict:
        hierarchy = registry._get_hierarchy()
        ctrls = hierarchy.find_by_snap_label(args["label"])
        return {"controllers": [c.info() for c in ctrls]}

    async def _handle_controller_unregister(self, args: Dict, registry) -> Dict:
        hierarchy = registry._get_hierarchy()
        hierarchy.unregister(args["name"])
        return {"unregistered": True}

    # ===== SPEEDLIGHT SIDECAR TOOLS =====

    def _register_speedlight_tools(self):
        """Register SpeedLight truth-sidecar tools."""

        self.register(ToolDefinition(
            name="speedlight_process",
            description="Run an item through the SpeedLight pipeline (tokenize → transform → emergence → audit)",
            category="speedlight",
            handler=self._handle_speedlight_process,
            parameters={
                "item": {"type": "string", "description": "Text or JSON to process"},
                "controller_name": {"type": "string", "optional": True, "description": "Controller context"},
            },
            returns={"envelope": "object"},
        ))

        self.register(ToolDefinition(
            name="speedlight_tokenize",
            description="Tokenize an item into morphon-tokens",
            category="speedlight",
            handler=self._handle_speedlight_tokenize,
            parameters={"item": {"type": "string"}},
            returns={"tokens": "array", "count": "number"},
        ))

        self.register(ToolDefinition(
            name="speedlight_transform",
            description="Project tokens into geometric space",
            category="speedlight",
            handler=self._handle_speedlight_transform,
            parameters={"item": {"type": "string"}},
            returns={"geo_state": "object"},
        ))

        self.register(ToolDefinition(
            name="speedlight_emergence",
            description="Detect emergent patterns in an item",
            category="speedlight",
            handler=self._handle_speedlight_emergence,
            parameters={"item": {"type": "string"}},
            returns={"emergence": "object"},
        ))

        self.register(ToolDefinition(
            name="speedlight_audit_chain",
            description="Get the audit chain for a controller's SpeedLight sidecar",
            category="speedlight",
            handler=self._handle_speedlight_audit,
            parameters={"controller_name": {"type": "string", "optional": True}},
            returns={"chain": "array", "count": "number"},
        ))

    # -- SpeedLight handlers --

    async def _handle_speedlight_process(self, args: Dict, registry) -> Dict:
        from cmplx_toolkit.controllers.speedlight import SpeedLight
        ctrl_name = args.get("controller_name", "mcp_registry")
        sl = SpeedLight(controller_name=ctrl_name)
        envelope = await sl.process(args.get("item", ""))
        return {"envelope": envelope}

    async def _handle_speedlight_tokenize(self, args: Dict, registry) -> Dict:
        from cmplx_toolkit.controllers.speedlight import GeoTokenizer
        tokenizer = GeoTokenizer()
        tokens = tokenizer.tokenize(args.get("item", ""))
        return {"tokens": tokens, "count": len(tokens)}

    async def _handle_speedlight_transform(self, args: Dict, registry) -> Dict:
        from cmplx_toolkit.controllers.speedlight import (GeoTokenizer,
                                                          GeoTransformer)
        tokenizer = GeoTokenizer()
        transformer = GeoTransformer()
        tokens = tokenizer.tokenize(args.get("item", ""))
        geo_state = transformer.transform(tokens)
        return {"geo_state": geo_state}

    async def _handle_speedlight_emergence(self, args: Dict, registry) -> Dict:
        from cmplx_toolkit.controllers.speedlight import (EmergenceDetector,
                                                          GeoTokenizer,
                                                          GeoTransformer)
        tokenizer = GeoTokenizer()
        transformer = GeoTransformer()
        detector = EmergenceDetector()
        tokens = tokenizer.tokenize(args.get("item", ""))
        geo_state = transformer.transform(tokens)
        emergence = detector.detect(geo_state, tokens)
        return {"emergence": emergence}

    async def _handle_speedlight_audit(self, args: Dict, registry) -> Dict:
        # If a controller is registered, get its SpeedLight chain
        hierarchy = registry._get_hierarchy()
        ctrl_name = args.get("controller_name", "")
        ctrl = hierarchy.get(ctrl_name) if ctrl_name else None
        if ctrl and ctrl._speedlight:
            chain = ctrl._speedlight.get_audit_chain()
            return {"chain": chain, "count": len(chain)}
        return {"chain": [], "count": 0}

    # ===== SNAP LABELER TOOLS =====

    def _register_snap_tools(self):
        """Register SNAP labeling tools."""

        self.register(ToolDefinition(
            name="snap_label",
            description="Generate SNAP labels for an item (text, code, data)",
            category="snap",
            handler=self._handle_snap_label,
            parameters={
                "item": {"type": "string", "description": "Item to label"},
                "key": {"type": "string", "optional": True, "description": "Unique key"},
                "context": {"type": "object", "optional": True},
            },
            returns={"label": "object"},
        ))

        self.register(ToolDefinition(
            name="snap_label_batch",
            description="Label multiple items at once",
            category="snap",
            handler=self._handle_snap_label_batch,
            parameters={
                "items": {"type": "array", "description": "List of strings to label"},
            },
            returns={"labels": "array"},
        ))

        self.register(ToolDefinition(
            name="snap_query",
            description="Query cached SNAP labels by label name",
            category="snap",
            handler=self._handle_snap_query,
            parameters={"label": {"type": "string"}},
            returns={"results": "array"},
        ))

        self.register(ToolDefinition(
            name="snap_add_rule",
            description="Add a custom SNAP labeling rule",
            category="snap",
            handler=self._handle_snap_add_rule,
            parameters={
                "name": {"type": "string"},
                "dimension": {"type": "string", "description": "structural|semantic|quality|risk|domain"},
                "labels": {"type": "array"},
                "pattern": {"type": "string", "description": "Regex pattern to match against text"},
            },
            returns={"added": "boolean", "rule_count": "number"},
        ))

        self.register(ToolDefinition(
            name="snap_stats",
            description="Get SNAP labeler statistics",
            category="snap",
            handler=self._handle_snap_stats,
            returns={"rule_count": "number", "cache_size": "number"},
        ))

    # -- SNAP handlers --

    async def _handle_snap_label(self, args: Dict, registry) -> Dict:
        labeler = registry._get_snap_labeler()
        item = args.get("item", "")
        key = args.get("key", "")
        context = args.get("context", {})
        label = labeler.label(item, key=key, context=context)
        return {"label": label.to_dict()}

    async def _handle_snap_label_batch(self, args: Dict, registry) -> Dict:
        labeler = registry._get_snap_labeler()
        items = args.get("items", [])
        labels = labeler.label_batch(items)
        return {"labels": [sl.to_dict() for sl in labels]}

    async def _handle_snap_query(self, args: Dict, registry) -> Dict:
        labeler = registry._get_snap_labeler()
        results = labeler.query_by_label(args.get("label", ""))
        return {"results": [sl.to_dict() for sl in results]}

    async def _handle_snap_add_rule(self, args: Dict, registry) -> Dict:
        import re as _re

        from cmplx_toolkit.controllers.snap_labeler import LabelRule
        labeler = registry._get_snap_labeler()
        pattern = _re.compile(args.get("pattern", ""), _re.IGNORECASE)

        def matcher(item, ctx, _p=pattern):
            text = ctx.get("text", "") or (item if isinstance(item, str) else "")
            return bool(_p.search(str(text)))

        rule = LabelRule(
            name=args["name"],
            dimension=args["dimension"],
            labels=args.get("labels", []),
            matcher=matcher,
        )
        labeler.add_rule(rule)
        return {"added": True, "rule_count": labeler.rule_count}

    async def _handle_snap_stats(self, args: Dict, registry) -> Dict:
        labeler = registry._get_snap_labeler()
        return {
            "rule_count": labeler.rule_count,
            "cache_size": len(labeler._label_cache),
        }

    # ===== WORKFLOW ORCHESTRATION TOOLS =====

    def _register_workflow_tools(self):
        """Register workflow orchestration tools (agent/task/crew/flow)."""

        self.register(ToolDefinition(
            name="workflow_create_agent",
            description="Create a CMPLXAgent with role/goal/backstory",
            category="workflow",
            handler=self._handle_workflow_create_agent,
            parameters={
                "role": {"type": "string"},
                "goal": {"type": "string"},
                "backstory": {"type": "string", "optional": True},
                "snap_role_type": {"type": "string", "optional": True,
                                   "description": "architect|researcher|analyst|critic|scribe|guardian|orchestrator"},
                "tools": {"type": "array", "optional": True},
            },
            returns={"agent_id": "string", "info": "object"},
        ))

        self.register(ToolDefinition(
            name="workflow_create_task",
            description="Create a CMPLXTask with description and expected output",
            category="workflow",
            handler=self._handle_workflow_create_task,
            parameters={
                "description": {"type": "string"},
                "expected_output": {"type": "string"},
                "agent_id": {"type": "string", "optional": True},
            },
            returns={"task_id": "string", "info": "object"},
        ))

        self.register(ToolDefinition(
            name="workflow_create_crew",
            description="Create a CMPLXCrew from agent/task IDs and run it",
            category="workflow",
            handler=self._handle_workflow_create_crew,
            parameters={
                "agent_ids": {"type": "array"},
                "task_ids": {"type": "array"},
                "process": {"type": "string", "default": "sequential",
                            "description": "sequential|hierarchical"},
                "inputs": {"type": "object", "optional": True},
            },
            returns={"result": "object"},
        ))

        self.register(ToolDefinition(
            name="workflow_list_agents",
            description="List all registered workflow agents",
            category="workflow",
            handler=self._handle_workflow_list_agents,
            returns={"agents": "array"},
        ))

        self.register(ToolDefinition(
            name="workflow_session_memory",
            description="Get or set session memory for the current workflow",
            category="workflow",
            handler=self._handle_workflow_session_memory,
            parameters={
                "action": {"type": "string", "description": "get|add|clear"},
                "content": {"type": "string", "optional": True},
                "role": {"type": "string", "optional": True},
            },
            returns={"memory": "object"},
        ))

    # -- Workflow handlers --

    async def _handle_workflow_create_agent(self, args: Dict, registry) -> Dict:
        try:
            from cmplx_toolkit.workflow.agent import CMPLXAgent
        except ImportError:
            return {"error": "workflow package not available"}

        agent = CMPLXAgent(
            role=args["role"],
            goal=args["goal"],
            backstory=args.get("backstory", ""),
            snap_role_type=args.get("snap_role_type"),
            tools=args.get("tools", []),
        )
        agent_id = getattr(agent, "agent_id", str(id(agent)))
        registry._agent_runs[agent_id] = {"agent": agent, "type": "workflow"}
        return {"agent_id": agent_id, "info": {"role": agent.role, "goal": agent.goal}}

    async def _handle_workflow_create_task(self, args: Dict, registry) -> Dict:
        try:
            from cmplx_toolkit.workflow.task import CMPLXTask
        except ImportError:
            return {"error": "workflow package not available"}

        agent = None
        agent_id = args.get("agent_id")
        if agent_id and agent_id in registry._agent_runs:
            agent = registry._agent_runs[agent_id].get("agent")

        task = CMPLXTask(
            description=args["description"],
            expected_output=args["expected_output"],
            agent=agent,
        )
        task_id = getattr(task, "task_id", str(id(task)))
        registry._agent_runs[task_id] = {"task": task, "type": "task"}
        return {"task_id": task_id, "info": {"description": task.description}}

    async def _handle_workflow_create_crew(self, args: Dict, registry) -> Dict:
        try:
            from cmplx_toolkit.workflow.crew import CMPLXCrew, Process
        except ImportError:
            return {"error": "workflow package not available"}

        agents = []
        for aid in args.get("agent_ids", []):
            entry = registry._agent_runs.get(aid, {})
            if "agent" in entry:
                agents.append(entry["agent"])

        tasks = []
        for tid in args.get("task_ids", []):
            entry = registry._agent_runs.get(tid, {})
            if "task" in entry:
                tasks.append(entry["task"])

        proc_str = args.get("process", "sequential").upper()
        process = Process[proc_str] if proc_str in Process.__members__ else Process.SEQUENTIAL

        crew = CMPLXCrew(agents=agents, tasks=tasks, process=process)
        result = crew.kickoff(inputs=args.get("inputs", {}))
        return {"result": result if isinstance(result, dict) else {"output": str(result)}}

    async def _handle_workflow_list_agents(self, args: Dict, registry) -> Dict:
        agents = []
        for aid, entry in registry._agent_runs.items():
            if entry.get("type") == "workflow" and "agent" in entry:
                a = entry["agent"]
                agents.append({"agent_id": aid, "role": a.role, "goal": a.goal})
        return {"agents": agents}

    async def _handle_workflow_session_memory(self, args: Dict, registry) -> Dict:
        try:
            from cmplx_toolkit.workflow.memory import SessionMemory
        except ImportError:
            return {"error": "workflow memory not available"}

        if not hasattr(registry, "_session_memory"):
            registry._session_memory = SessionMemory()

        action = args.get("action", "get")
        if action == "add":
            registry._session_memory.add(
                content=args.get("content", ""),
                role=args.get("role", "user"),
            )
            return {"memory": {"action": "added"}}
        elif action == "clear":
            registry._session_memory.clear()
            return {"memory": {"action": "cleared"}}
        else:
            return {"memory": {"messages": registry._session_memory.get_context()}}

    # ===== ADVANCED COMPOSITE TOOLS =====
    
    def _register_advanced_tools(self):
        """Register advanced composite tools."""
        
        # Import advanced tool handlers
        from .advanced_tools import (handle_autonomous_synthesis,
                                     handle_entropy_scan,
                                     handle_resonance_cascade_query)
        
        self.register(ToolDefinition(
            name="resonance_cascade_query",
            description="Query crystals by geometric resonance in E8 space (finds harmonically related content)",
            category="advanced",
            handler=handle_resonance_cascade_query,
            parameters={
                "query": {"type": "string", "description": "Query text to resonate against"},
                "min_resonance": {"type": "number", "default": 0.6, "description": "Minimum resonance threshold (0-1)"},
                "max_results": {"type": "number", "default": 10},
                "include_harmonics": {"type": "boolean", "default": True}
            },
            returns={
                "query_embedding": "array",
                "query_properties": "object",
                "resonant_matches": "number",
                "results": "array",
                "resonance_distribution": "object"
            }
        ))
        
        self.register(ToolDefinition(
            name="autonomous_knowledge_synthesis",
            description="Automatically synthesize knowledge from crystal collections using quorum and TMN",
            category="advanced",
            handler=handle_autonomous_synthesis,
            parameters={
                "source_crystal_ids": {"type": "array", "optional": True},
                "query": {"type": "string", "optional": True},
                "synthesis_depth": {"type": "number", "default": 2, "description": "Depth 1-3"},
                "create_proposal": {"type": "boolean", "default": False},
                "tags": {"type": "array", "optional": True}
            },
            returns={
                "synthesized": "boolean",
                "synthesis_crystal_id": "string",
                "synthesis_preview": "string",
                "deliberation_confidence": "number",
                "tmn_insights_learned": "number",
                "proposal_created": "boolean"
            }
        ))
        
        self.register(ToolDefinition(
            name="system_entropy_scan",
            description="Deep system diagnostics using geometric conservation laws and entropy analysis",
            category="advanced",
            handler=handle_entropy_scan,
            parameters={
                "scan_depth": {"type": "string", "enum": ["quick", "standard", "deep"], "default": "standard"},
                "include_predictions": {"type": "boolean", "default": True}
            },
            returns={
                "overall_harmony_score": "number",
                "components": "object",
                "geometric_analysis": "object",
                "anomalies": "array",
                "recommendations": "array",
                "conservation_status": "object",
                "predictions": "object"
            }
        ))


# Global registry instance
_cmplx_registry: Optional[CMPLXToolRegistry] = None


def get_cmplx_registry(config=None, data_root: Path = None) -> CMPLXToolRegistry:
    """Get or create global CMPLX tool registry."""
    global _cmplx_registry
    
    if _cmplx_registry is None:
        _cmplx_registry = CMPLXToolRegistry(config, data_root)
    
    return _cmplx_registry


def register_cmplx_tools(server):
    """Register all CMPLX tools with an MCP server."""
    registry = get_cmplx_registry()
    
    for tool_def in registry.tools.values():
        server.register_tool(
            name=tool_def.name,
            description=tool_def.description,
            handler=lambda args, td=tool_def: registry.call(td.name, args),
            parameters=tool_def.parameters,
            returns=tool_def.returns
        )
    
    logger.info(f"Registered {len(registry.tools)} CMPLX tools with MCP server")
    return registry


# Import asyncio for async checks
import asyncio
