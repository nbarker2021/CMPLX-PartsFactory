from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import json
import os
from pathlib import Path


@dataclass
class SNAPSpec:
    """Blueprint for a SNAP expert or tool.
    
    Defines what the expert is, what domain it operates in,
    what it takes as input, what it produces, and under what
    governance constraints it runs.
    """
    name: str
    domain: str
    purpose: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    governance: Dict[str, Any]


class SNAPDNA:
    """SNAPDNA — Expert blueprint factory.
    
    Generates SNAP tools and agent definitions from specs.
    Each expert gets:
      - A named identity
      - A domain and purpose
      - Defined I/O contracts
      - Governance constraints
      - An agent definition with instruction set
      - A brain template for knowledge persistence
    """
    
    def __init__(self, out_dir: str | Path | None = None):
        self.out_dir = Path(out_dir) if out_dir else Path("/tmp/snapdna_exports")
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self._specs: dict[str, SNAPSpec] = {}
        self._agents: dict[str, Path] = {}
        self._tools: dict[str, Path] = {}
    
    def new_spec(self, name: str, domain: str, purpose: str,
                 inputs: Dict[str, Any] | None = None,
                 outputs: Dict[str, Any] | None = None,
                 governance: Dict[str, Any] | None = None) -> SNAPSpec:
        """Create a new expert spec."""
        spec = SNAPSpec(
            name=name,
            domain=domain,
            purpose=purpose,
            inputs=inputs or {},
            outputs=outputs or {},
            governance=governance or {"lane": "general", "dr": 0},
        )
        self._specs[name] = spec
        return spec
    
    def emit_tool(self, spec: SNAPSpec, 
                  tool_code: str | None = None,
                  service_url: str | None = None) -> str:
        """Generate a concrete Python tool from a spec.
        
        If tool_code is provided, writes it directly.
        Otherwise generates a stub that calls the specified service.
        """
        fname = self.out_dir / f"{spec.name}.py"
        
        if tool_code:
            fname.write_text(tool_code, encoding="utf-8")
        else:
            code = self._generate_tool_stub(spec, service_url)
            fname.write_text(code, encoding="utf-8")
        
        self._tools[spec.name] = fname
        return str(fname)
    
    def emit_agent(self, spec: SNAPSpec,
                   instruction_set: str | None = None,
                   brain_data: Dict[str, Any] | None = None) -> str:
        """Generate an agent definition JSON from a spec.
        
        Creates:
          - spec.name.agent.json  (agent definition)
          - spec.name.brain.json  (brain template)
          - spec.name.instructions.md (instruction set)
        """
        agent_path = self.out_dir / f"{spec.name}.agent.json"
        brain_path = self.out_dir / f"{spec.name}.brain.json"
        instr_path = self.out_dir / f"{spec.name}.instructions.md"
        
        agent_def = {
            "agent_id": spec.name,
            "domain": spec.domain,
            "purpose": spec.purpose,
            "governance": spec.governance,
            "inputs": spec.inputs,
            "outputs": spec.outputs,
            "type": "derived_expert",
        }
        agent_path.write_text(json.dumps(agent_def, indent=2), encoding="utf-8")
        
        brain = brain_data or {
            "knowledge_base": {},
            "experience_log": [],
            "provenance": {"created_by": "SNAPDNA", "spec": spec.name},
        }
        brain_path.write_text(json.dumps(brain, indent=2), encoding="utf-8")
        
        instructions = instruction_set or f"""# {spec.name} Agent
Domain: {spec.domain}
Purpose: {spec.purpose}

## Capabilities
{json.dumps(list(spec.outputs.keys()), indent=2)}

## Governance
Lane: {spec.governance.get('lane', 'general')}
Digital Root: {spec.governance.get('dr', 0)}

## Operation
This agent was derived via SNAPDNA expert composition.
It operates within geometric governance constraints.
"""
        instr_path.write_text(instructions, encoding="utf-8")
        
        self._agents[spec.name] = agent_path
        return str(agent_path)
    
    def _generate_tool_stub(self, spec: SNAPSpec,
                            service_url: str | None = None) -> str:
        """Generate a stub tool implementation."""
        imports = []
        body_lines = []
        
        if service_url:
            imports.append("import requests")
            body_lines.append(f'    url = "{service_url}"')
            body_lines.append('    resp = requests.post(url, json=kwargs, timeout=30)')
            body_lines.append('    resp.raise_for_status()')
            body_lines.append('    return resp.json()')
        else:
            body_lines.append('    # TODO: implement expert logic')
            body_lines.append(f'    return {{"status": "ok", "expert": "{spec.name}", "domain": "{spec.domain}"}}')
        
        code = f'''"""Auto-generated SNAP tool: {spec.name}
Domain: {spec.domain}
Purpose: {spec.purpose}
"""
{chr(10).join(imports)}
import json

SPEC = {json.dumps(asdict(spec), indent=2)}

def run(**kwargs):
{chr(10).join(body_lines)}

def help():
    """Return this expert's spec as a dict."""
    return {json.dumps(asdict(spec), indent=2)}
'''
        return code
    
    def list_experts(self) -> list[dict]:
        """List all registered specs."""
        return [asdict(s) for s in self._specs.values()]
    
    def get_expert(self, name: str) -> SNAPSpec | None:
        return self._specs.get(name)


# Singleton factory
_fallback = "/tmp/snapdna_exports"
_env = os.environ.get("SNAPDNA_OUT_DIR", "")
_default_out = _env if _env else "/mnt/d/PartsFactory/CMPLX-PartsFactory/catalog/experts"
try:
    Path(_default_out).mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError):
    _default_out = _fallback
    Path(_default_out).mkdir(parents=True, exist_ok=True)
factory = SNAPDNA(out_dir=Path(_default_out))
