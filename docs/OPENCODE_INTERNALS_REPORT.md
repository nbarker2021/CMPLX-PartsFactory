# OPENCODE INTERNALS REPORT
## Comprehensive Analysis of Agent Behavior Control Architecture

**Source:** `/mnt/d/Manny Unification 2/agent ecosystem/oh-my-openagent-dev/oh-my-openagent-dev/`  
**Analysis Date:** 2026-05-11  
**Total Source Files:** ~1766 TypeScript files, 377k LOC  
**Report Scope:** Full chain from user message to LLM call, all control points, hooks, managers, config, agents, tools, MCPs, skills, and safety controls.

---

## EXECUTIVE SUMMARY

OpenCode (oh-my-opencode / oh-my-openagent) is a Claude Code plugin that implements a **layered behavior control architecture** with three core principles:

1. **Plugin Interface Layer** — 10 OpenCode hook handlers that intercept every interaction between the user and the LLM.
2. **52 Internal Lifecycle Hooks** — Organized into 4 tiers (Session 24, Tool-Guard 14, Transform 5, Continuation 7, Skill 2) that mutate prompts, parameters, messages, tools, and responses.
3. **Multi-Level Config Merge** — User config (~/.config/opencode/) is deep-merged with project config (.opencode/), then Zod-validated, then applied through a 6-phase config handler pipeline.

**Critical finding:** There is NO single "system prompt" file. The system prompt is **dynamically constructed per-agent, per-model, per-session** through `src/agents/sisyphus.ts` and related agent factories. The prompt construction is heavily hardcoded but partially overridable via `agents.{name}.prompt` and `agents.{name}.prompt_append` config fields.

**The message-to-LLM pipeline has 9 sequential control gates** before the LLM ever sees the message. Most are interceptable via config, but several safety/harm controls are hardcoded and cannot be disabled.

---

## 1. INITIALIZATION ARCHITECTURE

### 1.1 Entry Point (`src/index.ts`)

The plugin exports `pluginModule = { id: "oh-my-openagent", server: serverPlugin }`.

`serverPlugin(input, _options)` executes this exact sequence:

```
1. initConfigContext("opencode", null)
2. loadPluginConfig(directory, input)           // JSONC parse + merge + Zod validate
3. createPluginPostHog() + telemetry capture    // Non-fatal, silent on failure
4. initializeOpenClaw(pluginConfig.openclaw)    // Optional external integration
5. startTmuxCheck()                             // If tmux integration enabled
6. createManagers({ ctx, pluginConfig, tmuxConfig, modelCacheState, ... })
7. createTools({ ctx, pluginConfig, managers }) // 26 tools + skill context
8. createHooks({ ctx, pluginConfig, managers, ... }) // 52 hooks
9. createPluginInterface({ ctx, pluginConfig, managers, hooks, tools })
10. Return PluginInterface + experimental.session.compacting handler
```

**What loads first:** Config loading is first. Managers (BackgroundManager, TmuxSessionManager, SkillMcpManager, ConfigHandler, ModelFallbackControllerAccessor) are created before tools or hooks. Tools are created before hooks because hooks receive `mergedSkills` and `availableSkills` from the tool creation step.

### 1.2 Config Loading (`src/plugin-config.ts`)

**Multi-level merge order:**
1. User config: `~/.config/opencode/oh-my-opencode.json[c]` (or legacy `oh-my-openagent.json[c]`)
2. Project config: `{directory}/.opencode/oh-my-opencode.json[c]`
3. Zod defaults: `OhMyOpenCodeConfigSchema.parse({})`

**Merge rules:**
- `agents`, `categories`, `claude_code`: **deep merge recursively**
- `disabled_*` arrays (agents, hooks, mcps, skills, commands, tools): **Set union** (concat + dedupe)
- All other fields: **override replaces base**

**Partial parsing:** If full Zod validation fails, the loader attempts per-section partial parsing. Invalid sections are skipped with warnings. `PARTIAL_STRING_ARRAY_KEYS` can be parsed even if the overall config fails.

**Git master overrides:** The `git_master` field is loaded via explicit shallow merge after the main merge, because Zod defaults would otherwise overwrite user settings.

### 1.3 Managers (`src/create-managers.ts`)

Five managers control runtime behavior:

| Manager | Class | Purpose |
|---------|-------|---------|
| `tmuxSessionManager` | `TmuxSessionManager` | Spawns subagents in tmux panes, tracks pane state |
| `backgroundManager` | `BackgroundManager` | Controls async task execution, concurrency limits, circuit breaker |
| `skillMcpManager` | `SkillMcpManager` | Manages skill-embedded MCP servers (stdio + HTTP, per-session) |
| `configHandler` | `createConfigHandler` | 6-phase config loading pipeline (see below) |
| `modelFallbackControllerAccessor` | `createModelFallbackControllerAccessor` | Shared state accessor for model fallback across hooks |

**Tmux integration:** If `pluginConfig.tmux.enabled` is true, `markServerRunningInProcess()` is called and tmux cleanup is registered for process shutdown.

**Background manager callbacks:**
- `onSubagentSessionCreated`: Forwards to tmux session manager + OpenClaw dispatch
- `onShutdown`: Cleans up tmux sessions
- `enableParentSessionNotifications`: Controlled by `disabled_hooks` check for `"background-notification"`

---

## 2. THE FULL MESSAGE-TO-LLM PIPELINE

This is the complete chain of how a user message becomes an LLM API call, with every control point identified.

### Stage 1: OpenCode Runtime Receives User Message

The OpenCode editor/IDE runtime (not this plugin) receives the user's typed message. Before calling the LLM, the runtime invokes the plugin's registered handlers in this order:

### Stage 2: `chat.message` Handler (`src/plugin/chat-message.ts`)

**First plugin processing gate.** This handler receives:
- `input`: `{ sessionID, agent?, model? }`
- `output`: `{ message: Record<string, unknown>, parts: ChatMessagePart[] }`

**Execution sequence inside chat.message:**

```
1. setSessionAgent(input.sessionID, input.agent)           // Track which agent is active
2. firstMessageVariantGate.shouldOverride(sessionID)       // First-message special handling
3. getStoredMainSessionModel() -> output.message["model"]  // Restore persisted model override
4. hooks.modelFallback["chat.message"](input, output)      // If runtime fallback NOT enabled
5. setSessionModel(sessionID, modelOverride)               // Persist model choice
6. hooks.stopContinuationGuard["chat.message"](input)      // Check if continuation is stopped
7. hooks.backgroundNotificationHook["chat.message"](input, output)
8. hooks.runtimeFallback["chat.message"](input, output)    // If runtime fallback enabled
9. hooks.keywordDetector["chat.message"](input, output)    // Detect "ulw", "ultrawork", etc.
10. hooks.thinkMode["chat.message"](input, output)          // Inject thinking mode instructions
11. hooks.claudeCodeHooks["chat.message"](input, output)    // Claude Code compatibility layer
12. hooks.autoSlashCommand["chat.message"](input, output)   // Auto-execute slash commands
13. hooks.noSisyphusGpt["chat.message"](input, output)      // Block GPT models for Sisyphus
14. hooks.noHephaestusNonGpt["chat.message"](input, output) // Block non-GPT models for Hephaestus
15. hooks.startWork["chat.message"](input, output)          // Handle /start-work command
16. applyUltraworkModelOverrideOnMessage()                  // Override model for ultrawork mode
```

**What it controls:**
- **Model selection:** Can override the model before the LLM call. `modelOverride` is written to `output.message["model"]` as `{ providerID, modelID }`.
- **Prompt injection:** Keyword detector injects mode-specific instructions into `output.parts[textPartIndex].text` (e.g., ultrawork instructions).
- **Agent gating:** `noSisyphusGpt` and `noHephaestusNonGpt` hooks block incompatible model/agent combinations.
- **Continuation control:** `stopContinuationGuard` can halt the agent from continuing work.
- **Work start:** `startWork` hook transforms the message into a work-starting template if `/start-work` is detected.

**Configurable?** Yes — every hook except the model persistence logic can be disabled via `disabled_hooks`. However, the hook execution ORDER is hardcoded.

### Stage 3: `chat.params` Handler (`src/plugin/chat-params.ts`)

**Second gate: model parameter adjustment.** Called after `chat.message`. Receives the resolved model and adjusts temperature, topP, maxOutputTokens, reasoningEffort, thinking, and variant.

**Execution sequence:**

```
1. buildChatParamsInput(raw) -> normalizedInput
2. getSessionPromptParams(sessionID) -> apply stored params from session state
3. getModelCapabilities(providerID, modelID) -> fetch capability metadata
4. resolveCompatibleModelSettings(desired, capabilities) -> normalize settings
5. Apply compatibility results to output.temperature, output.topP, output.maxOutputTokens, output.options.thinking, output.options.reasoningEffort
6. args.anthropicEffort["chat.params"](normalizedInput, output) // Anthropic-specific effort hook
```

**What it controls:**
- All LLM sampling parameters are normalized against the **model capability database** (`src/shared/model-requirements.ts` and cached models.dev data).
- Unsupported settings are silently removed (e.g., `reasoningEffort` on Claude models).
- `variant` is downgraded to closest supported value.
- `maxTokens` is capped to model's reported max output limit.

**Configurable?** Partially. Users can set `agents.{name}.temperature`, `.top_p`, `.maxTokens`, `.thinking`, `.reasoningEffort`, `.variant` in config. But the **capability normalization is hardcoded** and cannot be bypassed.

### Stage 4: `chat.headers` Handler (`src/plugin/chat-headers.ts`)

**Third gate: HTTP header injection.** Currently minimal — injects Copilot `x-initiator` header if using GitHub Copilot provider. No user-configurable headers are supported.

### Stage 5: `experimental.chat.messages.transform` Handler (`src/plugin/messages-transform.ts`)

**Fourth gate: message array mutation.** This operates on the FULL message history, not just the current message.

**Execution sequence:**

```
1. hooks.contextInjectorMessagesTransform(input, output)   // Inject pending context into last user message
2. hooks.thinkingBlockValidator(input, output)             // Validate thinking blocks for Anthropic models
3. hooks.toolPairValidator(input, output)                  // Validate tool call/result pairing
```

**Context injection (`src/features/context-injector/injector.ts`):**
- Scans `output.messages` to find the **last user message**.
- If `contextCollector.hasPending(sessionID)`, inserts a **synthetic text part** before the user's text part.
- The synthetic part contains merged context from all registered sources (rules, directory agents, READMEs, etc.).
- Synthetic parts are marked `synthetic: true` (hidden in UI).

**Thinking block validator:** Validates that Anthropic thinking blocks are properly formed. Can reject malformed blocks.

**Tool pair validator:** Ensures every tool call has a corresponding tool result and vice versa. Prevents desync.

**Configurable?** `thinking-block-validator` and `tool-pair-validator` can be disabled via `disabled_hooks`. `contextInjectorMessagesTransform` is **always enabled** and cannot be disabled — it is not wrapped in a conditional.

### Stage 6: `experimental.chat.system.transform` Handler (`src/plugin/system-transform.ts`)

**Fifth gate: system prompt mutation.** Currently a **no-op** (`return async () => {}`). The handler signature accepts `input: { sessionID?, model }` and `output: { system: string[] }`, but does nothing.

**Implication:** There is NO plugin-level system prompt transformation hook currently active. System prompt construction happens entirely in the **agent factory functions** (see Stage 7).

### Stage 7: Agent Config Construction (`src/agents/` and `src/plugin-handlers/agent-config-handler.ts`)

**Sixth gate: system prompt assembly.** This happens during the `config` handler phase, not per-message, but the agent config (including the system prompt) is what the runtime uses for every LLM call.

**Config handler pipeline (`src/plugin-handlers/config-handler.ts`):**

```
1. setAdditionalAllowedMcpEnvVars(pluginConfig.mcp_env_allowlist)
2. applyProviderConfig(config, modelCacheState)              // Provider-level settings
3. clearFormatterCache()
4. loadPluginComponents(pluginConfig)                        // Load external agent definitions, skills, MCPs
5. applyAgentConfig({ config, pluginConfig, ctx, pluginComponents })  // BUILD AGENTS
6. applyToolConfig({ config, pluginConfig, agentResult })    // Register tools
7. applyMcpConfig({ config, pluginConfig, pluginComponents }) // Register MCPs
8. applyCommandConfig({ config, pluginConfig, ctx, pluginComponents }) // Register commands
```

**Agent construction (`applyAgentConfig` in `src/plugin-handlers/agent-config-handler.ts`):**

1. Discover skills from 7 sources:
   - `discoverConfigSourceSkills` (from `pluginConfig.skills.sources`)
   - `discoverUserClaudeSkills` (from `~/.claude/skills/`)
   - `discoverProjectClaudeSkills` (from `{project}/.claude/skills/`)
   - `discoverProjectAgentsSkills` (from `{project}/.opencode/agents/`)
   - `discoverOpencodeGlobalSkills`
   - `discoverOpencodeProjectSkills`
   - `discoverGlobalAgentsSkills`

2. Load agents from 8 sources:
   - Built-in agents (`createBuiltinAgents`)
   - User agents (`loadUserAgents`)
   - Project agents (`loadProjectAgents`)
   - OpenCode global agents (`loadOpencodeGlobalAgents`)
   - OpenCode project agents (`loadOpencodeProjectAgents`)
   - Plugin components agents (`pluginComponents.agents`)
   - Agent definition files (`loadAgentDefinitions` from `agent_definitions` paths)
   - OpenCode config agents (`readOpencodeConfigAgents`)

3. **Built-in agent factory (`src/agents/builtin-agents.ts`):**
   - Calls `createBuiltinAgents(disabledAgents, agentOverrides, directory, systemDefaultModel, categories, gitMasterConfig, discoveredSkills, ...)`
   - Fetches available models from cache (does NOT call OpenCode client APIs during init — deadlock risk)
   - Creates `sisyphus`, `hephaestus`, and `atlas` configs with special handling
   - Other agents (oracle, librarian, explore, etc.) are added via `collectPendingBuiltinAgents`

4. **Sisyphus prompt construction (`src/agents/sisyphus.ts`):**
   - `buildDynamicSisyphusPrompt(model, availableAgents, availableTools, availableSkills, availableCategories, useTaskSystem)`
   - Assembles 12 dynamic sections:
     1. `agentIdentity` — Hardcoded "Sisyphus" identity
     2. `keyTriggers` — Dynamic based on available agents/skills
     3. `toolSelection` — Dynamic table of available tools
     4. `exploreSection` — Dynamic based on available agents
     5. `librarianSection` — Dynamic based on available agents
     6. `categorySkillsGuide` — Dynamic based on categories + skills
     7. `delegationTable` — Dynamic based on available agents
     8. `oracleSection` — Dynamic based on available agents
     9. `hardBlocks` — Hardcoded safety constraints
     10. `antiPatterns` — Hardcoded anti-patterns
     11. `parallelDelegationSection` — Model-specific (GPT-5.4 vs others)
     12. `nonClaudePlannerSection` — Model-specific
     13. `taskManagementSection` — Task system on/off

   - **Model-specific mutations:**
     - `isGpt5_4Model(model)` -> uses entirely different prompt (`buildGpt54SisyphusPrompt`)
     - `isGeminiModel(model)` -> injects `buildGeminiIntentGateEnforcement()`, `buildGeminiToolMandate()`, `buildGeminiToolGuide()`, `buildGeminiToolCallExamples()`, `buildGeminiDelegationOverride()`, `buildGeminiVerificationOverride()` at specific anchor points in the prompt
     - `isGptModel(model)` -> adds `reasoningEffort: "medium"`
     - Other models -> adds `thinking: { type: "enabled", budgetTokens: 32000 }`

5. **Agent precedence in final config:**
   ```
   params.config.agent = {
     ...agentConfig,           // Built-in: Sisyphus, Hephaestus, Prometheus, Atlas
     ...otherBuiltinAgents,    // Oracle, Librarian, Explore, etc.
     ...filteredPluginAgents,
     ...filteredUserAgents,
     ...filteredOpencodeGlobalAgents,
     ...filteredProjectAgents,
     ...filteredOpencodeProjectAgents,
     ...filteredAgentDefinitionAgents,
     ...filteredOpencodeConfigAgents,
     ...filteredConfigAgents,  // Any remaining from OpenCode's own config
     build: { mode: "subagent", hidden: true },
     plan: planDemoteConfig,   // If planner enabled + replace_plan
   }
   ```
   Later entries override earlier ones. **Project agents override global agents. User agents override plugin agents.**

**What controls system prompts:**
- **Hardcoded:** The base Sisyphus prompt template (~450 lines in `src/agents/sisyphus.ts`) is 90% hardcoded text.
- **Dynamic:** Agent tables, tool lists, category guides are built from runtime-discovered agents/tools/categories.
- **Overridable:** `agents.sisyphus.prompt` replaces the entire prompt. `agents.sisyphus.prompt_append` appends text. Both support `file://` URIs.
- **Not overridable:** The model-specific injection logic (Gemini mandates, GPT-5.4 variant) is hardcoded in the factory.

### Stage 8: Tool Registration (`src/plugin/tool-registry.ts`)

**Seventh gate: what tools the LLM can see.**

`createToolRegistry` builds a `Record<string, ToolDefinition>` containing:

```
- builtinTools (read, write, edit, bash, webfetch, etc.)
- createGrepTools(ctx)
- createGlobTools(ctx)
- createAstGrepTools(ctx)
- createSessionManagerTools(ctx)
- backgroundTools (background_output, background_cancel)
- call_omo_agent (delegation to other agents)
- look_at (multimodal, if multimodal-looker agent enabled)
- task (delegate_task with categories/skills)
- skill_mcp (skill-embedded MCP tools)
- skill (skill execution)
- interactive_bash (if tmux enabled)
- task_create, task_get, task_list, task_update (if task system enabled)
- edit (hashline edit, if hashline_edit enabled)
```

**Tool filtering:**
1. `normalizeToolArgSchemas(toolDefinition)` — sanitizes all tool schemas
2. `filterDisabledTools(allTools, pluginConfig.disabled_tools)` — removes explicitly disabled tools
3. `trimToolsToCap(filteredTools, maxTools)` — if `experimental.max_tools` is set, removes low-priority tools until under cap

**Tool priority order for trimming (lowest priority first):**
`session_list`, `session_read`, `session_search`, `session_info`, `interactive_bash`, `look_at`, `call_omo_agent`, `task_create`, `task_get`, `task_list`, `task_update`, `background_output`, `background_cancel`, `edit`, `ast_grep_replace`, `ast_grep_search`, `glob`, `grep`, `skill_mcp`, `skill`, `task`, `lsp_*` tools.

**What controls tool availability:**
- `disabled_tools` array in config
- `experimental.max_tools` cap
- Agent-specific `permission` object (per-tool allow/ask/deny)
- `disabled_agents` indirectly (e.g., disabling `multimodal-looker` removes `look_at`)
- `hashline_edit` boolean (enables hashline edit tool)
- `new_task_system_enabled` / `experimental.task_system` (enables task tools)

### Stage 9: MCP Registration (`src/plugin-handlers/mcp-config-handler.ts` and `src/mcp/index.ts`)

**Eighth gate: MCP server integration.**

Three-tier MCP system:

| Tier | Source | Mechanism |
|------|--------|-----------|
| Built-in | `src/mcp/` | 3 remote HTTP MCPs: `websearch` (Exa/Tavily), `context7`, `grep_app` |
| Claude Code | `.mcp.json` | Loaded via `loadMcpConfigs()`, `${VAR}` env expansion |
| Skill-embedded | SKILL.md YAML | Managed by `SkillMcpManager` (stdio + HTTP, per-session) |

**Merge order:**
```
params.config.mcp = {
  ...createBuiltinMcps(disabledMcps, pluginConfig),
  ...mcpResult.servers,       // From .mcp.json
  ...userMcp,                 // From OpenCode's own mcp config
  ...pluginComponents.mcpServers,
}
```

User MCP entries override Claude Code `.mcp.json` entries. Warnings are logged on collision.

**What controls MCPs:**
- `disabled_mcps` array in config
- `mcp_env_allowlist` array (controls which env vars are passed to MCP servers)
- `claude_code.mcp` boolean (master switch for .mcp.json loading)

### Stage 10: Tool Execution Hooks

**Ninth gate: pre/post tool execution.**

#### `tool.execute.before` (`src/plugin/tool-execute-before.ts`)

Runs BEFORE the tool is executed. Sequential hook chain:

```
1. hooks.writeExistingFileGuard["tool.execute.before"]
2. hooks.questionLabelTruncator["tool.execute.before"]
3. hooks.claudeCodeHooks["tool.execute.before"]
4. hooks.nonInteractiveEnv["tool.execute.before"]
5. hooks.bashFileReadGuard["tool.execute.before"]
6. hooks.commentChecker["tool.execute.before"]
7. hooks.directoryAgentsInjector["tool.execute.before"]
8. hooks.directoryReadmeInjector["tool.execute.before"]
9. hooks.rulesInjector["tool.execute.before"]
10. hooks.tasksTodowriteDisabler["tool.execute.before"]
11. hooks.webfetchRedirectGuard["tool.execute.before"]
12. hooks.prometheusMdOnly["tool.execute.before"]
13. hooks.sisyphusJuniorNotepad["tool.execute.before"]
14. hooks.atlasHook["tool.execute.before"]
```

Plus special handling for:
- `bash` tool: strips null bytes from command strings
- `question` tool: sends session notification
- `task` tool: resolves subagent type, injects ULTRAWORK oracle verification prompts
- `skill` tool: handles `/ralph-loop`, `/ulw-loop`, `/cancel-ralph`, `/stop-continuation` commands

#### `tool.execute.after` (`src/plugin/tool-execute-after.ts`)

Runs AFTER the tool executes. Sequential hook chain:

```
1. recoverToolMetadata(input.sessionID, input) -> restore title/metadata from store
2. hooks.toolOutputTruncator["tool.execute.after"]
3. hooks.claudeCodeHooks["tool.execute.after"]
4. hooks.preemptiveCompaction["tool.execute.after"]
5. hooks.contextWindowMonitor["tool.execute.after"]
6. hooks.commentChecker["tool.execute.after"]
7. hooks.directoryAgentsInjector["tool.execute.after"]
8. hooks.directoryReadmeInjector["tool.execute.after"]
9. hooks.rulesInjector["tool.execute.after"]
10. hooks.emptyTaskResponseDetector["tool.execute.after"]
11. hooks.agentUsageReminder["tool.execute.after"]
12. hooks.categorySkillReminder["tool.execute.after"]
13. hooks.interactiveBashSession["tool.execute.after"]
14. hooks.editErrorRecovery["tool.execute.after"]
15. hooks.delegateTaskRetry["tool.execute.after"]
16. hooks.atlasHook["tool.execute.after"]
17. hooks.taskResumeInfo["tool.execute.after"]
18. hooks.readImageResizer["tool.execute.after"]
19. hooks.hashlineReadEnhancer["tool.execute.after"]
20. hooks.webfetchRedirectGuard["tool.execute.after"]
21. hooks.jsonErrorRecovery["tool.execute.after"]
```

**Special behavior for `extract`/`discard` tools:** All after-hooks run inside a try/catch that restores original output on failure. This prevents data loss on extraction tools.

### Stage 11: Event Handler (`src/plugin/event.ts`)

**Tenth gate: session lifecycle and error recovery.** The event handler processes:
- `session.created` — Sets main session, tmux tracking, OpenClaw dispatch
- `session.deleted` — Clears ALL session state (agent, model, fallback chains, message cursors, background consumption, stop continuation, prompt params, subagent sessions, tools, LSP cleanup, tmux cleanup, skill MCP disconnect)
- `session.idle` — Deduped synthetic/real idle handling, OpenClaw dispatch
- `message.updated` — Updates session agent/model tracking, **triggers model fallback on assistant errors**
- `session.status` — Retry deduplication, **triggers model fallback on retry statuses**
- `session.error` — **Session recovery first** (thinking blocks, tool results), then **model fallback second**
- `message.removed` — Restores background output consumption

**Model fallback trigger logic:**
1. Extract error name/message from the error object
2. `shouldRetryError(errorInfo)` — hardcoded error classifier
3. Determine agent name from session state or error message heuristics
4. `applyUserConfiguredFallbackChain()` — loads user's `fallback_models` config
5. `setPendingModelFallback()` — marks fallback as pending
6. If auto-retry eligible: `autoContinueAfterFallback()` -> abort session -> prompt "continue"

**Two fallback systems:**
- **Model fallback** (`model-fallback` hook): Proactive, triggered via `chat.message`. Per-agent chains from `src/shared/model-requirements.ts`.
- **Runtime fallback** (`runtime-fallback` hook): Reactive, triggered on `session.error`/`message.updated`/`session.status`. Configurable via `runtime_fallback` object.

### Stage 12: LLM API Call

After all plugin handlers complete, the OpenCode runtime sends the assembled request to the LLM provider. The plugin has no further control until the response returns.

---

## 3. DETAILED BREAKDOWN OF CONTROL POINTS

### 3.1 Hooks System (`src/create-hooks.ts`)

Hooks are organized into 3 groups:

#### Core Hooks (`src/plugin/hooks/create-core-hooks.ts`)
Combines Session + Tool-Guard + Transform hooks.

**Session Hooks (24 hooks):**
| Hook | File | Trigger | Behavior | Disable? |
|------|------|---------|----------|----------|
| `context-window-monitor` | `src/hooks/context-window-monitor.ts` | Event + tool.execute.after | Monitors token usage, triggers compaction | Yes |
| `preemptive-compaction` | `src/hooks/preemptive-compaction/` | Event + tool.execute.after | Auto-compacts context before overflow | Yes (requires `experimental.preemptive_compaction`) |
| `session-recovery` | `src/hooks/session-recovery/` | Event (session.error) | Recovers from thinking block / tool result errors | Yes |
| `session-notification` | `src/hooks/session-notification/` | Event + tool.execute.before | Desktop notifications on idle/question | Yes (conflict detection with external plugins) |
| `think-mode` | `src/hooks/think-mode/` | chat.message + event | Injects thinking mode instructions | Yes |
| `model-fallback` | `src/hooks/model-fallback/` | chat.message + event | Proactive model fallback on errors | Yes (requires `model_fallback: true`) |
| `anthropic-context-window-limit-recovery` | `src/hooks/anthropic-context-window-limit-recovery/` | Event | Recovers from Anthropic 1M context limit | Yes |
| `auto-update-checker` | `src/hooks/auto-update-checker/` | Event | Checks for plugin updates | Yes |
| `agent-usage-reminder` | `src/hooks/agent-usage-reminder/` | Event + tool.execute.after | Reminds agent to use available agents | Yes |
| `non-interactive-env` | `src/hooks/non-interactive-env/` | tool.execute.before | Injects non-interactive env vars | Yes |
| `interactive-bash-session` | `src/hooks/interactive-bash-session/` | Event + tool.execute.after | Manages tmux bash sessions | Yes (requires tmux enabled) |
| `ralph-loop` | `src/hooks/ralph-loop/` | chat.message + event + tool.execute.before | Manages autonomous work loops | Yes |
| `edit-error-recovery` | `src/hooks/edit-error-recovery/` | tool.execute.after | Recovers from edit tool failures | Yes |
| `delegate-task-retry` | `src/hooks/delegate-task-retry/` | tool.execute.after | Retries failed delegate tasks | Yes |
| `start-work` | `src/hooks/start-work/` | chat.message | Handles `/start-work` command | Yes |
| `prometheus-md-only` | `src/hooks/prometheus-md-only/` | tool.execute.before | Restricts Prometheus to markdown output | Yes |
| `sisyphus-junior-notepad` | `src/hooks/sisyphus-junior-notepad/` | tool.execute.before | Injects notepad context for Junior | Yes |
| `no-sisyphus-gpt` | `src/hooks/no-sisyphus-gpt/` | chat.message | Blocks GPT models for Sisyphus | Yes (NOT recommended to disable) |
| `no-hephaestus-non-gpt` | `src/hooks/no-hephaestus-non-gpt/` | chat.message | Blocks non-GPT models for Hephaestus | Yes |
| `question-label-truncator` | `src/hooks/question-label-truncator/` | tool.execute.before | Truncates question tool labels | Yes |
| `task-resume-info` | `src/hooks/task-resume-info/` | tool.execute.after | Injects task resume information | Yes |
| `anthropic-effort` | `src/hooks/anthropic-effort/` | chat.params | Sets Anthropic effort level | Yes |
| `runtime-fallback` | `src/hooks/runtime-fallback/` | chat.message + event | Reactive model fallback | Yes |
| `legacy-plugin-toast` | `src/hooks/legacy-plugin-toast/` | Event | Warns about legacy plugins | Yes |

**Tool-Guard Hooks (14 hooks):**
| Hook | File | Trigger | Behavior | Disable? |
|------|------|---------|----------|----------|
| `comment-checker` | `src/hooks/comment-checker/` | tool.execute.before/after | Validates code comment quality | Yes |
| `tool-output-truncator` | `src/hooks/tool-output-truncator.ts` | tool.execute.after | Truncates long tool outputs | Yes |
| `directory-agents-injector` | `src/hooks/directory-agents-injector/` | Event + tool.execute.before/after | Injects directory-specific agents | Yes (auto-disabled on OpenCode 1.1.37+) |
| `directory-readme-injector` | `src/hooks/directory-readme-injector/` | Event + tool.execute.before/after | Injects README context | Yes |
| `empty-task-response-detector` | `src/hooks/empty-task-response-detector/` | tool.execute.after | Detects empty task responses | Yes |
| `rules-injector` | `src/hooks/rules-injector/` | Event + tool.execute.before/after | Injects `.cursorrules`, `.claude-rules`, etc. | Yes |
| `tasks-todowrite-disabler` | `src/hooks/tasks-todowrite-disabler/` | tool.execute.before | Disables todo writes in task tool | Yes |
| `write-existing-file-guard` | `src/hooks/write-existing-file-guard/` | Event + tool.execute.before | Guards against overwriting existing files | Yes |
| `bash-file-read-guard` | `src/hooks/bash-file-read-guard/` | tool.execute.before | Guards bash commands that read files | Yes |
| `hashline-read-enhancer` | `src/hooks/hashline-read-enhancer/` | tool.execute.after | Annotates reads with LINE#ID hashes | Yes (requires `hashline_edit: true`) |
| `json-error-recovery` | `src/hooks/json-error-recovery/` | tool.execute.after | Recovers from JSON parse errors | Yes |
| `read-image-resizer` | `src/hooks/read-image-resizer/` | tool.execute.after | Resizes large images | Yes |
| `todo-description-override` | `src/hooks/todo-description-override/` | tool.execute.after | Overrides todo descriptions | Yes |
| `webfetch-redirect-guard` | `src/hooks/webfetch-redirect-guard/` | tool.execute.before/after | Guards against redirect loops | Yes |

**Transform Hooks (5 hooks):**
| Hook | File | Trigger | Behavior | Disable? |
|------|------|---------|----------|----------|
| `claude-code-hooks` | `src/hooks/claude-code-hooks/` | chat.message + event + tool.execute.before/after | Claude Code compatibility layer | Yes |
| `keyword-detector` | `src/hooks/keyword-detector/` | chat.message | Detects "ulw", "ultrawork", "plan", "@plan" | Yes |
| `context-injector-messages-transform` | `src/features/context-injector/injector.ts` | experimental.chat.messages.transform | Injects pending context into messages | **NO** |
| `thinking-block-validator` | `src/hooks/thinking-block-validator/` | experimental.chat.messages.transform | Validates thinking blocks | Yes |
| `tool-pair-validator` | `src/hooks/tool-pair-validator/` | experimental.chat.messages.transform | Validates tool call/result pairs | Yes |

#### Continuation Hooks (`src/plugin/hooks/create-continuation-hooks.ts`)
| Hook | File | Trigger | Behavior | Disable? |
|------|------|---------|----------|----------|
| `stop-continuation-guard` | `src/hooks/stop-continuation-guard/` | chat.message + event | Stops agent from continuing work | Yes |
| `compaction-context-injector` | `src/hooks/compaction-context-injector/` | experimental.session.compacting + event | Injects context during compaction | Yes |
| `compaction-todo-preserver` | `src/hooks/compaction-todo-preserver/` | experimental.session.compacting + event | Preserves todos during compaction | Yes |
| `todo-continuation-enforcer` | `src/hooks/todo-continuation-enforcer/` | Event | Forces agent to complete todos | Yes |
| `unstable-agent-babysitter` | `src/hooks/unstable-agent-babysitter/` | Event | Monitors unstable agents, auto-cancels | Yes |
| `background-notification` | `src/hooks/background-notification/` | chat.message + event | Notifies parent on background task completion | Yes |
| `atlas` | `src/hooks/atlas/` | Event + tool.execute.before/after | Atlas orchestration hook | Yes |

#### Skill Hooks (`src/plugin/hooks/create-skill-hooks.ts`)
| Hook | File | Trigger | Behavior | Disable? |
|------|------|---------|----------|----------|
| `category-skill-reminder` | `src/hooks/category-skill-reminder/` | Event + tool.execute.after | Reminds agent of available skills | Yes |
| `auto-slash-command` | `src/hooks/auto-slash-command/` | chat.message + event | Auto-executes slash commands | Yes |

### 3.2 Config Schema (`src/config/schema/oh-my-opencode-config.ts`)

Full Zod schema with these top-level fields:

```typescript
{
  $schema?: string
  new_task_system_enabled?: boolean        // Enable task system (default: false)
  default_run_agent?: string               // Default agent for `oh-my-opencode run`
  agent_definitions?: string[]             // Paths to external agent definition files
  disabled_mcps?: string[]
  disabled_agents?: string[]
  disabled_skills?: string[]
  disabled_hooks?: string[]                // CRITICAL: primary override mechanism
  disabled_commands?: string[]
  disabled_tools?: string[]                // Remove tools from LLM visibility
  mcp_env_allowlist?: string[]             // Env vars passed to MCP servers
  hashline_edit?: boolean                  // Enable hashline edit tool
  model_fallback?: boolean                 // Enable proactive model fallback
  agents?: AgentOverrides                  // Per-agent config overrides
  categories?: CategoriesConfig            // Category model delegation
  claude_code?: ClaudeCodeConfig           // Claude Code compatibility
  sisyphus_agent?: SisyphusAgentConfig     // Orchestration system config
  comment_checker?: CommentCheckerConfig
  experimental?: ExperimentalConfig        // Feature flags
  auto_update?: boolean
  skills?: SkillsConfig                    // Skill sources and overrides
  ralph_loop?: RalphLoopConfig
  runtime_fallback?: boolean | RuntimeFallbackConfig
  background_task?: BackgroundTaskConfig   // Concurrency limits
  notification?: NotificationConfig
  model_capabilities?: ModelCapabilitiesConfig
  openclaw?: OpenClawConfig                // External notifications
  babysitting?: BabysittingConfig
  git_master?: GitMasterConfig             // Git commit behavior
  browser_automation_engine?: BrowserAutomationConfig
  websearch?: WebsearchConfig
  tmux?: TmuxConfig
  sisyphus?: SisyphusConfig
  start_work?: StartWorkConfig
  _migrations?: string[]                    // Migration tracking
}
```

**Critical config fields for behavior control:**

| Field | Behavior Controlled | Overrideable? |
|-------|---------------------|---------------|
| `disabled_hooks` | Disables any of the 52 hooks | Yes |
| `disabled_tools` | Removes tools from LLM | Yes |
| `disabled_agents` | Removes agents from UI/prompts | Yes |
| `disabled_mcps` | Removes MCP servers | Yes |
| `disabled_commands` | Removes slash commands | Yes |
| `disabled_skills` | Removes skills from loading | Yes |
| `agents.{name}.prompt` | Replaces agent system prompt | Yes (supports file://) |
| `agents.{name}.prompt_append` | Appends to agent system prompt | Yes (supports file://) |
| `agents.{name}.model` | Overrides agent model | Yes |
| `agents.{name}.fallback_models` | Custom fallback chain | Yes |
| `agents.{name}.permission` | Per-tool permissions | Yes |
| `agents.{name}.tools` | Allowed tools whitelist | Yes |
| `categories` | Semantic model delegation | Yes |
| `experimental.max_tools` | Hard cap on tool count | Yes |
| `experimental.task_system` | Enable task tools | Yes |
| `experimental.aggressive_truncation` | Truncate tool outputs aggressively | Yes |
| `hashline_edit` | Enable hashline edit | Yes |
| `model_fallback` | Enable proactive fallback | Yes |
| `runtime_fallback` | Enable reactive fallback | Yes |
| `sisyphus_agent.disabled` | Disable entire orchestration | Yes |
| `claude_code.hooks` | Master switch for CC hooks | Yes |

### 3.3 Agents (`src/agents/`)

**11 built-in agents:**

| Agent | Mode | Default Model | Purpose |
|-------|------|---------------|---------|
| Sisyphus | primary | claude-opus-4-7 | Main orchestrator |
| Hephaestus | subagent | gpt-5.4 | Deep autonomous worker |
| Prometheus | subagent | claude-opus-4-7 | Planner (interview + plan generation) |
| Atlas | subagent | claude-sonnet-4-6 | Execution conductor |
| Oracle | subagent | gpt-5.4 | Architecture consultant |
| Librarian | subagent | minimax-m2.7 | External docs/OSS search |
| Explore | subagent | grok-code-fast-1 | Codebase grep/search |
| Multimodal-Looker | subagent | gpt-5.4 | Image analysis |
| Metis | subagent | claude-opus-4-7 | Plan gap analyzer |
| Momus | subagent | gpt-5.4 | Plan reviewer (high accuracy) |
| Sisyphus-Junior | subagent | inherits Atlas | Task executor (no delegation) |

**Agent mode definitions:**
- `primary`: Respects user's UI-selected model (Sisyphus, Atlas)
- `subagent`: Uses own fallback chain, ignores UI selection (all others)
- `all`: Available in both contexts

**Agent construction is hardcoded BUT overridable:**
- The factory functions (`createSisyphusAgent`, `createOracleAgent`, etc.) build prompts dynamically.
- `AgentOverrides` (from config `agents.{name}`) are applied AFTER factory construction in `builtin-agents.ts`.
- Override precedence: `agentOverrides` from config -> factory defaults.
- Protected agent names: Built-in agents cannot be overwritten by user/project/plugin agents. External agents with the same name are filtered out by `filterProtectedAgentOverrides`.

### 3.4 Tools (`src/tools/`)

**26 tools across 16 directories:**

| Tool | Source | Description |
|------|--------|-------------|
| `read`, `write`, `edit`, `multiedit` | builtinTools | File operations |
| `bash` | builtinTools | Shell execution |
| `webfetch` | builtinTools | HTTP fetching |
| `grep` | createGrepTools | Code search |
| `glob` | createGlobTools | File globbing |
| `ast_grep_search`, `ast_grep_replace` | createAstGrepTools | AST-based search/replace |
| `session_list`, `session_read`, `session_search`, `session_info` | createSessionManagerTools | Session management |
| `background_output`, `background_cancel` | createBackgroundTools | Background task control |
| `call_omo_agent` | createCallOmoAgent | Agent delegation |
| `look_at` | createLookAt | Multimodal image analysis |
| `task` | createDelegateTask | Category-based delegation |
| `skill_mcp` | createSkillMcpTool | Skill-embedded MCP execution |
| `skill` | createSkillTool | Skill execution |
| `interactive_bash` | interactive_bash | Tmux bash session |
| `task_create`, `task_get`, `task_list`, `task_update` | createTask*Tool | Task system (opt-in) |
| `edit` (hashline) | createHashlineEditTool | Hash-anchored line editing (opt-in) |
| `lsp_*` tools | LSP module | Language server integration |

**Tool pre/post processing:**
- All tool argument schemas are normalized via `normalizeToolArgSchemas()` before registration.
- `tool.execute.before` can mutate `output.args` before execution.
- `tool.execute.after` can mutate `output.title`, `output.output`, and `output.metadata` after execution.
- For `extract`/`discard` tools, after-hooks are wrapped in rollback protection.

### 3.5 MCP Integration (`src/mcp/`)

**Built-in MCPs:**

| MCP | Type | URL | Disabled? |
|-----|------|-----|-----------|
| `websearch` | Remote HTTP | Exa/Tavily via `createWebsearchConfig()` | `disabled_mcps` |
| `context7` | Remote HTTP | Fixed URL in `src/mcp/context7.ts` | `disabled_mcps` |
| `grep_app` | Remote HTTP | Fixed URL in `src/mcp/grep-app.ts` | `disabled_mcps` |

**Skill-embedded MCPs:** Managed by `SkillMcpManager` in `src/features/skill-mcp-manager/`. These are loaded per-session from SKILL.md YAML frontmatter. Connection lifecycle is tied to session lifecycle (disconnected on `session.deleted`).

### 3.6 Features (`src/features/`)

Key feature modules:

| Feature | Files | Behavior |
|---------|-------|----------|
| `background-agent` | 20+ files | Async task execution with concurrency limits, circuit breaker, task history |
| `context-injector` | `collector.ts`, `injector.ts`, `types.ts` | Collects and injects pending context into messages |
| `opencode-skill-loader` | 15+ files | Discovers and merges skills from 7 sources |
| `claude-code-plugin-loader` | 10+ files | Loads Claude Code plugins, agents, commands, MCPs |
| `skill-mcp-manager` | 5+ files | Manages skill-embedded MCP lifecycle |
| `tmux-subagent` | 25+ files | Tmux pane management for background agents |
| `team-mode` | 8+ files | Multi-agent team worktree management |
| `tool-metadata-store` | 8+ files | Persists tool call metadata across hooks |

### 3.7 Pre-defined Skills (`.opencode/skills/`)

Three built-in skills found in the repo:

1. **`work-with-pr`** (`SKILL.md`)
   - Full PR lifecycle: git worktree -> implement -> atomic commits -> PR creation -> verification loop (CI + review-work + Cubic approval) -> merge
   - Uses `task(category="quick", load_skills=["git-master"], ...)` for commits
   - Uses `task(category="unspecified-high", load_skills=["review-work"], ...)` for review

2. **`pre-publish-review`** (`SKILL.md`)
   - Pre-publish checklist and review

3. **`github-triage`** (`SKILL.md` + `scripts/gh_fetch.py`)
   - GitHub issue/PR triage automation

Skills are loaded via `discoverOpencodeProjectSkills(ctx.directory)` and merged into the agent prompt via `buildAvailableSkills()`.

---

## 4. WHAT IS CONFIGURABLE VS HARDCODED

### Fully Configurable (via `oh-my-opencode.jsonc`)

| Aspect | Config Path |
|--------|-------------|
| Disable any hook | `disabled_hooks: ["hook-name"]` |
| Disable any tool | `disabled_tools: ["tool-name"]` |
| Disable any agent | `disabled_agents: ["agent-name"]` |
| Disable any MCP | `disabled_mcps: ["mcp-name"]` |
| Disable any command | `disabled_commands: ["command-name"]` |
| Disable any skill | `disabled_skills: ["skill-name"]` |
| Override agent model | `agents.{name}.model` |
| Override agent prompt | `agents.{name}.prompt` (or `prompt_append`) |
| Override agent permissions | `agents.{name}.permission.{tool}` |
| Override agent tools whitelist | `agents.{name}.tools` |
| Custom fallback chains | `agents.{name}.fallback_models` |
| Category model delegation | `categories.{name}.model` |
| Max tools cap | `experimental.max_tools` |
| Task system | `experimental.task_system` / `new_task_system_enabled` |
| Tmux integration | `tmux.enabled` |
| Background task concurrency | `background_task.providerConcurrency` / `modelConcurrency` |
| Runtime fallback | `runtime_fallback` |
| Model fallback | `model_fallback` |
| Hashline edit | `hashline_edit` |
| OpenClaw external integration | `openclaw` |
| Comment checker | `comment_checker.custom_prompt` |
| Git behavior | `git_master` |
| Browser automation | `browser_automation_engine.provider` |

### Partially Configurable

| Aspect | Hardcoded Part | Configurable Part |
|--------|----------------|-------------------|
| System prompt | Base template structure (~80%) | `prompt`/`prompt_append` overrides |
| Tool definitions | Built-in tool schemas | `disabled_tools` filtering |
| Model capability normalization | Removal of unsupported settings | Desired settings in config |
| Agent precedence | Built-ins always loaded first | External agents override non-built-ins |
| Context injection | Injection logic and synthetic part creation | Content comes from hooks/rules |
| Hook execution order | Sequential order in handler files | Which hooks are enabled |

### Hardcoded (Cannot Be Overridden)

| Aspect | Location | Why Hardcoded |
|--------|----------|---------------|
| **Hook execution order** | `src/plugin/chat-message.ts`, `src/plugin/tool-execute-before.ts`, `src/plugin/tool-execute-after.ts` | Critical for correct behavior (e.g., file guard before execution) |
| **Sisyphus prompt base template** | `src/agents/sisyphus.ts` lines 82-467 | Core agent identity and behavior instructions |
| **Model-specific prompt mutations** | `src/agents/sisyphus.ts` (Gemini mandates, GPT-5.4 variant) | Required for model compatibility |
| **Agent mode behavior** | `src/agents/types.ts` | OpenCode runtime contract |
| **Capability normalization logic** | `src/plugin/chat-params.ts` | Prevents API errors from invalid parameters |
| **Error classification for fallback** | `src/shared/model-error-classifier.ts` | Determines which errors trigger fallback |
| **Tool output truncator thresholds** | `src/hooks/tool-output-truncator.ts` | Context window management |
| **Protected agent names** | `src/plugin-handlers/agent-override-protection.ts` | Prevents built-in agents from being corrupted |
| **Context injection (always on)** | `src/features/context-injector/injector.ts` | Not wrapped in conditional; core architecture |
| **Synthetic part format** | `src/features/context-injector/injector.ts` | UI hiding mechanism |
| **Partial config parsing keys** | `src/plugin-config.ts` `PARTIAL_STRING_ARRAY_KEYS` | Recovery mechanism |
| **Telemetry** | `src/index.ts` | Non-fatal but always attempts PostHog capture |
| **Safety guards in tool-execute-before** | Null byte stripping, subagent type resolution | Security/correctness |
| **Message-to-LLM pipeline handler order** | `src/plugin-interface.ts` | OpenCode plugin contract |

---

## 5. SAFETY/HARM CONTROLS THAT CANNOT BE OVERRIDDEN

### 5.1 Built-in Safety Controls

1. **Protected Agent Names** (`src/plugin-handlers/agent-override-protection.ts`)
   - Built-in agents (sisyphus, hephaestus, prometheus, atlas, oracle, librarian, explore, metis, momus, multimodal-looker, sisyphus-junior) cannot be overwritten by external agent definitions.
   - Attempts to define agents with these names from user/project/plugin sources are silently filtered out.
   - **Cannot be disabled.** This prevents malicious plugins from replacing the orchestrator with a compromised agent.

2. **Model Capability Normalization** (`src/plugin/chat-params.ts`)
   - Unsupported parameters are silently removed before the LLM call.
   - Example: `reasoningEffort` on Claude models is deleted.
   - **Cannot be bypassed.** This prevents API errors but also prevents forcing unsupported features.

3. **Error Recovery for Extract/Discard Tools** (`src/plugin/tool-execute-after.ts`)
   - If any after-hook fails on `extract` or `discard` tools, the original output is restored.
   - **Cannot be disabled.** Prevents data loss.

4. **Null Byte Stripping in Bash** (`src/plugin/tool-execute-before.ts`)
   - Null bytes (`\x00`) are stripped from bash commands.
   - **Cannot be disabled.** Security measure against command injection.

5. **Safe Hook Creation** (`src/shared/safe-create-hook.ts`)
   - All hooks are wrapped in try/catch. If a hook throws, it is caught and logged, but the pipeline continues.
   - Controlled by `experimental.safe_hook_creation` (default: `true`).
   - If set to `false`, hook failures could crash the plugin.

6. **Tool Schema Normalization** (`src/plugin/normalize-tool-arg-schemas.ts`)
   - All tool argument schemas are sanitized before registration.
   - **Cannot be disabled.** Prevents malformed schemas from breaking the LLM.

7. **Context Injection Always-On** (`src/features/context-injector/injector.ts`)
   - The `contextInjectorMessagesTransform` hook is created unconditionally in `createTransformHooks`.
   - It is not checked against `disabled_hooks`.
   - **Cannot be disabled.** Core to the plugin's context system.

8. **Session State Cleanup on Delete** (`src/plugin/event.ts`)
   - When `session.deleted` fires, ALL session state is unconditionally cleared:
     - Session agent, model, fallback chains, message cursors, background consumption, stop continuation, prompt params, subagent sessions, tools, LSP temp dirs, tmux panes, skill MCP connections.
   - **Cannot be bypassed.** Prevents state leakage between sessions.

9. **Anti-Duplication of Built-in Agents** (`src/plugin-handlers/agent-config-handler.ts`)
   - The `build` agent is always forced to `mode: "subagent"`, `hidden: true`.
   - The `plan` agent is demoted if `sisyphus_agent.replace_plan` is true.
   - **Cannot be overridden.** Maintains agent hierarchy integrity.

10. **Config Load Deadlock Prevention** (`src/agents/builtin-agents.ts`)
    - `createBuiltinAgents` explicitly does NOT call OpenCode client APIs during plugin initialization.
    - Comment: "Do NOT call OpenCode client APIs during plugin initialization. This function is called from config handler, and calling client API causes deadlock."
    - **Cannot be overridden.** Architectural constraint.

### 5.2 Safety-Related Hooks That Should Not Be Disabled

The documentation explicitly warns against disabling certain hooks:

- **`no-sisyphus-gpt`**: "do not disable. It blocks incompatible GPT models for Sisyphus while allowing the dedicated GPT-5.4 prompt path." Disabling this causes Sisyphus to receive the wrong prompt for its model, leading to degraded behavior.

- **`rules-injector`**: While disableable, disabling it removes `.cursorrules`, `.claude-rules`, and similar rule file injection, which may cause agents to violate project conventions.

- **`write-existing-file-guard`**: Disabling removes protection against accidental overwrites.

- **`session-recovery`**: Disabling removes automatic recovery from thinking block violations and missing tool results.

---

## 6. RECOMMENDATIONS FOR OVERRIDING BEHAVIOR

### 6.1 To Change System Prompt Behavior

**Approach 1: Append instructions (safest)**
```jsonc
{
  "agents": {
    "sisyphus": {
      "prompt_append": "Additional instructions here. Supports file:// URIs."
    }
  }
}
```

**Approach 2: Replace entire prompt (advanced)**
```jsonc
{
  "agents": {
    "sisyphus": {
      "prompt": "file:///absolute/path/to/custom-prompt.md"
    }
  }
}
```
Note: Replacing the prompt loses all dynamic sections (tool tables, delegation tables, category guides). You must rebuild these yourself if needed.

**Approach 3: Disable specific prompt-injecting hooks**
```jsonc
{
  "disabled_hooks": ["rules-injector", "directory-readme-injector"]
}
```

### 6.2 To Change Tool Availability

```jsonc
{
  "disabled_tools": ["interactive_bash", "webfetch"],
  "experimental": {
    "max_tools": 20
  }
}
```

### 6.3 To Change Model Selection Behavior

```jsonc
{
  "agents": {
    "sisyphus": {
      "model": "kimi-for-coding/k2p5",
      "fallback_models": [
        "openai/gpt-5.4",
        { "model": "anthropic/claude-opus-4-7", "variant": "max" }
      ]
    }
  },
  "categories": {
    "quick": { "model": "opencode/gpt-5-nano" }
  }
}
```

### 6.4 To Disable Unwanted Hooks

```jsonc
{
  "disabled_hooks": [
    "auto-update-checker",
    "startup-toast",
    "comment-checker",
    "agent-usage-reminder"
  ]
}
```

### 6.5 To Add Custom Agents

Place agent definition files in `agent_definitions`:
```jsonc
{
  "agent_definitions": [
    "./custom-agents/my-agent.md",
    "./custom-agents/another-agent.json"
  ]
}
```

Agent definitions support the same schema as built-in agents but cannot override protected built-in names.

### 6.6 To Control the Message-to-LLM Pipeline

The pipeline is hardcoded in `src/plugin-interface.ts`, but you can influence each stage:

| Stage | Influence Method |
|-------|-----------------|
| chat.message | `disabled_hooks` to remove keyword/think-mode/start-work effects; `agents.{name}.prompt_append` to inject instructions |
| chat.params | `agents.{name}.temperature`, `.top_p`, `.maxTokens`, `.variant`, `.reasoningEffort`, `.thinking` |
| chat.headers | Not user-configurable |
| messages.transform | `disabled_hooks` to remove thinking-block-validator, tool-pair-validator; context injection cannot be disabled |
| system.transform | Currently no-op; use `agents.{name}.prompt` instead |
| Agent config | `agents` overrides, `categories`, `disabled_agents` |
| Tool registry | `disabled_tools`, `experimental.max_tools`, agent `permission` object |
| MCP config | `disabled_mcps`, `claude_code.mcp` |
| tool.execute.before | `disabled_hooks` to remove guards |
| tool.execute.after | `disabled_hooks` to remove truncators/checkers |
| Event handler | `disabled_hooks` to remove recovery/fallback/notifications |

---

## 7. FULL HOOK POINTS AND INTERCEPTION CAPABILITIES

### 7.1 `chat.message` Hook Point

**Input:** `{ sessionID, agent?, model? }`  
**Output:** `{ message: Record<string, unknown>, parts: Array<{type, text?, ...}> }`

**What each hook can intercept:**

| Hook | Can Read | Can Mutate |
|------|----------|------------|
| `modelFallback` | input.sessionID, output.message.model | output.message.model (providerID/modelID) |
| `stopContinuationGuard` | input.sessionID | Nothing (read-only check) |
| `backgroundNotificationHook` | input.sessionID | Nothing |
| `runtimeFallback` | input.sessionID, output | output.message.model |
| `keywordDetector` | output.parts (prompt text) | output.parts[text].text (injects mode instructions) |
| `thinkMode` | output.parts | output.parts (injects think mode) |
| `claudeCodeHooks` | input, output | output.parts, output.message |
| `autoSlashCommand` | input, output | output (transforms slash commands) |
| `noSisyphusGpt` | input.agent, output.message.model | output.message.model (blocks GPT for Sisyphus) |
| `noHephaestusNonGpt` | input.agent, output.message.model | output.message.model (blocks non-GPT for Hephaestus) |
| `startWork` | output.parts | output.parts (injects work-starting template) |

### 7.2 `experimental.chat.messages.transform` Hook Point

**Input:** `{}`  
**Output:** `{ messages: Array<{info: Message, parts: Part[]}> }`

**What each hook can intercept:**

| Hook | Can Read | Can Mutate |
|------|----------|------------|
| `contextInjectorMessagesTransform` | output.messages (full history) | Last user message parts (inserts synthetic context part) |
| `thinkingBlockValidator` | output.messages | Can reject/modify thinking blocks |
| `toolPairValidator` | output.messages | Can fix tool call/result pairing |

### 7.3 `tool.execute.before` Hook Point

**Input:** `{ tool: string, sessionID: string, callID: string }`  
**Output:** `{ args: Record<string, unknown> }`

**What key hooks can mutate:**

| Hook | Can Mutate |
|------|------------|
| `writeExistingFileGuard` | output.args (blocks/modifies write args) |
| `bashFileReadGuard` | output.args (blocks bash file reads) |
| `rulesInjector` | Nothing (placeholder before hook) |
| `tasksTodowriteDisabler` | output.args (disables todo writes) |
| `prometheusMdOnly` | output.args (restricts output format) |
| `atlasHook` | output.args (orchestration logic) |

### 7.4 `tool.execute.after` Hook Point

**Input:** `{ tool, sessionID, callID }`  
**Output:** `{ title, output, metadata }`

**What key hooks can mutate:**

| Hook | Can Mutate |
|------|------------|
| `toolOutputTruncator` | output.output (truncates long outputs) |
| `commentChecker` | output.output (adds comment quality feedback) |
| `rulesInjector` | output.output (injects rule reminders) |
| `hashlineReadEnhancer` | output.output (adds LINE#ID hashes) |
| `jsonErrorRecovery` | output.output (fixes JSON errors) |
| `editErrorRecovery` | output (recovers from edit failures) |
| `delegateTaskRetry` | output (schedules retry for failed tasks) |

### 7.5 `event` Hook Point

**Input:** `{ event: { type: string, properties?: Record<string, unknown> } }`

**What key hooks intercept:**

| Event Type | Hooks Triggered | Behavior |
|------------|-----------------|----------|
| `session.created` | autoUpdateChecker, claudeCodeHooks, backgroundNotificationHook, sessionNotification, directoryAgentsInjector, directoryReadmeInjector, rulesInjector, thinkMode, ralphLoop, atlasHook, autoSlashCommand, ... | Initialization, context loading |
| `session.deleted` | All event hooks | Cleanup, state clearing |
| `session.idle` | todoContinuationEnforcer, contextWindowMonitor, preemptiveCompaction, backgroundNotificationHook, ... | Idle notifications, compaction triggers |
| `message.updated` | contextWindowMonitor, modelFallback (on assistant errors), ... | Error recovery, fallback |
| `session.error` | sessionRecovery, modelFallback, runtimeFallback, ... | Recovery or fallback |
| `session.status` | modelFallback (on retry), runtimeFallback, ... | Retry handling |

---

## 8. MEMORY / CONTEXT LOADING AND WHEN

### 8.1 Per-Session Memory

| Memory Type | Storage | Loaded When | Cleared When |
|-------------|---------|-------------|--------------|
| Session agent | `sessionAgentMap` (in-memory) | `chat.message` (setSessionAgent) | `session.deleted` |
| Session model | `sessionModelMap` (in-memory) | `chat.message` (setSessionModel) | `session.deleted` |
| Session prompt params | `sessionPromptParamsMap` (in-memory) | `chat.params` | `session.deleted` |
| Session tools | `sessionToolsStore` (in-memory) | Tool registration | `session.deleted` |
| Pending model fallback | `pendingModelFallbacks` (in-memory) | Error detection | Applied or `session.deleted` |
| Session fallback chain | `sessionFallbackChains` (in-memory) | User config or error | `session.deleted` |
| Context collector | `ContextCollector.sessions` (in-memory) | Various hooks register context | `session.deleted` or consume |
| Rules injector cache | `sessionCacheStore` + `sessionRuleScanCacheStore` (in-memory) | `tool.execute.after` (read tool) | `session.deleted`, `session.compacted` |
| Background output consumption | `backgroundOutputConsumptionMap` (in-memory) | Background task completion | `session.deleted`, `message.removed` |

### 8.2 Persistent Memory

| Memory Type | Storage | Loaded When | Saved When |
|-------------|---------|-------------|------------|
| Plugin config | JSONC files (user + project) | Plugin init | Not saved by plugin |
| Model capabilities cache | `models.dev` cache file | Startup (auto_update checker) | `refresh-model-capabilities` command |
| Task system state | `.sisyphus/tasks/` or configured path | Task tool usage | Task create/update |
| Ralph loop state | `{directory}/.ralph-loop-state.json` or `state_dir` | Loop start | Loop events |
| Boulder state (start-work) | `.sisyphus/boulder.json` | `/start-work` command | Task progress |
| Sisyphus notepads | `.sisyphus/notepads/{plan-name}/` | Atlas orchestration | Continuously |
| Prometheus plans | `.sisyphus/plans/*.md` | Prometheus interview | Plan generation |
| Agent definitions | External `.md`/`.json` files | Plugin init | External |
| Connected providers cache | In-memory + OpenCode runtime | Startup | Runtime-managed |
| Provider models cache | In-memory + OpenCode runtime | Startup | Runtime-managed |

### 8.3 Context Injection Sources

The `contextCollector` (global singleton) receives context from:

1. **Rules injector** — `.cursorrules`, `.claude-rules`, `.ai-rules`, `RULES.md`, etc. (injected after `read`/`write`/`edit`/`multiedit` tools)
2. **Directory agents injector** — `AGENTS.md` files in subdirectories
3. **Directory readme injector** — `README.md` files in subdirectories
4. **Claude Code hooks** — Claude Code plugin context
5. **Keyword detector** — Mode-specific instructions (ultrawork, plan, etc.)
6. **Think mode** — Thinking mode instructions
7. **Background notification** — Background task completion summaries
8. **Category skill reminder** — Available skills for current category
9. **Agent usage reminder** — Available agents reminder
10. **Atlas hook** — Orchestration context

All sources register with a priority (`critical`, `high`, `normal`, `low`). The collector merges them in priority order, separated by `\n\n---\n\n`.

---

## 9. CONCLUSION

OpenCode implements a **deeply instrumented** agent behavior control system with 52 lifecycle hooks, 11 agents, 26 tools, and 3 tiers of MCP integration. The architecture follows a strict pipeline model where every user message passes through 9+ control gates before reaching the LLM.

**Key takeaways for behavior modification:**

1. **The primary lever is `disabled_hooks`** — This is the most powerful config field. Disabling a hook completely removes that behavior from the pipeline.

2. **The secondary lever is `agents.{name}.prompt_append`** — This is the safest way to inject custom instructions without breaking dynamic prompt sections.

3. **The tertiary lever is `agents` and `categories` overrides** — Control model selection, permissions, and tool whitelists per agent.

4. **Hardcoded safety controls exist and are non-bypassable** — Protected agent names, capability normalization, null byte stripping, context injection, and extract/discard rollback are architectural constraints that cannot be disabled via config.

5. **The message-to-LLM pipeline is deterministic** — Hook execution order is hardcoded in `src/plugin-interface.ts` and the individual handler files. You cannot reorder hooks, only enable/disable them.

6. **Context is king** — The `ContextCollector` is the central nervous system of the plugin. It aggregates context from 10+ sources and injects it into the last user message via a synthetic part. This mechanism is always-on and cannot be disabled.

7. **Two fallback systems provide resilience** — `model-fallback` (proactive, per-agent chains) and `runtime-fallback` (reactive, error-triggered). Both are opt-in via config.

8. **Agent construction is factory-based and model-aware** — The same agent name (e.g., "sisyphus") produces different prompts and parameters depending on the resolved model (Claude, GPT, Gemini). This is hardcoded in the factory functions.

---

*End of Report*
