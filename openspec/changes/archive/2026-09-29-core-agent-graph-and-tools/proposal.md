# Proposal

## Why

To investigate alerts autonomously, the agent requires a core state graph engine configured with diagnostic system prompts, service health inspection tools, and integration with the pgvector runbook knowledge base. Establishing this core graph enables automated triage for non-sensitive incidents prior to integrating human-in-the-loop escalation gating.

## What Changes

- Define the core `AgentState` schema holding message history (`messages`).
- Bind safe diagnostic tools (`query_service_health`, `search_remediation_runbooks`) to the ChatGoogleGenerativeAI model.
- Configure system prompt instructions directing the agent to inspect service health first, search runbook documents second, and return actionable triage recommendations.
- Establish conditional tool routing between the agent reasoning node and safe tool execution nodes.
- Add an independent test suite (`tests/test_agent_graph.py`) to verify end-to-end graph execution, message normalization, and tool invocation for safe queries.

## Capabilities

### New Capabilities
- `triage-agent-graph`: Core LangGraph state graph routing, system prompt reasoning, and safe diagnostic tool integration for autonomous incident triage.

### Modified Capabilities
(None)

## Impact

- **Code**: `agent.py` core graph nodes, safe tool bindings, and system prompt logic.
- **Tools**: `query_service_health` (mock service metrics) and `search_remediation_runbooks` (pgvector retriever).
- **Tests**: `tests/test_agent_graph.py` for graph execution and tool routing verification.
