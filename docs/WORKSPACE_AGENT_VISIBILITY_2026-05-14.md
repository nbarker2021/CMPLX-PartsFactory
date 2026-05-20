# Workspace Agent Visibility

This file records the editor and agent wiring that makes the repo-kernel
control layer visible to live work.

## VS Code

- Workspace file: `CMPLX-PartsFactory.code-workspace`
- Settings: `.vscode/settings.json`
- Tasks: `.vscode/tasks.json`
- REST examples: `.vscode/repo-kernel.http`

Useful tasks:

- `repo-kernel: up`
- `repo-kernel: restart`
- `repo-kernel: health`
- `repo-kernel: workbook`
- `repo-kernel: gitnexus status`
- `repo-kernel: named capabilities`
- `repo-kernel: focused tests`

## Agent And Skill Files

- Agent orientation: `.agents/repo-kernel-control.md`
- OpenCode skill: `.opencode/skills/repo-kernel-control/SKILL.md`
- Claude skill: `.claude/skills/repo-kernel-control/SKILL.md`
- Root agent rules: `AGENTS.md`

## Canonical Rule

The visible workspace entrypoint is the repo-kernel controller on
`http://localhost:8786`. Agents should use `/api/global/...` routes and the live
workbook instead of guessing upstream ports from historical compose files.

Current named capability routes:

- `/api/global/knowledge/devkit-ingest`
- `/api/global/mcp/local-os`
- `/api/global/code-execution/octa64`
- `/api/global/validation/mcp-os`
- `/api/global/synthesis/cqe-modular`
