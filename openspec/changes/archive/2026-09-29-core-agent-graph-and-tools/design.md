# Design

## Context

The triage agent engine uses LangGraph `StateGraph` to manage message history and conditional tool execution loops.
`agent.py` contains the graph nodes, safe tools (`query_service_health`, `search_remediation_runbooks`), and model binding for `gemini-3.5-flash-lite` (or `gemini-1.5-flash`).

See `proposal.md` for motivation and high-level scope.

## Goals / Non-Goals

**Goals:**
- Provide a clean, robust StateGraph in `agent.py` for safe diagnostic tool execution.
- Maintain content string extraction (`extract_text`) for Gemini LLM output stability.
- Ensure conditional routing between `agent` and `safe_tools` nodes functions reliably.
- Create automated unit tests (`tests/test_agent_graph.py`) verifying graph traversal and tool responses with mocked LLM output.

**Non-Goals:**
- Implementing sensitive tool escalation gating (`escalate_ticket` interrupts - reserved for Change 3: `human-approval-gating`).
- FastAPI server routes or Gradio UI modifications.

## Decisions

### Decision 1: Graph Topology and Safe Tool Binding
**Choice:** Structure the graph with two main nodes (`agent` and `safe_tools`) connected via conditional routing `route_tools`.
- Nodes:
  - `agent`: Invokes `llm.invoke([system_prompt] + state["messages"])` and normalizes response content via `extract_text()`.
  - `safe_tools`: `ToolNode([query_service_health, search_remediation_runbooks])`.
- Edges:
  - `START` -> `agent`
  - `agent` -> `route_tools` (conditional: `safe_tools` or `END`)
  - `safe_tools` -> `agent`

### Decision 2: Content Normalization Helper (`extract_text`)
**Choice:** Maintain `extract_text(content)` helper to handle cases where Gemini returns structured content blocks (lists of dicts) rather than a flat string.
- Rationale: Prevents downstream type errors when passing message state to UI layers or Pydantic models.

### Decision 3: Graph Unit Testing Strategy (`tests/test_agent_graph.py`)
**Choice:** Mock LLM invocations using `unittest.mock.patch` on `ChatGoogleGenerativeAI.invoke`.
- Scenarios Tested:
  1. Direct text response (no tool calls) -> routes immediately to `END`.
  2. Health check tool call -> routes to `safe_tools`, executes tool, returns status string.
  3. Runbook search tool call -> routes to `safe_tools`, executes `search_remediation_runbooks`, returns runbook content.

## Risks / Trade-offs

- **[Risk] Gemini LLM Rate Limits during graph execution**: High frequency of tool call loops exceeding RPM quota.
  - **Mitigation**: System prompt directs model to minimize unnecessary tool calls and synthesize findings promptly.
- **[Risk] Unhandled tool exceptions**: Database connection errors inside `search_remediation_runbooks` crashing graph execution.
  - **Mitigation**: Exception handling inside tool implementations returning clean error messages to the model.

## Migration Plan

1. Verify `agent.py` state graph and safe tool definitions match design requirements.
2. Add `tests/test_agent_graph.py` testing graph node routing and safe tool execution.
3. Run `python -m unittest tests/test_agent_graph.py` to verify test suite passes.
